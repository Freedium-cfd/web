import aiohttp
from fastapi import Response
from aiohttp_retry import RetryClient
from aiohttp_socks import ProxyConnector
import random

from server import config
from medium_parser import retry_options

IFRAME_HEADERS = {"Access-Control-Allow-Origin": "*", "X-Frame-Options": "SAMEORIGIN"}


async def miro_proxy(miro_data: str, use_proxy: bool = False):
    url = f"https://miro.medium.com/{miro_data}"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}

    if use_proxy and config.PROXY_LIST:
        proxy = random.choice(config.PROXY_LIST)
        connector = ProxyConnector.from_url(proxy)
    else:
        connector = None

    async with aiohttp.ClientSession(connector=connector) as session:
        client = session if not use_proxy else RetryClient(client_session=session, raise_for_status=False, retry_options=retry_options)

        async with client.get(url, timeout=config.TIMEOUT, headers=headers) as request:
            request_content = await request.read()
            content_type = request.headers["Content-Type"]

    return Response(content=request_content, media_type=content_type)
