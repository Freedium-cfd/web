"""AthleticService — renders The Athletic articles for Freedium.

Pipeline:
  nytimes.com/athletic/… (or theathletic.com/…) → page __NEXT_DATA__ →
  pageProps.article → body HTML through the mdream sidecar → markdown +
  frontmatter → images rewritten to /img/nyt/.

Images live on static01.nyt.com, so the NYT image proxy already covers them.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from loguru import logger

from freedium_library.services.athletic import client as athletic_client
from freedium_library.services.base import BaseService
from freedium_library.services.exceptions import UnsupportedContentError
from freedium_library.utils.http import CurlRequest

# Same CDN the NYT service uses — reuse its /img source rather than adding one.
_NYT_IMG_PREFIX = "https://static01.nyt.com/"


def _normalize_url(path: str) -> str:
    url = path.strip()
    # Proxies/SvelteKit collapse the // in /https://host/… → https:/host/…
    if url.startswith("https:/") and not url.startswith("https://"):
        url = "https://" + url[len("https:/"):]
    elif url.startswith("http:/") and not url.startswith("http://"):
        url = "http://" + url[len("http:/"):]
    return url


def _is_athletic_url(url: str) -> bool:
    url = _normalize_url(url).lower()
    if not url.startswith(("https://", "http://")):
        return False
    rest = url.split("//", 1)[1]
    host, _, path = rest.partition("/")
    host = host.split("?", 1)[0]
    if host in ("theathletic.com", "www.theathletic.com"):
        return True
    # The Athletic under NYT lives at nytimes.com/athletic/…; plain nytimes.com
    # articles are handled by NytService.
    if host in ("nytimes.com", "www.nytimes.com"):
        return path.startswith("athletic/")
    return False


def _format_date(ts_ms: int | None) -> str:
    if not ts_ms:
        return ""
    try:
        return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()
    except (OSError, ValueError, TypeError):
        return ""


class AthleticService(BaseService):
    """Renders The Athletic articles."""

    def __init__(
        self,
        request: CurlRequest | None = None,
        mdream_url: str = "http://mdream:8085",
    ) -> None:
        # One client for the service's lifetime (services are singletons), so
        # the session and connection pool are reused across renders.
        self._request = request or CurlRequest(persistent=True)
        self._mdream_url = mdream_url.rstrip("/")

    def _is_valid(self, path: str) -> bool:
        return _is_athletic_url(path)

    async def _ais_valid(self, path: str) -> bool:
        return _is_athletic_url(path)

    async def _arender(self, path: str) -> str:
        url = _normalize_url(path)
        article = await athletic_client.fetch_article(self._request, url)

        body_html = article.get("article_body") or ""
        body_md = await self._to_markdown(body_html)
        if len(body_md) < 100:
            raise UnsupportedContentError("no renderable body in Athletic article")

        markdown = self._frontmatter(article, url) + body_md
        return markdown.replace(_NYT_IMG_PREFIX, "/img/nyt/")

    async def _to_markdown(self, body_html: str) -> str:
        """Convert the body HTML via the mdream sidecar (same converter the
        Economist web fallback uses)."""
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                resp = await c.post(
                    self._mdream_url + "/",
                    content=body_html.encode("utf-8"),
                    headers={"content-type": "text/html"},
                )
                resp.raise_for_status()
                return resp.text
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Athletic mdream conversion failed: {exc!r}")
            return ""

    @staticmethod
    def _frontmatter(article: dict[str, Any], url: str) -> str:
        import yaml

        authors: list[dict[str, str]] = []
        for entry in article.get("authors") or []:
            author = (entry or {}).get("author") or {}
            name = author.get("name")
            if not name:
                continue
            item: dict[str, str] = {"name": name}
            if author.get("avatar_uri"):
                item["avatar"] = author["avatar_uri"]
            authors.append(item)
        if not authors:
            authors = [{"name": "The Athletic"}]

        meta: dict[str, Any] = {
            "title": article.get("title") or "Untitled",
            "authors": authors,
            "publication": "The Athletic",
            "is_locked": False,
            "url": article.get("permalink") or url,
        }
        if article.get("excerpt"):
            meta["subtitle"] = article["excerpt"]
        date = _format_date(article.get("published_at"))
        if date:
            meta["date"] = date
        if article.get("primary_tag"):
            meta["tags"] = [article["primary_tag"]]

        image = article.get("image_uri_full") or article.get("image_uri")
        if image:
            caption = " — ".join(
                p for p in (article.get("image_caption"), article.get("image_credit")) if p
            )
            meta["preview_image"] = {
                "medium": image,
                "zoom": image,
                "caption": caption,
            }

        return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n"

    def _render(self, path: str) -> str:
        raise NotImplementedError("use async _arender")

    async def _asearch(self, keywords: list[str]) -> list[dict[str, str]]:
        return []

    def _search(self, keywords: list[str]) -> list[dict[str, str]]:
        return []
