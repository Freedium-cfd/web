import sentry_sdk

from server.utils.error import generate_error
from server.utils.logger_trace import trace


@trace
async def handle_500_error(request, exc):
    try:
        raise exc
    except Exception as e:
        sentry_sdk.capture_exception(e)

    return await generate_error()


def register_main_error_handler(app):
    app.add_exception_handler(500, handle_500_error)
