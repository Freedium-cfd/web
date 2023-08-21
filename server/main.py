from fastapi import FastAPI
import sentry_sdk
from loguru import logger

from server import redis_storage, config
from server.exceptions.main import register_main_error_handler
from server.handlers.main import register_main_router
from server.middlewares import register_middlewares

NAME = "Freedium"
VERSION = "0.1"
DISABLE_EXTERNAL_DOCS = True

APP_TITLE = f"{NAME}'s REST API"
APP_VERSION = VERSION

FASTAPI_APPLICATION_CONFIG = {"title": APP_TITLE, "version": APP_VERSION}

if DISABLE_EXTERNAL_DOCS:
    FASTAPI_APPLICATION_CONFIG.update({"openapi_url": None, "docs_url": None, "redoc_url": None})

if config.SENTRY_SDK_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_SDK_DSN,
            traces_sample_rate=1.0,
        )

app = FastAPI(**FASTAPI_APPLICATION_CONFIG)


@app.on_event("shutdown")
async def shutdown():
    logger.debug("Close Redis connection")
    await redis_storage.close()
    if config.SENTRY_SDK_DSN:
        logger.debug("Flush Sentry messages")
        sentry_sdk.flush()


register_main_router(app)
register_main_error_handler(app)

register_middlewares(app)
