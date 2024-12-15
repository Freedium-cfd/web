from dependency_injector import containers, providers

from freedium_library.api.config import APIConfig, ServerConfig


class APIContainer(containers.DeclarativeContainer):
    config = providers.Singleton(APIConfig)
    server_config = providers.Singleton(ServerConfig)
