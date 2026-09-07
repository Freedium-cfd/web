"""BloombergService — renders Bloomberg articles for Freedium.

Pipeline:
  public bloomberg.com URL → urllookup CDN API (structured JSON, no auth) →
  components→markdown (paragraphs, headers, images, blockquotes, links) →
  frontmatter (title, subtitle, author, date, tags, preview_image) →
  rewrite image URLs → /img/bbg/.

No auth, no signing, no proxy, no geo-block.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from loguru import logger

from freedium_library.services.base import BaseService
from freedium_library.services.bloomberg import client as bbg_client
from freedium_library.utils.http import CurlRequest

_BBG_IMG_PREFIX = "https://assets.bwbx.io/"


def _normalize_url(path: str) -> str:
    url = path.strip()
    # Collapsed scheme fix (proxy/SvelteKit).
    if url.startswith("https:/") and not url.startswith("https://"):
        url = "https://" + url[len("https:/"):]
    elif url.startswith("http:/") and not url.startswith("http://"):
        url = "http://" + url[len("http:/"):]
    return url


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace('"', "&quot;")
        .replace("<", "&lt;").replace(">", "&gt;")
    )


def _format_date(ts: int | None) -> str:
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except (OSError, ValueError):
        return ""


def _is_bloomberg_url(url: str) -> bool:
    url = _normalize_url(url).lower()
    if not url.startswith(("https://", "http://")):
        return False
    host = url.split("//", 1)[1].split("/", 1)[0].split("?", 1)[0]
    return host == "www.bloomberg.com" or host == "bloomberg.com"


class BloombergService(BaseService):
    """Renders bloomberg.com articles via the mobile CDN API."""

    def __init__(self, proxy: str | RequestProxyConfig | None = None) -> None:
        from freedium_library.utils.http.client.config import RequestConfig

        # One client per service (services are singletons) — reuses the session
        # and its WARP connections across renders.
        self._request = CurlRequest(config=RequestConfig.with_proxy(proxy), persistent=True)

    def _is_valid(self, path: str) -> bool:
        return _is_bloomberg_url(path)

    async def _ais_valid(self, path: str) -> bool:
        return _is_bloomberg_url(path)

    async def _arender(self, path: str) -> str:
        url = _normalize_url(path)
        data = await bbg_client.fetch_article(self._request, url)
        if not data or not data.get("components"):
            raise ValueError("empty Bloomberg response")

        body_md = self._components_to_markdown(data.get("components") or [])
        if len(body_md) < 50:
            raise ValueError("no renderable body components")

        markdown = self._frontmatter(data, url) + body_md
        return markdown.replace(_BBG_IMG_PREFIX, "/img/bbg/")

    @staticmethod
    def _parts_to_md(parts: list[dict[str, Any]]) -> str:
        """Render component parts → inline markdown (text + links)."""
        out: list[str] = []
        for p in parts:
            if not isinstance(p, dict):
                continue
            text = p.get("text", "")
            href = p.get("href", "")
            nested = p.get("parts")
            if nested:
                text = BloombergService._parts_to_md(nested)
            if href and text:
                out.append(f"[{text}]({href})")
            elif text:
                out.append(text)
        return "".join(out)

    @classmethod
    def _components_to_markdown(cls, components: list[dict[str, Any]]) -> str:
        out: list[str] = []
        for comp in components:
            if not isinstance(comp, dict):
                continue
            role = comp.get("role", "")
            parts = comp.get("parts", [])

            if role in ("paragraph", "p"):
                text = cls._parts_to_md(parts)
                if text.strip():
                    out.append(text)
            elif role in ("h2", "h3", "h4"):
                text = cls._parts_to_md(parts)
                if text.strip():
                    prefix = "##" if role == "h2" else "###"
                    out.append(f"{prefix} {text}")
            elif role == "blockquote":
                text = cls._parts_to_md(parts)
                if text.strip():
                    out.append(f"> {text}")
            elif role == "image":
                urls = comp.get("imageURLs") or {}
                img_url = urls.get("large") or urls.get("default") or ""
                caption = comp.get("caption", "")
                credit = comp.get("credit", "")
                if img_url:
                    visible = " — ".join(p for p in (caption, credit) if p)
                    cap_attr = f' data-caption="{_esc(visible)}"' if visible else ""
                    figcap = f"<figcaption>{_esc(visible)}</figcaption>" if visible else ""
                    out.append(
                        f'\n<figure><img src="{_esc(img_url)}" alt="{_esc(caption or "image")}"'
                        f' loading="lazy"{cap_attr} class="prose-image"/>{figcap}</figure>\n'
                    )
            elif role in ("listItem", "ul"):
                # ul.parts = [{role:"li", parts:[…]}, …]
                li_lines: list[str] = []
                for p in parts:
                    if isinstance(p, dict) and p.get("role") == "li":
                        text = cls._parts_to_md(p.get("parts", []))
                        if text.strip():
                            li_lines.append(f"- {text}")
                if li_lines:
                    out.append("\n".join(li_lines))
                else:
                    text = cls._parts_to_md(parts)
                    if text.strip():
                        out.append(f"- {text}")
            elif role == "video":
                video_url = comp.get("url") or comp.get("videoUrl") or ""
                title = comp.get("title") or "Video"
                if video_url:
                    out.append(f"[{title}]({video_url})")
            # headline, byline, ad, etc. → skipped (metadata in frontmatter)

        return "\n\n".join(out)

    @staticmethod
    def _frontmatter(data: dict[str, Any], url: str) -> str:
        import yaml

        title = data.get("title", "Untitled")
        summary = data.get("summary", "")
        byline = data.get("byline", "")
        section = data.get("primarySite") or data.get("primaryCategory") or ""
        date = _format_date(data.get("published"))

        authors: list[dict[str, str]] = []
        if byline:
            authors = [{"name": byline}]
        if not authors:
            authors = [{"name": "Bloomberg"}]

        meta: dict[str, Any] = {
            "title": title,
            "authors": authors,
            "publication": "Bloomberg",
            "is_locked": False,
            "url": url,
        }
        if summary:
            meta["subtitle"] = summary
        if date:
            meta["date"] = date
        if section:
            meta["tags"] = [section]

        lede = data.get("ledeImage") or {}
        lede_urls = lede.get("imageURLs") or {}
        lede_url = lede_urls.get("large") or lede_urls.get("default") or ""
        if lede_url:
            meta["preview_image"] = {
                "medium": lede_url,
                "zoom": lede_url,
                "caption": lede.get("caption", ""),
            }

        return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n"

    def _render(self, path: str) -> str:
        raise NotImplementedError("use async _arender")

    async def _asearch(self, keywords: list[str]) -> list[dict[str, str]]:
        return []

    def _search(self, keywords: list[str]) -> list[dict[str, str]]:
        return []
