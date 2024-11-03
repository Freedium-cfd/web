from unittest.mock import AsyncMock, Mock

import pytest

from freedium_library.models.request import Request
from freedium_library.services.medium.api import MediumApiService
from freedium_library.services.medium.validators import (
    _MediumServiceHashesValidator,  # type: ignore
    _MediumServiceURLValidator,  # type: ignore
)


@pytest.fixture
def mock_request() -> Mock:
    request = Mock()
    request.get = Mock()
    request.aget = AsyncMock()
    return request


@pytest.fixture
def mock_api_service() -> Mock:
    return Mock()


@pytest.fixture
def url_validator(
    mock_api_service: Mock, mock_request: Mock
) -> _MediumServiceURLValidator:
    hash_validator = _MediumServiceHashesValidator()
    return _MediumServiceURLValidator(
        api_service=mock_api_service,
        hash_validator=hash_validator,
        request=mock_request,
    )


def test_resolve_medium_short_link(
    url_validator: _MediumServiceURLValidator, mock_request: Mock
) -> None:
    mock_request.get.return_value = Mock(
        headers={"Location": "https://medium.com/story-123456789abc"}
    )

    result = url_validator.resolve_medium_short_link("vYe3nWA8wBb")

    assert result == "https://medium.com/story-123456789abc"
    mock_request.get.assert_called_once()
    assert "rsci.app.link/vYe3nWA8wBb" in mock_request.get.call_args[0][0]


@pytest.mark.asyncio
async def test_aresolve_medium_short_link(
    url_validator: _MediumServiceURLValidator, mock_request: Mock
) -> None:
    mock_request.aget.return_value = Mock(
        headers={"Location": "https://medium.com/story-123456789abc"}
    )

    result = await url_validator.aresolve_medium_short_link("vYe3nWA8wBb")

    assert result == "https://medium.com/story-123456789abc"
    mock_request.aget.assert_called_once()
    assert "rsci.app.link/vYe3nWA8wBb" in mock_request.aget.call_args[0][0]


@pytest.mark.asyncio
async def test_resolve_medium_url_with_short_link(
    url_validator: _MediumServiceURLValidator, mock_request: Mock
) -> None:
    mock_request.aget.return_value = Mock(
        headers={"Location": "https://medium.com/story-123456789abc"}
    )

    result = await url_validator.resolve_medium_url(
        "https://link.medium.com/vYe3nWA8wBb"
    )

    assert result == "123456789abc"
    mock_request.aget.assert_called_once()
    assert "rsci.app.link/vYe3nWA8wBb" in mock_request.aget.call_args[0][0]


@pytest.mark.asyncio
async def test_resolve_medium_url_invalid_hash(
    url_validator: _MediumServiceURLValidator, mock_request: Mock
) -> None:
    mock_request.aget.return_value = Mock(
        headers={"Location": "https://medium.com/invalid-story"}
    )

    result = await url_validator.resolve_medium_url(
        "https://link.medium.com/vYe3nWA8wBb"
    )

    assert result is None


@pytest.mark.asyncio
async def test_resolve_medium_url_with_real_short_link(
    url_validator: _MediumServiceURLValidator, mock_request: Mock
) -> None:
    mock_request.aget.return_value = Mock(
        headers={"Location": "https://medium.com/story-77ae792a1a43"}
    )

    result = await url_validator.resolve_medium_url(
        "https://link.medium.com/vYe3nWA8wBb"
    )

    assert result == "77ae792a1a43"
    mock_request.aget.assert_called_once()
    assert "rsci.app.link/vYe3nWA8wBb" in mock_request.aget.call_args[0][0]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_medium_url_with_real_short_link_integration() -> None:
    request = Request()
    api_service = MediumApiService(request=request)
    hash_validator = _MediumServiceHashesValidator()
    url_validator = _MediumServiceURLValidator(api_service, hash_validator, request)

    result = await url_validator.resolve_medium_url(
        "https://link.medium.com/vYe3nWA8wBb"
    )

    assert result == "77ae792a1a43"


@pytest.mark.asyncio
async def test_resolve_medium_url_facebook_redirect(
    url_validator: _MediumServiceURLValidator,
) -> None:
    result = await url_validator.resolve_medium_url(
        "https://l.facebook.com/l.php?u=https://medium.com/story-77ae792a1a43"
    )
    assert result == "77ae792a1a43"


@pytest.mark.asyncio
async def test_resolve_medium_url_google_cache(
    url_validator: _MediumServiceURLValidator,
) -> None:
    result = await url_validator.resolve_medium_url(
        "https://webcache.googleusercontent.com/search?q=https://medium.com/story-77ae792a1a43"
    )
    assert result == "77ae792a1a43"


@pytest.mark.asyncio
async def test_resolve_medium_url_google_redirect(
    url_validator: _MediumServiceURLValidator,
) -> None:
    result = await url_validator.resolve_medium_url(
        "https://google.com/url?url=https://medium.com/story-77ae792a1a43"
    )
    assert result == "77ae792a1a43"


@pytest.mark.asyncio
async def test_resolve_medium_url_12ft(
    url_validator: _MediumServiceURLValidator,
) -> None:
    result = await url_validator.resolve_medium_url(
        "https://12ft.io?q=https://medium.com/story-77ae792a1a43"
    )
    assert result == "77ae792a1a43"


@pytest.mark.asyncio
async def test_resolve_medium_url_global_identity(
    url_validator: _MediumServiceURLValidator,
) -> None:
    result = await url_validator.resolve_medium_url(
        "https://medium.com/m/global-identity-2?redirectUrl=https://medium.com/story-77ae792a1a43"
    )
    assert result == "77ae792a1a43"


@pytest.mark.asyncio
async def test_resolve_medium_url_mobile_link(
    url_validator: _MediumServiceURLValidator,
) -> None:
    result = await url_validator.resolve_medium_url("https://medium.com/p/77ae792a1a43")
    assert result == "77ae792a1a43"


def test_hash_validator_valid_hash(url_validator: _MediumServiceURLValidator) -> None:
    result = url_validator.hash_validator.is_valid("77ae792a1a43")
    assert result is True


def test_hash_validator_invalid_hash(url_validator: _MediumServiceURLValidator) -> None:
    result = url_validator.hash_validator.is_valid("invalid")
    assert result is False


def test_hash_validator_extract_hashes(
    url_validator: _MediumServiceURLValidator,
) -> None:
    result = url_validator.hash_validator.extract_hashes("story-77ae792a1a43-something")
    assert result == ["77ae792a1a43"]
