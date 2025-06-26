import warnings
from types import TracebackType
from typing import Any, Dict, Optional, Type

from httpx import (
    AsyncClient,
    AsyncHTTPTransport,
    Client,
    HTTPTransport,
    Response,
    Timeout,
)

from .abstract import AbstractRequest
from .config import RequestConfig
from .httpx_response import HttpxResponse
from .response import AbstractResponse


# https://github.com/encode/httpx/discussions/1748
class HttpxRequest(AbstractRequest):
    __slots__ = ("config", "_in_context_manager")

    def __init__(self, config: Optional[RequestConfig] = None):
        self.config = config or RequestConfig()
        self._in_context_manager = False
        warnings.warn(
            "Request should be used as a context manager using 'with' or 'async with' "
            "to ensure proper resource cleanup",
            stacklevel=2,
        )

    @property
    def proxy_url(self) -> Optional[str]:
        return self.config.proxy.url if self.config.proxy else None

    @property
    def _transport(self) -> HTTPTransport:
        return HTTPTransport(retries=self.config.retries)

    @property
    def _client(self) -> Client:
        return Client(
            transport=self._transport,
            proxy=self.proxy_url,
        )

    @property
    def _async_transport(self) -> AsyncHTTPTransport:
        return AsyncHTTPTransport(retries=self.config.retries)

    @property
    def _async_client(self) -> AsyncClient:
        return AsyncClient(
            transport=self._async_transport,
            proxy=self.proxy_url,
        )

    @property
    def _timeout_client(self) -> Timeout:
        timeout = Timeout(timeout=self.config.timeout)
        return timeout

    def __enter__(self) -> "HttpxRequest":
        self._in_context_manager = True
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._client.close()

    async def __aenter__(self) -> "HttpxRequest":
        self._in_context_manager = True
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self._async_client.aclose()

    def __del__(self):
        self._client.close()
        # asyncio.run(self._async_client.aclose()) # TODO: doesn't work

    def _check_context_manager(self):
        if not self._in_context_manager:
            warnings.warn(
                "Request is not being used as a context manager. This may lead to "
                "resource leaks. Use 'with' or 'async with' statement.",
                stacklevel=2,
            )

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        response = self._client.get(
            url,
            params=params,
            headers=headers,
            follow_redirects=follow_redirects,
            timeout=self._timeout_client,
        )
        return HttpxResponse(response)

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        response = self._client.post(
            url,
            json=data,
            headers=headers,
            follow_redirects=follow_redirects,
            timeout=self._timeout_client,
        )
        return HttpxResponse(response)

    def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        response = self._client.put(
            url,
            json=data,
            headers=headers,
            follow_redirects=follow_redirects,
            timeout=self._timeout_client,
        )
        return HttpxResponse(response)

    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        response = self._client.delete(
            url,
            headers=headers,
            follow_redirects=follow_redirects,
            timeout=self._timeout_client,
        )
        return HttpxResponse(response)

    async def aget(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        response = await self._async_client.get(
            url,
            params=params,
            headers=headers,
            follow_redirects=follow_redirects,
            timeout=self._timeout_client,
        )
        return HttpxResponse(response)

    async def apost(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        response = await self._async_client.post(
            url,
            json=data,
            headers=headers,
            follow_redirects=follow_redirects,
            timeout=self._timeout_client,
        )
        return HttpxResponse(response)

    async def aput(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        response = await self._async_client.put(
            url,
            json=data,
            headers=headers,
            follow_redirects=follow_redirects,
            timeout=self._timeout_client,
        )
        return HttpxResponse(response)

    async def adelete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        response = await self._async_client.delete(
            url,
            headers=headers,
            follow_redirects=follow_redirects,
            timeout=self._timeout_client,
        )
        return HttpxResponse(response)
