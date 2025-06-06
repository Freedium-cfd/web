from typing import Any, AsyncIterator, Iterator, Optional

from httpx import Response as HttpxNativeResponse

from .headers import Headers
from .response import AbstractResponse


class HttpxResponse(AbstractResponse):
    """Wrapper for httpx's Response class that implements AbstractResponse."""

    def __init__(self, response: HttpxNativeResponse):
        self._response = response
        self._headers: Optional[Headers] = None

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def headers(self) -> Headers:
        if self._headers is None:
            self._headers = Headers(self._response.headers)
        return self._headers

    @property
    def content(self) -> bytes:
        return self._response.content

    @property
    def text(self) -> str:
        return self._response.text

    def json(self) -> Any:
        return self._response.json()

    @property
    def url(self) -> str:
        return str(self._response.url)

    @property
    def is_success(self) -> bool:
        return self._response.is_success

    @property
    def is_redirect(self) -> bool:
        return self._response.is_redirect

    @property
    def is_error(self) -> bool:
        return self._response.is_error

    def raise_for_status(self) -> None:
        self._response.raise_for_status()

    def iter_content(self, chunk_size: Optional[int] = None) -> Iterator[bytes]:
        return self._response.iter_bytes(chunk_size)

    async def aiter_content(
        self, chunk_size: Optional[int] = None
    ) -> AsyncIterator[bytes]:
        return self._response.aiter_bytes(chunk_size)

    def close(self) -> None:
        self._response.close()

    def __getattr__(self, name: str) -> Any:
        """Delegate any other attributes to the underlying response object."""
        return getattr(self._response, name)
