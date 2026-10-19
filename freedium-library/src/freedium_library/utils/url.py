"""URL and HTML escaping utilities."""
from __future__ import annotations

import html
import re

_COLLAPSED_SCHEME_RE = re.compile(r"^(https?):/+(?!/)", re.IGNORECASE)


def normalize_url(path: str) -> str:
    """Normalize article URLs.

    Restores collapsed slashes (e.g. SvelteKit / proxy converting
    https://host/... -> https:/host/...) and ensures a proper scheme.
    """
    url = path.strip()
    url = _COLLAPSED_SCHEME_RE.sub(r"\1://", url)
    if url.startswith(("http://", "https://")):
        return url
    if url.startswith("//"):
        return f"https:{url}"
    return f"https://{url}"


def escape_html(text: str) -> str:
    """Escape text for embedding safely in HTML/XML tags or attributes."""
    return html.escape(text, quote=True)
