from fastapi import APIRouter, FastAPI

from .render import register_render_router


def register_router(app: FastAPI, router_prefix: str) -> None:
    router = APIRouter(prefix=router_prefix)
    register_render_router(router)

    app.include_router(router)
