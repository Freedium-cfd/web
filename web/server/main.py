from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import APIRouter, FastAPI
from loguru import logger
from pydantic_settings import BaseSettings

from server import redis_storage
from server.exceptions.main import register_main_error_handler
from server.handlers.main import register_main_router
from server.middlewares import register_middlewares

NAME = "Freedium"
VERSION = "1.0"


class Settings(BaseSettings):
    app_title: str = f"{NAME}'s REST API"
    app_version: str = VERSION
    disable_external_docs: bool = False
    sentry_sdk_dsn: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    logger.info("Application startup")
    yield
    # Shutdown
    logger.debug("Close Redis connection")
    await redis_storage.close()
    if settings.sentry_sdk_dsn:
        logger.debug("Flush Sentry messages")
        sentry_sdk.flush()


def create_router() -> APIRouter:
    router = APIRouter()
    register_main_router(router)
    return router


def create_application() -> FastAPI:
    app_config: dict[str, str | None] = {
        "title": settings.app_title,
        "version": settings.app_version,
    }

    if settings.disable_external_docs:
        external_docs: dict[str, str | None] = {
            "openapi_url": None,
            "docs_url": None,
            "redoc_url": None,
        }
        app_config.update(external_docs)

    app = FastAPI(**app_config, lifespan=lifespan)

    router = create_router()
    app.include_router(router)

    register_main_error_handler(app)
    register_middlewares(app)

    return app


app = create_application()
