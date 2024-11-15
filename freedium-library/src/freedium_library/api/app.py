from fastapi import FastAPI

from freedium_library.api.container import APIContainer
from freedium_library.api.error import register_error_handler
from freedium_library.api.handlers import register_router
from freedium_library.api.lifespan import lifespan
from freedium_library.api.middlewares import register_middlewares
from freedium_library.api.settings import ApplicationSettings

container = APIContainer()


def create_application() -> FastAPI:
    settings = ApplicationSettings()

    if container.config.DISABLE_DOCS:
        settings.disable_docs()

    app = FastAPI(**settings.to_dict(), lifespan=lifespan)  # type: ignore

    register_router(app, container.config.PREFIX_PATH)
    register_error_handler(app)
    register_middlewares(app)

    return app


app = create_application()
