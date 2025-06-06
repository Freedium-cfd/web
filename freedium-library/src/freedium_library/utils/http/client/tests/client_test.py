from typing import Any, Dict, Literal, Optional, cast

import pytest
from httpx import Request as HttpxNativeRequest
from pytest_httpx import HTTPXMock

from freedium_library.utils.http.client import HttpxRequest, RequestConfig


@pytest.fixture
def mock_response() -> dict[str, Any]:
    return {"status_code": 200, "json": {"status": "ok"}}


def test_sync_context_manager(httpx_mock: HTTPXMock, mock_response: dict[str, Any]):
    httpx_mock.add_response(**mock_response)

    with HttpxRequest() as client:
        response = client.get("http://test.com")
        assert response.status_code == 200
        # Access internal attribute for testing
        assert getattr(client, "_in_context_manager") is True


def test_sync_without_context_manager(
    httpx_mock: HTTPXMock, mock_response: dict[str, Any]
):
    httpx_mock.add_response(**mock_response)

    with pytest.warns(UserWarning, match="Request should be used as a context manager"):
        client = HttpxRequest()

    with pytest.warns(
        UserWarning, match="Request is not being used as a context manager"
    ):
        response = client.get("http://test.com")
        assert response.status_code == 200
        # Access internal attribute for testing
        assert getattr(client, "_in_context_manager") is False


@pytest.mark.asyncio
async def test_async_context_manager(
    httpx_mock: HTTPXMock, mock_response: dict[str, Any]
):
    httpx_mock.add_response(**mock_response)

    async with HttpxRequest() as client:
        response = await client.aget("http://test.com")
        assert response.status_code == 200
        # Access internal attribute for testing
        assert getattr(client, "_in_context_manager") is True


@pytest.mark.asyncio
async def test_async_without_context_manager(
    httpx_mock: HTTPXMock, mock_response: dict[str, Any]
):
    httpx_mock.add_response(**mock_response)

    with pytest.warns(UserWarning, match="Request should be used as a context manager"):
        client = HttpxRequest()

    with pytest.warns(
        UserWarning, match="Request is not being used as a context manager"
    ):
        response = await client.aget("http://test.com")
        assert response.status_code == 200
        # Access internal attribute for testing
        assert getattr(client, "_in_context_manager") is False


@pytest.mark.parametrize(
    "method,async_method,data",
    [
        ("get", "aget", None),
        ("post", "apost", {"key": "value"}),
        ("put", "aput", {"key": "value"}),
        ("delete", "adelete", None),
    ],
)
@pytest.mark.asyncio
async def test_http_methods(
    httpx_mock: HTTPXMock,
    mock_response: dict[str, Any],
    method: Literal["get", "post", "put", "delete"],
    async_method: Literal["aget", "apost", "aput", "adelete"],
    data: Optional[Dict[str, Any]],
):
    httpx_mock.add_response(**mock_response)

    async with HttpxRequest() as client:
        func = getattr(client, async_method)
        kwargs: Dict[str, Any] = {"url": "http://test.com"}
        if data:
            if async_method in ["apost", "aput"]:
                kwargs["data"] = data
            else:
                kwargs["params"] = data
        response = await func(**kwargs)
        assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,async_method,data",
    [
        ("get", "aget", None),
        ("post", "apost", {"key": "value"}),
        ("put", "aput", {"key": "value"}),
        ("delete", "adelete", None),
    ],
)
async def test_async_http_methods(
    httpx_mock: HTTPXMock,
    mock_response: dict[str, Any],
    method: Literal["get", "post", "put", "delete"],
    async_method: Literal["aget", "apost", "aput", "adelete"],
    data: Optional[Dict[str, Any]],
):
    httpx_mock.add_response(**mock_response)

    async with HttpxRequest() as client:
        func = getattr(client, async_method)
        kwargs: Dict[str, Any] = {"url": "http://test.com"}
        if data:
            if async_method in ["apost", "aput"]:
                kwargs["data"] = data
            else:
                kwargs["params"] = data
        response = await func(**kwargs)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_custom_config():
    config = RequestConfig(timeout=20, retries=5)
    async with HttpxRequest(config) as client:
        assert client.config.timeout == 20
        assert client.config.retries == 5


@pytest.mark.parametrize("context_manager", [True, False])
def test_resource_cleanup(context_manager: bool):
    if context_manager:
        with HttpxRequest() as client:
            pass
    else:
        with pytest.warns(
            UserWarning, match="Request should be used as a context manager"
        ):
            client = HttpxRequest()
        del client


@pytest.fixture
def request_client():
    return HttpxRequest()


@pytest.fixture
def custom_config():
    return RequestConfig(timeout=5, retries=2)


def test_request_config_defaults():
    config = RequestConfig()
    assert config.timeout == 6
    assert config.retries == 3


