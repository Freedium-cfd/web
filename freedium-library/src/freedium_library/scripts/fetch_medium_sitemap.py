#!/usr/bin/env python3
"""Crawl medium.com's sitemap tree and collect article URLs.

Walks the sitemap from the root index downward (sitemapindex -> nested
sitemaps -> urlset/<loc>), handling gzipped sub-sitemaps. Designed to run for
a long time and survive restarts:

  * Persistent state — the pending queue, the set of already-processed
    sitemaps, and the running URL count are checkpointed to a JSON file after
    every sitemap (atomic write). On restart it resumes from the queue and
    re-loads already-collected URLs, so it never re-emits a URL.
  * Rate limiting — a minimum delay between HTTP requests (--delay), plus
    honoring HTTP 429 Retry-After, so we don't hammer Medium.
  * Hard cap — stops at --limit URLs (default 1,000,000).
  * Graceful stop — SIGINT/SIGTERM checkpoints and exits cleanly; output is
    flushed continuously so a hard kill loses at most the current sitemap.

Usage:
    python fetch_medium_sitemap.py                       # defaults
    python fetch_medium_sitemap.py --limit 1000000 --delay 1.0 \
        --out medium-urls.txt --state medium-sitemap.state.json
    PROXY_LIST=socks5://haproxy-pb:1080 python fetch_medium_sitemap.py --proxy-from-env
    python fetch_medium_sitemap.py --filter '/[a-z0-9]{12}$'   # post-id-looking URLs only

Env:
    PROXY_LIST   comma-separated; first entry used when --proxy-from-env is set.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import signal
import sys
import time

import httpx

# Prefer defusedxml (immune to XXE / billion-laughs). Fall back to stdlib with
# an explicit DTD/entity reject guard — sitemap XML never declares either.
try:
    import defusedxml.ElementTree as ET  # type: ignore

    _DEFUSED = True
except ImportError:
    import xml.etree.ElementTree as ET  # noqa: S405

    _DEFUSED = False

_DTD_RE = re.compile(rb"<!(?:DOCTYPE|ENTITY)", re.IGNORECASE)

DEFAULT_ROOT = "https://medium.com/sitemap/sitemap.xml"
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_GZIP_MAGIC = b"\x1f\x8b"


# --------------------------------------------------------------------------- #
# state
# --------------------------------------------------------------------------- #
class State:
    """Crawl progress, checkpointed atomically to a JSON file."""

    def __init__(self, path: str, root: str):
        self.path = path
        self.pending: list[str] = [root]
        self.pending_set: set[str] = {root}
        self.done: set[str] = set()
        self.count: int = 0

    @classmethod
    def load_or_init(cls, path: str, root: str) -> "State":
        s = cls(path, root)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            s.pending = data.get("pending", [root])
            s.pending_set = set(s.pending)
            s.done = set(data.get("done", []))
            s.count = int(data.get("count", 0))
            print(
                f"[state] resumed: {len(s.pending)} pending, "
                f"{len(s.done)} done, {s.count} urls",
                flush=True,
            )
        return s

    def save(self) -> None:
        tmp = f"{self.path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(
                {"pending": self.pending, "done": sorted(self.done), "count": self.count},
                f,
            )
        os.replace(tmp, self.path)  # atomic

    def enqueue(self, url: str) -> None:
        if url not in self.done and url not in self.pending_set:
            self.pending.append(url)
            self.pending_set.add(url)

    def next(self) -> str | None:
        while self.pending:
            url = self.pending.pop(0)
            self.pending_set.discard(url)
            if url not in self.done:
                return url
        return None


# --------------------------------------------------------------------------- #
# fetch + parse
# --------------------------------------------------------------------------- #
class RateLimiter:
    def __init__(self, delay: float):
        self.delay = delay
        self._last = 0.0

    def wait(self) -> None:
        if self.delay <= 0:
            return
        gap = self.delay - (time.monotonic() - self._last)
        if gap > 0:
            time.sleep(gap)
        self._last = time.monotonic()


def fetch(client: httpx.Client, url: str, limiter: RateLimiter, retries: int = 4) -> bytes:
    """GET a sitemap, rate-limited, with retries + 429 Retry-After handling.
    Transparently gunzips .gz sub-sitemaps."""
    for attempt in range(retries):
        limiter.wait()
        try:
            r = client.get(url)
        except httpx.HTTPError as e:
            if attempt == retries - 1:
                raise
            time.sleep(2**attempt)
            print(f"[warn] {type(e).__name__} on {url}; retry {attempt + 1}", flush=True)
            continue
        if r.status_code == 429:
            wait = int(r.headers.get("retry-after", 2**attempt))
            print(f"[warn] 429 on {url}; sleeping {wait}s", flush=True)
            time.sleep(wait)
            continue
        if r.status_code >= 500:
            if attempt == retries - 1:
                r.raise_for_status()
            time.sleep(2**attempt)
            continue
        r.raise_for_status()
        body = r.content
        if body[:2] == _GZIP_MAGIC:
            body = gzip.decompress(body)
        return body
    raise RuntimeError(f"exhausted retries for {url}")


def classify(xml_bytes: bytes) -> tuple[str, list[str]]:
    """Return ('index', child_sitemaps) or ('urls', locs). Namespace-agnostic."""
    if not _DEFUSED and _DTD_RE.search(xml_bytes):
        # No defusedxml available and the doc declares a DTD/entity — refuse
        # rather than feed the stdlib parser an XXE / billion-laughs vector.
        raise ValueError("sitemap contains a DTD/entity declaration; refusing to parse")
    root = ET.fromstring(xml_bytes)
    root_tag = root.tag.rsplit("}", 1)[-1]
    locs = [
        el.text.strip()
        for el in root.iter()
        if el.tag.rsplit("}", 1)[-1] == "loc" and el.text and el.text.strip()
    ]
    return ("index" if root_tag == "sitemapindex" else "urls"), locs


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def load_seen(out_path: str) -> set[str]:
    """Re-load already-emitted URLs so a resume never re-emits one."""
    seen: set[str] = set()
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    seen.add(line)
        print(f"[out] loaded {len(seen)} existing urls from {out_path}", flush=True)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser(description="Crawl medium.com sitemap for article URLs.")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="root sitemap URL")
    ap.add_argument("--limit", type=int, default=1_000_000, help="max URLs to collect")
    ap.add_argument("--out", default="medium-urls.txt", help="output file (append, one URL/line)")
    ap.add_argument("--state", default="medium-sitemap.state.json", help="state file")
    ap.add_argument("--delay", type=float, default=1.0, help="min seconds between requests")
    ap.add_argument("--timeout", type=float, default=30.0, help="per-request timeout (s)")
    ap.add_argument("--filter", default=None, help="regex; only URLs matching are kept")
    ap.add_argument("--proxy-from-env", action="store_true", help="use PROXY_LIST[0] as proxy")
    args = ap.parse_args()

    pat = re.compile(args.filter) if args.filter else None
    proxy = None
    if args.proxy_from_env:
        from freedium_library.utils.http import get_warp_proxy

        proxy = get_warp_proxy()

    state = State.load_or_init(args.state, args.root)
    seen = load_seen(args.out)
    if state.count != len(seen):  # reconcile (output is source of truth)
        state.count = len(seen)

    stop = {"flag": False}

    def _stop(signum, _frame):
        print(f"\n[signal] {signal.Signals(signum).name} — checkpointing & exiting", flush=True)
        stop["flag"] = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    limiter = RateLimiter(args.delay)
    headers = {"User-Agent": DEFAULT_UA, "Accept": "application/xml,text/xml,*/*"}
    out = open(args.out, "a", encoding="utf-8")
    processed = 0
    start = time.monotonic()

    with httpx.Client(
        headers=headers, timeout=args.timeout, follow_redirects=True, proxy=proxy
    ) as client:
        while not stop["flag"] and state.count < args.limit:
            sm = state.next()
            if sm is None:
                print("[done] sitemap tree exhausted", flush=True)
                break
            try:
                body = fetch(client, sm, limiter)
                kind, locs = classify(body)
            except Exception as e:  # noqa: BLE001 — skip a bad sitemap, keep going
                print(f"[err] {sm}: {type(e).__name__}: {e}", flush=True)
                state.done.add(sm)
                state.save()
                continue

            if kind == "index":
                for u in locs:
                    state.enqueue(u)
            else:
                for u in locs:
                    if state.count >= args.limit:
                        break
                    if u in seen or (pat and not pat.search(u)):
                        continue
                    seen.add(u)
                    out.write(u + "\n")
                    state.count += 1

            out.flush()
            os.fsync(out.fileno())
            state.done.add(sm)
            state.save()

            processed += 1
            if processed % 20 == 0:
                rate = state.count / max(time.monotonic() - start, 1e-9)
                print(
                    f"[progress] {state.count} urls | {len(state.pending)} pending "
                    f"| {len(state.done)} sitemaps done | {rate:.0f} url/s",
                    flush=True,
                )

    out.close()
    state.save()
    print(
        f"[exit] {state.count} urls collected -> {args.out} "
        f"(pending {len(state.pending)}; rerun to continue)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
