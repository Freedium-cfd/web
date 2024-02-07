import asyncio
import time
from typing import Awaitable, Callable

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import Message

from server import transponder_code_correlation, url_correlation, xkcd_passwd, xp, config, home_page_process
from server.utils.notify import send_message
from server.utils.error import generate_error
from server.utils.utils import string_to_number_ascii


async def set_body(request: Request, body: bytes):
     async def receive() -> Message:
         return {"type": "http.request", "body": body}
     request._receive = receive


async def get_body(request: Request) -> bytes:
     body = await request.body()
     await set_body(request, body)
     return body


class LoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[StreamingResponse]]) -> Response:  # type: ignore
        start_time = time.time()
        generated_id = xp.generate_xkcdpassword(xkcd_passwd, delimiter="-", numwords=3)
        transponder_code = string_to_number_ascii(generated_id)
        transponder_code_correlation.set(transponder_code)
        url_correlation.set(request.url)
        with logger.contextualize(id=generated_id):
            logger.trace(f"Current ID '{generated_id}' transponder code is '{transponder_code}'")
            logger.trace(request.__dict__)

            await request.body()

            logger.debug(f"< HTTP/{request['http_version']} {request.method} {request.url}")
            logger.debug(f"< IP host origin: {request.client.host}")

            logger.debug("< Params:")
            for name, value in request.path_params.items():
                logger.debug(f"\t< {name}: {value}")

            logger.debug("< Headers:")
            for name, value in request.headers.items():
                value = self._sanitize_header(name, value)
                logger.debug(f"\t< {name}: {value}")

            if hasattr(request, "cookies") and request.cookies:
                logger.debug("< Coockies:")
                for name, value in request.cookies.items():
                    logger.debug(f"\t< {name}: {value}")

            # Workaround for stupid Starlette bug: https://github.com/tiangolo/fastapi/issues/394
            await get_body(request)

            try:
                response = await asyncio.wait_for(call_next(request), timeout=config.REQUEST_TIMEOUT)
            except Exception as ex:
                exception_class = type(ex)
                logger.exception(ex)
                await send_message(f"Error while processing url: <code>{url_correlation.get()}</code>, transponder_code: <code>{transponder_code_correlation.get()}</code>, error: <code>{ex}</code>. exception: <code>{exception_class.__name__}</code>. {home_page_process.get(transponder_code_correlation.get(), '')}")
                response = await generate_error()

            logger.trace(response.__dict__)

            response.headers["X-Request-ID"] = generated_id
            # response.headers["Access-Control-Expose-Headers"] = "X-Request-ID, Origin, X-Requested-With, Content-Type, Accept"

            logger.debug(f"> HTTP/{request['http_version']} {response.status_code}")

            logger.debug("> Headers:")
            for name, value in response.headers.items():
                value = self._sanitize_header(name, value)
                logger.debug(f"\t> {name}: {value}")

            if hasattr(response, "cookies"):
                logger.debug("> Coockies:")
                for name, value in response.cookies.items():
                    logger.debug(f"\t> {name}: {value}")

            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)

            return response

    def _sanitize_header(self, name, value):
        if name.lower() == "authorization":
            value = f"{value[:25]}******"
        return value
