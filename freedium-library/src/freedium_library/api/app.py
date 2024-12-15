from fastapi import FastAPI
from loguru import logger

from freedium_library.api.container import APIContainer
from freedium_library.api.error import register_error_handler
from freedium_library.api.handlers import register_router
from freedium_library.api.lifespan import lifespan
from freedium_library.api.middlewares import register_middlewares
from freedium_library.api.settings import ApplicationSettings


def create_application() -> FastAPI:
    api_container = APIContainer()

    settings = ApplicationSettings(container=api_container)
    config = api_container.config()

    if config.DISABLED_DOCS:
        logger.warning(f"Documentation is disabled: {config.DISABLED_DOCS}")
        settings.disable_docs()

    app = FastAPI(
        title=settings.title,
        version=settings.version,
        openapi_url=settings.openapi_url,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        lifespan=lifespan,
    )

    register_router(app, settings.prefix_path)
    register_error_handler(app)
    register_middlewares(app)

    return app


app = create_application()
