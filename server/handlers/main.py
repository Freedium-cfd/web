from html5lib.html5parser import parse
from html5lib import serialize
from fastapi.responses import HTMLResponse

from server import base_template, main_template, config

from fastapi import Request

from server.handlers.post import render_medium_post_link, render_postleter
from server.handlers.reverse_proxy import miro_proxy, iframe_proxy
from server.handlers.misc import report_problem, delete_from_cache
from server.utils.logger_trace import trace


@trace
async def route_processing(path: str, request: Request):
    if not path:
        return await main_page()
    if request.scope.get("query_string"):
        path = request.url.path + "?" + request.scope["query_string"].decode()
    else:
        path = request.url.path
    path = path.removeprefix("/")

    if path.startswith("render-no-cache/"):
        path = path.removeprefix("render-no-cache/")
        if path.startswith("/no-redis/"):
            path = path.removeprefix("/no-redis/")
            return await render_medium_post_link(path, True, False)
        return await render_medium_post_link(path, False)
    elif path.startswith("@miro/"):
        miro_data = path.removeprefix("@miro/")
        return await miro_proxy(miro_data)
    elif path.startswith("render_iframe/"):
        iframe_id = path.removeprefix("render_iframe/")
        return await iframe_proxy(iframe_id)

    return await render_medium_post_link(path)


@trace
async def main_page():
    postleter_template = await render_postleter(as_html=True)
    main_template_rendered = await main_template.render_async(postleter=postleter_template)
    base_template_rendered = await base_template.render_async(body_template=main_template_rendered, HOST_ADDRESS=config.HOST_ADDRESS)
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
