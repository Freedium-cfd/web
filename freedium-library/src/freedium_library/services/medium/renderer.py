"""
Optimized Medium to Markdown renderer.

This module provides high-performance conversion of Medium post data to Markdown format.
It processes paragraphs and inline markups efficiently using UTF-16 position-aware formatting.
Medium stores markup positions as UTF-16 code unit offsets, which this module handles correctly.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final

import yaml
from loguru import logger

from freedium_library.utils.utils.utf_handler import UTFEncoding, UTFHandler

if TYPE_CHECKING:
    from .api import MediumApiService
    from .models import GraphQLPost

# Type alias for Medium paragraph/markup dictionaries
ParagraphDict = dict[str, Any]
MarkupDict = dict[str, Any]


# Paragraph type constants
class ParagraphType:
    H2: Final[str] = "H2"
    H3: Final[str] = "H3"
    H4: Final[str] = "H4"
    P: Final[str] = "P"
    IMG: Final[str] = "IMG"
    ULI: Final[str] = "ULI"
    OLI: Final[str] = "OLI"
    PRE: Final[str] = "PRE"
    BQ: Final[str] = "BQ"
    PQ: Final[str] = "PQ"
    MIXTAPE_EMBED: Final[str] = "MIXTAPE_EMBED"
    IFRAME: Final[str] = "IFRAME"


# Markup type constants
class MarkupType:
    A: Final[str] = "A"
    STRONG: Final[str] = "STRONG"
    EM: Final[str] = "EM"
    CODE: Final[str] = "CODE"


# Anchor type constants
class AnchorType:
    LINK: Final[str] = "LINK"
    USER: Final[str] = "USER"


@dataclass(slots=True)
class MarkupSpan:
    """Represents a formatted text span with start/end positions and formatting markers."""

    start: int
    end: int
    prefix: str
    suffix: str


def _default_tags() -> list[str]:
    """Factory function for default tags list."""
    return []


@dataclass(slots=True)
class PostMetadata:
    """Extracted metadata from a Medium post."""

    post_id: str
    title: str
    subtitle: str
    preview_image_id: str
    creator_name: str
    creator_id: str
    collection_name: str | None
    reading_time: int
    first_published_at: int | None
    updated_at: int | None
    is_locked: bool
    medium_url: str
    tags: list[str] = field(default_factory=_default_tags)


def match_percentage(s1: str | None, s2: str | None) -> float:
    """Calculate similarity percentage between two strings."""
    if s1 is None or s2 is None:
        return 0.0
    return difflib.SequenceMatcher(None, s1, s2).ratio() * 100


def _escape_markdown_minimal(text: str) -> str:
    """Minimal escaping for code blocks - only escape backticks."""
    return text.replace("`", "\\`")


# Map of smart quote characters to standard ASCII quotes
_QUOTE_MAP = {
    '\u201c': '"',   # Left double quotation mark → "
    '\u201d': '"',   # Right double quotation mark → "
    '\u2018': "'",   # Left single quotation mark → '
    '\u2019': "'",   # Right single quotation mark → '
}


def _normalize_quotes(text: str) -> str:
    """
    Normalize smart quotes to standard ASCII quotes.

    Converts: \u201c \u201d \u2018 \u2019 → " and '
    """
    if not text:
        return text
    for smart_quote, ascii_quote in _QUOTE_MAP.items():
        text = text.replace(smart_quote, ascii_quote)
    return text


def _unescape_markdown_url(url: str) -> str:
    """
    Unescape markdown special characters in URLs.

    Medium API sometimes returns URLs with escaped characters like \\) or \\(
    which should not be escaped in markdown link syntax. Also handles trailing
    backslashes that break markdown link syntax.
    """
    if not url:
        return url
    # Unescape parentheses and brackets that shouldn't be escaped in URLs
    url = url.replace('\\)', ')')
    url = url.replace('\\(', '(')
    url = url.replace('\\[', '[')
    url = url.replace('\\]', ']')
    # Remove trailing backslash that breaks markdown link syntax
    # This happens when Medium's URL fragment ends with a character Medium tries to escape
    if url.endswith('\\'):
        url = url[:-1]
    return url


class _UTF16StringHandler(UTFHandler):
    """UTF-16 aware string handler for Medium markup processing."""

    def __init__(self, text: str) -> None:
        super().__init__(text, UTFEncoding.UTF16)

    def get_python_position(self, utf16_pos: int) -> int:
        """Convert UTF-16 code unit position to Python string index."""
        return self.get_original_position(utf16_pos)


class MarkupProcessor:
    """
    Efficiently processes inline markups and applies them to text.

    Uses UTF-16 position mapping since Medium stores positions as UTF-16 code units.
    """

    __slots__ = ("_text", "_spans", "_is_code", "_utf_handler")

    def __init__(
        self, text: str, markups: list[MarkupDict], *, is_code: bool = False
    ) -> None:
        self._text = text
        self._is_code = is_code
        # Initialize UTF-16 handler for proper position mapping
        self._utf_handler = _UTF16StringHandler(text) if text else None
        self._spans = self._parse_markups(markups)

    def _utf16_to_python_pos(self, utf16_pos: int) -> int:
        """Convert UTF-16 position to Python string position."""
        if not self._utf_handler or utf16_pos <= 0:
            return utf16_pos
        # Clamp to valid range
        return min(self._utf_handler.get_python_position(utf16_pos), len(self._text))

    def _parse_markups(self, markups: list[MarkupDict]) -> list[MarkupSpan]:
        """Parse markup definitions into MarkupSpan objects with Python positions."""
        spans: list[MarkupSpan] = []

        # First pass: identify all markups and their ranges
        markup_ranges: list[tuple[int, int, str, MarkupSpan]] = []

        for markup in markups:
            markup_type = markup.get("type")
            if not markup_type:
                # Skip markups without a type
                continue

            # Convert UTF-16 positions to Python positions
            start = self._utf16_to_python_pos(markup.get("start", 0))
            end = self._utf16_to_python_pos(markup.get("end", 0))

            # Trim leading/trailing whitespace from bold, italic, and code spans
            # This prevents invalid markdown like **text ** from being generated
            if markup_type in (MarkupType.STRONG, MarkupType.EM, MarkupType.CODE):
                text_segment = self._text[start:end]
                # Count leading whitespace
                leading_ws = len(text_segment) - len(text_segment.lstrip())
                # Count trailing whitespace
                trailing_ws = len(text_segment) - len(text_segment.rstrip())
                # Adjust positions
                start += leading_ws
                end -= trailing_ws

                # Skip markup if after trimming, only punctuation/whitespace remains
                trimmed_text = self._text[start:end]
                if trimmed_text and not any(c.isalnum() for c in trimmed_text):
                    # All non-alphanumeric (punctuation, whitespace, symbols) - skip
                    continue

            # Now markup_type is guaranteed to be a string
            markup_type_str: str = str(markup_type)

            if markup_type == MarkupType.STRONG:
                span = MarkupSpan(start, end, "**", "**")
                markup_ranges.append((start, end, markup_type_str, span))
            elif markup_type == MarkupType.EM:
                span = MarkupSpan(start, end, "_", "_")
                markup_ranges.append((start, end, markup_type_str, span))
            elif markup_type == MarkupType.CODE:
                span = MarkupSpan(start, end, "`", "`")
                markup_ranges.append((start, end, markup_type_str, span))
            elif markup_type == MarkupType.A:
                anchor_type = markup.get("anchorType")
                if anchor_type == AnchorType.LINK:
                    href = markup.get("href", "")
                    # Unescape markdown special characters in URL
                    href = _unescape_markdown_url(href)
                    span = MarkupSpan(start, end, "[", f"]({href})")
                    markup_ranges.append((start, end, markup_type_str, span))
                elif anchor_type == AnchorType.USER:
                    user_id = markup.get("userId", "")
                    url = f"https://medium.com/u/{user_id}"
                    span = MarkupSpan(start, end, "[", f"]({url})")
                    markup_ranges.append((start, end, markup_type_str, span))

        # Second pass: handle overlapping markup priorities
        # Priority order: LINK > CODE > EM/STRONG
        # - LINK markup wins over CODE (for clickable links)
        # - CODE markup wins over EM/STRONG (to preserve code formatting)
        # - LINK wins over EM/STRONG (to avoid broken markdown with overlaps)

        # Build sets of ranges for each high-priority markup type
        link_ranges = {(start, end) for start, end, mtype, _ in markup_ranges if mtype == MarkupType.A}
        code_ranges = {(start, end) for start, end, mtype, _ in markup_ranges if mtype == MarkupType.CODE}

        # Helper to check if ranges overlap
        def ranges_overlap(start1: int, end1: int, start2: int, end2: int) -> bool:
            return start1 < end2 and start2 < end1

        # Add spans, applying priority filtering
        for start, end, mtype, span in markup_ranges:
            # Skip CODE if there's a LINK in the exact same range
            if mtype == MarkupType.CODE and (start, end) in link_ranges:
                continue
            # Skip EM or STRONG if there's CODE in the exact same range
            if mtype in (MarkupType.EM, MarkupType.STRONG) and (start, end) in code_ranges:
                continue
            # Skip EM or STRONG if it overlaps with any LINK or CODE
            if mtype in (MarkupType.EM, MarkupType.STRONG):
                skip = False
                # Check overlap with links
                for link_start, link_end in link_ranges:
                    if ranges_overlap(start, end, link_start, link_end):
                        skip = True
                        break
                # Check overlap with code
                if not skip:
                    for code_start, code_end in code_ranges:
                        if ranges_overlap(start, end, code_start, code_end):
                            skip = True
                            break
                if skip:
                    continue
            spans.append(span)

        return spans

    def _split_overlapping(self, spans: list[MarkupSpan]) -> list[MarkupSpan]:
        """Split overlapping spans into non-overlapping segments."""
        if not spans:
            return []

        # Collect all boundary points
        events: list[tuple[int, int, MarkupSpan]] = []
        for span in spans:
            events.append((span.start, 0, span))  # 0 = start event
            events.append((span.end, 1, span))  # 1 = end event

        # Sort by position, then by event type (starts before ends at same position)
        events.sort(key=lambda x: (x[0], x[1]))

        result: list[MarkupSpan] = []
        active_spans: list[MarkupSpan] = []
        prev_pos = 0

        for pos, event_type, span in events:
            if active_spans and pos > prev_pos:
                # Create combined span for the segment [prev_pos, pos)
                combined_prefix = "".join(s.prefix for s in active_spans)
                combined_suffix = "".join(s.suffix for s in reversed(active_spans))
                result.append(MarkupSpan(prev_pos, pos, combined_prefix, combined_suffix))

            if event_type == 0:  # Start
                active_spans.append(span)
            else:  # End
                if span in active_spans:
                    active_spans.remove(span)

            prev_pos = pos

        return result

    def render(self) -> str:
        """Render the text with all markups applied."""
        if not self._spans:
            if self._is_code:
                return _escape_markdown_minimal(self._text)
            return self._text

        # Process overlapping spans
        processed_spans = self._split_overlapping(self._spans)

        # Build result efficiently using a list
        result: list[str] = []
        last_end = 0

        for span in processed_spans:
            # Add text before this span
            if span.start > last_end:
                segment = self._text[last_end : span.start]
                if self._is_code:
                    segment = _escape_markdown_minimal(segment)
                result.append(segment)

            # Add formatted text
            segment_text = self._text[span.start : span.end]
            if self._is_code:
                segment_text = _escape_markdown_minimal(segment_text)
            result.append(f"{span.prefix}{segment_text}{span.suffix}")

            last_end = span.end

        # Add remaining text
        if last_end < len(self._text):
            segment = self._text[last_end:]
            if self._is_code:
                segment = _escape_markdown_minimal(segment)
            result.append(segment)

        return "".join(result)


class MediumMarkdownRenderer:
    """
    High-performance Medium post to Markdown renderer.

    Converts Medium's internal paragraph-based format to clean Markdown.
    Handles all paragraph types including headers, paragraphs, lists,
    code blocks, quotes, images, and embeds.
    """

    __slots__ = ("_post_data", "_paragraphs", "_output", "_metadata", "_pos", "_api_service", "_use_base64_images")

    def __init__(
        self,
        post_data: GraphQLPost,
        api_service: MediumApiService,
        use_base64_images: bool = True,
    ) -> None:
        self._post_data = post_data
        self._output: list[str] = []
        self._pos = 0
        self._metadata: PostMetadata | None = None
        self._api_service = api_service
        self._use_base64_images = use_base64_images

        # Extract paragraphs from GraphQL post data
        if post_data.content and post_data.content.bodyModel:
            self._paragraphs: list[ParagraphDict] = [  # type: ignore[misc]
                p.model_dump(mode="json") if hasattr(p, "model_dump") else p
                for p in (post_data.content.bodyModel.paragraphs or [])
            ]
        else:
            self._paragraphs = []

    def _escape_html_attribute(self, text: str) -> str:
        """Escape text for use in HTML attributes to prevent XSS.

        Escapes: &, ", ', <, >
        """
        if not text:
            return text
        return (
            text.replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _generate_image_urls(
        self, image_id: str, original_width: int | None, original_height: int | None
    ) -> dict[str, int | str]:
        """Generate image URLs for different sizes.

        Returns dict with:
        - 'medium': 700px version (mobile/default)
        - 'original': 2000px version (desktop)
        - 'zoom': 4000px version (high-definition zoom for medium-zoom library)
        - 'width': Width for HTML attributes
        - 'height': Height for HTML attributes
        """
        base_url = "https://miro.medium.com/v2/resize:fit"

        urls: dict[str, int | str] = {
            "medium": f"{base_url}:700/{image_id}",
            "original": f"{base_url}:2000/{image_id}",
            "zoom": f"{base_url}:4000/{image_id}",
        }

        # Store dimensions for HTML attributes (prevent Cumulative Layout Shift)
        if original_width and original_height:
            urls["width"] = original_width
            urls["height"] = original_height
        else:
            # Fallback to 4:3 aspect ratio if dimensions unavailable
            urls["width"] = 700
            urls["height"] = 525

        return urls

    def _render_responsive_picture(self, metadata: dict[str, Any], alt_text: str) -> str:
        """Render a responsive picture element in HTML format for normal mode.

        Generates HTML picture element with:
        - Mobile: 700px version
        - Desktop: 2000px version
        - HD Zoom: 4000px version via data-zoom-src for medium-zoom library
        - Width/height attributes for layout shift prevention
        - Lazy loading and prose styling

        Args:
            metadata: Image metadata dict with 'id', 'originalWidth', 'originalHeight'
            alt_text: Alternative text for accessibility

        Returns:
            HTML string with picture element
        """
        image_id = metadata.get("id", "")
        if not image_id:
            return ""

        original_width = metadata.get("originalWidth")
        original_height = metadata.get("originalHeight")

        urls = self._generate_image_urls(image_id, original_width, original_height)

        alt_escaped = self._escape_html_attribute(alt_text)
        width = urls.get("width", 700)
        height = urls.get("height", 525)

        picture_html = f'''<picture>
  <source media="(max-width: 768px)" srcset="{urls['medium']} 1x">
  <source media="(min-width: 769px)" srcset="{urls['original']} 1x">
  <img src="{urls['medium']}" alt="{alt_escaped}" width="{width}" height="{height}" loading="lazy" data-zoom-src="{urls['zoom']}" class="prose-image"/>
</picture>'''

        return picture_html

    def _render_responsive_picture_base64(
        self,
        metadata: dict[str, Any],
        alt_text: str,
        medium_src: str,
        original_url: str,
        zoom_url: str,
    ) -> str:
        """Render a responsive picture element with embedded medium + linked original and zoom.

        Used when base64 embedding is enabled. Only the 700px version is embedded
        as a data URI to balance offline capability with payload size. The original
        version is linked for desktop users. The zoom version loads for high-DPI zoom views.

        Args:
            metadata: Image metadata dict with 'id', 'originalWidth', 'originalHeight'
            alt_text: Alternative text for accessibility
            medium_src: Base64 data URI or URL for 700px version
            original_url: URL for 2000px full-resolution version
            zoom_url: URL for 4000px high-definition zoom version

        Returns:
            HTML string with picture element
        """
        original_width = metadata.get("originalWidth")
        original_height = metadata.get("originalHeight")

        # Generate dimensions for layout shift prevention
        if original_width and original_height:
            width = original_width
            height = original_height
        else:
            width = 700
            height = 525

        alt_escaped = self._escape_html_attribute(alt_text)

        picture_html = f'''<picture>
  <source media="(max-width: 768px)" srcset="{medium_src} 1x">
  <source media="(min-width: 769px)" srcset="{original_url} 1x">
  <img src="{medium_src}" alt="{alt_escaped}" width="{width}" height="{height}" loading="lazy" data-zoom-src="{zoom_url}" class="prose-image"/>
</picture>'''

        return picture_html

    async def _get_image_as_base64(self, image_url: str) -> str | None:
        """Fetch image from URL and encode as base64 data URI.

        Uses the API service's HTTP client to fetch the image, respecting
        proxy settings and connection pooling configured in the service.

        Args:
            image_url: The URL of the image to fetch

        Returns:
            The complete data URI string or None if fetch fails.
        """
        return await self._api_service.fetch_image_as_base64(image_url)

    def _extract_metadata(self) -> PostMetadata:
        """Extract metadata from GraphQL post data."""
        post = self._post_data

        # Get preview image ID
        preview_image_id = ""
        if post.previewImage and post.previewImage.id:
            preview_image_id = post.previewImage.id

        # Get creator info from GraphQL structure
        creator_name = ""
        creator_id = ""
        if post.creator:
            creator_name = post.creator.name or ""
            creator_id = post.creator.id or ""

        # Get collection name from GraphQL structure
        collection_name = None
        if post.collection:
            collection_name = post.collection.name

        # Get tags from GraphQL structure
        tags: list[str] = []
        if post.tags:
            for tag in post.tags:
                if tag.displayTitle:
                    tags.append(tag.displayTitle)

        # Get reading time and subtitle
        reading_time = int(post.readingTime) if post.readingTime else 0
        subtitle = ""
        if post.previewContent and post.previewContent.subtitle:
            subtitle = post.previewContent.subtitle

        return PostMetadata(
            post_id=post.id or "",
            title=post.title or "",
            subtitle=subtitle,
            preview_image_id=preview_image_id,
            creator_name=creator_name,
            creator_id=creator_id,
            collection_name=collection_name,
            reading_time=reading_time,
            first_published_at=post.firstPublishedAt,
            updated_at=post.updatedAt,
            is_locked=post.isLocked or False,
            medium_url=post.mediumUrl or "",
            tags=tags,
        )

    def _should_skip_paragraph(self, paragraph: ParagraphDict, pos: int) -> bool:
        """Determine if a paragraph should be skipped (title/subtitle/preview image)."""
        if pos >= 4:
            return False

        para_type = paragraph.get("type", "")
        para_text = paragraph.get("text", "")
        meta = self._metadata

        if not meta:
            return False

        # Skip title paragraphs
        if para_type in (ParagraphType.H2, ParagraphType.H3, ParagraphType.H4):
            if match_percentage(para_text, meta.title) > 80:
                if meta.title.endswith("…"):
                    # Update title with full text
                    object.__setattr__(meta, "title", para_text)
                logger.trace("Title paragraph detected, skipping")
                return True

            # Skip tag-as-header
            if para_type == ParagraphType.H4 and para_text in meta.tags:
                logger.trace("Tag paragraph detected, skipping")
                return True

        # Skip subtitle paragraphs
        if para_type in (ParagraphType.H4, ParagraphType.P):
            if match_percentage(para_text, meta.subtitle) > 80:
                if not meta.subtitle.endswith("…"):
                    logger.trace("Subtitle paragraph detected, skipping")
                    return True
            elif meta.subtitle and meta.subtitle.endswith("…") and len(para_text) > 100:
                # Clear truncated subtitle
                object.__setattr__(meta, "subtitle", "")

        # Skip preview image
        if para_type == ParagraphType.IMG:
            img_meta = paragraph.get("metadata", {})
            if img_meta and img_meta.get("id") == meta.preview_image_id:
                logger.trace("Preview image detected, skipping")
                return True

        return False

    def _render_text(
        self, text: str | None, markups: list[MarkupDict], *, is_code: bool = False
    ) -> str:
        """Render text with inline markups applied."""
        if not text:
            text = ""
        # Process markups first (uses original text positions)
        processor = MarkupProcessor(text, markups, is_code=is_code)
        result = processor.render()
        # Normalize smart quotes after markup processing to avoid position misalignment
        return _normalize_quotes(result)

    def _render_header(self, paragraph: ParagraphDict, level: int) -> None:
        """Render H2/H3/H4 headers."""
        text = self._render_text(paragraph.get("text"), paragraph.get("markups", []))
        prefix = "#" * level
        self._output.append(f"{prefix} {text}")
        self._output.append("")

    def _render_paragraph(self, paragraph: ParagraphDict) -> None:
        """Render a regular paragraph."""
        text = self._render_text(paragraph.get("text"), paragraph.get("markups", []))
        self._output.append(text)
        self._output.append("")

    async def _render_image(self, paragraph: ParagraphDict) -> None:
        """Render an image paragraph as a responsive picture element.

        Generates HTML picture element with:
        - Mobile: 700px version
        - Desktop: original resolution version
        - Lazy loading and layout shift prevention
        """
        metadata = paragraph.get("metadata", {})
        image_id = metadata.get("id", "")
        alt_text = metadata.get("alt", "")

        if not image_id:
            return

        # Normalize quotes in alt text
        alt_text = _normalize_quotes(alt_text)

        # Generate responsive picture element
        if self._use_base64_images:
            # Base64 mode: embed only 700px as data URI, link original as URL, link zoom as URL
            medium_url = f"https://miro.medium.com/v2/resize:fit:700/{image_id}"
            medium_src = await self._get_image_as_base64(medium_url)
            if medium_src is None:
                # Fallback to URL if base64 encoding fails
                medium_src = medium_url

            original_url = f"https://miro.medium.com/v2/resize:fit:2000/{image_id}"
            zoom_url = f"https://miro.medium.com/v2/resize:fit:4000/{image_id}"
            picture_html = self._render_responsive_picture_base64(
                metadata, alt_text, medium_src, original_url, zoom_url
            )
        else:
            # Normal mode: both URLs linked (no base64)
            picture_html = self._render_responsive_picture(metadata, alt_text)

        self._output.append(picture_html)

        # Add caption if present
        caption = paragraph.get("text")
        if caption:
            caption_text = self._render_text(caption, paragraph.get("markups", []))
            self._output.append(f"*{caption_text}*")

        self._output.append("")

    async def _render_image_row(self, start_pos: int) -> int:
        """Render a row of images (OUTSET_ROW layout) with responsive pictures.

        Renders each image as a responsive picture element with mobile and desktop versions.

        Returns new position to continue processing from.
        """
        images: list[str] = []
        pos = start_pos

        while pos < len(self._paragraphs):
            para = self._paragraphs[pos]
            if para.get("type") != ParagraphType.IMG:
                break

            layout = para.get("layout", "")
            if pos > start_pos and layout != "OUTSET_ROW_CONTINUE":
                break

            metadata = para.get("metadata", {})
            image_id = metadata.get("id", "")
            alt_text = metadata.get("alt", "")

            if image_id:
                alt_text = _normalize_quotes(alt_text)

                # Generate responsive picture element for each image
                if self._use_base64_images:
                    # Base64 mode: embed only 700px as data URI, link original and zoom as URLs
                    medium_url = f"https://miro.medium.com/v2/resize:fit:700/{image_id}"
                    medium_src = await self._get_image_as_base64(medium_url)
                    if medium_src is None:
                        # Fallback to URL if base64 encoding fails
                        medium_src = medium_url

                    original_url = f"https://miro.medium.com/v2/resize:fit:2000/{image_id}"
                    zoom_url = f"https://miro.medium.com/v2/resize:fit:4000/{image_id}"
                    picture_html = self._render_responsive_picture_base64(
                        metadata, alt_text, medium_src, original_url, zoom_url
                    )
                else:
                    # Normal mode: both URLs linked (no base64)
                    picture_html = self._render_responsive_picture(metadata, alt_text)

                images.append(picture_html)

            pos += 1

        # Output all images
        for img in images:
            self._output.append(img)

        self._output.append("")
        return pos - 1

    def _collect_list_items(self, start_pos: int, list_type: str) -> tuple[list[str], int]:
        """Collect consecutive list items. Returns (items, new_position)."""
        items: list[str] = []
        pos = start_pos

        while pos < len(self._paragraphs):
            para = self._paragraphs[pos]
            if para.get("type") != list_type:
                break

            text = self._render_text(para.get("text"), para.get("markups", []))
            items.append(text)
            pos += 1

        return items, pos - 1

    def _render_unordered_list(self, start_pos: int) -> int:
        """Render unordered list. Returns new position."""
        items, end_pos = self._collect_list_items(start_pos, ParagraphType.ULI)

        for item in items:
            self._output.append(f"- {item}")

        self._output.append("")
        return end_pos

    def _render_ordered_list(self, start_pos: int) -> int:
        """Render ordered list. Returns new position."""
        items, end_pos = self._collect_list_items(start_pos, ParagraphType.OLI)

        for i, item in enumerate(items, 1):
            self._output.append(f"{i}. {item}")

        self._output.append("")
        return end_pos

    def _render_code_block(self, start_pos: int) -> int:
        """Render code block (PRE). Returns new position."""
        code_lines: list[str] = []
        language = ""
        pos = start_pos
        decorations: list[dict[str, Any]] = []

        while pos < len(self._paragraphs):
            para = self._paragraphs[pos]
            if para.get("type") != ParagraphType.PRE:
                break

            # Get language from first block
            if not language:
                code_meta = para.get("codeBlockMetadata", {})
                if code_meta:
                    language = code_meta.get("lang", "") or ""

            # Collect text and track STRONG/EM markups for decorations
            text_original = para.get("text") or ""
            markups = para.get("markups", [])

            # The frontend (remark-parse) will add a trailing newline to code blocks,
            # then the frontend strips it with .replace(/\n$/, '')
            # So we need to ADD a newline here, then our positions will be calculated correctly
            # Actually, the text already has proper length. The issue is that remark-parse
            # processes the markdown code block differently.

            # Let's not strip anything and let the full text go through
            text_for_markdown = text_original

            # Convert UTF-16 positions to Python positions
            utf_handler = _UTF16StringHandler(text_original) if text_original else None

            # Calculate line offset for decorations (in Python string positions)
            line_offset = sum(len(line) + 1 for line in code_lines) if code_lines else 0

            for markup in markups:
                mtype = markup.get("type")
                if mtype == MarkupType.STRONG or mtype == MarkupType.EM:
                    # Convert Medium's UTF-16 positions to Python positions
                    start_utf16 = markup.get("start", 0)
                    end_utf16 = markup.get("end", 0)

                    if utf_handler:
                        start_py = utf_handler.get_python_position(start_utf16)
                        end_py = utf_handler.get_python_position(end_utf16)
                    else:
                        start_py = start_utf16
                        end_py = end_utf16

                    final_start = line_offset + start_py
                    final_end = line_offset + end_py

                    # Only add valid decorations
                    if start_py < end_py and end_py <= len(text_original):
                        decorations.append({
                            "start": final_start,
                            "end": final_end,
                            "type": "strong" if mtype == MarkupType.STRONG else "em"
                        })

            # Store text for markdown output - don't strip anything
            code_lines.append(text_for_markdown)
            pos += 1

        # Output code block with decoration metadata if present
        # Use "text" as default language if none specified
        lang_output = language if language else "text"

        # The frontend will normalize the markdown code block text.
        # Specifically, remark-parse strips trailing spaces before newlines in code blocks.
        # Since our code_lines contain the original text with embedded '\n' characters,
        # we need to simulate the frontend's normalization to adjust decoration positions.

        # Join code_lines with '\n' to recreate the full text as it will appear in markdown
        full_text_for_markdown = '\n'.join(code_lines)

        # Simulate frontend normalization: strip trailing spaces before '\n' within the text
        # Split by '\n', rstrip spaces from each line, then rejoin
        normalized_text = '\n'.join(line.rstrip(' ') for line in full_text_for_markdown.split('\n'))

        # Calculate the length difference
        original_length = len(full_text_for_markdown)
        final_length = len(normalized_text)
        chars_removed = original_length - final_length


        # Adjust decoration positions to match the normalized text
        if chars_removed > 0 and decorations:
            adjusted_decorations = []

            # Build a position mapping from original to normalized text
            # Track character-by-character mapping
            pos_map = {}
            norm_pos = 0

            # Split and process line by line
            orig_lines = full_text_for_markdown.split('\n')
            for line_idx, orig_line in enumerate(orig_lines):
                norm_line = orig_line.rstrip(' ')
                line_offset_in_orig = sum(len(orig_lines[i]) + 1 for i in range(line_idx))  # +1 for '\n'
                if line_idx == 0:
                    line_offset_in_orig = 0

                # Map each character in the normalized line
                for i in range(len(norm_line)):
                    orig_pos = line_offset_in_orig + i
                    pos_map[orig_pos] = norm_pos
                    norm_pos += 1

                # Add newline mapping (except for last line)
                if line_idx < len(orig_lines) - 1:
                    nl_pos_in_orig = line_offset_in_orig + len(orig_line)
                    pos_map[nl_pos_in_orig] = norm_pos
                    norm_pos += 1

            # Adjust each decoration using the position map
            for dec in decorations:
                old_start: int = dec['start']  # type: ignore[assignment]
                old_end: int = dec['end']  # type: ignore[assignment]

                # Find the closest mapped positions
                new_start: int = pos_map.get(old_start, old_start)  # type: ignore[assignment]
                # For end, we need to map the position of the last character, then add 1
                new_end: int = pos_map.get(old_end - 1, old_end - 1) + 1 if old_end > 0 else 0  # type: ignore[assignment]

                # Clamp to valid range
                new_start = min(new_start, final_length)  # type: ignore[arg-type]
                new_end = min(new_end, final_length)  # type: ignore[arg-type]

                # Only include if still valid
                if new_start < new_end:
                    adjusted_decorations.append({  # type: ignore[misc]
                        "start": new_start,
                        "end": new_end,
                        "type": dec['type']
                    })


            decorations = adjusted_decorations

        if decorations:
            import json
            decorations_json = json.dumps(decorations)
            # Escape double quotes for markdown attribute (but don't normalize smart quotes in JSON)
            escaped_json = decorations_json.replace('"', '\\"')
            self._output.append(f'```{lang_output} decorations="{escaped_json}"')
        else:
            self._output.append(f"```{lang_output}")

        self._output.extend(code_lines)
        self._output.append("```")
        self._output.append("")

        return pos - 1

    def _render_blockquote(self, paragraph: ParagraphDict) -> None:
        """Render a blockquote (BQ)."""
        text = self._render_text(paragraph.get("text"), paragraph.get("markups", []))
        self._output.append(f"> {text}")
        self._output.append("")

    def _render_pullquote(self, paragraph: ParagraphDict) -> None:
        """Render a pull quote (PQ)."""
        text = self._render_text(paragraph.get("text"), paragraph.get("markups", []))
        # Pull quotes rendered as blockquotes with emphasis
        self._output.append(f"> *{text}*")
        self._output.append("")

    def _render_mixtape_embed(self, paragraph: ParagraphDict) -> None:
        """Render a mixtape embed (embedded link card)."""
        mixtape: dict[str, Any] = paragraph.get("mixtapeMetadata", {})
        if not mixtape:
            logger.warning("MIXTAPE_EMBED missing metadata, skipping")
            return

        href: str = mixtape.get("href", "")
        if not href:
            logger.warning("MIXTAPE_EMBED missing href, skipping")
            return

        text: str = paragraph.get("text", "")
        markups: list[MarkupDict] = paragraph.get("markups", [])

        # Extract title and description from markups
        if len(markups) >= 3:
            title_range = markups[1]
            desc_range = markups[2]
            start_t: int = title_range.get("start", 0)
            end_t: int = title_range.get("end", 0)
            start_d: int = desc_range.get("start", 0)
            end_d: int = desc_range.get("end", 0)
            title = _normalize_quotes(text[start_t:end_t])
            description = _normalize_quotes(text[start_d:end_d])
        else:
            title = _normalize_quotes(text)
            description = ""

        # Render as a link with description
        self._output.append(f"[**{title}**]({href})")
        if description:
            self._output.append(f"*{description}*")
        self._output.append("")

    async def _render_iframe(self, paragraph: ParagraphDict) -> None:
        """Render an iframe embed by fetching and embedding the actual HTML content."""
        logger.debug("Processing IFRAME paragraph")
        logger.debug(f"Full paragraph data: {paragraph}")

        iframe_data = paragraph.get("iframe", {})
        logger.debug(f"Iframe data: {iframe_data}")

        # First check if we have direct mediaResource in the iframe
        media_resource = iframe_data.get("mediaResource", {})
        logger.debug(f"Media resource: {media_resource}")

        # Get iframe source from mediaResource
        iframe_src_val = media_resource.get("iframeSrc")
        iframe_id = media_resource.get("id")

        # Get iframe dimensions
        iframe_width = media_resource.get("iframeWidth")
        iframe_height = media_resource.get("iframeHeight")

        # If dimensions are available in paragraph.iframe directly, use those as fallback
        if not iframe_width and iframe_data.get("iframeWidth"):
            iframe_width = iframe_data["iframeWidth"]
        if not iframe_height and iframe_data.get("iframeHeight"):
            iframe_height = iframe_data["iframeHeight"]

        logger.debug(f"Iframe dimensions: {iframe_width}x{iframe_height}")

        # If we have an API service and an iframe_id, fetch the actual HTML content
        if self._api_service and iframe_id:
            logger.debug(f"Fetching iframe content for ID: {iframe_id}")
            try:
                iframe_html = await self._api_service.fetch_iframe_content(iframe_id)
                if iframe_html:
                    # Apply the same patching logic
                    patched_html = iframe_html.replace(
                        "document.domain = document.domain",
                        'console.log("[FREEDIUM] iframe workaround started")'
                    )

                    # Escape double quotes for srcdoc attribute
                    # Note: We need to escape & first, then ", otherwise we'd double-escape
                    escaped_html = patched_html.replace('&', '&amp;').replace('"', '&quot;')

                    # Build iframe tag with srcdoc
                    iframe_attrs = ['class="w-full border"']
                    if iframe_width:
                        iframe_attrs.append(f'width="{iframe_width}"')
                    if iframe_height:
                        iframe_attrs.append(f'height="{iframe_height}"')
                    iframe_attrs.append('frameborder="0"')
                    iframe_attrs.append('allowfullscreen')
                    iframe_attrs.append(f'srcdoc="{escaped_html}"')

                    attrs_str = " ".join(iframe_attrs)
                    self._output.append(f'<iframe {attrs_str}></iframe>')
                    self._output.append("")
                    logger.debug(f"Successfully embedded iframe content for ID: {iframe_id}")
                    return
                else:
                    logger.warning(f"No content received for iframe {iframe_id}")
            except Exception as e:
                logger.error(f"Failed to fetch iframe content for ID {iframe_id}: {e}")

        # Fallback: render as link (original behavior)
        if iframe_src_val:
            if iframe_width and iframe_height:
                self._output.append(f"<!-- iframe: {iframe_width}x{iframe_height} -->")
            self._output.append(f"[Embedded content]({iframe_src_val})")
        elif iframe_id:
            if iframe_width and iframe_height:
                self._output.append(f"<!-- iframe: {iframe_width}x{iframe_height} -->")
            self._output.append(f"[Embedded content: {iframe_id}]")
        else:
            logger.warning("No iframe source or ID found, skipping iframe")
            return

        self._output.append("")

    async def _process_paragraph(self, pos: int) -> int:
        """Process a single paragraph. Returns the next position to process."""
        paragraph = self._paragraphs[pos]
        para_type = paragraph.get("type", "")

        # Skip title/subtitle/preview image in first few paragraphs
        if self._should_skip_paragraph(paragraph, pos):
            return pos + 1

        if para_type == ParagraphType.H2:
            self._render_header(paragraph, 2)
        elif para_type == ParagraphType.H3:
            self._render_header(paragraph, 3)
        elif para_type == ParagraphType.H4:
            self._render_header(paragraph, 4)
        elif para_type == ParagraphType.P:
            self._render_paragraph(paragraph)
        elif para_type == ParagraphType.IMG:
            layout = paragraph.get("layout", "")
            if layout == "OUTSET_ROW":
                return await self._render_image_row(pos) + 1
            elif layout == "FULL_WIDTH":
                logger.warning("IMG FULL_WIDTH layout not fully supported")
                await self._render_image(paragraph)
            else:
                await self._render_image(paragraph)
        elif para_type == ParagraphType.ULI:
            return self._render_unordered_list(pos) + 1
        elif para_type == ParagraphType.OLI:
            return self._render_ordered_list(pos) + 1
        elif para_type == ParagraphType.PRE:
            return self._render_code_block(pos) + 1
        elif para_type == ParagraphType.BQ:
            self._render_blockquote(paragraph)
        elif para_type == ParagraphType.PQ:
            self._render_pullquote(paragraph)
        elif para_type == ParagraphType.MIXTAPE_EMBED:
            self._render_mixtape_embed(paragraph)
        elif para_type == ParagraphType.IFRAME:
            await self._render_iframe(paragraph)
        else:
            logger.warning(f"Unknown paragraph type: {para_type}")

        return pos + 1

    async def render(self) -> str:
        """Render the full post to Markdown."""
        if not self._paragraphs:
            return ""

        # Extract metadata first
        self._metadata = self._extract_metadata()

        # Process all paragraphs
        self._pos = 0
        while self._pos < len(self._paragraphs):
            self._pos = await self._process_paragraph(self._pos)

        # Join output and clean up extra blank lines
        result = "\n".join(self._output)

        # Remove trailing whitespace and normalize multiple blank lines
        lines = result.split("\n")
        cleaned: list[str] = []
        prev_blank = False

        for line in lines:
            line = line.rstrip()
            is_blank = not line

            if is_blank and prev_blank:
                continue

            cleaned.append(line)
            prev_blank = is_blank

        return "\n".join(cleaned).strip()

    def _extract_table_of_contents(self) -> list[dict[str, str]]:
        """Extract table of contents from H2 and H3 headings with plain text (no markdown links)."""
        toc: list[dict[str, str]] = []

        for i, paragraph in enumerate(self._paragraphs):
            # Skip paragraphs we would normally skip
            if self._should_skip_paragraph(paragraph, i):
                continue

            para_type = paragraph.get("type", "")
            if para_type not in (ParagraphType.H2, ParagraphType.H3):
                continue

            # Get plain text without rendering markups
            text = paragraph.get("text", "").strip()
            if not text:
                continue

            # Normalize quotes in heading text
            text = _normalize_quotes(text)

            # Create slug from plain text
            slug = (
                text.lower()
                .replace(" ", "-")
                .replace("_", "-")
            )
            # Remove non-alphanumeric characters except hyphens
            slug = "".join(c for c in slug if c.isalnum() or c == "-")
            # Remove consecutive hyphens
            while "--" in slug:
                slug = slug.replace("--", "-")
            slug = slug.strip("-")

            if slug:
                toc.append({"id": slug, "title": text})

        return toc

    async def render_with_frontmatter(self) -> str:
        """Render the post with YAML frontmatter metadata."""
        if self._metadata is None:
            self._metadata = self._extract_metadata()

        meta = self._metadata
        content = await self.render()

        # Build metadata dictionary for YAML serialization
        metadata: dict[str, Any] = {
            "title": meta.title,
            "author": meta.creator_name,
        }

        if meta.subtitle:
            metadata["subtitle"] = meta.subtitle

        if meta.collection_name:
            metadata["publication"] = meta.collection_name

        # Handle preview image: generate responsive sizes like regular images
        if meta.preview_image_id:
            # Generate multiple image sizes using same logic as article images
            urls = self._generate_image_urls(meta.preview_image_id, None, None)
            medium_url = urls["medium"]  # type: ignore[index]
            original_url = urls["original"]  # type: ignore[index]
            zoom_url = urls["zoom"]  # type: ignore[index]

            if self._use_base64_images:
                # Base64 mode: embed medium size, link original and zoom
                medium_src = await self._get_image_as_base64(medium_url)  # type: ignore[index]
                if medium_src is None:
                    medium_src = medium_url  # type: ignore[index]

                # Store as JSON for responsive image data
                metadata["preview_image"] = {
                    "medium": medium_src,
                    "original": original_url,  # type: ignore[index]
                    "zoom": zoom_url,  # type: ignore[index]
                }
            else:
                # Normal mode: both sizes linked
                metadata["preview_image"] = {
                    "medium": medium_url,  # type: ignore[index]
                    "original": original_url,  # type: ignore[index]
                    "zoom": zoom_url,  # type: ignore[index]
                }

        metadata["reading_time"] = meta.reading_time
        metadata["url"] = meta.medium_url

        if meta.tags:
            metadata["tags"] = meta.tags

        # Add table of contents
        toc = self._extract_table_of_contents()
        if toc:
            metadata["table_of_contents"] = toc

        # Serialize to YAML with proper formatting
        frontmatter_yaml = yaml.dump(
            metadata,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

        frontmatter = f"---\n{frontmatter_yaml}---\n"

        return frontmatter + content

    @property
    def metadata(self) -> PostMetadata:
        """Get post metadata (lazy-loaded)."""
        if self._metadata is None:
            self._metadata = self._extract_metadata()
        return self._metadata
