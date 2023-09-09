import sentry_sdk
import pickle
import aiohttp
from fastapi.responses import HTMLResponse
from loguru import logger
from contextlib import suppress

from aiohttp_client_cache import CachedSession, SQLiteBackend
import random
from server import MediumParser, base_template, config, main_template, medium_parser_exceptions, minify_html, url_correlation, redis_storage, postleter_template, is_valid_medium_post_id_hexadecimal
from server.utils.error import (
    generate_error,
)
from fastapi import Response
from server.utils.logger_trace import trace
from server.utils.utils import aio_redis_cache, correct_url, safe_check_redis_connection
from server.utils.notify import send_message

CACHE_LIFE_TIME = 60 * 60 * 24
TIMEOUT = 5

IFRAME_HEADERS = {'Access-Control-Allow-Origin': '*'}


@trace
async def route_processing(path: str):
    if not path:
        return await main_page()
    elif path == "render_postleter":
        return await render_postleter()
    else:
        return await render_medium_post_link(path)


@trace
async def render_iframe(iframe_id):
    async with aiohttp.ClientSession() as client:
        request = await client.get(
            f"https://medium.com/media/{iframe_id}",
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"},
        )
        request_content = await request.text()
    return Response(content=request_content, media_type="text/html; charset=utf-8", headers=IFRAME_HEADERS)


@trace
@aio_redis_cache(7 * 60)
async def render_postleter(limit: int = 120, as_html: bool = False):
    async with CachedSession(cache=SQLiteBackend('medium_cache.sqlite')) as session:
        post_id_list = [i async for i in session.cache.responses.keys()]

    random_post_id_list = random.choices(post_id_list, k=limit)

    outlenget_posts_list = []
    for post_id in random_post_id_list:
        try:
            post = MediumParser(post_id)
            await post.query()
            post_metadata = await post.generate_metadata(as_dict=True)
            outlenget_posts_list.append(post_metadata)
        except Exception as ex:
            await send_message(f"Couldn't render post_id for postleter: {post_id}, ex: {ex}")

    postleter_template_rendered = await postleter_template.render_async(post_list=outlenget_posts_list)
    postleter_template_rendered_minified = minify_html(postleter_template_rendered)
    if as_html:
        return postleter_template_rendered_minified
    return HTMLResponse(postleter_template_rendered_minified)


@trace
async def main_page():
    postleter_template = await render_postleter(as_html=True)
    main_template_rendered = await main_template.render_async(postleter=postleter_template)
    base_template_rendered = await base_template.render_async(body_template=main_template_rendered)
    base_template_rendered_minified = minify_html(base_template_rendered)
    return HTMLResponse(base_template_rendered_minified)


@trace
async def render_medium_post_link(path: str):
    redis_available = await safe_check_redis_connection(redis_storage)

    try:
        if is_valid_medium_post_id_hexadecimal(path):
            medium_parser = MediumParser(path)
        else:
            url = correct_url(path)
            medium_parser = await MediumParser.from_url(url)
        medium_post_id = medium_parser.post_id
        if redis_available:
            redis_result = await redis_storage.get(medium_post_id)
        else:
            redis_result = None
        if not redis_result:
            await medium_parser.query(timeout=config.TIMEOUT, use_cache=False)
            rendered_medium_post = await medium_parser.render_as_html(minify=False, template_folder="server/templates")
        else:
            rendered_medium_post = pickle.loads(redis_result)
    except medium_parser_exceptions.InvalidURL as ex:
        logger.exception(ex)
        sentry_sdk.capture_exception(ex)
        return await generate_error(
            "Unable to identify the Medium article URL.",
            status_code=404,
        )
    except (medium_parser_exceptions.InvalidMediumPostURL, medium_parser_exceptions.InvalidMediumPostID, medium_parser_exceptions.MediumPostQueryError) as ex:
        logger.exception(ex)
        sentry_sdk.capture_exception(ex)
        return await generate_error(
            "Unable to identify the link as a Medium.com article page. Please check the URL for any typing errors.",
            status_code=404,
        )
    except medium_parser_exceptions.InvalidMediumPostID as ex:
        logger.exception(ex)
        sentry_sdk.capture_exception(ex)
        return await generate_error("Unable to identify the Medium article ID.", status_code=500)
    except Exception as ex:
        logger.exception(ex)
        sentry_sdk.capture_exception(ex)
        return await generate_error(status_code=500)
    else:
        base_context = {
            "enable_ads_header": config.ENABLE_ADS_BANNER,
            "body_template": rendered_medium_post.data,
            "title": rendered_medium_post.title,
            "description": rendered_medium_post.description,
        }
        base_template_rendered = await base_template.render_async(base_context)
        minified_rendered_post = base_template_rendered

        # minified_rendered_post = minify_html(base_template_rendered)

        if not redis_result:
            if not redis_available:
                await send_message("ERROR: Redis is not available. Please check your configuration.")
            else:
                await redis_storage.setex(medium_post_id, CACHE_LIFE_TIME, pickle.dumps(rendered_medium_post))
            await send_message(f"✅ Successfully rendered post: {url_correlation.get()}", True)

        return HTMLResponse(minified_rendered_post)


def register_main_router(app):
    app.add_api_route(path="/render_iframe/{iframe_id}", endpoint=render_iframe, methods=["GET"])
    app.add_api_route(
        path="/{path:path}",
        endpoint=route_processing,
        methods=["GET"],
        response_model=str,
        tags=["pages"],
        summary=None,
        description=None,
    )
