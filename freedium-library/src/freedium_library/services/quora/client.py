"""Quora web client.

Fetches the Quora page using CurlRequest with Chrome TLS impersonation to avoid
Cloudflare/bot challenges. Extracts the GraphQL Relay JSON payload pushed to
window.ansFrontendGlobals.data.inlineQueryResults.
"""
from __future__ import annotations

import json
from typing import Any

from freedium_library.services.exceptions import ArticleNotFoundError
from freedium_library.utils.http import CurlRequest

HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
}


def _extract_relay_payload(html: str) -> dict[str, Any] | None:
    """Extract post or answer object from Quora's inline query results in HTML."""
    idx = 0
    candidate = None
    while True:
        pos = html.find('.push("', idx)
        if pos == -1:
            break
        start = pos + 6
        p = start + 1
        while p < len(html):
            if html[p] == '"' and html[p - 1] != "\\":
                break
            p += 1
        raw_str = html[start : p + 1]
        idx = p + 1
        try:
            decoded = json.loads(raw_str)
            obj = json.loads(decoded)
            data = obj.get("data", {})
            if "post" in data and data["post"]:
                return data["post"]
            if "question" in data and data["question"]:
                candidate = data["question"]
            if "answer" in data and data["answer"]:
                return data["answer"]
        except Exception:
            pass

    return candidate


async def fetch_content(request: CurlRequest, url: str) -> dict[str, Any]:
    """Fetch Quora page and extract post or question/answer payload."""
    from freedium_library.services.exceptions import UpstreamBlockedError

    try:
        resp = await request.aget(url, headers=HEADERS)
        resp.raise_for_status()
    except Exception as e:
        err_msg = str(e).lower()
        if "403" in err_msg or "turnstile" in err_msg or "cloudflare" in err_msg:
            raise UpstreamBlockedError("Quora is protected by Cloudflare bot challenge") from e
        raise

    if "just a moment" in resp.text.lower() or "turnstile" in resp.text.lower():
        raise UpstreamBlockedError("Quora is protected by Cloudflare bot challenge")

    payload = _extract_relay_payload(resp.text)
    if not payload:
        raise ArticleNotFoundError("Could not find post or answer in Quora page")

    return payload
