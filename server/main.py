from math import ceil
import sentry_sdk
import asyncio
from contextlib import suppress
from fastapi.exceptions import HTTPException
from fastapi import FastAPI, Depends, APIRouter
from loguru import logger
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from server import config, redis_storage
from server.exceptions.main import register_main_error_handler
from server.handlers.main import register_main_router
from server.middlewares import register_middlewares
from server.utils.utils import safe_check_redis_connection

NAME = "Freedium"
VERSION = "1.0"
DISABLE_EXTERNAL_DOCS = True

APP_TITLE = f"{NAME}'s REST API"
APP_VERSION = VERSION

FASTAPI_APPLICATION_CONFIG = {"title": APP_TITLE, "version": APP_VERSION}

if DISABLE_EXTERNAL_DOCS:
    FASTAPI_APPLICATION_CONFIG.update({"openapi_url": None, "docs_url": None, "redoc_url": None})

if config.SENTRY_SDK_DSN:
    sentry_sdk.init(dsn=config.SENTRY_SDK_DSN, traces_sample_rate=1.0)


async def limiter_callback(request, response, pexpire: int):
    expire = ceil(pexpire / 1000)

    raise HTTPException(429, {"error": "Too many requests. Probably you use Freedium to train own AI moodel, hmm? :/"}, headers={"Retry-After": str(expire)})


async def limiter_identifier(request):
    forwarded_ip = request.headers.get("X-Forwarded-For")
    original_ip = request.headers.get("ip")
    if forwarded_ip:
        ip = forwarded_ip.split(",")[0]
    elif original_ip:
        ip = original_ip
    else:
        ip = "127.0.0.1"
    return str(ip)


app = FastAPI(**FASTAPI_APPLICATION_CONFIG)
router = APIRouter(dependencies=[Depends(RateLimiter(times=5, seconds=2, identifier=limiter_identifier, callback=limiter_callback))])


@app.on_event("startup")
async def startup():
    if await safe_check_redis_connection(redis_storage):
        await FastAPILimiter.init(redis_storage)


@app.on_event("shutdown")
async def shutdown():
    logger.debug("Close Redis connection")
    await redis_storage.close()
    if config.SENTRY_SDK_DSN:
        logger.debug("Flush Sentry messages")
        sentry_sdk.flush()


register_main_router(router)
register_main_error_handler(app)

register_middlewares(app)

app.include_router(router)
