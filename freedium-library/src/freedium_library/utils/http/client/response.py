import abc
from typing import Any, AsyncIterator, Iterator, Optional

from .headers import AbstractHeaders


class AbstractResponse(abc.ABC):
    """Abstract base class for HTTP responses."""

    @property
    @abc.abstractmethod
    def status_code(self) -> int:
        """HTTP status code."""
        pass

    @property
    @abc.abstractmethod
    def headers(self) -> AbstractHeaders:
        """HTTP response headers."""
        pass

    @property
    @abc.abstractmethod
    def content(self) -> bytes:
        """Raw response content as bytes."""
        pass

    @property
    @abc.abstractmethod
    def text(self) -> str:
        """Response content as text."""
        pass

    @abc.abstractmethod
    def json(self) -> Any:
        """Parse response content as JSON."""
        pass

    @property
    @abc.abstractmethod
    def url(self) -> str:
        """Final URL of the response."""
        pass

    @property
    @abc.abstractmethod
    def is_success(self) -> bool:
        """Whether the request was successful (status code 2xx)."""
        pass

    @property
    @abc.abstractmethod
    def is_redirect(self) -> bool:
        """Whether the response is a redirect."""
        pass

    @property
    @abc.abstractmethod
    def is_error(self) -> bool:
        """Whether the response is an error (status code 4xx or 5xx)."""
        pass

    @abc.abstractmethod
    def raise_for_status(self) -> None:
        """Raise an exception if the response has an error status code."""
        pass

    @abc.abstractmethod
    def iter_content(self, chunk_size: Optional[int] = None) -> Iterator[bytes]:
        """Iterate over the response content in chunks."""
        pass

    @abc.abstractmethod
    async def aiter_content(
        self, chunk_size: Optional[int] = None
    ) -> AsyncIterator[bytes]:
        """Async iterate over the response content in chunks."""
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """Close the response and release resources."""
        pass
