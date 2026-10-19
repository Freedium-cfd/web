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

    # Initialize service resolver using centralized factory
    from freedium_library.services.resolver import build_service_resolver
    from freedium_library.utils.http import get_warp_proxy

    medium_service = medium_container.service()
    warp_proxy = get_warp_proxy()
    resolver = build_service_resolver(proxy=warp_proxy, medium_service=medium_service)

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
