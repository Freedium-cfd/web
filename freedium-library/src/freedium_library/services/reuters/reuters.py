"""ReutersService — renders Reuters articles for Freedium.

Pipeline:
  public reuters.com URL + ?outputType=json → structured JSON blocks →
  content_elements→markdown (paragraphs with HTML links, headers, images,
  lists) → frontmatter (title, authors, date, section, preview_image) →
  rewrite image URLs → /img/reuters/.

No auth, no signing, no proxy, no geo-block.
"""
from __future__ import annotations

import re
from typing import Any

from loguru import logger

from freedium_library.services.base import BaseService
from freedium_library.services.reuters import client as reuters_client
from freedium_library.utils.http import CurlRequest

_REUTERS_IMG_PREFIXES = [
    "https://www.reuters.com/resizer/",
    "https://cloudfront-us-east-2.images.arcpublishing.com/reuters/",
]


def _normalize_url(path: str) -> str:
    url = path.strip()
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


def _is_reuters_url(url: str) -> bool:
    url = _normalize_url(url).lower()
    if not url.startswith(("https://", "http://")):
        return False
    host = url.split("//", 1)[1].split("/", 1)[0].split("?", 1)[0]
    return host == "www.reuters.com" or host == "reuters.com"


def _extract_article(raw: list | dict) -> dict:
    """Extract article fields from the JSON blocks."""
    if isinstance(raw, dict):
        raw = [raw]
    article: dict[str, Any] = {
        "title": "", "description": "", "authors": [],
        "published": "", "section": "",
        "image_url": "", "image_caption": "",
        "content_elements": [],
    }
    for block in raw:
        if not isinstance(block, dict):
            continue
        bt = block.get("type", "")
        if bt == "page-metadata":
            meta = block.get("data", {})
            article["title"] = meta.get("title", article["title"])
            article["section"] = meta.get("analytics", {}).get("topic_channel", "")
        if bt == "article_detail" or "content_elements" in (block.get("data") or {}):
            data = block.get("data", {})
            art = data.get("article", data)
            if art.get("title"):
                article["title"] = art["title"]
            # `subtitle` is the standfirst shown on the page; `description` is
            # the (differently worded, shorter) SEO blurb. Prefer the former.
            article["description"] = (
                art.get("subtitle") or art.get("description") or article["description"]
            )
            authors = art.get("authors") or []
            article["authors"] = [
                {"name": a.get("name", "")} for a in authors if isinstance(a, dict) and a.get("name")
            ]
            article["published"] = art.get("published_time") or art.get("display_date") or ""
            # Lead image — Reuters uses different promo_items keys: basic,
            # images, lead_art; or a top-level thumbnail as fallback.
            promo = art.get("promo_items", {})
            if isinstance(promo, dict):
                for key in ("basic", "images", "lead_art"):
                    cand = promo.get(key, {})
                    if isinstance(cand, dict) and cand.get("url"):
                        article["image_url"] = cand["url"]
                        article["image_caption"] = cand.get("caption", "")
                        break
            if not article["image_url"]:
                thumb = art.get("thumbnail", {})
                if isinstance(thumb, dict) and thumb.get("url"):
                    article["image_url"] = thumb["url"]
                    article["image_caption"] = thumb.get("caption", "")
            article["content_elements"] = art.get("content_elements", [])
    return article


class ReutersService(BaseService):

    def __init__(self, proxy: str | RequestProxyConfig | None = None) -> None:
        from freedium_library.utils.http.client.config import RequestConfig

        # One client per service (services are singletons) — reuses the session
        # and its WARP connections across renders.
        self._request = CurlRequest(config=RequestConfig.with_proxy(proxy), persistent=True)

    def _is_valid(self, path: str) -> bool:
        return _is_reuters_url(path)

    async def _ais_valid(self, path: str) -> bool:
        return _is_reuters_url(path)

    async def _arender(self, path: str) -> str:
        url = _normalize_url(path)
        raw = await reuters_client.fetch_article(self._request, url)
        article = _extract_article(raw)
        if not article["title"] and not article["content_elements"]:
            raise ValueError("empty Reuters response")

        body_md = self._elements_to_markdown(article["content_elements"])
        markdown = self._frontmatter(article, url) + body_md
        for prefix in _REUTERS_IMG_PREFIXES:
            markdown = markdown.replace(prefix, "/img/reuters/")
        return markdown

    @staticmethod
    def _elements_to_markdown(elements: list[dict[str, Any]]) -> str:
        out: list[str] = []
        for elem in elements:
            if not isinstance(elem, dict):
                continue
            t = elem.get("type", "")
            content = elem.get("content", "")

            if t == "paragraph" and isinstance(content, str) and content.strip():
                out.append(content)
            elif t == "header":
                text = re.sub(r"<[^>]+>", "", str(content)).strip()
                if text:
                    out.append(f"## {text}")
            elif t == "image":
                img_url = elem.get("url", "")
                caption = elem.get("caption", "")
                if img_url:
                    cap_attr = f' data-caption="{_esc(caption)}"' if caption else ""
                    figcap = f"<figcaption>{_esc(caption)}</figcaption>" if caption else ""
                    out.append(
                        f'\n<figure><img src="{_esc(img_url)}" alt="{_esc(caption or "image")}"'
                        f' loading="lazy"{cap_attr} class="prose-image"/>{figcap}</figure>\n'
                    )
            elif t == "pullquote":
                text = re.sub(r"<[^>]+>", "", str(content)).strip()
                if text:
                    out.append(f"> {text}")
            elif t == "list":
                for item in elem.get("items") or []:
                    if isinstance(item, dict):
                        text = re.sub(r"<[^>]+>", "", str(item.get("content", ""))).strip()
                        if text:
                            out.append(f"- {text}")
        return "\n\n".join(out)

    @staticmethod
    def _frontmatter(article: dict[str, Any], url: str) -> str:
        import yaml

        authors = article["authors"] or [{"name": "Reuters"}]
        meta: dict[str, Any] = {
            "title": article["title"] or "Untitled",
            "authors": authors,
            "publication": "Reuters",
            "is_locked": False,
            "url": url,
        }
        if article["description"]:
            meta["subtitle"] = article["description"]
        if article["published"]:
            meta["date"] = article["published"]
        if article["section"]:
            meta["tags"] = [article["section"]]
        if article["image_url"]:
            meta["preview_image"] = {
                "medium": article["image_url"],
                "zoom": article["image_url"],
                "caption": article["image_caption"],
            }
        return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n"

    def _render(self, path: str) -> str:
        raise NotImplementedError("use async _arender")

    async def _asearch(self, keywords: list[str]) -> list[dict[str, str]]:
        return []

    def _search(self, keywords: list[str]) -> list[dict[str, str]]:
        return []
