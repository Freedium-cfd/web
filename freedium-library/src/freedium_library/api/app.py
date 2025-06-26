from fastapi import FastAPI
from loguru import logger

from freedium_library.api.container import APIContainer
from freedium_library.api.error import register_error_handler
from freedium_library.api.handlers import register_router
from freedium_library.api.lifespan import lifespan
from freedium_library.api.middlewares import register_middlewares
from freedium_library.api.settings import ApplicationSettings
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    """
    Customize the OpenAPI schema to remove the HEAD method.
    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    for path in openapi_schema.get("paths", {}):
        if "head" in openapi_schema["paths"][path]:
            del openapi_schema["paths"][path]["head"]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


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

    app.openapi = lambda: custom_openapi(app)
    return app


app = create_application()
