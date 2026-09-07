"""Public, read-only image proxy: GET /img/{width}/{image_id}.

Serves Medium CDN images from a Mongo cache. On a miss, fetches from
miro.medium.com through the WARP proxy (PROXY_LIST), stores, and returns.
SSRF-safe: the upstream host is hardcoded; width is allowlisted; image_id
is regex-validated. Browser never contacts Medium.
"""
from __future__ import annotations

import asyncio
import os
import re
import subprocess

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from loguru import logger

from freedium_library.utils.cache.db.image_cache import ImageCacheBackend

# Widths we actually emit (feed covers 800/1400; article body 700/2000/4000).
_ALLOWED_WIDTHS = {700, 800, 1400, 2000, 4000}
# Medium image ids: alphanumeric, '*', '.', '-', '_', and '@' (retina
# suffix like "@2x"). Never a slash/scheme; '@' sits in the URL path after
# the hardcoded host, so it can't act as a userinfo separator.
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._*@-]{0,200}$")
# _MAX_BYTES now in _img_config.MAX_BYTES (Pydantic default: 15 MiB)

# Strict raster allowlist. We serve these bytes from OUR origin, so an
# image/svg+xml (which can carry <script>) would be stored XSS on our
# domain. Only allow inert raster types; reject everything else.
_SAFE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/avif"}

# nosniff + inline + immutable. nosniff stops the browser from
# re-interpreting bytes as a different (scriptable) type.
_RESP_HEADERS = {
    "Cache-Control": "public, max-age=31536000, immutable",
    "X-Content-Type-Options": "nosniff",
    "Content-Disposition": "inline",
}

# _UA replaced by _img_config.UA (Pydantic ImageProxyConfig)

_backend: ImageCacheBackend | None = None


def _safe_type(raw: str) -> str | None:
    """Return the allowlisted content-type, or None if not a safe raster type."""
    ct = (raw or "").split(";")[0].strip().lower()
    return ct if ct in _SAFE_TYPES else None


def _get_backend() -> ImageCacheBackend:
    global _backend
    if _backend is None:
        _backend = ImageCacheBackend(
            connection_string=os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
            database=os.environ.get("MONGO_DB", "freedium_cache"),
        )
    return _backend


