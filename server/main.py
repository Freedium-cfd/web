import sentry_sdk
import asyncio
from contextlib import suppress
from fastapi import FastAPI
from loguru import logger

from server import config, redis_storage, bot, db_backup_startup_correlation, db_backup_startup_lock
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


async def send_db_backup_task():
    while True:
        if bot:
            with suppress(Exception):
                with open("medium_cache.sqlite", "rb") as db_file:
                    await bot.send_document(chat_id=config.TELEGRAM_ADMIN_ID, document=db_file)
        else:
            logger.warning("No bot instance")
        await asyncio.sleep(60 * 60 * 24)


@app.on_event("startup")
async def startup():
    with db_backup_startup_lock:
        if not db_backup_startup_correlation.get("registered"):
            logger.warning("Register db backup task")
            asyncio.create_task(send_db_backup_task())
            db_backup_startup_correlation["registered"] = True


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
