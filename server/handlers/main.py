import sentry_sdk

from fastapi.responses import HTMLResponse

from server import base_template, main_template, MediumParser, medium_parser_exceptions, minify_html, config
from server.utils.logger_trace import trace

from server.utils.error import (
    generate_error,
)
from server.utils.utils import aio_redis_cache


@aio_redis_cache(60 * 60)
async def main_page():
    main_template_rendered = await main_template.render_async()
    base_template_rendered = await base_template.render_async(body_template=main_template_rendered)
    base_template_rendered_minified = minify_html(base_template_rendered)
    return HTMLResponse(base_template_rendered_minified)


@trace
async def render_medium_post_link(path: str):
    if not path:
        return await main_page()

    # path = correct_url(path) (???)

    try:
        medium_parser = await MediumParser.from_url(path)
        rendered_medium_post = await medium_parser.render_as_html(minify=False, template_folder="server/templates")
    except medium_parser_exceptions.InvalidURL as ex:
        sentry_sdk.capture_exception(ex)
        return await generate_error(
            "Unable to identify the Medium article URL.",
            status_code=404,
        )
    except (medium_parser_exceptions.InvalidMediumPostURL, medium_parser_exceptions.InvalidMediumPostID, medium_parser_exceptions.MediumPostQueryError) as ex:
        sentry_sdk.capture_exception(ex)
        return await generate_error(
            "Unable to identify the link as a Medium.com article page. Please check the URL for any typing errors.",
            status_code=404,
        )
    except medium_parser_exceptions.InvalidMediumPostID as ex:
        sentry_sdk.capture_exception(ex)
        return await generate_error("Unable to identify the Medium article ID.", status_code=500)
    except Exception as ex:
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

        minified_rendered_post = minify_html(base_template_rendered)
        return HTMLResponse(minified_rendered_post)


def register_main_router(app):
    app.add_api_route(
        path="/{path:path}",
        endpoint=render_medium_post_link,
        methods=["GET"],
        response_model=str,
        tags=["pages"],
        summary=None,
        description=None,
    )
