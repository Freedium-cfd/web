import random

import aiohttp
from aiohttp_retry import RetryClient
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup
from fastapi import Response
from medium_parser import retry_options

from server import config
from server.utils.logger_trace import trace

IFRAME_HEADERS = {"Access-Control-Allow-Origin": "*", "X-Frame-Options": "SAMEORIGIN"}


@trace
async def iframe_proxy(iframe_id: str):
    connector = ProxyConnector.from_url(random.choice(config.PROXY_LIST)) if config.PROXY_LIST else None

    async with aiohttp.ClientSession(connector=connector) as session:
        async with RetryClient(
            client_session=session, raise_for_status=False, retry_options=retry_options
        ) as retry_client:
            async with retry_client.get(
                f"https://medium.com/media/{iframe_id}",
                timeout=config.REQUEST_TIMEOUT,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
                },
            ) as request:
                request_content = await request.text()

    patched_content = patch_iframe_content(request_content)
    return Response(content=patched_content, media_type="text/html", headers=IFRAME_HEADERS)


def patch_iframe_content(content: str) -> str:
    content = content.replace(
        "document.domain = document.domain", 'console.log("[FREEDIUM] iframe workaround started")'
    )

    soup = BeautifulSoup(content, "html.parser")
    iframe_resizer_script = BeautifulSoup(
        '<script src="https://cdn.jsdelivr.net/npm/@iframe-resizer/child"></script>', "html.parser"
    ).script
    soup.head.append(iframe_resizer_script)

    return soup.prettify()
