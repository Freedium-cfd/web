from enum import Enum
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .render_content import ARTICLE_PAYLOAD, TEXT


class ServiceName(str, Enum):
    MEDIUM = "medium"
    TWITTER = "twitter"


async def render_page(service_name: ServiceName) -> JSONResponse:
    return JSONResponse(
        content={
            "text": TEXT,
            "service_name": service_name.value,
            "article": ARTICLE_PAYLOAD,
        }
    )


def register_render_router(router: APIRouter) -> None:
    render_router = APIRouter(prefix="/services")

    async def render_service_page(service_name: ServiceName) -> JSONResponse:
        return await render_page(service_name)

    for method in ["GET", "HEAD"]:
        render_router.add_api_route(
            "/{service_name}/render",
            endpoint=render_service_page,
            methods=[method],
            summary="Render service page",
            description="Render service page",
            operation_id=f"render_page_{method}",
            tags=["render"],
        )

    router.include_router(render_router)
