import asyncio
import time

from beartype import beartype
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from loguru import logger
from pydantic import BaseModel

from freedium_library.api.blocked_domains import is_blocked_domain
from freedium_library.api.error_log import log_errored_link, log_successful_render
from freedium_library.api.metrics import (
    ARTICLE_RENDER,
    RENDERED_CACHE_HITS,
    RENDERED_CACHE_MISSES,
    track_render,
)
from freedium_library.services.medium import MediumService
from freedium_library.services.medium.container import MediumContainer
from freedium_library.services.medium.exceptions import InvalidMediumServicePathError
from freedium_library.services.recent_posts import RecentPostsService
from freedium_library.services.resolver import ServiceResolver, ServiceResolutionError

# How long to render inline before handing off to the TaskIQ worker.
# L1-warm renders (the common case) finish in well under this budget and
# are returned directly. Only genuinely-cold renders (L1 miss → slow Medium
# GraphQL fetch through WARP) exceed it and get dispatched to the worker.
INLINE_BUDGET = 3.0


class RenderRequest(BaseModel):
    """Request body for universal render endpoint."""

    content: str
    frontmatter: bool = False


class RenderResponse(BaseModel):
    """Response from render endpoint."""

    markdown: str = ""
    service: str = ""
    cache_status: str = "miss"
    task_id: str | None = None  # set when render is dispatched to TaskIQ (202)


async def _record_recent(
    request: Request | None, metadata: object
) -> None:
    """Push a rendered post's metadata into the recent-posts feed.

    Best-effort: any failure (no service wired up, lock contention, etc.)
    must never break the render response — recent posts is decorative.
    The service is read off app.state because it's instantiated by the
    lifespan singleton, not the per-request DI container.
    """
    if request is None:
        return
    service: RecentPostsService | None = getattr(
        request.app.state, "recent_posts_service", None
    )
    if service is None:
        return
    try:
        await service.record(metadata)  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001 — defensive: never break render
        logger.warning(f"Failed to record recent post: {exc}")


@beartype
@inject
async def render_medium_post(
    post_id: str,
    include_frontmatter: bool = False,
    request: Request | None = None,
    medium_service: MediumService = Provide[MediumContainer.service],
) -> PlainTextResponse:
    """
    Render a Medium post to Markdown format.

    Args:
        post_id: The Medium post ID or URL to render
        include_frontmatter: Whether to include YAML frontmatter
        request: The HTTP request (used to access app state for recent-posts feed)
        medium_service: The Medium service instance (injected)

    Returns:
        Rendered Markdown content
    """
    with track_render(ARTICLE_RENDER) as ctx:
        try:
            # Use the *_and_metadata variants so we capture PostMetadata in the same
            # GraphQL fetch — no extra round-trip just for the recent-posts feed.
            if include_frontmatter:
                content, metadata = (
                    await medium_service.arender_with_frontmatter_and_metadata(post_id)
                )
            else:
                content, metadata = await medium_service.arender_with_metadata(post_id)

            await _record_recent(request, metadata)
            client_ua = request.headers.get("User-Agent", "") if request else ""
            log_successful_render(post_id, "inline", client_ua)
            return PlainTextResponse(content=content, media_type="text/markdown")

        except InvalidMediumServicePathError as e:
            ctx.set_outcome("parser_failure")
            client_ua = request.headers.get("User-Agent", "") if request else ""
            log_errored_link(post_id, "parser_failure", None, str(e), client_ua=client_ua)
            raise HTTPException(status_code=404, detail=str(e)) from e


