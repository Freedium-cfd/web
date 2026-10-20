from __future__ import annotations

import asyncio
import base64
from typing import TYPE_CHECKING, Any

from beartype import beartype
from loguru import logger

from freedium_library.api.metrics import CACHE_HITS, CACHE_MISSES
from freedium_library.utils import JSON
from freedium_library.utils.hash import HashLib
from freedium_library.utils.json import json as _json
from freedium_library.utils.time import get_unix_ms

from .models import GraphQLPost

if TYPE_CHECKING:
    from freedium_library.services.medium.config import MediumConfig
    from freedium_library.utils.cache.db.mongo import AsyncMongoDBCacheBackend
    from freedium_library.utils.http import CurlRequest


_GRAPHQL_RETRY_BACKOFFS: tuple[float, ...] = (0.5, 1.5)  # delays before retry 2 and 3

_RETRY_USER_AGENTS = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1 (compatible; YandexMobileBot/3.0;",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
)

_RETRY_CLIENT_NAMES = ("android", "ios", "web")


def resolve_graphql_references(data: Any, root_data: dict[str, Any]) -> Any:
    """
    Recursively resolve GraphQL __ref references in the data structure.

    Args:
        data: The data structure to resolve (dict, list, or primitive)
        root_data: The root GraphQL response data containing all entities

    Returns:
        The data with all __ref references resolved to actual objects
    """
    if isinstance(data, dict):
        # Check if this is a reference object
        if "__ref" in data and len(data) == 1:  # type: ignore[arg-type]
            ref_key: str = data["__ref"]  # type: ignore[assignment]
            logger.trace(f"Resolving reference: {ref_key}")

            # Look up the reference in root_data
            if ref_key in root_data:
                resolved: Any = root_data[ref_key]
                logger.trace(f"Found referenced object: {ref_key}")
                # Recursively resolve any references in the resolved object
                return resolve_graphql_references(resolved, root_data)  # type: ignore[return-value]
            else:
                logger.warning(f"Could not find referenced object: {ref_key}")
                return data  # type: ignore[return-value]

        # Not a reference, recursively process all values
        result: dict[str, Any] = {k: resolve_graphql_references(v, root_data) for k, v in data.items()}  # type: ignore[misc]
        return result

    elif isinstance(data, list):
        # Recursively process list items
        result_list: list[Any] = [resolve_graphql_references(item, root_data) for item in data]  # type: ignore[misc]
        return result_list

    else:
        # Primitive value, return as-is
        return data


