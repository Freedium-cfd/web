from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from freedium_library.api.container import APIContainer
from freedium_library.api.handlers import render
from freedium_library.services.medium.container import MediumContainer
from freedium_library.services.resolver import ServiceResolver

api_container = APIContainer()
medium_container = MediumContainer()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.container = api_container
    app.state.medium_container = medium_container

    # Initialize service resolver
    resolver = ServiceResolver()

    # Register services
    medium_service = medium_container.service()
    resolver.register("medium", medium_service)

    app.state.service_resolver = resolver

    # Wire dependency injection to modules
    medium_container.wire(modules=[render])

    yield

    # Unwire on shutdown
    medium_container.unwire()
