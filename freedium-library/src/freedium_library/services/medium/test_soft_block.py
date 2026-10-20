from unittest.mock import AsyncMock, MagicMock
import pytest

from freedium_library.services.medium.exceptions import MediumBlockedError


@pytest.mark.asyncio
async def test_medium_soft_block_raises_medium_blocked_error(monkeypatch):
    """When Medium returns 200 with null post (soft-block), query_post_graphql raises MediumBlockedError."""
    from freedium_library.services.medium.api import MediumApiService

    request = MagicMock()
    # Mock apost to return 200 with data.post = None
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"data": {"post": null}}'

    # Async context manager mock for request
    cm = AsyncMock()
    cm.apost = AsyncMock(return_value=mock_resp)
    request.__aenter__.return_value = cm

    config = MagicMock()
    config.cookies = None

    service = MediumApiService(request=request, config=config, cache=None)

    with pytest.raises(MediumBlockedError) as exc_info:
        await service.query_post_graphql("some_post_id")

    assert "soft-block" in str(exc_info.value)
    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "UPSTREAM_BLOCKED"
