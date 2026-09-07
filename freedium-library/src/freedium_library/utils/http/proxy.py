"""Centralized WARP proxy balancer configuration and resolution."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freedium_library.utils.http.client.config import RequestProxyConfig


def get_warp_proxy() -> str | None:
    """Return the primary WARP proxy balancer URL, or None when unset.

    Prefers WARP_PROXY_BALANCER; falls back to legacy PROXY_LIST for
    backward compatibility. If comma-separated, takes the first entry.
    """
    raw = os.environ.get("WARP_PROXY_BALANCER", "").strip()
    if not raw:
        raw = os.environ.get("PROXY_LIST", "").strip()
    if not raw:
        return None
    first = raw.split(",")[0].strip()
    return first or None


def get_warp_proxy_config() -> RequestProxyConfig | None:
    """Return the primary RequestProxyConfig for the WARP proxy balancer, or None."""
    from freedium_library.utils.http.client.config import RequestProxyConfig

    return RequestProxyConfig.from_url(get_warp_proxy())
