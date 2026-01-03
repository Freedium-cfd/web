import warnings
from types import TracebackType
from typing import Any, Dict, Optional, Type

from curl_cffi.requests import Session, AsyncSession

from .abstract import AbstractRequest
from .config import RequestConfig
from .curl_response import CurlResponse
from .response import AbstractResponse


class CurlRequest(AbstractRequest):
    __slots__ = ("config", "_in_context_manager", "_session", "_async_session")

    def __init__(self, config: Optional[RequestConfig] = None):
        self.config = config or RequestConfig()
        self._in_context_manager = False
        self._session: Any = None
        self._async_session: Any = None
        warnings.warn(
            "Request should be used as a context manager using 'with' or 'async with' "
            "to ensure proper resource cleanup",
            stacklevel=2,
        )

    def _get_session(self) -> Any:
        if not self._session:
            self._session = Session(impersonate="chrome110")
        return self._session

    async def _get_async_session(self) -> Any:
        if not self._async_session:
            self._async_session = AsyncSession(impersonate="chrome110")
        return self._async_session

    def __enter__(self) -> "CurlRequest":
        self._in_context_manager = True
        self._session = Session(impersonate="chrome110")
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._session:
            self._session.close()
        self._session = None

    async def __aenter__(self) -> "CurlRequest":
        self._in_context_manager = True
        self._async_session = AsyncSession(impersonate="chrome110")
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._async_session:
            await self._async_session.close()
        self._async_session = None

    def __del__(self):
        if self._session:
            self._session.close()
        # Can't handle async session cleanup in __del__

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
        session = self._get_session()
        response = session.get(
            url,
            params=params,
            headers=headers,
            allow_redirects=follow_redirects,
            timeout=self.config.timeout,
        )
        return CurlResponse(response)

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        session = self._get_session()
        response = session.post(
            url,
            json=data,
            headers=headers,
            allow_redirects=follow_redirects,
            timeout=self.config.timeout,
        )
        return CurlResponse(response)

    def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        session = self._get_session()
        response = session.put(
            url,
            json=data,
            headers=headers,
            allow_redirects=follow_redirects,
            timeout=self.config.timeout,
        )
        return CurlResponse(response)

    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        session = self._get_session()
        response = session.delete(
            url,
            headers=headers,
            allow_redirects=follow_redirects,
            timeout=self.config.timeout,
        )
        return CurlResponse(response)

    async def aget(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        session = await self._get_async_session()
        response = await session.get(
            url,
            params=params,
            headers=headers,
            allow_redirects=follow_redirects,
            timeout=self.config.timeout,
        )
        return CurlResponse(response)

    async def apost(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        session = await self._get_async_session()
        response = await session.post(
            url,
            json=data,
            headers=headers,
            allow_redirects=follow_redirects,
            timeout=self.config.timeout,
        )
        return CurlResponse(response)

    async def aput(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        session = await self._get_async_session()
        response = await session.put(
            url,
            json=data,
            headers=headers,
            allow_redirects=follow_redirects,
            timeout=self.config.timeout,
        )
        return CurlResponse(response)

    async def adelete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> AbstractResponse:
        self._check_context_manager()
        session = await self._get_async_session()
        response = await session.delete(
            url,
            headers=headers,
            allow_redirects=follow_redirects,
            timeout=self.config.timeout,
        )
        return CurlResponse(response)
