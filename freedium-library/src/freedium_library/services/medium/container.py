from dependency_injector import containers, providers

from freedium_library.services.medium.validators import (
    MediumServicePathValidator,
)
from freedium_library.utils.http import CurlRequest

from .api import MediumApiService
from .config import MediumConfig
from .medium import MediumService


class MediumContainer(containers.DeclarativeContainer):
    config = providers.Singleton(MediumConfig)
    request = providers.Singleton(CurlRequest)
    api_service = providers.Singleton(
        MediumApiService,
        request=request,
        config=config,
    )
    validator = providers.Singleton(
        MediumServicePathValidator,
        api_service=api_service,
    )
    service = providers.Singleton(
        MediumService,
        request=request,
        api_service=api_service,
        path_validator=validator,
    )
