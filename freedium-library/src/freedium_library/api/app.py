from fastapi import FastAPI
from loguru import logger

from freedium_library.api.container import APIContainer
from freedium_library.api.error import register_error_handler
from freedium_library.api.handlers import register_router
from freedium_library.api.lifespan import lifespan
from freedium_library.api.middlewares import register_middlewares
from freedium_library.api.settings import ApplicationSettings


def create_application() -> FastAPI:
    container = APIContainer()
    container.wire(modules=["freedium_library.api.settings"])

    settings = ApplicationSettings(container=container)
    config = container.config()

    if config.DISABLED_DOCS:
        logger.warning(f"Documentation is disabled: {config.DISABLED_DOCS}")
        settings.disable_docs()

    app = FastAPI(**settings.to_dict(), lifespan=lifespan)  # type: ignore

    register_router(app, settings.prefix_path)
    register_error_handler(app)
    register_middlewares(app)

    return app


app = create_application()
