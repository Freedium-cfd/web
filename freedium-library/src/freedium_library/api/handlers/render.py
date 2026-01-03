from beartype import beartype
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from freedium_library.services.medium import MediumService
from freedium_library.services.medium.container import MediumContainer
from freedium_library.services.medium.exceptions import InvalidMediumServicePathError
from freedium_library.services.resolver import ServiceResolver, ServiceResolutionError


class RenderRequest(BaseModel):
    """Request body for universal render endpoint."""

    content: str
    frontmatter: bool = False


class RenderResponse(BaseModel):
    """Response from render endpoint."""

    markdown: str
    service: str


@beartype
@inject
async def render_medium_post(
    post_id: str,
    include_frontmatter: bool = False,
    medium_service: MediumService = Provide[MediumContainer.service],
) -> PlainTextResponse:
    """
    Render a Medium post to Markdown format.

    Args:
        post_id: The Medium post ID or URL to render
        include_frontmatter: Whether to include YAML frontmatter
        medium_service: The Medium service instance (injected)

    Returns:
        Rendered Markdown content
    """
    try:
        if include_frontmatter:
            content = await medium_service.arender_with_frontmatter(post_id)
        else:
            content = await medium_service.arender(post_id)

        return PlainTextResponse(content=content, media_type="text/markdown")

    except InvalidMediumServicePathError as e:
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
    try:
        # Get resolver from app state
        resolver: ServiceResolver = http_request.app.state.service_resolver

        # Resolve the content to appropriate service
        service_name, service = await resolver.resolve(request.content)

        # Render using the resolved service
        if request.frontmatter:
            markdown = await service.arender_with_frontmatter(request.content)
        else:
            markdown = await service.arender(request.content)

        return RenderResponse(markdown=markdown, service=service_name)

    except ServiceResolutionError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InvalidMediumServicePathError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
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
        post_id: str,
        frontmatter: bool = Query(False, description="Include YAML frontmatter"),
    ) -> PlainTextResponse:
        return await render_medium_post(post_id, include_frontmatter=frontmatter)

    render_router.add_api_route(
        "/medium/{post_id:path}",
        endpoint=_render_medium,
        methods=["GET"],
        summary="Render Medium post",
        description="Render a Medium post to Markdown format (legacy endpoint)",
        tags=["render"],
        response_class=PlainTextResponse,
    )

    router.include_router(render_router)
