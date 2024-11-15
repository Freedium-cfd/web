from fastapi import APIRouter

handler_router = APIRouter()


@handler_router.get("/render")
async def render_page():
    return "render"


def register_render_router(router: APIRouter) -> None:
    router.add_api_route(path="/render", endpoint=render_page, methods=["GET"])
