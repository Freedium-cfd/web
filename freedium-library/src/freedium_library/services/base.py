from abc import ABC, abstractmethod
from typing import Any

from dependency_injector.wiring import Provide

from freedium_library.container import Container
from freedium_library.models.request import Request


class BaseService(ABC):
    def __init__(self, request: Request = Provide[Container.request]):
        self.request = request

    @abstractmethod
    def is_valid(self) -> bool:
        pass

    @abstractmethod
    async def ais_valid(self) -> bool:
        pass

    @abstractmethod
    def render(self) -> Any:
        pass

    @abstractmethod
    async def arender(self) -> Any:
        pass
