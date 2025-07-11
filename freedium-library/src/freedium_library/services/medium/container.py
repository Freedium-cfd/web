from dependency_injector import containers, providers

from freedium_library.services.medium.validators import (
    MediumServicePathValidator,
)
from freedium_library.utils.http import HttpxRequest

from .api import MediumApiService
from .config import MediumConfig


class MediumContainer(containers.DeclarativeContainer):
    config = providers.Singleton(MediumConfig)
    request = providers.Singleton(HttpxRequest)
    api_service = providers.Singleton(
        MediumApiService,
        request=request,
        config=config,
    )
    validator = providers.Singleton(MediumServicePathValidator)
