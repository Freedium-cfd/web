from __future__ import annotations

from typing import TYPE_CHECKING

from beartype import beartype
from loguru import logger

from freedium_library.services.base import BaseService

from .api import MediumApiService
from .exceptions import InvalidMediumServicePathError
from .models import GraphQLPost
from .renderer import MediumMarkdownRenderer, PostMetadata
from .validators import MediumServicePathValidator

if TYPE_CHECKING:
    from freedium_library.utils.http import HttpxRequest


class MediumService(BaseService):
    """
    Service for fetching and rendering Medium posts as Markdown.

    This service validates Medium URLs/post IDs, fetches post data from the Medium API,
    and renders the content as clean Markdown format.
    """

    def __init__(
        self,
        request: HttpxRequest,
        api_service: MediumApiService,
        path_validator: MediumServicePathValidator,
    ):
        self.request = request
        self.api_service = api_service
        self.path_validator = path_validator

    def _is_valid(self, path: str) -> bool:
        return self.path_validator.is_valid(path)

    async def _ais_valid(self, path: str) -> bool:
        return await self.path_validator.ais_valid(path)

    def _render(self, path: str) -> str:
        """Synchronously render a Medium post to Markdown."""
        raise NotImplementedError(
            "Synchronous rendering not supported. Use async arender() instead."
        )

    async def _arender(self, path: str) -> str:
        """Asynchronously fetch and render a Medium post to Markdown."""
        post_id = await self.path_validator.aextract_post_id(path)
        if not post_id:
            raise InvalidMediumServicePathError(f"Could not extract post ID from: {path}")

        logger.debug(f"Fetching post data for ID: {post_id}")
        post_data = await self.api_service.query_post_by_id(post_id)

        if post_data is None:
            raise InvalidMediumServicePathError(f"Failed to fetch post: {post_id}")

        return self._render_to_markdown(post_data)

    @beartype
    async def arender_with_metadata(self, path: str) -> tuple[str, PostMetadata]:
        """
        Asynchronously fetch and render a Medium post to Markdown with metadata.

        Returns:
            Tuple of (markdown_content, post_metadata)
        """
        post_id = await self.path_validator.aextract_post_id(path)
        if not post_id:
            raise InvalidMediumServicePathError(f"Could not extract post ID from: {path}")

        logger.debug(f"Fetching post data for ID: {post_id}")
        post_data = await self.api_service.query_post_by_id(post_id)

        if post_data is None:
            raise InvalidMediumServicePathError(f"Failed to fetch post: {post_id}")

        renderer = MediumMarkdownRenderer(post_data)
        content = renderer.render()
        return content, renderer.metadata

    @beartype
    async def arender_with_frontmatter(self, path: str) -> str:
        """
        Asynchronously fetch and render a Medium post to Markdown with YAML frontmatter.

        Returns:
            Markdown content with YAML frontmatter containing post metadata.
        """
        post_id = await self.path_validator.aextract_post_id(path)
        if not post_id:
            raise InvalidMediumServicePathError(f"Could not extract post ID from: {path}")

        logger.debug(f"Fetching post data for ID: {post_id}")
        post_data = await self.api_service.query_post_by_id(post_id)

        if post_data is None:
            raise InvalidMediumServicePathError(f"Failed to fetch post: {post_id}")

        renderer = MediumMarkdownRenderer(post_data)
        return renderer.render_with_frontmatter()

    def _render_to_markdown(self, post_data: GraphQLPost) -> str:
        """Convert post data to Markdown format."""
        renderer = MediumMarkdownRenderer(post_data)
        return renderer.render()

    async def _asearch(self, keywords: list[str]) -> list[dict[str, str]]:
        """Search for Medium posts (not implemented)."""
        raise NotImplementedError("Search not implemented")

    def _search(self, keywords: list[str]) -> list[dict[str, str]]:
        """Synchronous search (not implemented)."""
        raise NotImplementedError("Search not implemented")
