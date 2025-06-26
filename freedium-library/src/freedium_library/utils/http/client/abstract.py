import abc
from types import TracebackType
from typing import Any, Dict, Optional, Type, TypeVar

from .response import AbstractResponse

T = TypeVar("T", bound="AbstractRequest")


class AbstractRequest(abc.ABC):
    """Abstract base class for HTTP request clients."""

    @abc.abstractmethod
    def __enter__(self) -> "AbstractRequest":
        """Enter the context manager."""
        pass

    @abc.abstractmethod
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Exit the context manager."""
        pass

    @abc.abstractmethod
    async def __aenter__(self) -> "AbstractRequest":
        """Enter the async context manager."""
        pass

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Exit the async context manager."""
        pass

    @abc.abstractmethod
    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        """Perform a GET request."""
        pass

    @abc.abstractmethod
    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        """Perform a POST request."""
        pass

    @abc.abstractmethod
    def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        """Perform a PUT request."""
        pass

    @abc.abstractmethod
    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        """Perform a DELETE request."""
        pass

    @abc.abstractmethod
    async def aget(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        """Perform an async GET request."""
        pass

    @abc.abstractmethod
    async def apost(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        """Perform an async POST request."""
        pass

    @abc.abstractmethod
    async def aput(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        """Perform an async PUT request."""
        pass

    @abc.abstractmethod
    async def adelete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        """Perform an async DELETE request."""
        pass
