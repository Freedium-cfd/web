import sentry_sdk
import pickle
from fastapi.responses import HTMLResponse
from html5lib.html5parser import parse
from html5lib import serialize
from loguru import logger

from server import base_template, config, url_correlation, redis_storage, postleter_template, home_page_process, transponder_code_correlation
from server.utils.error import generate_error
from server.utils.logger_trace import trace
from server.utils.notify import send_message
from server.utils.cache import aio_redis_cache
from server.utils.utils import correct_url, safe_check_redis_connection

from medium_parser import medium_parser_exceptions
from medium_parser import cache as medium_cache
from medium_parser.core import MediumParser
from medium_parser.utils import is_valid_medium_post_id_hexadecimal

@trace
@aio_redis_cache(10 * 60)
async def render_postleter(limit: int = 30, as_html: bool = False):
    random_post_id_list = [i[0] for i in medium_cache.random(limit)]
    home_page_process[transponder_code_correlation.get()] = random_post_id_list

    outlet_posts_list = []
    for post_id in random_post_id_list:
        try:
            post = MediumParser(post_id, timeout=config.TIMEOUT, host_address=config.HOST_ADDRESS, auth_cookies=config.MEDIUM_AUTH_COOKIES)
            await post.query()
            post_metadata = await post.generate_metadata(as_dict=True)
            outlet_posts_list.append(post_metadata)
        except Exception as ex:
            logger.error(f"Couldn't render post_id for postleter: {post_id}, ex: {ex}")
            # send_message(f"Couldn't render post_id for postleter: {post_id}, ex: {ex}")

    postleter_template_rendered = await postleter_template.render_async(post_list=outlet_posts_list)
    if as_html:
        return postleter_template_rendered
    return HTMLResponse(postleter_template_rendered)


@trace
async def render_medium_post_link(path: str, use_cache: bool = True, use_redis: bool = True):
    redis_available = await safe_check_redis_connection(redis_storage)

    try:
        if is_valid_medium_post_id_hexadecimal(path):
            medium_parser = MediumParser(path, timeout=config.TIMEOUT, host_address=config.HOST_ADDRESS, auth_cookies=config.MEDIUM_AUTH_COOKIES)
        else:
            url = correct_url(path)
            medium_parser = await MediumParser.from_url(url, timeout=config.TIMEOUT, host_address=config.HOST_ADDRESS, auth_cookies=config.MEDIUM_AUTH_COOKIES)
        medium_post_id = medium_parser.post_id
        if redis_available and use_cache and use_redis:
            redis_result = await redis_storage.get(medium_post_id)
        else:
            redis_result = None
        if not redis_result:
            await medium_parser.query(use_cache=use_cache)
            rendered_medium_post = await medium_parser.render_as_html("server/templates")
        else:
            rendered_medium_post = pickle.loads(redis_result)
    except medium_parser_exceptions.InvalidURL as ex:
        logger.exception(ex)
        sentry_sdk.capture_exception(ex)
        return await generate_error(
            "Unable to identify the Medium article URL.",
            status_code=404,
        )
    except (medium_parser_exceptions.InvalidMediumPostURL, medium_parser_exceptions.MediumPostQueryError, medium_parser_exceptions.PageLoadingError) as ex:
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
    except medium_parser_exceptions.NotValidMediumURL as ex:
        return await generate_error("You sure that this is a valid Medium.com URL?", status_code=404, quiet=True)
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
        rendered_post = await base_template.render_async(base_context, HOST_ADDRESS=config.HOST_ADDRESS)
        parsed_rendered_post = parse(rendered_post)
        serialized_rendered_post = serialize(parsed_rendered_post, encoding='utf-8')

        if not redis_result:
            if not redis_available:
                send_message("ERROR: Redis is not available. Please check your configuration.")
            elif use_redis:
                await redis_storage.setex(medium_post_id, config.CACHE_LIFE_TIME, pickle.dumps(rendered_medium_post))
            send_message(f"✅ Successfully rendered post: {url_correlation.get()}", True, "GOOD")

        return HTMLResponse(serialized_rendered_post)
