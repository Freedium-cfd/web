from dependency_injector import containers, providers

from freedium_library.models.request import Request


class Container(containers.DeclarativeContainer):
    request = providers.Singleton(Request)
