import random

import aiohttp
from aiohttp_retry import RetryClient
from aiohttp_socks import ProxyConnector
from fastapi import Response
from loguru import logger
from medium_parser import retry_options

from server import config
from server.utils.logger_trace import trace

IFRAME_HEADERS = {"Access-Control-Allow-Origin": "*", "X-Frame-Options": "SAMEORIGIN"}


@trace
async def iframe_proxy(iframe_id: str):
    """
    Proxy iframe content from Medium's media endpoint.

    Args:
        iframe_id: The Medium iframe/media ID

    Returns:
        Response with patched HTML content
    """
    logger.debug(f"Fetching iframe content for ID: {iframe_id}")

    connector = ProxyConnector.from_url(random.choice(config.PROXY_LIST)) if config.PROXY_LIST else None

    async with aiohttp.ClientSession(connector=connector) as session:
        async with RetryClient(
            client_session=session, raise_for_status=False, retry_options=retry_options
        ) as retry_client:
            async with retry_client.get(
                f"https://medium.com/media/{iframe_id}",
                timeout=config.REQUEST_TIMEOUT,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
            ) as request:
                if request.status != 200:
                    logger.error(
                        f"Failed to fetch iframe {iframe_id}\n"
                        f"Status code: {request.status}"
                    )
                    return Response(content="", media_type="text/html", headers=IFRAME_HEADERS)

                request_content = await request.text()

    patched_content = patch_iframe_content(request_content)
    return Response(content=patched_content, media_type="text/html", headers=IFRAME_HEADERS)


def patch_iframe_content(content: str) -> str:
    """
    Patch iframe content to work in Freedium context.

    Replaces Medium's domain-based security mechanism with a console log
    to avoid cross-origin issues.

    Args:
        content: Raw HTML content from Medium

    Returns:
        Patched HTML content
    """
    return content.replace(
        "document.domain = document.domain",
        'console.log("[FREEDIUM] iframe workaround started")'
    )
