from __future__ import annotations

from typing import TYPE_CHECKING, Any

from beartype import beartype
from loguru import logger

from freedium_library.utils import JSON
from freedium_library.utils.hash import HashLib
from freedium_library.utils.time import get_unix_ms

from .models import GraphQLPost

if TYPE_CHECKING:
    from freedium_library.services.medium.config import MediumConfig
    from freedium_library.utils.http import CurlRequest


class MediumApiService:
    def __init__(
        self,
        request: CurlRequest,
        config: MediumConfig,
    ):
        self.request = request
        self.config = config

    @beartype
    async def query_post_by_id(
        self, post_id: str
    ) -> GraphQLPost | None:
        logger.debug("Using graphql implementation")
        return await self.query_post_graphql(post_id)

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

        graphql_data = {
            "operationName": "FullPostQuery",
            "variables": {
                "postId": post_id,
                "postMeteringOptions": {},
            },
            "query": "query FullPostQuery($postId: ID!, $postMeteringOptions: PostMeteringOptions) { post(id: $postId) { __typename id ...FullPostData } meterPost(postId: $postId, postMeteringOptions: $postMeteringOptions) { __typename ...MeteringInfoData } }  fragment UserFollowData on User { id socialStats { followingCount followerCount } viewerEdge { isFollowing } }  fragment NewsletterData on NewsletterV3 { id viewerEdge { id isSubscribed } }  fragment UserNewsletterData on User { id newsletterV3 { __typename ...NewsletterData } }  fragment ImageMetadataData on ImageMetadata { id originalWidth originalHeight focusPercentX focusPercentY alt }  fragment CollectionFollowData on Collection { id subscriberCount viewerEdge { isFollowing } }  fragment CollectionNewsletterData on Collection { id newsletterV3 { __typename ...NewsletterData } }  fragment BylineData on Post { id readingTime creator { __typename id imageId username name bio tippingLink viewerEdge { isUser } ...UserFollowData ...UserNewsletterData } collection { __typename id name avatar { __typename id ...ImageMetadataData } ...CollectionFollowData ...CollectionNewsletterData } isLocked firstPublishedAt latestPublishedVersion }  fragment ResponseCountData on Post { postResponses { count } }  fragment InResponseToPost on Post { id title creator { name } clapCount responsesCount isLocked }  fragment PostVisibilityData on Post { id collection { viewerEdge { isEditor canEditPosts canEditOwnPosts } } creator { id } isLocked visibility }  fragment PostMenuData on Post { id title creator { __typename ...UserFollowData } collection { __typename ...CollectionFollowData } }  fragment PostMetaData on Post { __typename id title visibility ...ResponseCountData clapCount viewerEdge { clapCount } detectedLanguage mediumUrl readingTime updatedAt isLocked allowResponses isProxyPost latestPublishedVersion isSeries firstPublishedAt previewImage { id } inResponseToPostResult { __typename ...InResponseToPost } inResponseToMediaResource { mediumQuote { startOffset endOffset paragraphs { text type markups { type start end anchorType } } } } inResponseToEntityType canonicalUrl collection { id slug name shortDescription avatar { __typename id ...ImageMetadataData } viewerEdge { isFollowing isEditor canEditPosts canEditOwnPosts isMuting } } creator { id isFollowing name bio imageId mediumMemberAt twitterScreenName viewerEdge { isBlocking isMuting isUser } } previewContent { subtitle } pinnedByCreatorAt ...PostVisibilityData ...PostMenuData }  fragment LinkMetadataList on Post { linkMetadataList { url alts { type url } } }  fragment MediaResourceData on MediaResource { id iframeSrc thumbnailUrl iframeHeight iframeWidth title }  fragment IframeData on Iframe { iframeHeight iframeWidth mediaResource { __typename ...MediaResourceData } }  fragment MarkupData on Markup { name type start end href title rel type anchorType userId creatorIds }  fragment CatalogSummaryData on Catalog { id name description type visibility predefined responsesLocked creator { id name username imageId bio viewerEdge { isUser } } createdAt version itemsLastInsertedAt postItemsCount }  fragment CatalogPreviewData on Catalog { __typename ...CatalogSummaryData id itemsConnection(pagingOptions: { limit: 10 } ) { items { entity { __typename ... on Post { id previewImage { id } } } } paging { count } } }  fragment MixtapeMetadataData on MixtapeMetadata { mediaResourceId href thumbnailImageId mediaResource { mediumCatalog { __typename ...CatalogPreviewData } } }  fragment ParagraphData on Paragraph { id name href text iframe { __typename ...IframeData } layout markups { __typename ...MarkupData } metadata { __typename ...ImageMetadataData } mixtapeMetadata { __typename ...MixtapeMetadataData } type hasDropCap dropCapImage { __typename ...ImageMetadataData } codeBlockMetadata { lang mode } }  fragment QuoteData on Quote { id postId userId startOffset endOffset paragraphs { __typename id ...ParagraphData } quoteType }  fragment HighlightsData on Post { id highlights { __typename ...QuoteData } }  fragment PostFooterCountData on Post { __typename id clapCount viewerEdge { clapCount } ...ResponseCountData responsesLocked mediumUrl title collection { id viewerEdge { isMuting isFollowing } } creator { id viewerEdge { isMuting isFollowing } } }  fragment TagNoViewerEdgeData on Tag { id normalizedTagSlug displayTitle followerCount postCount }  fragment VideoMetadataData on VideoMetadata { videoId previewImageId originalWidth originalHeight }  fragment SectionData on Section { name startIndex textLayout imageLayout videoLayout backgroundImage { __typename ...ImageMetadataData } backgroundVideo { __typename ...VideoMetadataData } }  fragment PostBodyData on RichText { sections { __typename ...SectionData } paragraphs { __typename id ...ParagraphData } }  fragment FullPostData on Post { __typename ...BylineData ...PostMetaData ...LinkMetadataList ...HighlightsData ...PostFooterCountData tags { __typename id ...TagNoViewerEdgeData } content(postMeteringOptions: $postMeteringOptions) { bodyModel { __typename ...PostBodyData } validatedShareKey } }  fragment MeteringInfoData on MeteringInfo { maxUnlockCount unlocksRemaining postIds }",
        }

        response_data: dict[str, Any] | None = None
        exception: Exception | None = None
        url = "https://medium.com/_/graphql"

        logger.debug("GraphQL request started...")

        try:
            async with self.request as request:
                response = await request.apost(url, headers=headers, data=graphql_data)

                logger.debug(f"Response status code: {response.status_code}")

                if response.status_code != 200:
                    logger.error(
                        f"Failed to fetch post by ID {post_id}\n"
                        f"Status code: {response.status_code}\n"
                        f"Response: {response.text[:500]}"
                    )
                    return None

                try:
                    response_data = JSON.loads(response.text)
                except Exception as ex:
                    logger.error(f"Failed to parse response as JSON: {ex}")
                    logger.debug(f"Response text: {response.text[:500]}")
                    exception = ex

        except Exception as ex:
            logger.error(f"Request failed for post {post_id}: {ex}")
            logger.exception(ex)
            return None

        logger.debug("GraphQL request finished...")

        if exception:
            logger.error(
                f"Exception occurred while fetching post {post_id}, so let's just fuck it up"
            )
            raise exception

        if response_data is None:
            logger.warning(f"Response data is None for post {post_id}")
            return None

        # Parse GraphQL response directly - let Pydantic handle validation
        try:
            graphql_post = GraphQLPost.model_validate(response_data["data"]["post"])
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