@beartype
async def render_universal(
    http_request: Request,
    request: RenderRequest,
) -> RenderResponse:
    """
    Universal render endpoint that detects service and renders content.

    Args:
        http_request: The HTTP request object (contains app state)
        request: Request containing content string and options

    Returns:
        Rendered markdown and service name

    Raises:
        HTTPException 404: If no service can handle the content
        HTTPException 500: If rendering fails
    """
    # Reject sites that are definitely not paywalled articles (YouTube,
    # social, search, shopping) before burning any fetch/render work.
    # Proxies/SvelteKit collapse the // in URLs → https:/host; normalize here
    # so the L2 cache key matches the key the service stored under.
    import re as _re

    request.content = _re.sub(r"^(https?):/+", r"\1://", request.content.strip())

    if await is_blocked_domain(request.content):
        from freedium_library.api.blocked_domains import _host

        host = _host(request.content)
        if host == "wsj.com" or host.endswith(".wsj.com"):
            raise HTTPException(
                status_code=422, detail="The Wall Street Journal is not supported"
            )
        if host == "substack.com" or host.endswith(".substack.com"):
            raise HTTPException(
                status_code=422, detail="Substack is not supported"
            )
        if host == "wired.com" or host.endswith(".wired.com"):
            raise HTTPException(
                status_code=422, detail="Wired is not supported"
            )
        raise HTTPException(status_code=422, detail="unsupported_site")

    # The real browser/bot UA, forwarded by SvelteKit SSR as X-Client-UA.
    # Falls back to the direct User-Agent header (covers internal/testing
    # calls that bypass the web tier).
    client_ua = http_request.headers.get(
        "X-Client-UA", http_request.headers.get("User-Agent", "")
    )
    t0 = time.perf_counter()

    # --- L2: rendered-output cache ---
    import json as _json

    rendered_cache = getattr(http_request.app.state, "rendered_cache", None)
    if rendered_cache is not None:
        try:
            cached = await rendered_cache.apull(request.content)
            if cached is not None:
                data = _json.loads(cached.value)
                RENDERED_CACHE_HITS.inc()
                has_embedded = "data:image" in data["markdown"]
                cache_status = f"l2_hit_{'embedded' if has_embedded else 'cdn'}"
                log_successful_render(
                    request.content, cache_status, client_ua,
                    render_ms=(time.perf_counter() - t0) * 1000,
                )
                return RenderResponse(
                    markdown=data["markdown"],
                    service=data["service"],
                    cache_status=cache_status,
                )
        except Exception:
            pass  # treat L2 read failure as a miss
    RENDERED_CACHE_MISSES.inc()

    from freedium_library.tasks.cache import render_article_async

    async def _render_inline(timeout: float | None) -> RenderResponse:
        """Resolve + render the content, optionally under a time budget.

        When `timeout` is set, each render coroutine is wrapped in
        `asyncio.wait_for`; a slow (cold) render raises asyncio.TimeoutError
        which the caller turns into a worker hand-off. When `timeout` is
        None the render runs to completion (broker-down fallback path).
        """

        async def _wait(coro):
            # Cap concurrent renders per process. The acquire is inside the
            # wait_for budget, so when the cap is saturated a contended request
            # times out and offloads to the worker instead of blocking forever.
            from freedium_library.api.render_limit import render_semaphore

            async def _guarded():
                async with render_semaphore:
                    return await coro

            if timeout is None:
                return await _guarded()
            return await asyncio.wait_for(_guarded(), timeout=timeout)

        # Get resolver from app state
        resolver: ServiceResolver = http_request.app.state.service_resolver

        # Resolve the content to appropriate service
        service_name, service = await resolver.resolve(request.content)

        # Render using the resolved service. For Medium, use the *_and_metadata
        # variants so we can populate the recent-posts feed in the same GraphQL
        # fetch — no extra round-trip just for feed data. The render_semaphore
        # cap is applied inside _wait (under the INLINE_BUDGET), so a contended
        # burst offloads to the worker rather than thrashing the CPU.
        if service_name == "medium" and isinstance(service, MediumService):
            if request.frontmatter:
                markdown, metadata = await _wait(
                    service.arender_with_frontmatter_and_metadata(request.content)
                )
            else:
                markdown, metadata = await _wait(
                    service.arender_with_metadata(request.content)
                )
            await _record_recent(http_request, metadata)
        else:
            if request.frontmatter:
                markdown = await _wait(
                    service.arender_with_frontmatter(request.content)
                )
            else:
                markdown = await _wait(service.arender(request.content))

        # Write to L2 rendered cache (async via TaskIQ)
        if rendered_cache is not None:
            from freedium_library.tasks.cache import write_rendered_cache
            try:
                await write_rendered_cache.kiq(request.content, markdown, service_name)
            except Exception:
                pass  # broker down — fall through silently

        log_successful_render(
            request.content, "inline", client_ua,
            render_ms=(time.perf_counter() - t0) * 1000,
        )
        return RenderResponse(
            markdown=markdown, service=service_name, cache_status="inline"
        )

    with track_render(ARTICLE_RENDER) as ctx:
        try:
            # Render inline with a short budget. L1-warm articles return in
            # well under INLINE_BUDGET and never touch the worker queue.
            return await _render_inline(timeout=INLINE_BUDGET)

        except asyncio.TimeoutError:
            # Genuinely slow (cold / L1 miss). The wait_for already cancelled
            # the render. Hand off to the TaskIQ worker and let the frontend
            # poll for the result.
            try:
                dispatch = await render_article_async.kiq(
                    content=request.content,
                    frontmatter=request.frontmatter,
                )
            except Exception:
                # Broker unreachable — serve the article inline anyway,
                # just slowly (no budget). Preserve error handling below.
                try:
                    return await _render_inline(timeout=None)
                except (ServiceResolutionError, InvalidMediumServicePathError) as e:
                    ctx.set_outcome("parser_failure")
                    log_errored_link(request.content, "parser_failure", None, str(e), client_ua=client_ua)
                    raise HTTPException(status_code=404, detail=str(e)) from e
                except Exception as e:
                    ctx.set_outcome("network_error")
                    log_errored_link(request.content, "network_error", None, str(e), client_ua=client_ua)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error rendering content: {str(e)}",
                    ) from e
            return RenderResponse(
                markdown="",
                service="pending",
                cache_status="pending",
                task_id=dispatch.task_id,
            )

        except ServiceResolutionError as e:
            ctx.set_outcome("parser_failure")
            log_errored_link(request.content, "parser_failure", None, str(e), client_ua=client_ua)
            raise HTTPException(status_code=404, detail=str(e)) from e
        except InvalidMediumServicePathError as e:
            ctx.set_outcome("parser_failure")
            log_errored_link(request.content, "parser_failure", None, str(e), client_ua=client_ua)
            raise HTTPException(status_code=404, detail=str(e)) from e
        except Exception as e:
            ctx.set_outcome("network_error")
            log_errored_link(request.content, "network_error", None, str(e), client_ua=client_ua)
            raise HTTPException(
                status_code=500,
                detail=f"Error rendering content: {str(e)}",
            ) from e


