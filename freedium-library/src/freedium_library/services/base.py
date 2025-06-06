from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide
from loguru import logger

from freedium_library.container import Container

if TYPE_CHECKING:
    from freedium_library.utils.http import HttpxRequest


class BaseService(ABC):
    def __init__(self, request: HttpxRequest = Provide[Container.request]):
        self.request = request

    def _prepare(self):
        pass

    def is_valid(self, path: str) -> bool:
        with logger.contextualize(cls=str(self)):
            return self._is_valid(path)

    async def ais_valid(self, path: str) -> bool:
        with logger.contextualize(cls=str(self)):
            return await self._ais_valid(path)

    def render(self, path: str) -> str:
        with logger.contextualize(cls=str(self)):
            return self._render(path)

    async def arender(self, path: str) -> str:
        with logger.contextualize(cls=str(self)):
            return await self._arender(path)

    async def asearch(self, keywords: list[str]) -> list[dict[str, str]]:
        with logger.contextualize(cls=str(self)):
            return await self._asearch(keywords)

    def search(self, keywords: list[str]) -> list[dict[str, str]]:
        with logger.contextualize(cls=str(self)):
            return self._search(keywords)

    @abstractmethod
    def _is_valid(self, path: str) -> bool:
        pass

    @abstractmethod
    async def _ais_valid(self, path: str) -> bool:
        pass

    @abstractmethod
    def _render(self, path: str) -> str:
        pass

    @abstractmethod
    async def _arender(self, path: str) -> str:
        pass

    @abstractmethod
    async def _asearch(self, keywords: list[str]) -> list[dict[str, str]]:
        pass

    @abstractmethod
    def _search(self, keywords: list[str]) -> list[dict[str, str]]:
        pass

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
