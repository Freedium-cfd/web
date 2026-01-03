from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from freedium_library.utils import JSON

from .models import MediumPostDataResponse

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

    async def query_post_by_id(
        self, post_id: str
    ) -> MediumPostDataResponse | None:
        logger.debug("Using post api implementation")
        return await self.query_post_api(post_id)

    async def query_post_graphql(
        self, post_id: str
    ) -> MediumPostDataResponse | None:
        logger.debug("Graphql fetch is deprecated, using post api")
        return await self.query_post_api(post_id)

    async def query_post_api(
        self, post_id: str
    ) -> MediumPostDataResponse | None:
        logger.debug(f"Starting request construction for post {post_id}")

        headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        if self.config.cookies is not None:
            headers["Cookie"] = self.config.cookies

        response_data: dict[str, Any] | None = None
        exception: Exception | None = None
        url = f"https://medium.com/_/api/posts/{post_id}"

        logger.debug("Request started...")

        async with self.request as request:
            response = await request.aget(url, headers=headers)

            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch post by ID {post_id} with status code: {response.status_code}"
                )
                return None

            try:
                text = response.text
                guard_prefix = "])}while(1);</x>"
                if text.startswith(guard_prefix):
                    text = text[len(guard_prefix) :]
                response_data = JSON.loads(text)
            except Exception as ex:
                logger.debug("Failed to parse response data as JSON")
                logger.exception(ex)
                exception = ex

        logger.debug("Request finished...")

        if exception:
            logger.error(
                f"Exception occured while fetching post {post_id}, so let's just fuck it up"
            )
            raise exception

        if response_data is None:
            return None

        return MediumPostDataResponse.model_validate(response_data)
