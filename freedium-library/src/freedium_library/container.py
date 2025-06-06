from dependency_injector import containers, providers

from freedium_library.utils.http import HttpxRequest


class Container(containers.DeclarativeContainer):
    request = providers.Singleton(HttpxRequest)
