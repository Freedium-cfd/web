import asyncio
import pickle

from fastapi.responses import HTMLResponse
from html5lib import serialize
from html5lib.html5parser import parse
from async_lru import alru_cache
from loguru import logger
from medium_parser import medium_parser_exceptions
from medium_parser.core import MediumParser

from server import config, home_page_process, medium_cache, redis_storage, transponder_code_correlation
from server.services.jinja import base_template, postleter_template
from server.utils.cache import aio_redis_cache
from server.utils.exceptions import handle_exception
from server.utils.logger_trace import trace
from server.utils.notify import send_message
from server.utils.utils import safe_check_redis_connection


@trace
@aio_redis_cache(10 * 60)
async def render_postleter(limit: int = 30, as_html: bool = False):
    random_post_id_list = [i[0] for i in medium_cache.random(limit)]
    home_page_process[transponder_code_correlation.get()] = random_post_id_list

    outlet_posts_list = []
    tasks = []
    for post_id in random_post_id_list:
        async def fetch_post_metadata(post_id):
            try:
                post = MediumParser(post_id, cache=medium_cache, timeout=3, host_address=config.HOST_ADDRESS, auth_cookies=config.MEDIUM_AUTH_COOKIES)
                await post.query(force_cache=True, retry=1)
                post_metadata = await post.generate_metadata(as_dict=True)
                outlet_posts_list.append(post_metadata)
            except Exception as ex:
                await handle_exception(ex, message=f"Couldn't render post_id for postleter: {post_id}. Just ignore that")

        task = fetch_post_metadata(post_id)
        tasks.append(task)

    await asyncio.gather(*tasks)

    postleter_template_rendered = postleter_template.render(post_list=outlet_posts_list)
    if as_html:
        return postleter_template_rendered
    return HTMLResponse(postleter_template_rendered)


@alru_cache(maxsize=20)
async def render_medium_post_link(path: str, use_cache: bool = True, use_redis: bool = True):
    redis_available = await safe_check_redis_connection(redis_storage)
    logger.debug("Redis available: {}", redis_available)

    try:
        medium_parser = await MediumParser.from_unknown(path, cache=medium_cache, timeout=config.TIMEOUT, host_address=config.HOST_ADDRESS, auth_cookies=config.MEDIUM_AUTH_COOKIES)
        logger.debug("MediumParser initialized for path: {}", path)
        redis_result = None
        if redis_available and use_cache and use_redis:
            redis_result = await redis_storage.get(medium_parser.post_id)
            logger.debug("Redis cache hit for post_id: {}", medium_parser.post_id)

        if not redis_result:
            logger.debug("No cache found, querying MediumParser")
            await medium_parser.query(use_cache=use_cache)
            rendered_medium_post = await medium_parser.render_as_html("server/templates")
            logger.debug("Rendered Medium post from HTML template")
            if redis_available and use_redis:
                await redis_storage.setex(medium_parser.post_id, config.CACHE_LIFE_TIME, pickle.dumps(rendered_medium_post))
                logger.debug("Stored rendered post in Redis cache")
        else:
            rendered_medium_post = pickle.loads(redis_result)
            logger.debug("Loaded rendered post from Redis cache")

    except medium_parser_exceptions.InvalidURL as ex:
        return await handle_exception(
            ex,
            "Unable to identify the Medium article URL.",
            status_code=404,
        )
    except (medium_parser_exceptions.InvalidMediumPostURL, medium_parser_exceptions.MediumPostQueryError, medium_parser_exceptions.PageLoadingError) as ex:
        return await handle_exception(
            ex,
            "Unable to identify the link as a Medium.com article page. Please check the URL for any typing errors.",
            status_code=404,
        )
    except medium_parser_exceptions.InvalidMediumPostID as ex:
        return await handle_exception(ex, "Unable to identify the Medium article ID.", status_code=500)
    except medium_parser_exceptions.NotValidMediumURL as ex:
        return await handle_exception(ex, "You sure that this is a valid Medium.com URL?", status_code=404, quiet=True)
    except Exception as ex:
        return await handle_exception(ex, status_code=500)
    else:
        base_context = {
            "enable_ads_header": config.ENABLE_ADS_BANNER,
            "body_template": rendered_medium_post.data,
            "title": rendered_medium_post.title,
            "description": rendered_medium_post.description,
        }
        rendered_post = base_template.render(base_context, HOST_ADDRESS=config.HOST_ADDRESS)
        parsed_rendered_post = parse(rendered_post)
        serialized_rendered_post = serialize(parsed_rendered_post, encoding="utf-8")

        send_message(f"✅ Successfully rendered post: {path}", True, "GOOD")
        return HTMLResponse(serialized_rendered_post)
