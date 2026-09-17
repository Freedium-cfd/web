"""WapoService — renders Washington Post articles for Freedium.

Pipeline:
  public WaPo URL → Rainbow content API (structured JSON, no auth) →
  items→markdown (paragraphs, headers, images, blockquotes) → frontmatter
  (title, subtitle, authors+avatar+bio, date, tags, preview_image) →
  rewrite image URLs → /img/wapo/.

No proxy needed — the API responds from any IP (no geo-block, no fingerprint).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from freedium_library.services.base import BaseService
from freedium_library.services.exceptions import ArticleNotFoundError, UnsupportedContentError
from freedium_library.services.wapo import client as wapo_client

# washingtonpost.com article URLs (various section/blog/year patterns).
# Excludes non-article pages (/video/, /photography/, /podcasts/).
_WAPO_ARTICLE_RE = re.compile(
    r"^https?://(www\.)?washingtonpost\.com/"
    r"(?!video/|photography/|podcasts/|games/|crosswords/)"
    r"[a-z0-9-]+/",
    re.IGNORECASE,
)
_COLLAPSED_SCHEME_RE = re.compile(r"^(https?):/+", re.IGNORECASE)

# WaPo image CDN hosts — separate patterns so the redirect source maps to the
# correct CDN (see images.py _IMG_SOURCES).
_ARC_IMG_RE = re.compile(
    r"https?://cloudfront-us-east-1\.images\.arcpublishing\.com/wapo/", re.IGNORECASE
)
_LEGACY_IMG_RE = re.compile(
    r"https?://img\.washingtonpost\.com/", re.IGNORECASE
)


def _normalize_url(path: str) -> str:
    return _COLLAPSED_SCHEME_RE.sub(r"\1://", path.strip())


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace('"', "&quot;")
        .replace("<", "&lt;").replace(">", "&gt;")
    )


def _format_date(ts_ms: int | None) -> str:
    if not ts_ms:
        return ""
    try:
        return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()
    except (OSError, ValueError):
        return ""


class WapoService(BaseService):
    """Renders washingtonpost.com articles via the Rainbow content API."""

    def _is_valid(self, path: str) -> bool:
        return bool(_WAPO_ARTICLE_RE.match(_normalize_url(path)))

    async def _ais_valid(self, path: str) -> bool:
        return self._is_valid(path)

    async def _arender(self, path: str) -> str:
        url = _normalize_url(path)
        # WaPo's Rainbow API returns 415 without a trailing slash.
        if not url.endswith("/"):
            url += "/"
        data = await wapo_client.fetch_article(url)
        if not data or not data.get("items"):
            raise ArticleNotFoundError("empty WaPo response")

        body_md = self._items_to_markdown(data.get("items") or [])
        if len(body_md) < 50:
            raise UnsupportedContentError("no renderable body items")

        markdown = self._frontmatter(data, url) + body_md
        markdown = _ARC_IMG_RE.sub("/img/wapo/", markdown)
        return _LEGACY_IMG_RE.sub("/img/wapo-legacy/", markdown)

    @staticmethod
    def _items_to_markdown(items: list[dict[str, Any]]) -> str:
        out: list[str] = []
        for item in items:
            t = item.get("type", "")
            sub = item.get("subtype", "")
            content = item.get("content", "")

            if t == "sanitized_html" and sub == "paragraph":
                out.append(content)
            elif t == "sanitized_html" and sub == "header":
                text = re.sub(r"<[^>]+>", "", str(content)).strip()
                if text:
                    out.append(f"## {text}")
            elif t == "image":
                img_url = item.get("imageURL", "")
                caption = item.get("fullcaption", item.get("blurb", ""))
                if img_url:
                    cap_attr = f' data-caption="{_esc(caption)}"' if caption else ""
                    figcap = f"<figcaption>{_esc(caption)}</figcaption>" if caption else ""
                    out.append(
                        f'\n<figure><img src="{_esc(img_url)}" alt="{_esc(caption or "image")}"'
                        f' loading="lazy"{cap_attr} class="prose-image"/>{figcap}</figure>\n'
                    )
            elif t == "blockquote":
                text = re.sub(r"<[^>]+>", "", str(content)).strip()
                if text:
                    out.append(f"> {text}")
            elif t == "interstitial_link" or t == "link":
                link_url = item.get("url", "")
                link_text = content or link_url
                if link_url:
                    out.append(f"[{link_text}]({link_url})")
            # ad, autorecirc_carousel, kicker, title, date, byline, author_info,
            # deck, audio → skipped (metadata goes in frontmatter).

        return "\n\n".join(out)

    @staticmethod
    def _frontmatter(data: dict[str, Any], url: str) -> str:
        import yaml

        title = data.get("title", "Untitled")
        blurb = data.get("blurb", "")
        section = data.get("section", "")
        date = _format_date(data.get("display_date") or data.get("published"))

        # Authors from author_info items (name + bio + avatar).
        authors: list[dict[str, str]] = []
        for item in data.get("items") or []:
            if item.get("type") == "author_info":
                entry: dict[str, str] = {"name": item.get("name") or "Unknown"}
                if item.get("image"):
                    entry["avatar"] = item["image"]
                if item.get("bio"):
                    entry["bio"] = item["bio"]
                authors.append(entry)
        if not authors:
            # Fallback to byline item.
            for item in data.get("items") or []:
                if item.get("type") == "byline":
                    name = re.sub(r"<[^>]+>", "", item.get("content", "")).strip()
                    name = re.sub(r"^By\s+", "", name, flags=re.IGNORECASE).strip()
                    if name:
                        authors = [{"name": name}]
                    break
        if not authors:
            authors = [{"name": "The Washington Post"}]

        meta: dict[str, Any] = {
            "title": title,
            "authors": authors,
            "publication": data.get("source") or "The Washington Post",
            "is_locked": False,
            "url": url,
        }
        if blurb:
            meta["subtitle"] = blurb
        if date:
            meta["date"] = date
        if section:
            meta["tags"] = [section]

        # Lead image.
        for item in data.get("items") or []:
            if item.get("type") == "image" and item.get("imageURL"):
                meta["preview_image"] = {
                    "medium": item["imageURL"],
                    "zoom": item["imageURL"],
                    "caption": item.get("fullcaption", ""),
                }
                break

        return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n"

    def _render(self, path: str) -> str:
        raise NotImplementedError("use async _arender")

    async def _asearch(self, keywords: list[str]) -> list[dict[str, str]]:
        return []

    def _search(self, keywords: list[str]) -> list[dict[str, str]]:
        return []
