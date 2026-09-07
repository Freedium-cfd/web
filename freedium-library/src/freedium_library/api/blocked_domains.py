"""Denylist of sites that are definitely NOT paywalled articles.

Freedium unlocks article paywalls (Medium, etc.). Pasting a YouTube / social /
search / shopping link should be rejected immediately — rather than burning a
WARP fetch + GraphQL attempt and returning a confusing 404/500.

The live list lives in the Mongo `blocked_domains` collection (ops edit it by
hand, no redeploy). It's read through a small in-process TTL cache so the
render path doesn't hit Mongo per request. `_SEED_DOMAINS` below is migrated
into the collection on startup when it's empty, and is also the fallback if
Mongo is unavailable. Matching is suffix-based, so a bare entry like
"google.com" also blocks every subdomain (mail.google.com, docs.google.com, …).
"""
from __future__ import annotations

import re
import time
from urllib.parse import urlparse

from loguru import logger

_SEED_DOMAINS: tuple[str, ...] = (
    # video
    "youtube.com", "youtu.be", "vimeo.com", "twitch.tv", "dailymotion.com",
    "rumble.com", "bilibili.com",
    # social / messaging / forums
    "x.com", "twitter.com", "facebook.com", "fb.com", "fb.watch",
    "instagram.com", "tiktok.com", "threads.net", "reddit.com", "linkedin.com",
    "pinterest.com", "snapchat.com", "t.me", "telegram.org", "whatsapp.com",
    "quora.com", "tumblr.com", "bsky.app", "mastodon.social", "discord.com",
    "discord.gg", "slack.com", "vk.com", "weibo.com", "ok.ru",
    # search / portals
    "google.com", "bing.com", "duckduckgo.com", "yahoo.com", "yandex.com",
    "baidu.com", "ecosia.org", "ask.com", "aol.com",
    # shopping
    "amazon.com", "ebay.com", "aliexpress.com", "etsy.com", "walmart.com",
    "bestbuy.com", "target.com", "flipkart.com", "shopify.com", "alibaba.com",
    "temu.com", "shein.com",
    # streaming / music
    "netflix.com", "spotify.com", "apple.com", "music.apple.com", "hulu.com",
    "disneyplus.com", "max.com", "hbomax.com", "primevideo.com", "peacocktv.com",
    "soundcloud.com", "bandcamp.com", "deezer.com",
    # dev / reference
    "github.com", "gitlab.com", "stackoverflow.com", "wikipedia.org",
    "npmjs.com", "pypi.org", "bitbucket.org", "codepen.io", "jsfiddle.net",
    "replit.com", "kaggle.com", "huggingface.co", "docker.com", "w3schools.com",
    "openstreetmap.org",
    # productivity / cloud / accounts
    "outlook.com", "office.com", "microsoft.com", "dropbox.com", "icloud.com",
    "notion.so", "cloudflare.com", "paypal.com", "stripe.com", "zoom.us",
    "adobe.com",
    # gaming
    "steampowered.com", "epicgames.com", "roblox.com",
    # unsupported publications
    "wsj.com", "substack.com",
)

# SvelteKit collapses the "//" in /https://… paths to "https:/…", so normalise
# a single-slash scheme back before parsing.
_COLLAPSED_SCHEME = re.compile(r"^(https?):/(?!/)", re.IGNORECASE)

_COLLECTION = "blocked_domains"
_TTL_SECONDS = 300
_cache: dict[str, object] = {"value": None, "at": 0.0}


def _host(url: str) -> str:
    s = _COLLAPSED_SCHEME.sub(r"\1://", url.strip())
    if "//" not in s:
        s = "https://" + s
    try:
        host = (urlparse(s).hostname or "").lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def _matches(content: str, domains: frozenset[str]) -> bool:
    """Pure, sync matcher (no I/O) — host is (a subdomain of) a denylisted
    domain. A bare Medium post id (no host) is never blocked."""
    host = _host(content)
    if not host or "." not in host:
        return False
    return any(host == d or host.endswith("." + d) for d in domains)


def _collection():
    from freedium_library.utils.mongo import get_collection

    return get_collection(_COLLECTION)


async def seed_blocked_domains() -> None:
    """Migrate _SEED_DOMAINS into Mongo when missing. Idempotent — once seeded,
    the collection is owned by ops and never auto-overwritten, but any newly
    added seed domains are inserted on startup.

    Hardened against duplicate seeding across rapid restarts: a unique index on
    `domain` makes dupes impossible, and the insert is unordered so a racing
    seed's duplicate-key errors are skipped, not fatal."""
    try:
        coll = _collection()
        await coll.create_index("domain", unique=True)  # idempotent
        existing = {
            doc["domain"]
            async for doc in coll.find({}, {"domain": 1, "_id": 0})
            if doc.get("domain")
        }
        to_insert = [
            {"domain": d, "note": "seed"}
            for d in _SEED_DOMAINS
            if d not in existing
        ]
        if to_insert:
            try:
                await coll.insert_many(to_insert, ordered=False)
                logger.info(f"blocked_domains: seeded {len(to_insert)} new domain(s)")
            except Exception:
                pass
    except Exception as exc:  # noqa: BLE001 — never crash startup over the denylist
        logger.warning(f"blocked_domains seed failed: {exc!r}")


async def get_blocked_domains() -> frozenset[str]:
    """Denylist via a 300s in-process TTL cache. Falls back to _SEED_DOMAINS if
    Mongo is empty or unavailable, so the guard always works."""
    now = time.time()
    cached = _cache.get("value")
    if cached is not None and now - float(_cache["at"]) < _TTL_SECONDS:
        return cached  # type: ignore[return-value]
    try:
        domains = {
            doc["domain"]
            async for doc in _collection().find({}, {"domain": 1, "_id": 0})
            if doc.get("domain")
        }
        value = frozenset(domains) if domains else frozenset(_SEED_DOMAINS)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"blocked_domains load failed, using seed: {exc!r}")
        value = frozenset(_SEED_DOMAINS)
    _cache["value"] = value
    _cache["at"] = now
    return value


async def is_blocked_domain(content: str) -> bool:
    return _matches(content, await get_blocked_domains())
