from dependency_injector import containers, providers

from .api import MediumApiService
from .validators import MediumServicePathValidator


class MediumContainer(containers.DeclarativeContainer):
    medium_api_service = providers.Singleton(MediumApiService)
    medium_path_validator = providers.Singleton(MediumServicePathValidator)
