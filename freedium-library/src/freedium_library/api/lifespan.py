import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from dependency_injector import providers

from freedium_library.api.config import CacheConfig
from freedium_library.api.container import APIContainer
from freedium_library.api.error_log import register_error_log_sink
from freedium_library.api.handlers import articles, download, render
from freedium_library.services.cache.container import CacheContainer
from freedium_library.services.medium import MediumService
from freedium_library.services.medium.container import MediumContainer
from freedium_library.services.recent_posts.container import RecentPostsContainer
from freedium_library.services.recent_posts.seed_urls import SEED_URLS
from freedium_library.services.recent_posts.service import RecentPostsService
from freedium_library.services.resolver import ServiceResolver

api_container = APIContainer()
cache_container = CacheContainer()
medium_container = MediumContainer()
recent_posts_container = RecentPostsContainer()

_cache_settings = CacheConfig()
if _cache_settings.CACHE_ENABLED:
    medium_container.cache_backend.override(cache_container.graphql_backend)
else:
    medium_container.cache_backend.override(providers.Object(None))


async def _warmup_recent_feed(
    medium_service: MediumService,
    recent_posts_service: RecentPostsService,
    urls: list[str],
) -> None:
    """Render each seed URL through the medium service and record the
    resulting metadata into the recent-posts feed. Best-effort: any URL
    that fails (Medium unreachable, post deleted, etc.) is logged and
    skipped — warmup is non-essential, so we never crash the app over it.
    """
    if not urls:
        return
    logger.info(f"Warming up recent-posts feed from {len(urls)} URL(s)")
    for url in urls:
        try:
            _, metadata = await medium_service.arender_with_metadata(url)
            await recent_posts_service.record(metadata)
            logger.info(f"Warmup: recorded {metadata.post_id} ({metadata.title[:60]})")
        except Exception as exc:  # noqa: BLE001 — best-effort; never crash on warmup
            logger.warning(f"Warmup failed for {url}: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    register_error_log_sink()

    # Memory-leak diagnostics: TRACEMALLOC=1 enables per-worker allocation
    # tracking, surfaced via GET /internal/memtrace (secret-gated). Off by
    # default — tracemalloc adds ~5-10% overhead.
    import os

    if os.environ.get("TRACEMALLOC", "").lower() in ("1", "true"):
        import tracemalloc

        tracemalloc.start(25)

    # Migrate the non-article domain denylist into Mongo when empty (ops own
    # it thereafter). Best-effort: never crash startup over it.
    from freedium_library.api.blocked_domains import seed_blocked_domains

    await seed_blocked_domains()

    # TaskIQ result backend — used by /render/poll/{task_id} to check
    # render results produced by the worker process. Startup ensures
    # the Redis connection pool is warm.
    from freedium_library.tasks import result_backend as _rb

    try:
        await _rb.startup()
    except Exception:
        pass  # Redis unavailable — poll endpoint returns 404

    app.state.container = api_container
    app.state.cache_container = cache_container
    app.state.medium_container = medium_container
    app.state.recent_posts_container = recent_posts_container

    if _cache_settings.CACHE_ENABLED:
        try:
            await cache_container.graphql_backend().ainit_db()
            logger.info(
                f"Post cache enabled: {_cache_settings.MONGO_URL} "
                f"db={_cache_settings.MONGO_DB} coll={_cache_settings.MONGO_COLLECTION}"
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Cache init failed; render will proceed cache-less: {exc}")
        try:
            rendered_cache = cache_container.rendered_backend()
            await rendered_cache.ainit_db()
            app.state.rendered_cache = rendered_cache
            logger.info("Rendered-output cache (L2) enabled")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Rendered cache init failed: {exc}")
            app.state.rendered_cache = None
    else:
        logger.info("Post cache disabled (CACHE_ENABLED=false)")
        app.state.rendered_cache = None
    recent_posts_service = recent_posts_container.service()
    app.state.recent_posts_service = recent_posts_service

    # Initialize service resolver
    resolver = ServiceResolver()

    # Register specific-host services BEFORE Medium. Medium's validator is
    # permissive — it accepts any URL and tries to resolve it as a Medium
    # post, so it must be last to avoid stealing FT/NYT/WaPo/etc. URLs.
    medium_service = medium_container.service()
    from freedium_library.utils.http import get_warp_proxy

    warp_proxy = get_warp_proxy()

    # The Athletic (opt-in). Before NYT: its articles live under
    # nytimes.com/athletic/. NytService's path rules don't claim those today,
    # but registering first keeps that true if those rules ever loosen.
    from freedium_library.api.config import AthleticConfig

    _ath_cfg = AthleticConfig()
    if _ath_cfg.ENABLED:
        from freedium_library.services.athletic import AthleticService

        resolver.register("athletic", AthleticService(mdream_url=_ath_cfg.MDREAM_URL))
        logger.info("Athletic service registered")

    # NYT (opt-in). Needs NYT_SIGNING_KEY in env (the RSA signing key, never
    # committed); without it the client can't sign → leave unregistered.
    from freedium_library.api.config import NytConfig

    _nyt_cfg = NytConfig()
    if _nyt_cfg.ENABLED:
        from freedium_library.services.nyt import NytService
        from freedium_library.services.nyt import client as _nyt_client

        if _nyt_client._NYT_PRIVATE_KEY is not None:
            resolver.register(
                "nyt", NytService(proxy=warp_proxy, mdream_url=_nyt_cfg.MDREAM_URL)
            )
            logger.info("NYT service registered (egress via WARP)")
        else:
            logger.warning("NYT_ENABLED but NYT_SIGNING_KEY missing/invalid — NYT not registered")

    # WaPo (opt-in). No auth/signing needed — the Rainbow API is open.
    from freedium_library.api.config import WapoConfig

    if WapoConfig().ENABLED:
        from freedium_library.services.wapo import WapoService

        resolver.register("wapo", WapoService())
        logger.info("WaPo service registered")

    # Financial Times (opt-in). Unauthenticated mobile app API.
    from freedium_library.api.config import FtConfig

    if FtConfig().ENABLED:
        from freedium_library.services.ft import FtService

        resolver.register("ft", FtService())
        logger.info("FT service registered")

    # The Economist (opt-in). HMAC-signed GraphQL + curl_cffi web fallback.
    from freedium_library.api.config import EconomistConfig

    if EconomistConfig().ENABLED:
        from freedium_library.services.economist import EconomistService

        resolver.register("economist", EconomistService())
        logger.info("Economist service registered")

    # Reuters (opt-in). No auth — ?outputType=json on any Reuters URL.
    from freedium_library.api.config import ReutersConfig

    if ReutersConfig().ENABLED:
        from freedium_library.services.reuters import ReutersService

        resolver.register("reuters", ReutersService(proxy=warp_proxy))
        logger.info("Reuters service registered")

    # Bloomberg (opt-in). Mobile CDN API with CurlRequest + WARP.
    from freedium_library.api.config import BloombergConfig

    if BloombergConfig().ENABLED:
        from freedium_library.services.bloomberg import BloombergService

        resolver.register("bloomberg", BloombergService(proxy=warp_proxy))
        logger.info("Bloomberg service registered")

    # Medium LAST — its validator is permissive (accepts any URL, tries to
    # resolve as a Medium post). Specific-host services must match first.
    from freedium_library.api.config import MediumConfig

    if MediumConfig().ENABLED:
        resolver.register("medium", medium_service)
        logger.info("Medium service registered (last — catch-all)")
    else:
        logger.info("Medium service disabled (MEDIUM_ENABLED=false)")

    app.state.service_resolver = resolver

    # Wire dependency injection to modules
    medium_container.wire(modules=[download, render])
    recent_posts_container.wire(modules=[articles])

    # Warm up the recent-posts feed in the background so the home page
    # shows real article metadata when Medium is reachable. Non-blocking:
    # the API starts serving immediately even while warmup is in flight.
    if os.environ.get("FREEDIUM_DISABLE_WARMUP", "").lower() in ("1", "true", "yes"):
        warmup_task = None
    else:
        warmup_task = asyncio.create_task(
            _warmup_recent_feed(medium_service, recent_posts_service, SEED_URLS)
        )

    yield

    # Cancel background tasks
    if warmup_task is not None and not warmup_task.done():
        warmup_task.cancel()
        try:
            await warmup_task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass

    # Unwire on shutdown
    medium_container.unwire()
    recent_posts_container.unwire()

    try:
        await _rb.shutdown()
    except Exception:
        pass

    if _cache_settings.CACHE_ENABLED:
        try:
            await cache_container.graphql_backend().aclose()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Cache close failed: {exc}")
        if getattr(app.state, "rendered_cache", None):
            try:
                await app.state.rendered_cache.aclose()
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Rendered cache close failed: {exc}")
