from abc import ABC, abstractmethod
from typing import List, Union

from ..models import CacheResponse


class AbstractCacheBackend(ABC):
    @abstractmethod
    def connect(self) -> None:
        """Initialize database connection"""
        raise NotImplementedError("Connect must be implemented by subclass")

    @abstractmethod
    def ensure_connection(self) -> None:
        """Ensure database connection is established"""
        raise NotImplementedError("Ensure_connection must be implemented by subclass")

    @abstractmethod
    async def aensure_connection(self) -> None:
        """Ensure database connection is established asynchronously"""
        raise NotImplementedError(
            "Async ensure_connection must be implemented by subclass"
        )

    @abstractmethod
    def init_db(self) -> None:
        """Initialize database schema"""
        raise NotImplementedError("Init_db must be implemented by subclass")

    @abstractmethod
    async def ainit_db(self) -> None:
        """Initialize database schema asynchronously"""
        raise NotImplementedError("Async init_db must be implemented by subclass")

    @abstractmethod
    def all(self) -> List[dict]:
        """Retrieve all cached items"""
        raise NotImplementedError("All must be implemented by subclass")

    @abstractmethod
    async def aall(self) -> List[dict]:
        """Retrieve all cached items asynchronously"""
        raise NotImplementedError("Async all must be implemented by subclass")

    @abstractmethod
    def all_length(self) -> int:
        """Get total number of cached items"""
        raise NotImplementedError("All_length must be implemented by subclass")

    @abstractmethod
    async def aall_length(self) -> int:
        """Get total number of cached items asynchronously"""
        raise NotImplementedError("Async all_length must be implemented by subclass")

    @abstractmethod
    def random(self, size: int) -> List[CacheResponse]:
        """Get random cached items"""
        raise NotImplementedError("Random must be implemented by subclass")

    @abstractmethod
    async def arandom(self, size: int) -> List[CacheResponse]:
        """Get random cached items asynchronously"""
        raise NotImplementedError("Async random must be implemented by subclass")

    @abstractmethod
    def pull(self, key: str) -> Union[CacheResponse, None]:
        """Retrieve item from cache"""
        raise NotImplementedError("Pull must be implemented by subclass")

    @abstractmethod
    async def apull(self, key: str) -> Union[CacheResponse, None]:
        """Retrieve item from cache asynchronously"""
        raise NotImplementedError("Async pull must be implemented by subclass")

    @abstractmethod
    def push(self, key: str, value: Union[str, dict]) -> None:
        """Store item in cache"""
        raise NotImplementedError("Push must be implemented by subclass")

    @abstractmethod
    async def apush(self, key: str, value: Union[str, dict]) -> None:
        """Store item in cache asynchronously"""
        raise NotImplementedError("Async push must be implemented by subclass")

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove item from cache"""
        raise NotImplementedError("Delete must be implemented by subclass")

    @abstractmethod
    async def adelete(self, key: str) -> None:
        """Remove item from cache asynchronously"""
        raise NotImplementedError("Async delete must be implemented by subclass")

    @abstractmethod
    def close(self) -> None:
        """Close database connection"""
        raise NotImplementedError("Close must be implemented by subclass")

    @abstractmethod
    async def aclose(self) -> None:
        """Close database connection asynchronously"""
        raise NotImplementedError("Async close must be implemented by subclass")
