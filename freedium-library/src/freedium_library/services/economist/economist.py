"""EconomistService — renders The Economist articles for Freedium.

Dual fetch: HMAC-signed GraphQL API (primary, full body) + curl_cffi web
scraping (__NEXT_DATA__, fallback). Structured body components → markdown.
Images from cdn.static-economist.com → /img/economist/.
"""
from __future__ import annotations

import re
from typing import Any

from loguru import logger

from freedium_library.services.base import BaseService
from freedium_library.services.economist import client as eco_client
from freedium_library.utils.http import CurlRequest
from freedium_library.utils.url import escape_html as _esc, normalize_url as _normalize_url

_ECO_IMG_PREFIX = "https://www.economist.com/cdn-cgi/image/"
_ECO_IMG_PREFIX2 = "https://cdn.static-economist.com/"


def _is_economist_url(url: str) -> bool:
    url = _normalize_url(url).lower()
    if not url.startswith(("https://", "http://")):
        return False
    host = url.split("//", 1)[1].split("/", 1)[0].split("?", 1)[0]
    return host == "www.economist.com" or host == "economist.com"


class EconomistService(BaseService):

    def __init__(self, request: CurlRequest | None = None, mdream_url: str = "http://mdream:8085") -> None:
        # One client per service (services are singletons), so the session and
        # its connection pool are reused across renders.
        self._request = request or CurlRequest(persistent=True)
        self._mdream_url = mdream_url.rstrip("/")

    def _is_valid(self, path: str) -> bool:
        return _is_economist_url(path)

    async def _ais_valid(self, path: str) -> bool:
        return _is_economist_url(path)

    async def _arender(self, path: str) -> str:
        url = _normalize_url(path)
        request = self._request

        # Try GraphQL first (standard articles → full body).
        data: dict = {}
        try:
            data = await eco_client.fetch_article(request, url)
        except Exception as exc:
            logger.debug(f"Economist fetch_article failed: {exc}")

        body_md = self._body_to_markdown(data.get("body") or []) if data else ""
        # If body is empty (interactive/insider/video), fall back to the
        # web page HTML → mdream conversion.
        if len(body_md) < 50:
            body_md = await self._web_fallback(request, url)
        if len(body_md) < 50:
            raise ValueError("no renderable body")

        markdown = self._frontmatter(data, url) + body_md
        markdown = markdown.replace(_ECO_IMG_PREFIX, "/img/economist/")
        return markdown.replace(_ECO_IMG_PREFIX2, "/img/economist-static/")

    @classmethod
    def _body_to_markdown(cls, body: list[dict[str, Any]]) -> str:
        out: list[str] = []
        for comp in body:
            if not isinstance(comp, dict):
                continue
            # GraphQL: __typename="ParagraphComponent", type="PARAGRAPH".
            # Web: type="PARAGRAPH". Normalize to lowercase for all checks.
            t = (comp.get("__typename") or comp.get("type") or "").lower()

            if "paragraph" in t:
                text = cls._annotated_text(comp)
                if text.strip():
                    out.append(text)
            elif "crosshead" in t:
                text = comp.get("text", "")
                if text.strip():
                    out.append(f"## {text}")
            elif "image" in t:
                img_url = comp.get("url", "")
                caption = (comp.get("caption") or {}).get("text", "") if isinstance(comp.get("caption"), dict) else ""
                credit = comp.get("credit", "")
                if img_url:
                    visible = " — ".join(p for p in (caption, credit) if p)
                    cap_attr = f' data-caption="{_esc(visible)}"' if visible else ""
                    figcap = f"<figcaption>{_esc(visible)}</figcaption>" if visible else ""
                    out.append(
                        f'\n<figure><img src="{_esc(img_url)}" alt="{_esc(caption or "image")}"'
                        f' loading="lazy"{cap_attr} class="prose-image"/>{figcap}</figure>\n'
                    )
            elif "blockquote" in t or "pullquote" in t:
                text = comp.get("text", "")
                if text.strip():
                    out.append(f"> {text}")
            elif "list" in t:
                for item in comp.get("items") or []:
                    text = item.get("text", "") if isinstance(item, dict) else str(item)
                    if text.strip():
                        out.append(f"- {text}")
            elif "infobox" in t:
                for sub in comp.get("components") or []:
                    sub_md = cls._body_to_markdown([sub])
                    if sub_md.strip():
                        out.append(sub_md)
        return "\n\n".join(out)

    @staticmethod
    def _annotated_text(comp: dict[str, Any]) -> str:
        """Render ParagraphComponent with annotations (links, bold, italic)."""
        text = comp.get("text", "")
        annotations = comp.get("annotations") or []
        if not annotations:
            return text
        # Apply annotations in reverse order (so indices stay valid).
        sorted_anns = sorted(annotations, key=lambda a: a.get("index", 0), reverse=True)
        chars = list(text)
        for ann in sorted_anns:
            atype = ann.get("type", "")
            idx = ann.get("index", 0)
            length = ann.get("length", 0)
            end = idx + length
            segment = text[idx:end]
            attrs = {a["name"]: a["value"] for a in ann.get("attributes") or [] if "name" in a and "value" in a}
            if atype == "link":
                href = attrs.get("href", "")
                replacement = f"[{segment}]({href})" if href else segment
            elif atype == "bold":
                replacement = f"**{segment}**"
            elif atype == "italic":
                replacement = f"_{segment}_"
            else:
                continue
            chars[idx:end] = list(replacement)
        return "".join(chars)

    @staticmethod
    def _frontmatter(data: dict[str, Any], url: str) -> str:
        import yaml

        headline = data.get("headline", "Untitled")
        rubric = data.get("rubric", "")
        byline = data.get("byline", "")
        section = (data.get("section") or {}).get("name", "") if isinstance(data.get("section"), dict) else ""
        date = data.get("datePublished", "")

        authors: list[dict[str, str]] = []
        if byline:
            authors = [{"name": byline}]
        if not authors:
            authors = [{"name": "The Economist"}]

        meta: dict[str, Any] = {
            "title": headline,
            "authors": authors,
            "publication": "The Economist",
            "is_locked": False,
            "url": url,
        }
        if rubric:
            meta["subtitle"] = rubric
        if date:
            meta["date"] = date
        if section:
            meta["tags"] = [section]
        if data.get("flyTitle"):
            meta["kicker"] = data["flyTitle"]

        # Cover image from teaserImage or leadComponent.
        for key in ("teaserImage", "leadComponent"):
            img = data.get(key)
            if isinstance(img, dict) and img.get("url"):
                cap = (img.get("caption") or {}).get("text", "") if isinstance(img.get("caption"), dict) else ""
                meta["preview_image"] = {
                    "medium": img["url"],
                    "zoom": img["url"],
                    "caption": cap,
                }
                break

        return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n"

    async def _web_fallback(self, request: CurlRequest, url: str) -> str:
        """Fetch the web page HTML + convert via mdream sidecar. Works for
        interactive, insider, and any non-standard Economist layout."""
        import httpx

        try:
            html = await eco_client.fetch_web_html(request, url)
        except Exception as exc:
            logger.debug(f"Economist web fetch failed: {exc}")
            return ""
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                resp = await c.post(
                    self._mdream_url + "/",
                    content=html.encode("utf-8"),
                    headers={"content-type": "text/html"},
                )
                resp.raise_for_status()
                return resp.text
        except Exception as exc:
            logger.debug(f"mdream conversion failed: {exc}")
            return ""

    def _render(self, path: str) -> str:
        raise NotImplementedError("use async _arender")

    async def _asearch(self, keywords: list[str]) -> list[dict[str, str]]:
        return []

    def _search(self, keywords: list[str]) -> list[dict[str, str]]:
        return []
