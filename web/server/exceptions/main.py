from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI, Request, Response

import sentry_sdk

from server.utils.error import generate_error
from server.utils.logger_trace import trace


@trace
async def handle_500_error(request: Request, exc: Exception) -> Response:
    try:
        raise exc
    except Exception as e:
        sentry_sdk.capture_exception(e)

    return await generate_error()


def register_main_error_handler(app: FastAPI) -> None:
    app.add_exception_handler(500, handle_500_error)
