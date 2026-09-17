"""FtService — renders Financial Times articles for Freedium.

Pipeline:
  ft.com/content/{uuid} → extract UUID → app-api.ft.com (no auth) →
  structured body tree → markdown (paragraphs with inline links, headings,
  pull-quotes, images) → frontmatter → rewrite images → /img/ft/.

No auth, no signing, no proxy. CurlRequest for TLS fingerprint.
"""
from __future__ import annotations

from typing import Any

from loguru import logger

from freedium_library.services.base import BaseService
from freedium_library.services.exceptions import UnsupportedContentError
from freedium_library.services.ft import client as ft_client
from freedium_library.utils.http import CurlRequest

# FT image URLs (images.ft.com/v3/image/raw/...) are public CDN URLs that
# work directly — no need to proxy them through /img/ft/. They include query
# params (source, width, quality) that break the simple prefix-redirect.


def _normalize_url(path: str) -> str:
    url = path.strip()
    if url.startswith("https:/") and not url.startswith("https://"):
        url = "https://" + url[len("https:/"):]
    return url


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace('"', "&quot;")
        .replace("<", "&lt;").replace(">", "&gt;")
    )


def _is_ft_url(url: str) -> bool:
    url = _normalize_url(url).lower()
    if not url.startswith(("https://", "http://")):
        return False
    host = url.split("//", 1)[1].split("/", 1)[0].split("?", 1)[0]
    return host in ("www.ft.com", "ft.com", "app.ft.com")


def _extract_text(children: list) -> str:
    """Recursively extract text from a rich document node tree."""
    parts: list[str] = []
    for node in children:
        if not isinstance(node, dict):
            continue
        ntype = node.get("type", "")
        if ntype == "text":
            parts.append(node.get("value", ""))
        elif ntype == "link":
            href = node.get("url", "")
            inner = _extract_text(node.get("children", []))
            parts.append(f"[{inner}]({href})" if href else inner)
        elif ntype == "strong":
            inner = _extract_text(node.get("children", []))
            parts.append(f"**{inner}**")
        elif ntype == "emphasis":
            inner = _extract_text(node.get("children", []))
            parts.append(f"_{inner}_")
        elif "children" in node:
            parts.append(_extract_text(node["children"]))
    return "".join(parts)


class FtService(BaseService):

    def __init__(self, request: CurlRequest | None = None) -> None:
        # One client per service (services are registered as singletons), so
        # the underlying session and its connection pool are reused across
        # renders instead of being rebuilt — and torn down — every time.
        self._request = request or CurlRequest(persistent=True)

    def _is_valid(self, path: str) -> bool:
        return _is_ft_url(path)

    async def _ais_valid(self, path: str) -> bool:
        return _is_ft_url(path)

    async def _arender(self, path: str) -> str:
        url = _normalize_url(path)
        data = await ft_client.fetch_article(self._request, url)

        structured = data.get("body", {}).get("structured", {})
        body = structured.get("tree", {}).get("children", [])
        refs = structured.get("references", [])
        body_md = self._tree_to_markdown(body, data, refs)
        if len(body_md) < 50:
            raise UnsupportedContentError("no renderable body in FT article")

        return self._frontmatter(data, url) + body_md

    @classmethod
    def _tree_to_markdown(cls, children: list, article: dict, refs: list | None = None) -> str:
        out: list[str] = []
        for node in children:
            if not isinstance(node, dict):
                continue
            ntype = node.get("type", "")

            if ntype == "paragraph":
                text = _extract_text(node.get("children", []))
                if text.strip():
                    out.append(text)
            elif ntype in ("heading", "subheading", "header"):
                text = _extract_text(node.get("children", []))
                if text.strip():
                    out.append(f"## {text}")
            elif ntype == "pull-quote":
                text = _extract_text(node.get("children", []))
                if text.strip():
                    out.append(f"> {text}")
            elif ntype == "promo-box":
                text = _extract_text(node.get("children", []))
                if text.strip():
                    out.append(f"> {text}")
            elif ntype == "main-image":
                mi = article.get("mainImage") or {}
                img_url = mi.get("url", "")
                caption = mi.get("caption") or ""
                credit = mi.get("credit") or ""
                if img_url:
                    visible = " — ".join(p for p in (caption, credit) if p)
                    cap_attr = f' data-caption="{_esc(visible)}"' if visible else ""
                    figcap = f"<figcaption>{_esc(visible)}</figcaption>" if visible else ""
                    out.append(
                        f'\n<figure><img src="{_esc(img_url)}" alt="{_esc(caption or "image")}"'
                        f' loading="lazy"{cap_attr} class="prose-image"/>{figcap}</figure>\n'
                    )
            elif ntype == "image":
                img_url = node.get("url", "")
                caption = node.get("caption") or ""
                if img_url:
                    out.append(
                        f'\n<figure><img src="{_esc(img_url)}" alt="{_esc(caption or "image")}"'
                        f' loading="lazy" class="prose-image"/></figure>\n'
                    )
            elif ntype == "image-set":
                # Resolve via referenceIndex → refs[index].picture
                ref_idx = (node.get("data") or {}).get("referenceIndex")
                if refs and ref_idx is not None and ref_idx < len(refs):
                    pic = refs[ref_idx].get("picture") or {}
                    images = pic.get("images") or []
                    img_url = images[0].get("url", "") if images else ""
                    if not img_url:
                        fb = pic.get("fallbackImage") or {}
                        img_url = fb.get("url", "")
                    caption = pic.get("caption") or ""
                    credit = pic.get("credit") or ""
                    if img_url:
                        visible = " — ".join(p for p in (caption, credit) if p)
                        cap_attr = f' data-caption="{_esc(visible)}"' if visible else ""
                        figcap = f"<figcaption>{_esc(visible)}</figcaption>" if visible else ""
                        out.append(
                            f'\n<figure><img src="{_esc(img_url)}" alt="{_esc(caption or "image")}"'
                            f' loading="lazy"{cap_attr} class="prose-image"/>{figcap}</figure>\n'
                        )
            elif ntype in ("unordered-list", "ordered-list"):
                for li in node.get("children", []):
                    text = _extract_text(li.get("children", []) if isinstance(li, dict) else [])
                    if text.strip():
                        out.append(f"- {text}")
        return "\n\n".join(out)

    @staticmethod
    def _frontmatter(data: dict[str, Any], url: str) -> str:
        import yaml

        headline = data.get("topper", {}).get("headline") or data.get("title") or "Untitled"
        standfirst = data.get("standfirst", "")

        byline_tree = data.get("byline", {}).get("tree", {})
        byline_text = _extract_text(byline_tree.get("children", [])).strip()
        authors: list[dict[str, str]] = []
        if byline_text:
            authors = [{"name": byline_text}]
        if not authors:
            authors = [{"name": "Financial Times"}]

        meta: dict[str, Any] = {
            "title": headline,
            "authors": authors,
            "publication": "Financial Times",
            "is_locked": False,
            "url": url,
        }
        if standfirst:
            meta["subtitle"] = standfirst
        if data.get("publishedDate"):
            meta["date"] = data["publishedDate"]

        mi = data.get("mainImage") or {}
        if mi.get("url"):
            meta["preview_image"] = {
                "medium": mi["url"],
                "zoom": mi["url"],
                "caption": mi.get("caption") or "",
            }

        return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n"

    def _render(self, path: str) -> str:
        raise NotImplementedError("use async _arender")

    async def _asearch(self, keywords: list[str]) -> list[dict[str, str]]:
        return []

    def _search(self, keywords: list[str]) -> list[dict[str, str]]:
        return []