def register_render_router(router: APIRouter) -> None:
    render_router = APIRouter(prefix="/render")

    # Universal endpoint - detects service automatically
    render_router.add_api_route(
        "",
        endpoint=render_universal,
        methods=["POST"],
        summary="Render content (universal)",
        description="Render any supported content type to Markdown. Automatically detects the service.",
        tags=["render"],
        response_model=RenderResponse,
    )

    # Legacy Medium-specific endpoint (kept for backwards compatibility)
    async def _render_medium(
        request: Request,
        post_id: str,
        frontmatter: bool = Query(False, description="Include YAML frontmatter"),
    ) -> PlainTextResponse:
        return await render_medium_post(
            post_id, include_frontmatter=frontmatter, request=request
        )

    render_router.add_api_route(
        "/medium/{post_id:path}",
        endpoint=_render_medium,
        methods=["GET"],
        summary="Render Medium post",
        description="Render a Medium post to Markdown format (legacy endpoint)",
        tags=["render"],
        response_class=PlainTextResponse,
    )

    # TaskIQ render poll endpoint — the frontend calls this after
    # receiving 202 {task_id} from render_universal.
    async def _poll_render_task(task_id: str):
        from freedium_library.tasks import result_backend

        try:
            ready = await result_backend.is_result_ready(task_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Task not found")

        if not ready:
            return {"status": "pending"}

        result = await result_backend.get_result(task_id)
        if result.is_err:
            # Don't leak exception details to the frontend
            return {"status": "error", "error": "Render failed — please try again"}

        data = result.return_value  # {"markdown", "service"}
        return {"status": "done", "markdown": data["markdown"], "service": data["service"]}

    render_router.add_api_route(
        "/poll/{task_id}",
        endpoint=_poll_render_task,
        methods=["GET"],
        summary="Poll a background render task",
        description=(
            "Called by the frontend while waiting for a TaskIQ-dispatched "
            "cold-cache render. Returns {status:'pending'} until the worker "
            "finishes, then {markdown,service,status:'done'} or {status:'error'}."
        ),
        tags=["render"],
    )

    router.include_router(render_router)
