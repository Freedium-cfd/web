from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import parse_qs, urlparse

from dependency_injector.wiring import Provide
from loguru import logger

from freedium_library.container import Container
from freedium_library.utils import URLProcessor

if TYPE_CHECKING:
    from freedium_library.models.request import Request

    from .api import MediumApiService


class MediumServicePathValidator:
    def __init__(
        self,
        api_service: MediumApiService,
    ):
        self.api_service = api_service
        self.hash_validator = _MediumServiceHashesValidator()
        self.url_validator = _MediumServiceURLValidator(
            self.api_service, self.hash_validator
        )

    def is_valid(self, path: str) -> bool:
        return self.url_validator.is_valid(path) or self.hash_validator.extract_hashes(
            path
        )


class _MediumServiceURLValidator:
    def __init__(
        self,
        api_service: MediumApiService,
        hash_validator: _MediumServiceHashesValidator,
        request: Request = Provide[Container.request],
    ):
        self.api_service = api_service
        self.request = request
        self.hash_validator = hash_validator

    def is_valid(self, url: str) -> bool: ...

    def _get_short_link_request_params(
        self, short_url_id: str
    ) -> tuple[str, dict[str, Any]]:
        req_url = f"https://rsci.app.link/{short_url_id}"
        req_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        }  # TODO: use random user agent generator library
        return req_url, {"headers": req_headers, "follow_redirects": False}

    async def resolve_medium_url(self, url: str) -> Optional[str]:
        logger.debug(f"Trying resolve {url=}")
        parsed_url = urlparse(url)
        parsed_netloc = URLProcessor.un_wwwify(parsed_url.netloc)

        if parsed_url.path.startswith("/p/"):
            logger.debug("URL is Medium 'mobile' link")
            post_id = parsed_url.path.rsplit("/p/")[1]

        elif parsed_netloc == "l.facebook.com" and parsed_url.path.startswith("/l.php"):
            logger.debug("URL seems like is Facebook redirect (tracking) link")

            parsed_query = parse_qs(parsed_url.query)
            if parsed_query.get("u") and len(parsed_query["u"]) == 1:
                post_url = parsed_query["u"][0]
                return await self.resolve_medium_url(post_url)

            logger.debug("...but we get fucked up...")
            return None

        elif (
            parsed_netloc == "webcache.googleusercontent.com"
            and parsed_url.path.startswith("/search")
        ):
            logger.debug("URL seems like is Google Web Archive page link")

            parsed_query = parse_qs(parsed_url.query)
            if parsed_query.get("q") and len(parsed_query["q"]) == 1:
                post_url = parsed_query["q"][0].removeprefix("cache:")
                return await self.resolve_medium_url(post_url)

            logger.debug("...but we get fucked up...")
            return None

        elif parsed_netloc == "google.com" and parsed_url.path.startswith("/url"):
            logger.debug("URL seems like is Google redirect (tracking) link")

            parsed_query = parse_qs(parsed_url.query)
            if parsed_query.get("url") and len(parsed_query["url"]) == 1:
                logger.debug("..and we got 'url' passed param. Make resolve them....")
                post_url = parsed_query["url"][0]
                return await self.resolve_medium_url(post_url)
            elif parsed_query.get("q") and len(parsed_query["q"]) == 1:
                logger.debug("..and we got 'q' passed param. Make resolve them....")
                post_url = parsed_query["q"][0]
                return await self.resolve_medium_url(post_url)

            logger.debug("...but we get fucked up...")
            return None

        elif parsed_netloc == "12ft.io":
            logger.debug("URL seems like is from our partner named 12ft.io")

            parsed_query = parse_qs(parsed_url.query)
            if parsed_query.get("q") and len(parsed_query["q"]) == 1:
                logger.debug("..and we got 'q' passed param. Make resolve them....")
                post_url = parsed_query["q"][0]
                return await self.resolve_medium_url(post_url)

            logger.debug("...but we get fucked up...")
            return None

        elif parsed_url.path.startswith("/m/global-identity-2"):
            logger.debug(
                "URL seems like is Medium redirect (tracking) link. Possibly from email subscription"
            )

            parsed_query = parse_qs(parsed_url.query)
            if (
                parsed_query.get("redirectUrl")
                and len(parsed_query["redirectUrl"]) == 1
            ):
                logger.debug(
                    "..and we got 'redirectUrl' passed param. Make resolve them...."
                )
                post_url = parsed_query["redirectUrl"][0]
                return await self.resolve_medium_url(post_url)

            logger.debug("...but we get fucked up...")
            return None

        elif parsed_netloc == "link.medium.com":
            logger.debug(
                "URL seems like is Medium short (SHORT) redirect (tracking) link. Make resolve them..."
            )
            short_url_id = parsed_url.path.removeprefix("/")
            post_url = await self.aresolve_medium_short_link(short_url_id)
            return await self.resolve_medium_url(post_url)

        else:
            logger.debug(
                "We can't determine the URL type. Let's just try to extract the post_id..."
            )
            post_url = parsed_url.path.split("/")[-1]
            post_id = post_url.split("-")[-1]

        if not self.hash_validator.is_valid(post_id):
            logger.warning(f"...but hoops, that's invalid post_id: {post_id}")
            return None

        return post_id

    def resolve_medium_short_link(self, short_url_id: str) -> str:
        req_url, params = self._get_short_link_request_params(short_url_id)
        response = self.request.get(req_url, **params)
        return response.headers["Location"]

    async def aresolve_medium_short_link(self, short_url_id: str) -> str:
        req_url, params = self._get_short_link_request_params(short_url_id)
        response = await self.request.aget(req_url, **params)
        return response.headers["Location"]


class _MediumServiceHashesValidator:
    def is_valid(self, hash: str) -> bool:
        return bool(self.extract_hashes(hash))

    def extract_hashes(self, path: str) -> list[str]:
        logger.debug(f"Extracting hashes from path: {path}")
        if not path:
            return []

        # we ignore ? symbols, because they can be in the end of the path right before the query params
        logger.trace("Stage 1: finding hashes preceded by '-'")
        match = re.findall(r"-(\b[a-fA-F0-9]{8,12}\b)\??", path)
        if not match:
            logger.trace("Stage 2: finding hashes without '-'")
            match = re.findall(r"(\b[a-fA-F0-9]{8,12}\b)\??", path)

        return match if match else []
