import pytest

from freedium_library.services.medium.api import MediumApiService
from freedium_library.services.medium.config import MediumConfig
from freedium_library.utils.http import CurlRequest


POST_IDS = [
    "87bda01ea633",
    "27832c8f6644",
    "b4ee755ee6c5",
    "9dc802a10618",
    "950fee2f8eef",
    "4e4017b89905",
    "252990763468",
    "395390432598",
    "22aad3d232cb",
    "d8f9aa42f6a0",
    "515dd5a43948",
    "d4222bd1a0b3",
    "c58fe28d0c88",
    "cdff5e1f9ff7",
    "cd842ce3f0a3",
    "c81e00f6320d",
]


@pytest.mark.asyncio
async def test_query_post_by_id_integration() -> None:
    config = MediumConfig()
    known_unavailable_ids = {"b4ee755ee6c5"}

    async with CurlRequest() as request:
        api_service = MediumApiService(request=request, config=config)

        failures: list[str] = []
        for post_id in POST_IDS:
            response = await api_service.query_post_by_id(post_id)
            if response is None or response.payload is None or response.payload.value is None:
                if post_id in known_unavailable_ids:
                    pytest.xfail(f"Post {post_id} is unavailable in the public API")
                failures.append(post_id)
                continue

            assert response.payload.value.id == post_id

        assert not failures, f"Failed to fetch/parse post IDs: {', '.join(failures)}"
