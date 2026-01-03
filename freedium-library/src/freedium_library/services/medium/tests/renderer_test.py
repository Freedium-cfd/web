"""Tests for the Medium to Markdown renderer."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from freedium_library.services.medium.renderer import (
    MarkupDict,
    MarkupProcessor,
    MediumMarkdownRenderer,
    ParagraphDict,
    PostMetadata,
    match_percentage,
)


class TestMatchPercentage:
    """Tests for the match_percentage function."""

    def test_identical_strings(self) -> None:
        assert match_percentage("hello", "hello") == 100.0

    def test_completely_different(self) -> None:
        assert match_percentage("abc", "xyz") == 0.0

    def test_partial_match(self) -> None:
        result = match_percentage("hello world", "hello there")
        assert 40 < result < 70  # Partial overlap

    def test_none_values(self) -> None:
        assert match_percentage(None, "hello") == 0.0
        assert match_percentage("hello", None) == 0.0
        assert match_percentage(None, None) == 0.0


class TestMarkupProcessor:
    """Tests for inline markup processing."""

    def test_no_markups(self) -> None:
        processor = MarkupProcessor("Hello world", [])
        assert processor.render() == "Hello world"

    def test_bold_markup(self) -> None:
        markups: list[MarkupDict] = [{"type": "STRONG", "start": 0, "end": 5}]
        processor = MarkupProcessor("Hello world", markups)
        assert processor.render() == "**Hello** world"

    def test_italic_markup(self) -> None:
        markups: list[MarkupDict] = [{"type": "EM", "start": 6, "end": 11}]
        processor = MarkupProcessor("Hello world", markups)
        assert processor.render() == "Hello _world_"

    def test_code_markup(self) -> None:
        markups: list[MarkupDict] = [{"type": "CODE", "start": 0, "end": 5}]
        processor = MarkupProcessor("Hello world", markups)
        assert processor.render() == "`Hello` world"

    def test_link_markup(self) -> None:
        markups: list[MarkupDict] = [
            {
                "type": "A",
                "anchorType": "LINK",
                "start": 0,
                "end": 5,
                "href": "https://example.com",
            }
        ]
        processor = MarkupProcessor("Hello world", markups)
        assert processor.render() == "[Hello](https://example.com) world"

    def test_user_link_markup(self) -> None:
        markups: list[MarkupDict] = [
            {
                "type": "A",
                "anchorType": "USER",
                "start": 0,
                "end": 4,
                "userId": "abc123",
            }
        ]
        processor = MarkupProcessor("John Doe", markups)
        assert processor.render() == "[John](https://medium.com/u/abc123) Doe"

    def test_multiple_non_overlapping_markups(self) -> None:
        markups: list[MarkupDict] = [
            {"type": "STRONG", "start": 0, "end": 5},
            {"type": "EM", "start": 6, "end": 11},
        ]
        processor = MarkupProcessor("Hello world", markups)
        assert processor.render() == "**Hello** _world_"

    def test_overlapping_markups(self) -> None:
        # Bold from 0-7, italic from 3-11
        markups: list[MarkupDict] = [
            {"type": "STRONG", "start": 0, "end": 7},
            {"type": "EM", "start": 3, "end": 11},
        ]
        processor = MarkupProcessor("Hello world", markups)
        result = processor.render()
        # Should handle overlap by splitting spans
        assert "**" in result
        assert "_" in result

    def test_empty_text(self) -> None:
        processor = MarkupProcessor("", [])
        assert processor.render() == ""

    def test_code_escapes_backticks(self) -> None:
        processor = MarkupProcessor("code with `backticks`", [], is_code=True)
        assert processor.render() == "code with \\`backticks\\`"


class TestPostMetadata:
    """Tests for PostMetadata dataclass."""

    def test_default_tags(self) -> None:
        metadata = PostMetadata(
            post_id="123",
            title="Test",
            subtitle="Sub",
            preview_image_id="img1",
            creator_name="Author",
            creator_id="auth1",
            collection_name=None,
            reading_time=5,
            first_published_at=None,
            updated_at=None,
            is_locked=False,
            medium_url="https://medium.com/test",
        )
        assert metadata.tags == []

    def test_with_tags(self) -> None:
        metadata = PostMetadata(
            post_id="123",
            title="Test",
            subtitle="Sub",
            preview_image_id="img1",
            creator_name="Author",
            creator_id="auth1",
            collection_name="Tech",
            reading_time=5,
            first_published_at=1234567890,
            updated_at=1234567890,
            is_locked=True,
            medium_url="https://medium.com/test",
            tags=["python", "programming"],
        )
        assert metadata.tags == ["python", "programming"]
        assert metadata.collection_name == "Tech"
        assert metadata.is_locked is True


class TestMediumMarkdownRendererParagraphs:
    """Tests for paragraph rendering in MediumMarkdownRenderer."""

    def _create_mock_post_data(self, paragraphs: list[ParagraphDict]) -> Any:
        """Create a mock post data structure."""
        mock_body_model = Mock()
        mock_body_model.paragraphs = paragraphs

        mock_content = Mock()
        mock_content.bodyModel = mock_body_model

        mock_preview_image = Mock()
        mock_preview_image.id = "preview123"

        mock_preview_content = Mock()
        mock_preview_content.subtitle = "Test subtitle"

        mock_creator = Mock()
        mock_creator.name = "Test Author"
        mock_creator.id = "creator123"

        mock_post_data = Mock()
        mock_post_data.content = mock_content
        mock_post_data.previewImage = mock_preview_image
        mock_post_data.previewContent = mock_preview_content
        mock_post_data.creator = mock_creator
        mock_post_data.collection = None
        mock_post_data.tags = []
        mock_post_data.readingTime = 5.0
        mock_post_data.id = "post123"
        mock_post_data.title = "Test Title"
        mock_post_data.firstPublishedAt = None
        mock_post_data.updatedAt = None
        mock_post_data.isLocked = False
        mock_post_data.mediumUrl = "https://medium.com/test"

        return mock_post_data

    def test_header_h2(self) -> None:
        paragraphs: list[ParagraphDict] = [
            {"type": "H2", "name": "h2_1", "text": "Main Header", "markups": []}
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)
        result = renderer.render()
        assert "## Main Header" in result

    def test_header_h3(self) -> None:
        paragraphs: list[ParagraphDict] = [
            {"type": "H3", "name": "h3_1", "text": "Sub Header", "markups": []}
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)
        result = renderer.render()
        assert "### Sub Header" in result

    def test_paragraph(self) -> None:
        paragraphs: list[ParagraphDict] = [
            {"type": "P", "name": "p1", "text": "This is a paragraph.", "markups": []}
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)
        result = renderer.render()
        assert "This is a paragraph." in result

    def test_unordered_list(self) -> None:
        paragraphs: list[ParagraphDict] = [
            {"type": "ULI", "name": "li1", "text": "First item", "markups": []},
            {"type": "ULI", "name": "li2", "text": "Second item", "markups": []},
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)
        result = renderer.render()
        assert "- First item" in result
        assert "- Second item" in result

    def test_ordered_list(self) -> None:
        paragraphs: list[ParagraphDict] = [
            {"type": "OLI", "name": "li1", "text": "First item", "markups": []},
            {"type": "OLI", "name": "li2", "text": "Second item", "markups": []},
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)
        result = renderer.render()
        assert "1. First item" in result
        assert "2. Second item" in result

    def test_code_block(self) -> None:
        paragraphs: list[ParagraphDict] = [
            {
                "type": "PRE",
                "name": "code1",
                "text": "print('hello')",
                "markups": [],
                "codeBlockMetadata": {"lang": "python"},
            }
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)
        result = renderer.render()
        assert "```python" in result
        assert "print('hello')" in result
        assert "```" in result

    def test_blockquote(self) -> None:
        paragraphs: list[ParagraphDict] = [
            {"type": "BQ", "name": "bq1", "text": "A wise quote", "markups": []}
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)
        result = renderer.render()
        assert "> A wise quote" in result

    def test_image(self) -> None:
        paragraphs: list[ParagraphDict] = [
            {
                "type": "IMG",
                "name": "img1",
                "text": "Image caption",
                "markups": [],
                "metadata": {"id": "image123", "alt": "Alt text"},
                "layout": "INSET_CENTER",
            }
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)
        result = renderer.render()
        assert "![Alt text]" in result
        assert "image123" in result
        assert "*Image caption*" in result


class TestMediumMarkdownRendererMetadata:
    """Tests for metadata extraction."""

    def test_metadata_property(self) -> None:
        mock_content = Mock()
        mock_content.bodyModel = {"paragraphs": []}

        mock_virtuals = Mock()
        mock_virtuals.previewImage = {"imageId": "preview123"}
        mock_virtuals.readingTime = 10.5
        mock_virtuals.subtitle = "Test subtitle"
        mock_virtuals.tags = [{"name": "python"}, "javascript"]

        mock_value = Mock()
        mock_value.content = mock_content
        mock_value.virtuals = mock_virtuals
        mock_value.id = "post123"
        mock_value.title = "Amazing Article"
        mock_value.creatorId = "creator123"
        mock_value.homeCollectionId = None
        mock_value.firstPublishedAt = 1704067200000
        mock_value.updatedAt = 1704153600000
        mock_value.isSubscriptionLocked = False
        mock_value.mediumUrl = "https://medium.com/amazing-article"

        mock_payload = Mock()
        mock_payload.value = mock_value
        mock_payload.references = None

        mock_post_data = Mock()
        mock_post_data.payload = mock_payload

        renderer = MediumMarkdownRenderer(mock_post_data)  # type: ignore[arg-type]
        metadata = renderer.metadata

        assert metadata.post_id == "post123"
        assert metadata.title == "Amazing Article"
        assert metadata.reading_time == 10
        assert "python" in metadata.tags
        assert "javascript" in metadata.tags


class TestMediumMarkdownRendererTableOfContents:
    """Tests for table of contents extraction."""

    def _create_mock_post_data(self, paragraphs: list[ParagraphDict]) -> Any:
        """Create a mock post data structure."""
        mock_body_model = Mock()
        mock_body_model.paragraphs = paragraphs

        mock_content = Mock()
        mock_content.bodyModel = mock_body_model

        mock_preview_image = Mock()
        mock_preview_image.id = "preview123"

        mock_preview_content = Mock()
        mock_preview_content.subtitle = "Test subtitle"

        mock_creator = Mock()
        mock_creator.name = "Test Author"
        mock_creator.id = "creator123"

        mock_post_data = Mock()
        mock_post_data.content = mock_content
        mock_post_data.previewImage = mock_preview_image
        mock_post_data.previewContent = mock_preview_content
        mock_post_data.creator = mock_creator
        mock_post_data.collection = None
        mock_post_data.tags = []
        mock_post_data.readingTime = 5.0
        mock_post_data.id = "post123"
        mock_post_data.title = "Test Title"
        mock_post_data.firstPublishedAt = None
        mock_post_data.updatedAt = None
        mock_post_data.isLocked = False
        mock_post_data.mediumUrl = "https://medium.com/test"

        return mock_post_data

    def test_extract_h2_and_h3_headings(self) -> None:
        """Test that H2 and H3 headings are extracted to table of contents."""
        paragraphs: list[ParagraphDict] = [
            {"type": "H2", "name": "h2_1", "text": "Introduction", "markups": []},
            {"type": "H3", "name": "h3_1", "text": "Getting Started", "markups": []},
            {"type": "P", "name": "p1", "text": "Some content", "markups": []},
            {"type": "H2", "name": "h2_2", "text": "Conclusion", "markups": []},
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)

        result = renderer.render_with_frontmatter()

        # Check that table_of_contents is in frontmatter
        assert "table_of_contents:" in result

        # Check expected entries are present (as plain text, not markdown links)
        assert '"title": "Introduction"' in result
        assert '"title": "Getting Started"' in result
        assert '"title": "Conclusion"' in result

        # Check IDs are slugified
        assert '"id": "introduction"' in result
        assert '"id": "getting-started"' in result
        assert '"id": "conclusion"' in result

    def test_extract_toc_with_markdown_links(self) -> None:
        """Test that markdown links in headings are preserved as plain text in TOC."""
        paragraphs: list[ParagraphDict] = [
            {
                "type": "H2",
                "name": "h2_1",
                "text": "Check out the nginx cache guide",
                "markups": [
                    {
                        "type": "A",
                        "anchorType": "LINK",
                        "start": 14,
                        "end": 33,
                        "href": "https://www.nginx.com/blog/nginx-caching-guide/",
                    }
                ],
            },
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)

        result = renderer.render_with_frontmatter()

        # The TOC should have plain text (not markdown syntax)
        assert '"title": "Check out the nginx cache guide"' in result
        # The markdown content should still have the link
        assert "[nginx cache guide]" in result

    def test_skip_h4_in_toc(self) -> None:
        """Test that H4 headings are not included in the table of contents."""
        paragraphs: list[ParagraphDict] = [
            {"type": "H2", "name": "h2_1", "text": "Main Header", "markups": []},
            {"type": "H4", "name": "h4_1", "text": "Small Header", "markups": []},
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)

        result = renderer.render_with_frontmatter()

        # H2 should be in TOC
        assert '"title": "Main Header"' in result
        # H4 should NOT be in TOC
        assert '"title": "Small Header"' not in result

    def test_empty_toc(self) -> None:
        """Test that empty table of contents is handled correctly."""
        paragraphs: list[ParagraphDict] = [
            {"type": "P", "name": "p1", "text": "Just a paragraph", "markups": []},
        ]
        post_data = self._create_mock_post_data(paragraphs)
        renderer = MediumMarkdownRenderer(post_data)

        result = renderer.render_with_frontmatter()

        # When no headings, table_of_contents should not be in frontmatter
        assert "table_of_contents:" not in result

