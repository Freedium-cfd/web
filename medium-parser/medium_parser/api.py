import random
from typing import List, Optional

from curl_cffi.requests import AsyncSession
from loguru import logger

from medium_parser.time import get_unix_ms
from medium_parser.utils import generate_random_sha256_hash


class MediumApi:
    __slots__ = ("auth_cookies", "proxy_list", "timeout")

    def __init__(
        self,
        auth_cookies: Optional[str] = None,
        proxy_list: Optional[List[str]] = None,
        timeout: int = 3,
    ):
        self.auth_cookies = auth_cookies
        self.proxy_list = proxy_list
        self.timeout = timeout

    async def query_post_by_id(self, post_id: str):
        logger.debug("Using graphql implementation")
        return await self.query_post_graphql(post_id)

    async def query_post_graphql(self, post_id: str):
        logger.debug(f"Starting request construction for post {post_id}")

        proxy = None
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            logger.debug(f"Using proxy: {proxy}")

        headers = {
            "X-APOLLO-OPERATION-ID": generate_random_sha256_hash(),
            "X-APOLLO-OPERATION-NAME": "FullPostQuery",
            "Accept": "multipart/mixed; deferSpec=20220824, application/json, application/json",
            "Accept-Language": "en-US",
            "X-Obvious-CID": "android",
            "X-Xsrf-Token": "1",
            "X-Client-Date": str(get_unix_ms()),
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1 (compatible; YandexMobileBot/3.0;",  # "donkey/4.5.1187420",  # <---- There is Medium version
            "Cache-Control": "public, max-age=-1",
            "Content-Type": "application/json",
            "Connection": "Keep-Alive",
        }

        if self.auth_cookies is not None:
            headers["Cookie"] = self.auth_cookies

        graphql_data = {
            "operationName": "FullPostQuery",
            "variables": {
                "postId": post_id,
                "postMeteringOptions": {},
            },
"query": "query FullPostQuery($postId: ID!, $postMeteringOptions: PostMeteringOptions) { post(id: $postId) { __typename id ...FullPostData } meterPost(postId: $postId, postMeteringOptions: $postMeteringOptions) { __typename ...MeteringInfoData } }  fragment UserFollowData on User { id socialStats { followingCount followerCount } viewerEdge { isFollowing } }  fragment NewsletterData on NewsletterV3 { id viewerEdge { id isSubscribed } }  fragment UserNewsletterData on User { id newsletterV3 { __typename ...NewsletterData } }  fragment ImageMetadataData on ImageMetadata { id originalWidth originalHeight focusPercentX focusPercentY alt }  fragment CollectionFollowData on Collection { id subscriberCount viewerEdge { isFollowing } }  fragment CollectionNewsletterData on Collection { id newsletterV3 { __typename ...NewsletterData } }  fragment BylineData on Post { id readingTime creator { __typename id imageId username name bio tippingLink viewerEdge { isUser } ...UserFollowData ...UserNewsletterData } collection { __typename id name avatar { __typename id ...ImageMetadataData } ...CollectionFollowData ...CollectionNewsletterData } isLocked firstPublishedAt latestPublishedVersion }  fragment ResponseCountData on Post { postResponses { count } }  fragment InResponseToPost on Post { id title creator { name } clapCount responsesCount isLocked }  fragment PostVisibilityData on Post { id collection { viewerEdge { isEditor canEditPosts canEditOwnPosts } } creator { id } isLocked visibility }  fragment PostMenuData on Post { id title creator { __typename ...UserFollowData } collection { __typename ...CollectionFollowData } }  fragment PostMetaData on Post { __typename id title visibility ...ResponseCountData clapCount viewerEdge { clapCount } detectedLanguage mediumUrl readingTime updatedAt isLocked allowResponses isProxyPost latestPublishedVersion isSeries firstPublishedAt previewImage { id } inResponseToPostResult { __typename ...InResponseToPost } inResponseToMediaResource { mediumQuote { startOffset endOffset paragraphs { text type markups { type start end anchorType } } } } inResponseToEntityType canonicalUrl collection { id slug name shortDescription avatar { __typename id ...ImageMetadataData } viewerEdge { isFollowing isEditor canEditPosts canEditOwnPosts isMuting } } creator { id isFollowing name bio imageId mediumMemberAt twitterScreenName viewerEdge { isBlocking isMuting isUser } } previewContent { subtitle } pinnedByCreatorAt ...PostVisibilityData ...PostMenuData }  fragment LinkMetadataList on Post { linkMetadataList { url alts { type url } } }  fragment MediaResourceData on MediaResource { id iframeSrc thumbnailUrl iframeHeight iframeWidth title }  fragment IframeData on Iframe { iframeHeight iframeWidth mediaResource { __typename ...MediaResourceData } }  fragment MarkupData on Markup { name type start end href title rel type anchorType userId creatorIds }  fragment CatalogSummaryData on Catalog { id name description type visibility predefined responsesLocked creator { id name username imageId bio viewerEdge { isUser } } createdAt version itemsLastInsertedAt postItemsCount }  fragment CatalogPreviewData on Catalog { __typename ...CatalogSummaryData id itemsConnection(pagingOptions: { limit: 10 } ) { items { entity { __typename ... on Post { id previewImage { id } } } } paging { count } } }  fragment MixtapeMetadataData on MixtapeMetadata { mediaResourceId href thumbnailImageId mediaResource { mediumCatalog { __typename ...CatalogPreviewData } } }  fragment ParagraphData on Paragraph { id name href text iframe { __typename ...IframeData } layout markups { __typename ...MarkupData } metadata { __typename ...ImageMetadataData } mixtapeMetadata { __typename ...MixtapeMetadataData } type hasDropCap dropCapImage { __typename ...ImageMetadataData } codeBlockMetadata { lang mode } }  fragment QuoteData on Quote { id postId userId startOffset endOffset paragraphs { __typename id ...ParagraphData } quoteType }  fragment HighlightsData on Post { id highlights { __typename ...QuoteData } }  fragment PostFooterCountData on Post { __typename id clapCount viewerEdge { clapCount } ...ResponseCountData responsesLocked mediumUrl title collection { id viewerEdge { isMuting isFollowing } } creator { id viewerEdge { isMuting isFollowing } } }  fragment TagNoViewerEdgeData on Tag { id normalizedTagSlug displayTitle followerCount postCount }  fragment VideoMetadataData on VideoMetadata { videoId previewImageId originalWidth originalHeight }  fragment SectionData on Section { name startIndex textLayout imageLayout videoLayout backgroundImage { __typename ...ImageMetadataData } backgroundVideo { __typename ...VideoMetadataData } }  fragment PostBodyData on RichText { sections { __typename ...SectionData } paragraphs { __typename id ...ParagraphData } }  fragment FullPostData on Post { __typename ...BylineData ...PostMetaData ...LinkMetadataList ...HighlightsData ...PostFooterCountData tags { __typename id ...TagNoViewerEdgeData } content(postMeteringOptions: $postMeteringOptions) { bodyModel { __typename ...PostBodyData } validatedShareKey } }  fragment MeteringInfoData on MeteringInfo { maxUnlockCount unlocksRemaining postIds }",
        }

        response_data = None
        exception = None

        logger.debug("Request started...")

        try:
            async with AsyncSession() as session:
                response = await session.post(
                    "https://medium.com/_/graphql",
                    headers=headers,
                    json=graphql_data,
                    proxies={"http": proxy, "https": proxy} if proxy else None,
                    timeout=self.timeout,
                    impersonate="chrome110",
                )

                if response.status_code != 200:
                    logger.error(
                        f"Failed to fetch post by ID {post_id} with status code: {response.status_code}, response: {response.text}"
                    )
                    return None

                response_data = response.json()
                with open("/app/web/sidufh.json", "wb") as file:
                    file.write(response.content)

        except Exception as ex:
            logger.debug("Failed to make request or parse response")
            logger.exception(ex)
            exception = ex

        logger.debug("Request finished...")

        if exception:
            logger.error(
                f"Exception occurred while fetching post {post_id}, so let's just fuck it up"
            )
            raise exception

        return response_data