def _jxl_to_jpeg(jxl: bytes) -> bytes:
    """Decode JXL → JPEG via djxl (temp files). Runs in thread-pool executor.
    djxl's --pixels_to_jpeg needs a named output file (can't auto-detect
    format from stdin/stdout). ~12-80ms per call."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".jxl", delete=False) as f_in:
        f_in.write(jxl)
        in_path = f_in.name
    out_path = in_path + ".jpg"
    try:
        subprocess.run(
            ["djxl", "--pixels_to_jpeg", in_path, out_path],
            capture_output=True, check=True, timeout=15,
        )
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(in_path)
        except OSError:
            pass
        try:
            os.unlink(out_path)
        except OSError:
            pass


from freedium_library.api.config import ImageProxyConfig

_img_config = ImageProxyConfig()

_REDIRECT_HEADERS: dict[str, str] = {
    "Cache-Control": "public, max-age=31536000, immutable",
    "Referrer-Policy": "no-referrer",
}


def _proxy() -> str | None:
    from freedium_library.utils.http import get_warp_proxy

    return get_warp_proxy()


# Unified source-prefixed redirect map. Each entry's CDN host is hardcoded
# (SSRF-safe); the request path is appended verbatim. Used by /img/{source}/.
_IMG_SOURCES: dict[str, str] = {
    "medium": "https://miro.medium.com/v2/resize:fit:",  # rest = {width}/{id}
    "nyt": "https://static01.nyt.com/",                   # rest = {path}
    "wapo": "https://cloudfront-us-east-1.images.arcpublishing.com/wapo/",
    "wapo-legacy": "https://img.washingtonpost.com/",
    "bbg": "https://assets.bwbx.io/",
    "reuters": "https://cloudfront-us-east-2.images.arcpublishing.com/reuters/",
    "economist": "https://www.economist.com/cdn-cgi/image/",
    "economist-static": "https://cdn.static-economist.com/",
    "ft": "https://images.ft.com/",
    "ft-cdn": "https://d1e00ek4ebabms.cloudfront.net/",
}


def register_images_router(app: FastAPI) -> None:
    # Legacy numeric route registered FIRST so the bare /img/{width}/{id} form
    # (baked into millions of cached Medium markdown docs) keeps working. The
    # {width:int} convertor only matches a numeric first segment, so source-
    # prefixed paths (/img/medium/…, /img/nyt/…) fall through to the unified
    # route registered at the end of this function.
    @app.get("/img/{width:int}/{image_id}", include_in_schema=False)
    async def get_image(width: int, image_id: str, request: Request) -> Response:
        if width not in _ALLOWED_WIDTHS:
            raise HTTPException(status_code=400, detail="unsupported width")
        if not _ID_RE.match(image_id):
            raise HTTPException(status_code=400, detail="invalid image id")

        if _img_config.SERVE_MODE == "redirect":
            from fastapi.responses import RedirectResponse
            return RedirectResponse(
                url=f"{_img_config.CDN_BASE}:{width}/{image_id}",
                status_code=307,
                headers=_REDIRECT_HEADERS,
            )

        key = f"{width}:{image_id}"
        backend = _get_backend()

        try:
            cached = await backend.aget(key)
        except Exception as exc:  # cache read failure → treat as miss
            logger.warning(f"image_cache read failed for {key}: {exc!r}")
            cached = None

        if cached is not None:
            data, content_type = cached
            # JXL stored: serve natively to supporting browsers, fall back to
            # on-the-fly JPEG for Firefox/legacy via djxl (12ms decode).
            if content_type == "image/jxl":
                accept = request.headers.get("accept", "")
                # Only serve JXL natively if the client explicitly advertises
                # image/jxl support. No wildcard matching — clients that send
                # image/* or */* but don't list image/jxl get the JPEG fallback.
                supports_jxl = any(
                    mt.strip() == "image/jxl"
                    for mt in accept.split(",")
                )
                if supports_jxl:
                    from freedium_library.api.metrics import IMAGE_SERVE, JXL_SERVE
                    JXL_SERVE.labels(format="jxl").inc()
                    IMAGE_SERVE.labels(format="jxl_native").inc()
                    return Response(content=data, media_type="image/jxl",
                                    headers=_RESP_HEADERS)
                # Firefox fallback
                try:
                    loop = asyncio.get_running_loop()
                    jpeg = await loop.run_in_executor(None, _jxl_to_jpeg, data)
                    from freedium_library.api.metrics import IMAGE_SERVE, JXL_SERVE
                    JXL_SERVE.labels(format="jpeg_fallback").inc()
                    IMAGE_SERVE.labels(format="jxl_fallback").inc()
                    return Response(content=jpeg, media_type="image/jpeg",
                                    headers=_RESP_HEADERS)
                except Exception:
                    logger.error(f"jxl fallback decode failed for {key}")
                    from freedium_library.api.metrics import JXL_SERVE
                    JXL_SERVE.labels(format="fallback_error").inc()
                    # Serve JXL bytes anyway — better than a broken-image 502
                    return Response(content=data, media_type="image/jxl",
                                    headers=_RESP_HEADERS)

            # Stored types are already allowlisted, but normalize defensively.
            from freedium_library.api.metrics import IMAGE_SERVE
            safe = _safe_type(content_type) or "image/jpeg"
            fmt = (safe or "image/jpeg").split("/")[-1]  # "png", "jpeg", "gif", "webp"
            IMAGE_SERVE.labels(format=fmt).inc()
            return Response(content=data, media_type=safe, headers=_RESP_HEADERS)

        # Miss → fetch from Medium CDN. Host is hardcoded and redirects are
        # NOT followed (an off-host 3xx would be an SSRF vector). Body is
        # streamed with a hard byte cap to bound memory.
        upstream = f"https://miro.medium.com/v2/resize:fit:{width}/{image_id}"
        try:
            async with httpx.AsyncClient(
                proxy=_proxy(),
                timeout=25.0,
                follow_redirects=False,
                headers={"User-Agent": _img_config.UA},
            ) as client:
                async with client.stream("GET", upstream) as resp:
                    if resp.status_code != 200:
                        code = resp.status_code if resp.status_code in (403, 404) else 502
                        raise HTTPException(status_code=code, detail="upstream error")

                    content_type = _safe_type(resp.headers.get("content-type", ""))
                    if content_type is None:
                        raise HTTPException(status_code=502, detail="unsupported image type")

                    declared = resp.headers.get("content-length")
                    if declared is not None and declared.isdigit() and int(declared) > _img_config.MAX_BYTES:
                        raise HTTPException(status_code=502, detail="image too large")

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in resp.aiter_bytes():
                        total += len(chunk)
                        if total > _img_config.MAX_BYTES:
                            raise HTTPException(status_code=502, detail="image too large")
                        chunks.append(chunk)
                    data = b"".join(chunks)
        except HTTPException:
            raise  # preserve the specific status (400/404/502/...)
        except Exception as exc:
            logger.warning(f"image fetch failed for {key}: {exc!r}")
            raise HTTPException(status_code=502, detail="upstream image fetch failed")

        try:
            await backend.aput(key, data, content_type)
        except Exception as exc:  # cache write failure must not break the response
            logger.warning(f"image_cache write failed for {key}: {exc!r}")

        return Response(content=data, media_type=content_type, headers=_RESP_HEADERS)

    # Unified source-prefixed redirect — registered AFTER the numeric legacy
    # route so /img/{width}/{id} keeps matching that. Handles /img/medium/…
    # (new Medium renders) and /img/nyt/… (NYT CDN). 307 → source CDN host
    # (hardcoded, SSRF-safe), no-referrer + immutable.
    @app.get("/img/{source}/{rest:path}", include_in_schema=False)
    async def get_image_src(source: str, rest: str) -> Response:
        from fastapi.responses import RedirectResponse

        base = _IMG_SOURCES.get(source)
        if base is None:
            raise HTTPException(status_code=404, detail="unknown image source")
        return RedirectResponse(
            url=base + rest, status_code=307, headers=_REDIRECT_HEADERS
        )
