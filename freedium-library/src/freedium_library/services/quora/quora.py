"""QuoraService — renders Quora posts and answers for Freedium.

Pipeline:
  public quora.com URL → fetch HTML with Chrome TLS impersonation →
  extract Relay GraphQL JSON (.push(...)) →
  sections/spans → markdown (paragraphs, headers, images, blockquotes, links) →
  frontmatter (title, author, date, tags, preview_image) →
  rewrite image URLs → /img/quora/.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
import html
import re
from typing import Any

from loguru import logger

from freedium_library.services.base import BaseService
from freedium_library.services.exceptions import ArticleNotFoundError, UnsupportedContentError
from freedium_library.services.quora import client as quora_client
from freedium_library.utils.http import CurlRequest
from freedium_library.utils.http.client.config import RequestConfig, RequestProxyConfig
from freedium_library.utils.url import escape_html as _esc, normalize_url as _normalize_url

_QUORA_IMG_PREFIX = "https://qph.cf2.quoracdn.net/"


def _is_quora_url(url: str) -> bool:
    normalized = _normalize_url(url).lower()
    if not normalized.startswith(("https://", "http://")):
        return False
    try:
        host = normalized.split("//", 1)[1].split("/", 1)[0].split("?", 1)[0]
        return host == "quora.com" or host.endswith(".quora.com")
    except Exception:
        return False


class QuoraService(BaseService):
    """Renders quora.com posts and answers into Markdown with YAML frontmatter."""

    def __init__(
        self,
        proxy: str | RequestProxyConfig | None = None,
        flaresolverr_url: str = "http://flaresolverr:8191",
    ) -> None:
        self._request = CurlRequest(config=RequestConfig.with_proxy(proxy), impersonate="chrome124", persistent=True)
        self._flaresolverr_url = flaresolverr_url

    def _is_valid(self, path: str) -> bool:
        return _is_quora_url(path)

    async def _ais_valid(self, path: str) -> bool:
        return _is_quora_url(path)

    async def _arender(self, path: str) -> str:
        url = _normalize_url(path)
        data = await quora_client.fetch_content(self._request, url, flaresolverr_url=self._flaresolverr_url)
        if not data:
            raise ArticleNotFoundError("Empty Quora response")

        doc_json = data.get("contentQtextDocument", {}).get("legacyJson")
        if not doc_json:
            # Fallback for answer objects if nested
            doc_json = data.get("answer", {}).get("contentQtextDocument", {}).get("legacyJson")

        if not doc_json:
            raise UnsupportedContentError("No readable content document in Quora post")

        try:
            doc = json.loads(doc_json)
        except Exception as e:
            raise UnsupportedContentError(f"Failed to parse Quora content document: {e}") from e

        body_md = self._doc_to_markdown(doc)
        if len(body_md.strip()) < 30:
            raise UnsupportedContentError("Rendered body too short")

        markdown = self._frontmatter(data, url) + body_md
        return markdown.replace(_QUORA_IMG_PREFIX, "/img/quora/")

    @staticmethod
    def _render_spans(spans: list[dict[str, Any]]) -> str:
        """Render a sequence of styled spans into inline markdown."""
        out: list[str] = []
        for sp in spans:
            if not isinstance(sp, dict):
                continue
            text = sp.get("text", "")
            mods = sp.get("modifiers") or {}

            # Image modifier on span
            img_url = mods.get("image")
            if img_url:
                out.append(f'\n\n<figure><img src="{_esc(img_url)}" loading="lazy" class="prose-image"/></figure>\n\n')
                continue

            if not text:
                continue

            # Code
            if mods.get("code"):
                text = f"`{text}`"
            # Bold
            if mods.get("bold"):
                text = f"**{text}**"
            # Italic
            if mods.get("italic"):
                text = f"_{text}_"
            # Strikethrough
            if mods.get("strikethrough"):
                text = f"~~{text}~~"
            # Link
            link_obj = mods.get("link")
            if isinstance(link_obj, dict):
                target_url = link_obj.get("url") or link_obj.get("target") or ""
                if target_url:
                    text = f"[{text}]({target_url})"

            out.append(text)
        return "".join(out)

    @classmethod
    def _doc_to_markdown(cls, doc: dict[str, Any]) -> str:
        """Convert Quora's sections document AST into clean Markdown."""
        sections = doc.get("sections") or []
        out: list[str] = []

        for sec in sections:
            if not isinstance(sec, dict):
                continue
            sec_type = sec.get("type", "plain")
            spans = sec.get("spans") or []
            rendered = cls._render_spans(spans).strip()

            if not rendered:
                continue

            if sec_type in ("header", "heading"):
                out.append(f"### {rendered}")
            elif sec.get("quoted") or sec_type in ("quote", "blockquote"):
                out.append(f"> {rendered}")
            elif sec_type == "code_block":
                out.append(f"```\n{rendered}\n```")
            elif sec_type == "ordered_list":
                out.append(f"1. {rendered}")
            elif sec_type in ("unordered_list", "bullet"):
                out.append(f"- {rendered}")
            else:
                out.append(rendered)

        return "\n\n".join(out)

    @staticmethod
    def _frontmatter(data: dict[str, Any], url: str) -> str:
        import yaml

        title_raw = data.get("title") or ""
        title = "Untitled"
        if title_raw:
            try:
                t_doc = json.loads(title_raw) if isinstance(title_raw, str) else title_raw
                sections = t_doc.get("sections") or []
                spans = [sp.get("text", "") for sec in sections for sp in sec.get("spans", [])]
                extracted_title = "".join(spans).strip()
                if extracted_title:
                    title = extracted_title
            except Exception:
                title = str(title_raw).strip()

        # Author extraction
        author_data = data.get("author") or {}
        author_name = "Quora"
        avatar_url = ""
        names = author_data.get("names") or []
        if names and isinstance(names, list) and isinstance(names[0], dict):
            given = names[0].get("givenName", "")
            family = names[0].get("familyName", "")
            full = f"{given} {family}".strip()
            if full:
                author_name = full

        profile_img = author_data.get("profileImageUrl")
        if profile_img:
            avatar_url = profile_img

        authors: list[dict[str, str]] = [{"name": author_name}]
        if avatar_url:
            authors[0]["avatar"] = avatar_url

        # Date / creation timestamp
        date_str = ""
        created_time = data.get("creationTime")
        if created_time:
            try:
                # Quora timestamps are usually in microseconds or seconds
                ts = int(created_time)
                if ts > 10_000_000_000:
                    ts = ts // 1_000_000
                date_str = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            except Exception:
                pass

        meta: dict[str, Any] = {
            "title": title,
            "authors": authors,
            "publication": "Quora",
            "is_locked": False,
            "url": url,
        }
        if date_str:
            meta["date"] = date_str

        # Preview image if available from content
        preview_img = ""
        doc_json = data.get("contentQtextDocument", {}).get("legacyJson")
        if doc_json:
            try:
                doc = json.loads(doc_json)
                for sec in doc.get("sections") or []:
                    for sp in sec.get("spans") or []:
                        img = (sp.get("modifiers") or {}).get("image")
                        if img:
                            preview_img = img
                            break
                    if preview_img:
                        break
            except Exception:
                pass

        if preview_img:
            meta["preview_image"] = {
                "medium": preview_img.replace(_QUORA_IMG_PREFIX, "/img/quora/"),
                "zoom": preview_img.replace(_QUORA_IMG_PREFIX, "/img/quora/"),
                "caption": title,
            }

        return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n"

    def _render(self, path: str) -> str:
        raise NotImplementedError("use async _arender")

    async def _asearch(self, keywords: list[str]) -> list[dict[str, str]]:
        return []

    def _search(self, keywords: list[str]) -> list[dict[str, str]]:
        return []
