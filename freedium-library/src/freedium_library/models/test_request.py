from typing import Any, Literal, Optional

import pytest
from httpx import Response
from pytest_httpx import HTTPXMock

from freedium_library.models.request import Request, RequestConfig


@pytest.fixture
def mock_response() -> dict[str, Any]:
    return {"status_code": 200, "json": {"status": "ok"}}


def test_sync_context_manager(httpx_mock: HTTPXMock, mock_response: dict[str, Any]):
    httpx_mock.add_response(**mock_response)

    with Request() as client:
        response = client.get("http://test.com")
        assert response.status_code == 200
        assert client._in_context_manager is True


def test_sync_without_context_manager(
    httpx_mock: HTTPXMock, mock_response: dict[str, Any]
):
    httpx_mock.add_response(**mock_response)

    with pytest.warns(UserWarning, match="Request should be used as a context manager"):
        client = Request()

    with pytest.warns(
        UserWarning, match="Request is not being used as a context manager"
    ):
        response = client.get("http://test.com")
        assert response.status_code == 200
        assert client._in_context_manager is False


@pytest.mark.asyncio
async def test_async_context_manager(
    httpx_mock: HTTPXMock, mock_response: dict[str, Any]
):
    httpx_mock.add_response(**mock_response)

    async with Request() as client:
        response = await client.aget("http://test.com")
        assert response.status_code == 200
        assert client._in_context_manager is True


@pytest.mark.asyncio
async def test_async_without_context_manager(
    httpx_mock: HTTPXMock, mock_response: Response
):
    httpx_mock.add_response(**mock_response)

    with pytest.warns(UserWarning, match="Request should be used as a context manager"):
        client = Request()

    with pytest.warns(
        UserWarning, match="Request is not being used as a context manager"
    ):
        response = await client.aget("http://test.com")
        assert response.status_code == 200
        assert client._in_context_manager is False


@pytest.mark.parametrize(
    "method,async_method,data",
    [
        ("get", "aget", None),
        ("post", "apost", {"key": "value"}),
        ("put", "aput", {"key": "value"}),
        ("delete", "adelete", None),
    ],
)
def test_http_methods(
    httpx_mock: HTTPXMock,
    mock_response: dict[str, Any],
    method: Literal["get", "post", "put", "delete"],
    async_method: Literal["aget", "apost", "aput", "adelete"],
    data: Optional[dict[Any, Any]],
):
    httpx_mock.add_response(**mock_response)

    with Request() as client:
        func = getattr(client, method)
        kwargs = {"url": "http://test.com"}
        if data:
            kwargs["data"] = data
        response = func(**kwargs)
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
    data: Optional[dict[Any, Any]],
):
    httpx_mock.add_response(**mock_response)

    async with Request() as client:
        func = getattr(client, async_method)
        kwargs = {"url": "http://test.com"}
        if data:
            kwargs["data"] = data
        response = await func(**kwargs)
        assert response.status_code == 200


def test_custom_config():
    config = RequestConfig(timeout=20, retries=5)  # , backoff_factor=0.2
    client = Request(config)
    assert client.config.timeout == 20
    assert client.config.retries == 5
    # assert client.config.backoff_factor == 0.2


@pytest.mark.parametrize("context_manager", [True, False])
def test_resource_cleanup(context_manager):
    if context_manager:
        with Request() as client:
            pass
    else:
        client = Request()
        del client


@pytest.fixture
def request_client():
    return Request()


@pytest.fixture
def custom_config():
    return RequestConfig(timeout=5, retries=2)  # , backoff_factor=0.2


def test_request_config_defaults():
    config = RequestConfig()
    assert config.timeout == 6
    assert config.retries == 3
    # assert config.backoff_factor == 0.1


def test_request_custom_config():
    config = RequestConfig(timeout=5, retries=2)  # , backoff_factor=0.2
    request = Request(config=config)
    assert request.config.timeout == 5
    assert request.config.retries == 2
    # assert request.config.backoff_factor == 0.2


