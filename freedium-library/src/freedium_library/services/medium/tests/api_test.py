"""Tests for Medium API service."""

from typing import Any

from freedium_library.services.medium.api import resolve_graphql_references


class TestResolveGraphQLReferences:
    """Tests for GraphQL __ref reference resolution."""

    def test_resolve_simple_reference(self) -> None:
        """Test that a simple __ref is resolved."""
        data = {"field": {"__ref": "Entity:123"}}
        root = {"Entity:123": {"id": "123", "name": "Test"}}

        result = resolve_graphql_references(data, root)

        assert result["field"]["id"] == "123"
        assert result["field"]["name"] == "Test"
        assert "__ref" not in result["field"]

    def test_resolve_nested_reference(self) -> None:
        """Test that nested __ref references are resolved."""
        data = {
            "post": {
                "content": {
                    "bodyModel": {
                        "paragraphs": [
                            {
                                "type": "IFRAME",
                                "iframe": {"mediaResource": {"__ref": "MediaResource:abc123"}},
                            }
                        ]
                    }
                }
            }
        }
        root = {
            "MediaResource:abc123": {
                "id": "abc123",
                "iframeSrc": "https://example.com/embed/video",
                "iframeWidth": 800,
                "iframeHeight": 600,
            }
        }

        result = resolve_graphql_references(data, root)

        media_resource = result["post"]["content"]["bodyModel"]["paragraphs"][0]["iframe"][
            "mediaResource"
        ]
        assert "__ref" not in media_resource
        assert media_resource["id"] == "abc123"
        assert media_resource["iframeSrc"] == "https://example.com/embed/video"
        assert media_resource["iframeWidth"] == 800
        assert media_resource["iframeHeight"] == 600

    def test_resolve_missing_reference(self) -> None:
        """Test that missing references are handled gracefully."""
        data = {"field": {"__ref": "Entity:missing"}}
        root: dict[str, Any] = {}

        result = resolve_graphql_references(data, root)

        # Should return the reference object unchanged
        assert result["field"]["__ref"] == "Entity:missing"

    def test_resolve_list_with_references(self) -> None:
        """Test that references in lists are resolved."""
        data = {"items": [{"__ref": "Item:1"}, {"__ref": "Item:2"}]}
        root = {"Item:1": {"id": "1", "name": "First"}, "Item:2": {"id": "2", "name": "Second"}}

        result = resolve_graphql_references(data, root)

        assert result["items"][0]["name"] == "First"
        assert result["items"][1]["name"] == "Second"

    def test_resolve_no_references(self) -> None:
        """Test that data without references is returned unchanged."""
        data = {"id": "123", "name": "Test", "nested": {"value": 42}}

        result = resolve_graphql_references(data, {})

        assert result == data

    def test_resolve_chained_references(self) -> None:
        """Test that chained references (reference pointing to reference) are resolved."""
        data = {"field": {"__ref": "Entity:A"}}
        root = {
            "Entity:A": {"next": {"__ref": "Entity:B"}},
            "Entity:B": {"id": "B", "name": "Final"},
        }

        result = resolve_graphql_references(data, root)

        assert result["field"]["next"]["name"] == "Final"
        assert "__ref" not in result["field"]["next"]
