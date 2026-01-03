import asyncio
import sys
import json
sys.path.insert(0, 'src')

from freedium_library.services.medium.api import MediumApiService
from freedium_library.services.medium.config import MediumConfig
from freedium_library.utils.http.client.curl import CurlRequest
from freedium_library.utils import JSON

async def main():
    config = MediumConfig()
    async with CurlRequest() as request:
        api = MediumApiService(request, config)

        # Get raw response
        response = await request.apost(
            "https://medium.com/_/graphql",
            headers={
                "X-APOLLO-OPERATION-ID": "test",
                "X-APOLLO-OPERATION-NAME": "FullPostQuery",
                "Accept": "multipart/mixed; deferSpec=20220824, application/json, application/json",
                "Accept-Language": "en-US",
                "X-Obvious-CID": "android",
                "X-Xsrf-Token": "1",
                "X-Client-Date": "1704279600000",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X)",
                "Cache-Control": "public, max-age=-1",
                "Content-Type": "application/json",
            },
            data={
                "operationName": "FullPostQuery",
                "variables": {
                    "postId": "9dc802a10618",
                    "postMeteringOptions": {},
                },
                "query": "query FullPostQuery($postId: ID!, $postMeteringOptions: PostMeteringOptions) { post(id: $postId) { __typename id title detectedLanguage mediumUrl latestPublishedVersion firstPublishedAt updatedAt allowResponses isLocked isProxyPost isSeries canonicalUrl creator { id name username imageId bio twitterScreenName } collection { id name slug shortDescription } content(postMeteringOptions: $postMeteringOptions) { bodyModel { __typename } } previewContent { subtitle } } }",
            },
        )

        response_data = JSON.loads(response.text)

        # Save to file
        with open("graphql_response.json", "w") as f:
            json.dump(response_data, f, indent=2)

        print(f"Saved response to graphql_response.json")
        print(f"Response keys: {list(response_data.keys())}")
        if 'data' in response_data and 'post' in response_data['data']:
            print(f"Post keys: {list(response_data['data']['post'].keys())}")

if __name__ == "__main__":
    asyncio.run(main())
