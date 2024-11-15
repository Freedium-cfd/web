from dependency_injector import containers, providers

from freedium_library.api.config import APIConfig


class APIContainer(containers.DeclarativeContainer):
    config: APIConfig = providers.Singleton(APIConfig)  # type: ignore
