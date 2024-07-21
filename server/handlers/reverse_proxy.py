import aiohttp
from fastapi import Response

from server import config
from server.utils.logger_trace import trace

from bs4 import BeautifulSoup, Comment

IFRAME_HEADERS = {"Access-Control-Allow-Origin": "*", "X-Frame-Options": "SAMEORIGIN"}

@trace
async def iframe_proxy(iframe_id):
    # How Medium embeds works: https://stackoverflow.com/questions/56594766/medium-embed-ly-notifyresize-does-not-work-on-safari
    async with aiohttp.ClientSession() as client:
        request = await client.get(
            f"https://medium.com/media/{iframe_id}",
            timeout=config.TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"},
        )
        request_content = await request.text()
        request_content = request_content.replace("document.domain = document.domain", 'console.log("[FREEDIUM] iframe workaround started")')

    request_content_soup = BeautifulSoup(request_content, "html.parser")
    iframe_hack_script = '<script src="https://cdn.jsdelivr.net/npm/@iframe-resizer/child"></script>'
    new_script_tag = BeautifulSoup(iframe_hack_script, 'html.parser').script

    request_content_soup.head.append(new_script_tag)

    return Response(content=request_content_soup.prettify(), media_type="text/html", headers=IFRAME_HEADERS)


async def miro_proxy(miro_data: str):
    async with aiohttp.ClientSession() as client:
        request = await client.get(
           f"https://miro.medium.com/{miro_data}",
            timeout=config.TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"},
        )
        request_content = await request.read()
        content_type = request.headers["Content-Type"]
    return Response(content=request_content, media_type=content_type)
