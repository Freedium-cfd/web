import asyncio
import pickle

from fastapi.responses import HTMLResponse
from html5lib import serialize
from html5lib.html5parser import parse
from async_lru import alru_cache
from loguru import logger
from medium_parser import medium_parser_exceptions

from server import config, medium_cache, redis_storage, medium_parser
from server.services.jinja import base_template, homepage_template
from server.utils.cache import aio_redis_cache
from server.utils.exceptions import handle_exception
from server.utils.logger_trace import trace
from server.utils.notify import send_message
from server.utils.utils import safe_check_redis_connection


@trace
@aio_redis_cache(10 * 60)
async def render_homepage(limit: int = config.HOME_PAGE_MAX_POSTS, as_html: bool = False):
    random_post_id_list = list(set([i[0] for i in medium_cache.random(limit)]))

    outlet_posts_list = []
    tasks = []
    for post_id in random_post_id_list:
        async def fetch_post_metadata(post_id):
            try:
                logger.debug(f"Fetching post_id: {post_id}")
                post_data = await medium_parser.query(post_id, force_cache=True, retry=1)
                post_metadata = await medium_parser.generate_metadata(post_data, post_id, as_dict=True)
                outlet_posts_list.append(post_metadata)
            except Exception as ex:
                await handle_exception(ex, message=f"Couldn't render post_id for postleter: {post_id}. Just ignore that")

        task = fetch_post_metadata(post_id)
        tasks.append(task)

    await asyncio.gather(*tasks)

    homepage_template_rendered = homepage_template.render(post_list=outlet_posts_list)
    if as_html:
        return homepage_template_rendered

    return HTMLResponse(homepage_template_rendered)


async def render_medium_post_link(path: str, use_cache: bool = True, use_redis: bool = True):
    redis_available = await safe_check_redis_connection(redis_storage)
    logger.debug(f"Redis available: {redis_available}")

    try:
        post_id = await medium_parser.resolve(path)
        redis_result = None
        if redis_available and use_cache and use_redis:
            redis_result = await redis_storage.get(post_id)
            logger.debug(f"Redis cache hit for post_id: {post_id}")

        if not redis_result:
            logger.debug(f"No cache found, querying...: {post_id}")
            rendered_medium_post = await medium_parser.render_as_html(post_id)
            logger.debug("Rendered Medium post from HTML template")
            if redis_available and use_redis:
                await redis_storage.setex(post_id, config.CACHE_LIFE_TIME, pickle.dumps(rendered_medium_post))
                logger.debug(f"Stored rendered post in Redis cache: {post_id}")
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
            "host_address": config.HOST_ADDRESS,
            "enable_ads_header": config.ENABLE_ADS_BANNER,
            "body_template": rendered_medium_post.data,
            "title": rendered_medium_post.title,
            "description": rendered_medium_post.description,
        }
        rendered_post = base_template.render(base_context)
        parsed_rendered_post = parse(rendered_post)
        serialized_rendered_post = serialize(parsed_rendered_post, encoding="utf-8")

        send_message(f"✅ Successfully rendered post: {path}", True, "GOOD")
        return HTMLResponse(serialized_rendered_post)
