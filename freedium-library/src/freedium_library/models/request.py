from typing import Any, Dict, Optional

from httpx import AsyncClient, Client, Response


class Request:
    def __init__(self):
        self._client = Client()
        self._async_client = AsyncClient()

    def __del__(self):
        self._client.close()
        # self._async_client.close()

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> Response:
        return self._client.get(
            url, params=params, headers=headers, follow_redirects=follow_redirects
        )

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> Response:
        return self._client.post(
            url, json=data, headers=headers, follow_redirects=follow_redirects
        )

    def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> Response:
        return self._client.put(
            url, json=data, headers=headers, follow_redirects=follow_redirects
        )

    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> Response:
        return self._client.delete(
            url, headers=headers, follow_redirects=follow_redirects
        )

    async def aget(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> Response:
        return await self._async_client.get(
            url, params=params, headers=headers, follow_redirects=follow_redirects
        )

    async def apost(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> Response:
        return await self._async_client.post(
            url, json=data, headers=headers, follow_redirects=follow_redirects
        )

    async def aput(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> Response:
        return await self._async_client.put(
            url, json=data, headers=headers, follow_redirects=follow_redirects
        )

    async def adelete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> Response:
        return await self._async_client.delete(
            url, headers=headers, follow_redirects=follow_redirects
        )