def test_get_request(request_client: Request, httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    expected_response = {"key": "value"}
    httpx_mock.add_response(json=expected_response)

    response = request_client.get(url)
    assert response.json() == expected_response
    request = httpx_mock.get_request()
    assert request.url == url


def test_post_request(request_client: Request, httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    data = {"test": "data"}
    httpx_mock.add_response(json={"status": "success"})

    response = request_client.post(url, data=data)
    request = httpx_mock.get_request()
    assert request.url == url
    assert request.read().decode() == '{"test": "data"}'


def test_put_request(request_client: Request, httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    data = {"test": "data"}
    httpx_mock.add_response(json={"status": "updated"})

    response = request_client.put(url, data=data)
    request = httpx_mock.get_request()
    assert request.url == url
    assert request.read().decode() == '{"test": "data"}'


def test_delete_request(request_client: Request, httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    httpx_mock.add_response(json={"status": "deleted"})

    response = request_client.delete(url)
    request = httpx_mock.get_request()
    assert request.url == url


@pytest.mark.asyncio
async def test_aget_request(request_client: Request, httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    expected_response = {"key": "value"}
    httpx_mock.add_response(json=expected_response)

    response = await request_client.aget(url)
    assert response.json() == expected_response
    request = httpx_mock.get_request()
    assert request.url == url


@pytest.mark.asyncio
async def test_apost_request(request_client: Request, httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    data = {"test": "data"}
    httpx_mock.add_response(json={"status": "success"})

    response = await request_client.apost(url, data=data)
    request = httpx_mock.get_request()
    assert request.url == url
    assert request.read().decode() == '{"test": "data"}'


@pytest.mark.asyncio
async def test_aput_request(request_client: Request, httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    data = {"test": "data"}
    httpx_mock.add_response(json={"status": "updated"})

    response = await request_client.aput(url, data=data)
    request = httpx_mock.get_request()
    assert request.url == url
    assert request.read().decode() == '{"test": "data"}'


@pytest.mark.asyncio
async def test_adelete_request(request_client: Request, httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    httpx_mock.add_response(json={"status": "deleted"})

    response = await request_client.adelete(url)
    request = httpx_mock.get_request()
    assert request.url == url


def test_context_manager(httpx_mock: HTTPXMock):
    with Request() as client:
        url = "https://api.example.com/data"
        httpx_mock.add_response(json={"key": "value"})
        response = client.get(url)
        assert response.json() == {"key": "value"}


@pytest.mark.asyncio
async def test_async_context_manager(httpx_mock: HTTPXMock):
    async with Request() as client:
        url = "https://api.example.com/data"
        httpx_mock.add_response(json={"key": "value"})
        response = await client.aget(url)
        assert response.json() == {"key": "value"}


def test_request_with_params(request_client: Request, httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    params = {"query": "test"}
    httpx_mock.add_response(json={"result": "success"})

    response = request_client.get(url, params=params)
    request = httpx_mock.get_request()
    assert "query=test" in str(request.url)


def test_request_with_headers(request_client: Request, httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    headers = {"Authorization": "Bearer token"}
    httpx_mock.add_response(json={"result": "success"})

    response = request_client.get(url, headers=headers)
    request = httpx_mock.get_request()
    assert request.headers["Authorization"] == "Bearer token"


def test_invalid_json_response(request_client: Request, httpx_mock: HTTPXMock):
    url = "https://api.example.com/data"
    httpx_mock.add_response(text="Invalid JSON")

    response = request_client.get(url)
    with pytest.raises(ValueError):
        response.json()


@pytest.mark.asyncio
async def test_invalid_json_response_async(
    request_client: Request, httpx_mock: HTTPXMock
):
    url = "https://api.example.com/data"
    httpx_mock.add_response(text="Invalid JSON")

    response = await request_client.aget(url)
    with pytest.raises(ValueError):
        response.json()


def test_closed_context_manager_access(httpx_mock: HTTPXMock):
    mock_response_json = {"test": "hahaha"}
    httpx_mock.add_response(json=mock_response_json)

    client = Request()
    with client:
        pass

    response = client.get("https://api.example.com/data")
    assert response.is_closed is True
    response.json() == mock_response_json

    response.close()
    assert response.is_closed


@pytest.mark.asyncio
async def test_closed_context_manager_access_async(httpx_mock: HTTPXMock):
    mock_response_json = {"test": "hahaha"}
    httpx_mock.add_response(json=mock_response_json)

    client = Request()
    with client:
        pass

    response = await client.aget("https://api.example.com/data")
    assert response.is_closed is True
    response.json() == mock_response_json

    response.aclose()
    assert response.is_closed
