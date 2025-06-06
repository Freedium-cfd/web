from typing import (
    Any,
    AsyncGenerator,
    AsyncIterator,
    Coroutine,
    Generator,
    Iterator,
    Optional,
    cast,
)

from curl_cffi.requests import Response as CurlCffiResponse

from .headers import Headers
from .response import AbstractResponse


class CurlResponse(AbstractResponse):
    """Wrapper for curl_cffi's Response class that implements AbstractResponse."""

    def __init__(self, response: CurlCffiResponse):
        self._response = response
        self._headers: Optional[Headers] = None

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def headers(self) -> Headers:
        if self._headers is None:
            headers_dict = {
                k: v if v is not None else "" for k, v in self._response.headers.items()
            }
            self._headers = Headers(headers_dict)
        return self._headers

    @property
    def content(self) -> bytes:
        return self._response.content

    @property
    def text(self) -> str:
        return self._response.text

    def json(self, **kwargs: Any) -> Any:
        result: Any = self._response.json(**kwargs)  # type: ignore
        return result

    @property
    def url(self) -> str:
        return str(self._response.url)

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def is_redirect(self) -> bool:
        return 300 <= self.status_code < 400

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400

    def raise_for_status(self) -> None:
        self._response.raise_for_status()

    def iter_content(self, chunk_size: Optional[int] = None) -> Iterator[bytes]:
        def _iter_content() -> Generator[bytes, Any, None]:
            for chunk in self._response.iter_content(
                chunk_size=chunk_size, decode_unicode=False
            ):  # type: ignore
                yield cast(bytes, chunk)

        return _iter_content()

    def aiter_content(
        self, chunk_size: Optional[int] = None
    ) -> Coroutine[Any, Any, AsyncIterator[bytes]]:
        async def _aiter_content() -> AsyncGenerator[bytes, Any]:
            async for chunk in self._response.aiter_content(
                chunk_size=chunk_size, decode_unicode=False
            ):  # type: ignore
                yield cast(bytes, chunk)

        return cast(Coroutine[Any, Any, AsyncIterator[bytes]], _aiter_content())

    def close(self) -> None:
        self._response.close()

    def __getattr__(self, name: str) -> Any:
        """Delegate any other attributes to the underlying response object."""
        return getattr(self._response, name)
