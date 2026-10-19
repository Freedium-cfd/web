"""The Athletic article client.

The Athletic's paywall is soft: the full article ships inside the page's
__NEXT_DATA__ payload and is only hidden by a JS overlay, so a plain fetch
(which runs no JS) gets everything. No auth, no API key.

The app's GraphQL API is deliberately not used — its body field is gated
server-side by the JWT's subscription status, and the metadata op that would
only resolve an id → permalink needs a captured token. Since Freedium is
always given a full URL, the web page alone is sufficient.
"""
from __future__ import annotations

import json
import re
from typing import Any

from freedium_library.utils.http import CurlRequest

# Browser UA + a search referrer: The Athletic serves the un-gated payload to
# what looks like an organic search visit.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://www.google.com/",
}

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)


async def fetch_article(request: CurlRequest, url: str) -> dict[str, Any]:
    """The page's `pageProps.article` object: body HTML plus metadata."""
    from freedium_library.services.exceptions import UpstreamBlockedError

    try:
        resp = await request.aget(url, headers=HEADERS)
        resp.raise_for_status()
    except Exception as e:
        err_msg = str(e).lower()
        if "403" in err_msg or "datadome" in err_msg:
            raise UpstreamBlockedError("The Athletic is protected by DataDome bot challenge") from e
        raise

    if "datadome" in resp.text.lower() or "captcha" in resp.text.lower():
        raise UpstreamBlockedError("The Athletic is protected by DataDome bot challenge")

    m = _NEXT_DATA_RE.search(resp.text)
    if not m:
        raise ValueError("no __NEXT_DATA__ in Athletic page")
    data = json.loads(m.group(1))

    article = (data.get("props") or {}).get("pageProps", {}).get("article")
    if not isinstance(article, dict) or not article.get("article_body"):
        raise ValueError("no article body in Athletic page")
    return article
