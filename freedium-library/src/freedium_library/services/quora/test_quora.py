"""Unit tests for QuoraService (URL matching, AST markdown conversion, frontmatter)."""
from __future__ import annotations

import json
import pytest

from freedium_library.services.quora.quora import (
    QuoraService,
    _is_quora_url,
    _normalize_url,
)


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.quora.com/profile/Nidai-Kitetsu/ONE-PIECE-THEORY-AGE-OF-SEA-CIRCLE", True),
        ("https://quora.com/Why-is-the-sky-blue", True),
        ("https:/www.quora.com/profile/User/Post-Slug", True),
        ("https://space.quora.com/Some-Post", True),
        ("http://quora.com/test", True),
        # Non-quora URLs
        ("https://medium.com/@user/slug", False),
        ("https://www.nytimes.com/2026/01/01/us/politics/test.html", False),
        ("https://store.hbr.org/product/123", False),
        ("", False),
        ("not-a-url", False),
    ],
)
def test_is_quora_url(url: str, expected: bool) -> None:
    assert _is_quora_url(url) is expected


def test_normalize_url():
    assert _normalize_url("https:/quora.com/test") == "https://quora.com/test"
    assert _normalize_url("http:/quora.com/test") == "http://quora.com/test"
    assert _normalize_url("quora.com/test") == "https://quora.com/test"


class TestQuoraMarkdownConversion:
    def test_renders_plain_paragraph_with_modifiers(self):
        doc = {
            "sections": [
                {
                    "type": "plain",
                    "spans": [
                        {"text": "Normal ", "modifiers": {}},
                        {"text": "bold text", "modifiers": {"bold": True}},
                        {"text": " and ", "modifiers": {}},
                        {"text": "italic text", "modifiers": {"italic": True}},
                        {"text": " and ", "modifiers": {}},
                        {"text": "code snippet", "modifiers": {"code": True}},
                        {"text": " and ", "modifiers": {}},
                        {"text": "link text", "modifiers": {"link": {"type": "url", "url": "https://example.com"}}},
                    ],
                }
            ]
        }
        md = QuoraService._doc_to_markdown(doc)
        expected = "Normal **bold text** and _italic text_ and `code snippet` and [link text](https://example.com)"
        assert md == expected

    def test_renders_headings_and_quotes(self):
        doc = {
            "sections": [
                {
                    "type": "header",
                    "spans": [{"text": "Main Heading", "modifiers": {}}],
                },
                {
                    "type": "plain",
                    "quoted": True,
                    "spans": [{"text": "A famous quote.", "modifiers": {}}],
                },
            ]
        }
        md = QuoraService._doc_to_markdown(doc)
        assert "### Main Heading" in md
        assert "> A famous quote." in md

    def test_renders_inline_images(self):
        doc = {
            "sections": [
                {
                    "type": "plain",
                    "spans": [{"text": "Intro text", "modifiers": {}}],
                },
                {
                    "type": "image",
                    "spans": [
                        {
                            "text": "",
                            "modifiers": {
                                "image": "https://qph.cf2.quoracdn.net/main-qimg-12345.png"
                            },
                        }
                    ],
                },
            ]
        }
        md = QuoraService._doc_to_markdown(doc)
        assert "Intro text" in md
        assert '<figure><img src="https://qph.cf2.quoracdn.net/main-qimg-12345.png"' in md


class TestQuoraFrontmatter:
    def test_frontmatter_extraction(self):
        data = {
            "title": json.dumps({
                "sections": [{"spans": [{"text": "ONE PIECE THEORY: AGE OF SEA CIRCLE\n"}]}]
            }),
            "author": {
                "names": [{"givenName": "Nidai", "familyName": "Kitetsu"}],
                "profileImageUrl": "https://qph.cf2.quoracdn.net/main-thumb-123.jpg",
            },
            "creationTime": 1700000000,
            "contentQtextDocument": {
                "legacyJson": json.dumps({
                    "sections": [
                        {
                            "type": "image",
                            "spans": [
                                {
                                    "modifiers": {
                                        "image": "https://qph.cf2.quoracdn.net/main-qimg-cover.jpg"
                                    }
                                }
                            ],
                        }
                    ]
                })
            },
        }

        fm = QuoraService._frontmatter(data, "https://www.quora.com/profile/Nidai-Kitetsu/test")
        assert "title: 'ONE PIECE THEORY: AGE OF SEA CIRCLE'" in fm or "title: ONE PIECE THEORY: AGE OF SEA CIRCLE" in fm
        assert "name: Nidai Kitetsu" in fm
        assert "avatar: https://qph.cf2.quoracdn.net/main-thumb-123.jpg" in fm
        assert "publication: Quora" in fm
        assert "preview_image:" in fm
        assert "/img/quora/main-qimg-cover.jpg" in fm