@pytest.mark.asyncio
async def test_request_custom_config(custom_config: RequestConfig):
    async with HttpxRequest(config=custom_config) as request:
        assert request.config.timeout == 5
        assert request.config.retries == 2


@pytest.mark.asyncio
async def test_get_request(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    expected_response = {"key": "value"}
    httpx_mock.add_response(json=expected_response)

    async with HttpxRequest() as request_client:
        response = await request_client.aget(url)
        assert response.json() == expected_response
        request = cast(HttpxNativeRequest, httpx_mock.get_request())
        assert str(request.url) == url


@pytest.mark.asyncio
async def test_post_request(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    data = {"test": "data"}
    httpx_mock.add_response(json={"status": "success"})

    async with HttpxRequest() as request_client:
        response = await request_client.apost(url, data=data)
        assert response.status_code == 200
        request = cast(HttpxNativeRequest, httpx_mock.get_request())
        assert str(request.url) == url
        assert request.read().decode() == '{"test":"data"}'


@pytest.mark.asyncio
async def test_put_request(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    data = {"test": "data"}
    httpx_mock.add_response(json={"status": "updated"})

    async with HttpxRequest() as request_client:
        response = await request_client.aput(url, data=data)
        assert response.status_code == 200
        request = cast(HttpxNativeRequest, httpx_mock.get_request())
        assert str(request.url) == url
        assert request.read().decode() == '{"test":"data"}'


@pytest.mark.asyncio
async def test_delete_request(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    httpx_mock.add_response(json={"status": "deleted"})

    async with HttpxRequest() as request_client:
        response = await request_client.adelete(url)
        assert response.status_code == 200
        request = cast(HttpxNativeRequest, httpx_mock.get_request())
        assert str(request.url) == url


@pytest.mark.asyncio
async def test_aget_request(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    expected_response = {"key": "value"}
    httpx_mock.add_response(json=expected_response)

    async with HttpxRequest() as request_client:
        response = await request_client.aget(url)
        assert response.json() == expected_response
        request = cast(HttpxNativeRequest, httpx_mock.get_request())
        assert str(request.url) == url


@pytest.mark.asyncio
async def test_apost_request(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    data = {"test": "data"}
    httpx_mock.add_response(json={"status": "success"})

    async with HttpxRequest() as request_client:
        response = await request_client.apost(url, data=data)
        assert response.status_code == 200
        request = cast(HttpxNativeRequest, httpx_mock.get_request())
        assert str(request.url) == url
        assert request.read().decode() == '{"test":"data"}'


@pytest.mark.asyncio
async def test_aput_request(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    data = {"test": "data"}
    httpx_mock.add_response(json={"status": "updated"})

    async with HttpxRequest() as request_client:
        response = await request_client.aput(url, data=data)
        assert response.status_code == 200
        request = cast(HttpxNativeRequest, httpx_mock.get_request())
        assert str(request.url) == url
        assert request.read().decode() == '{"test":"data"}'


@pytest.mark.asyncio
async def test_adelete_request(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    httpx_mock.add_response(json={"status": "deleted"})

    async with HttpxRequest() as request_client:
        response = await request_client.adelete(url)
        assert response.status_code == 200
        request = cast(HttpxNativeRequest, httpx_mock.get_request())
        assert str(request.url) == url


def test_context_manager(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"status": "ok"})

    with HttpxRequest() as client:
        response = client.get("http://test.com")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_async_context_manager_cleanup(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"status": "ok"})

    async with HttpxRequest() as client:
        response = await client.aget("http://test.com")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_request_with_params(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    params = {"param1": "value1", "param2": "value2"}
    httpx_mock.add_response(json={"status": "success"})

    async with HttpxRequest() as request_client:
        response = await request_client.aget(url, params=params)
        assert response.status_code == 200
        request = cast(HttpxNativeRequest, httpx_mock.get_request())
        assert str(request.url) == f"{url}?param1=value1&param2=value2"


@pytest.mark.asyncio
async def test_request_with_headers(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    headers = {"X-Custom-Header": "test"}
    httpx_mock.add_response(json={"status": "success"})

    async with HttpxRequest() as request_client:
        response = await request_client.aget(url, headers=headers)
        assert response.status_code == 200
        request = cast(HttpxNativeRequest, httpx_mock.get_request())
        assert str(request.url) == url
        assert request.headers["X-Custom-Header"] == "test"


@pytest.mark.asyncio
async def test_invalid_json_response(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    httpx_mock.add_response(content=b"invalid json", status_code=200)

    async with HttpxRequest() as request_client:
        response = await request_client.aget(url)
        assert response.status_code == 200
        with pytest.raises(Exception):
            response.json()


@pytest.mark.asyncio
async def test_invalid_json_response_async(httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    httpx_mock.add_response(content=b"invalid json", status_code=200)

    async with HttpxRequest() as request_client:
        response = await request_client.aget(url)
        assert response.status_code == 200
        with pytest.raises(Exception):
            response.json()