class MediumApiService:
    def __init__(
        self,
        request: CurlRequest,
        config: MediumConfig,
        cache: "AsyncMongoDBCacheBackend | None" = None,
    ):
        self.request = request
        self.config = config
        self.cache = cache

    async def query_post_by_id(
        self, post_id: str
    ) -> GraphQLPost | dict | None:
        """Post fetch with Mongo cache in front of Medium.

        On hit, deserialize stored JSON and return without touching Medium.
        On miss/disabled, hit Medium then write back (failures non-fatal).
        Read/write failures fall through to Medium and never break callers.
        """
        logger.debug("Using graphql implementation")

        if self.cache is not None:
            try:
                cached = await self.cache.apull(post_id)
            except Exception as ex:  # noqa: BLE001 — cache read errors must not break render
                logger.warning(f"Cache read failed for {post_id}: {ex}; falling through to Medium")
                cached = None

            if cached is not None:
                try:
                    envelope = _json.loads(cached.value)
                    CACHE_HITS.inc()
                    # Envelope distinguishes model dumps from raw dicts so we
                    # can rehydrate accurately. Legacy/unknown payloads are
                    # returned as-is.
                    if isinstance(envelope, dict) and "_shape" in envelope:
                        if envelope["_shape"] == "model":
                            return GraphQLPost.model_validate(envelope["data"])
                        return envelope["data"]
                    return envelope
                except Exception as ex:  # noqa: BLE001
                    logger.warning(f"Cache deserialize failed for {post_id}: {ex}; falling through to Medium")

        CACHE_MISSES.inc()
        result = await self.query_post_graphql(post_id)

        if self.cache is not None and result is not None:
            try:
                if isinstance(result, GraphQLPost):
                    envelope = {"_shape": "model", "data": result.model_dump(mode="json")}
                elif isinstance(result, dict):
                    envelope = {"_shape": "dict", "data": result}
                else:
                    envelope = None
                if envelope is not None:
                    from freedium_library.tasks.cache import write_graphql_cache
                    serialized = _json.dumps(envelope)
                    try:
                        await write_graphql_cache.kiq(post_id, serialized if isinstance(serialized, str) else serialized.decode())
                    except Exception:
                        # Broker down — write synchronously as fallback
                        await self.cache.apush(post_id, envelope)
            except Exception as ex:  # noqa: BLE001 — cache write errors must not break render
                logger.warning(f"Cache write failed for {post_id}: {ex}")

        return result

    @beartype
    async def query_post_graphql(
        self, post_id: str
    ) -> GraphQLPost | None:
        logger.debug(f"Starting graphql request construction for post {post_id}")

        headers = {
            "X-APOLLO-OPERATION-ID": HashLib.random_sha256(),
            "X-APOLLO-OPERATION-NAME": "FullPostQuery",
            "Accept": "multipart/mixed; deferSpec=20220824, application/json, application/json",
            "Accept-Language": "en-US",
            "X-Obvious-CID": "android",
            "X-Xsrf-Token": "1",
            "X-Client-Date": str(get_unix_ms()),
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1 (compatible; YandexMobileBot/3.0;",
            "Cache-Control": "public, max-age=-1",
            "Content-Type": "application/json",
            "Connection": "Keep-Alive",
        }

        if self.config.cookies is not None:
            headers["Cookie"] = self.config.cookies

        graphql_data: dict[str, Any] = {
            "operationName": "FullPostQuery",
            "variables": {
                "postId": post_id,
                "postMeteringOptions": {},
            },
            "query": "query FullPostQuery($postId: ID!, $postMeteringOptions: PostMeteringOptions) { post(id: $postId) { __typename id ...FullPostData } meterPost(postId: $postId, postMeteringOptions: $postMeteringOptions) { __typename ...MeteringInfoData } }  fragment UserFollowData on User { id socialStats { followingCount followerCount } viewerEdge { isFollowing } }  fragment NewsletterData on NewsletterV3 { id viewerEdge { id isSubscribed } }  fragment UserNewsletterData on User { id newsletterV3 { __typename ...NewsletterData } }  fragment ImageMetadataData on ImageMetadata { id originalWidth originalHeight focusPercentX focusPercentY alt }  fragment CollectionFollowData on Collection { id subscriberCount viewerEdge { isFollowing } }  fragment CollectionNewsletterData on Collection { id newsletterV3 { __typename ...NewsletterData } }  fragment BylineData on Post { id readingTime creator { __typename id imageId username name bio tippingLink viewerEdge { isUser } ...UserFollowData ...UserNewsletterData } collection { __typename id name avatar { __typename id ...ImageMetadataData } ...CollectionFollowData ...CollectionNewsletterData } isLocked firstPublishedAt latestPublishedVersion }  fragment ResponseCountData on Post { postResponses { count } }  fragment InResponseToPost on Post { id title creator { name } clapCount responsesCount isLocked }  fragment PostVisibilityData on Post { id collection { viewerEdge { isEditor canEditPosts canEditOwnPosts } } creator { id } isLocked visibility }  fragment PostMenuData on Post { id title creator { __typename ...UserFollowData } collection { __typename ...CollectionFollowData } }  fragment PostMetaData on Post { __typename id title visibility ...ResponseCountData clapCount viewerEdge { clapCount } detectedLanguage mediumUrl readingTime updatedAt isLocked allowResponses isProxyPost latestPublishedVersion isSeries firstPublishedAt previewImage { id } inResponseToPostResult { __typename ...InResponseToPost } inResponseToMediaResource { mediumQuote { startOffset endOffset paragraphs { text type markups { type start end anchorType } } } } inResponseToEntityType canonicalUrl collection { id slug name shortDescription avatar { __typename id ...ImageMetadataData } viewerEdge { isFollowing isEditor canEditPosts canEditOwnPosts isMuting } } creator { id isFollowing name bio imageId mediumMemberAt twitterScreenName viewerEdge { isBlocking isMuting isUser } } previewContent { subtitle } pinnedByCreatorAt ...PostVisibilityData ...PostMenuData }  fragment LinkMetadataList on Post { linkMetadataList { url alts { type url } } }  fragment MediaResourceData on MediaResource { id iframeSrc thumbnailUrl iframeHeight iframeWidth title }  fragment IframeData on Iframe { iframeHeight iframeWidth mediaResource { __typename ...MediaResourceData } }  fragment MarkupData on Markup { name type start end href title rel type anchorType userId creatorIds }  fragment CatalogSummaryData on Catalog { id name description type visibility predefined responsesLocked creator { id name username imageId bio viewerEdge { isUser } } createdAt version itemsLastInsertedAt postItemsCount }  fragment CatalogPreviewData on Catalog { __typename ...CatalogSummaryData id itemsConnection(pagingOptions: { limit: 10 } ) { items { entity { __typename ... on Post { id previewImage { id } } } } paging { count } } }  fragment MixtapeMetadataData on MixtapeMetadata { mediaResourceId href thumbnailImageId mediaResource { mediumCatalog { __typename ...CatalogPreviewData } } }  fragment ParagraphData on Paragraph { id name href text iframe { __typename ...IframeData } layout markups { __typename ...MarkupData } metadata { __typename ...ImageMetadataData } mixtapeMetadata { __typename ...MixtapeMetadataData } type hasDropCap dropCapImage { __typename ...ImageMetadataData } codeBlockMetadata { lang mode } }  fragment QuoteData on Quote { id postId userId startOffset endOffset paragraphs { __typename id ...ParagraphData } quoteType }  fragment HighlightsData on Post { id highlights { __typename ...QuoteData } }  fragment PostFooterCountData on Post { __typename id clapCount viewerEdge { clapCount } ...ResponseCountData responsesLocked mediumUrl title collection { id viewerEdge { isMuting isFollowing } } creator { id viewerEdge { isMuting isFollowing } } }  fragment TagNoViewerEdgeData on Tag { id normalizedTagSlug displayTitle followerCount postCount }  fragment VideoMetadataData on VideoMetadata { videoId previewImageId originalWidth originalHeight }  fragment SectionData on Section { name startIndex textLayout imageLayout videoLayout backgroundImage { __typename ...ImageMetadataData } backgroundVideo { __typename ...VideoMetadataData } }  fragment PostBodyData on RichText { sections { __typename ...SectionData } paragraphs { __typename id ...ParagraphData } }  fragment FullPostData on Post { __typename ...BylineData ...PostMetaData ...LinkMetadataList ...HighlightsData ...PostFooterCountData tags { __typename id ...TagNoViewerEdgeData } content(postMeteringOptions: $postMeteringOptions) { bodyModel { __typename ...PostBodyData } validatedShareKey } }  fragment MeteringInfoData on MeteringInfo { maxUnlockCount unlocksRemaining postIds }",
        }

        response_data: dict[str, Any] | None = None
        url = "https://medium.com/_/graphql"

        logger.debug("GraphQL request started...")

        # Retry transient WARP/Medium failures. Three distinct failure modes
        # observed in production, all transient (recover on a later attempt):
        #   1. status 0 / connection reset through the WARP SOCKS tunnel
        #   2. non-200 status
        #   3. HTTP 200 but data.post == null — Medium soft-blocking the shared
        #      WARP exit IP (it returns null instead of 429)
        # Intermediate attempts log at DEBUG; we only ERROR once all attempts
        # are exhausted, and INFO when a retry recovers — so a successful
        # render never leaves a scary WARNING/ERROR behind.
        last_reason = "no response"
        has_soft_block = False
        for attempt in range(3):
            # Rotate headers and client identities across retries
            req_headers = dict(headers)
            req_headers["User-Agent"] = _RETRY_USER_AGENTS[attempt % len(_RETRY_USER_AGENTS)]
            req_headers["X-Obvious-CID"] = _RETRY_CLIENT_NAMES[attempt % len(_RETRY_CLIENT_NAMES)]
            req_headers["X-APOLLO-OPERATION-ID"] = HashLib.random_sha256()

            try:
                async with self.request as request:
                    response = await request.apost(url, headers=req_headers, data=graphql_data)
                if response.status_code != 200:
                    last_reason = f"status {response.status_code}"
                    if response.status_code in (403, 429, 502, 503):
                        has_soft_block = True
                else:
                    try:
                        parsed = JSON.loads(response.text)
                    except Exception as ex:
                        parsed = None
                        last_reason = f"invalid JSON ({ex})"
                    if parsed is not None and ((parsed.get("data") or {}).get("post")) is not None:
                        response_data = parsed
                        if attempt > 0:
                            logger.info(
                                f"GraphQL for {post_id} recovered on attempt {attempt + 1}/3"
                            )
                        break
                    elif parsed is not None:
                        last_reason = "HTTP 200 with null post (Medium soft-block)"
                        has_soft_block = True
            except Exception as ex:  # connection-level failure through WARP, etc.
                last_reason = f"{type(ex).__name__}: {ex}"
            logger.debug(f"GraphQL attempt {attempt + 1}/3 for {post_id}: {last_reason}")
            if attempt < 2:
                await asyncio.sleep(_GRAPHQL_RETRY_BACKOFFS[attempt])

        if response_data is None:
            logger.error(
                f"Failed to fetch post by ID {post_id} after 3 attempts ({last_reason})"
            )
            if has_soft_block:
                from .exceptions import MediumBlockedError

                raise MediumBlockedError(f"Medium temporarily soft-blocked egress IP ({last_reason})")
            return None

        logger.debug("GraphQL request finished...")

        # Resolve __ref references in the response data before Pydantic parsing
        # This ensures mediaResource references in iframes are properly resolved
        try:
            post_data = response_data["data"]["post"]
            # Resolve references using the full response_data["data"] as the lookup source
            resolved_post_data = resolve_graphql_references(post_data, response_data.get("data", {}))
            logger.debug("Successfully resolved GraphQL references")
        except Exception as e:
            logger.warning(f"Failed to resolve GraphQL references: {e}, continuing with unresolved data")
            resolved_post_data = response_data["data"]["post"]

        # Parse GraphQL response - Pydantic will handle validation
        try:
            graphql_post = GraphQLPost.model_validate(resolved_post_data)
            logger.debug(f"Successfully parsed GraphQL post: {graphql_post.id}")
            return graphql_post
        except (KeyError, TypeError) as e:
            logger.error(f"Invalid GraphQL response structure for post {post_id}: {e}")
            logger.debug(f"Response data: {response_data}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse GraphQL post {post_id}: {e}")
            return None

    async def query_post_api(
        self, post_id: str
    ) -> GraphQLPost | None:
        raise RuntimeError(
            "query_post_api is deprecated and no longer supported. Use query_post_graphql instead."
        )

    @beartype
    async def fetch_iframe_content(self, iframe_id: str) -> str:
        """
        Fetch iframe content from Medium's media endpoint.

        Args:
            iframe_id: The Medium iframe/media ID

        Returns:
            The HTML content of the iframe
        """
        logger.debug(f"Fetching iframe content for ID: {iframe_id}")

        url = f"https://medium.com/media/{iframe_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        try:
            async with self.request as request:
                response = await request.aget(url, headers=headers)

                logger.debug(f"Iframe response status code: {response.status_code}")

                if response.status_code != 200:
                    logger.error(
                        f"Failed to fetch iframe {iframe_id}\n"
                        f"Status code: {response.status_code}\n"
                        f"Response: {response.text[:500]}"
                    )
                    return ""

                return response.text

        except Exception as ex:
            logger.error(f"Request failed for iframe {iframe_id}: {ex}")
            logger.exception(ex)
            return ""

    @beartype
    async def fetch_image_as_base64(self, image_url: str) -> str | None:
        """
        Fetch image from URL and encode as base64 data URI.

        Uses the existing HTTP client to fetch the image, respecting proxy settings
        and connection pooling. Automatically detects content type from response headers.

        Args:
            image_url: The URL of the image to fetch

        Returns:
            A complete data URI string (e.g., "data:image/jpeg;base64,...") or None if fetch fails
        """
        logger.debug(f"Fetching image as base64 from URL: {image_url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "image/*,*/*;q=0.8",
        }

        try:
            async with self.request as request:
                response = await request.aget(image_url, headers=headers)

                logger.debug(f"Image fetch response status code: {response.status_code}")

                if response.status_code != 200:
                    logger.warning(
                        f"Failed to fetch image from {image_url}\n"
                        f"Status code: {response.status_code}"
                    )
                    return None

                # Get content type from response headers
                content_type = response.headers.get("Content-Type", "image/jpeg")
                # Handle cases where content type includes charset or other params
                if ";" in content_type:
                    content_type = content_type.split(";")[0].strip()

                # Encode binary content as base64
                b64_data = base64.b64encode(response.content).decode("utf-8")
                data_uri = f"data:{content_type};base64,{b64_data}"

                logger.debug(f"Successfully encoded image as base64 (size: {len(b64_data)} chars)")
                return data_uri

        except Exception as ex:
            logger.warning(f"Request failed for image {image_url}: {ex}")
            return None
