from dependency_injector import containers, providers

from freedium_library.utils.http import Request

from .api import MediumApiService
from .config import MediumConfig
from .validators import MediumServicePathValidator


class MediumContainer(containers.DeclarativeContainer):
    config = providers.Singleton(MediumConfig)
    request = providers.Singleton(Request)
    api_service = providers.Singleton(
        MediumApiService,
        request=request,
        config=config,
    )
    validator = providers.Singleton(MediumServicePathValidator)
