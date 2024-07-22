from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from html5lib import serialize
from html5lib.html5parser import parse
from loguru import logger

from server import config
from server.handlers.misc import delete_from_cache, report_problem
from server.handlers.post import render_medium_post_link, render_homepage
from server.handlers.reverse_proxy import iframe_proxy, miro_proxy
from server.services.jinja import base_template, main_template
from server.utils.logger_trace import trace


@trace
async def route_processing(path: str, request: Request):
    if not path:
        return await main_page()

    query_params = request.query_params
    redis = not "no-redis" in query_params
    db_cache = not "no-db-cache" in query_params

    logger.trace(f"no_cache: {db_cache}, no_redis: {redis}")

    path = path.removeprefix("/")
    url = str(request.url)

    logger.debug(f"Path: {path}, URL: {url}")
    logger.trace(request.url.netloc)
    logger.trace(request.url.scheme)

    url = url.removeprefix(f"{request.url.scheme}://{request.url.netloc}/")
    logger.trace(url)

    if not db_cache or not redis:
        key_data = request.headers.get("ADMIN_SECRET_KEY")

        if key_data != config.ADMIN_SECRET_KEY:
            return JSONResponse({"message": f"Wrong secret key: {key_data}"}, status_code=403)

    # if path.startswith("@miro/"):
    #     miro_data = path.removeprefix("@miro/")
    #     return await miro_proxy(miro_data)
    if path.startswith("render_iframe/"):
        iframe_id = path.removeprefix("render_iframe/")
        return await iframe_proxy(iframe_id)

    return await render_medium_post_link(url, db_cache, redis)


@trace
async def main_page():
    homepage_template = await render_homepage(as_html=True)
    main_template_rendered = main_template.render(postleter=homepage_template)
    base_template_rendered = base_template.render(body_template=main_template_rendered, HOST_ADDRESS=config.HOST_ADDRESS)
    parsed_template = parse(base_template_rendered)
    serialized_template = serialize(parsed_template, encoding='utf-8')
    return HTMLResponse(serialized_template)


def register_main_router(app):
    app.add_api_route(path="/delete-from-cache", endpoint=delete_from_cache, methods=["POST"])
    app.add_api_route(path="/report-problem", endpoint=report_problem, methods=["POST"])
    app.add_api_route(
        path="/{path:path}",
        endpoint=route_processing,
        methods=["GET", "HEAD"],
        response_model=str,
        tags=["pages"],
        summary=None,
        description=None,
    )
