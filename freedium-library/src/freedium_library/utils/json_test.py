from typing import Any, Dict
from unittest.mock import patch

import pytest

from freedium_library.utils.json import (
    JSON,
    JSONBackend,
    OrjsonBackend,
    StandardJSONBackend,
    UjsonBackend,
)

# Test data
SIMPLE_DICT: Dict[str, Any] = {"key": "value", "number": 42}
COMPLEX_DICT: Dict[str, Any] = {
    "string": "hello",
    "number": 42,
    "float": 3.14,
    "bool": True,
    "null": None,
    "array": [1, 2, 3],
    "nested": {"a": 1, "b": 2},
}
UNICODE_DICT: Dict[str, str] = {"unicode": "Hello 世界"}


@pytest.fixture
def json_backends() -> list[JSONBackend]:
    return [OrjsonBackend(), UjsonBackend(), StandardJSONBackend()]


def test_backend_interface() -> None:
    """Test that all backends implement the required interface"""
    for backend in [OrjsonBackend(), UjsonBackend(), StandardJSONBackend()]:
        assert isinstance(backend, JSONBackend)
        assert callable(backend.dumps)
        assert callable(backend.loads)
        assert isinstance(backend.name, str)
        assert str(backend).startswith("JSON Backend:")
        assert repr(backend).endswith(f"backend='{backend.name}')")


@pytest.mark.parametrize(
    "backend", [OrjsonBackend(), UjsonBackend(), StandardJSONBackend()]
)
class TestBackendBehavior:
    def test_simple_roundtrip(self, backend: JSONBackend) -> None:
        """Test serialization and deserialization of simple data"""
        serialized: str = backend.dumps(SIMPLE_DICT)
        deserialized: Dict[str, Any] = backend.loads(serialized)
        assert deserialized == SIMPLE_DICT

    def test_complex_roundtrip(self, backend: JSONBackend) -> None:
        """Test serialization and deserialization of complex data"""
        serialized: str = backend.dumps(COMPLEX_DICT)
        deserialized: Dict[str, Any] = backend.loads(serialized)
        assert deserialized == COMPLEX_DICT

    def test_unicode_handling(self, backend: JSONBackend) -> None:
        """Test proper Unicode handling"""
        serialized: str = backend.dumps(UNICODE_DICT)
        deserialized: Dict[str, str] = backend.loads(serialized)
        assert deserialized == UNICODE_DICT

    def test_pretty_printing(self, backend: JSONBackend) -> None:
        """Test pretty printing functionality"""
        ugly: str = backend.dumps(COMPLEX_DICT, pretty=False)
        pretty: str = backend.dumps(COMPLEX_DICT, pretty=True)
        assert len(pretty) > len(ugly)
        assert backend.loads(pretty) == backend.loads(ugly)


class TestJSONClass:
    def test_backend_selection(self) -> None:
        """Test automatic backend selection"""
        json = JSON()
        assert json.backend() in ["orjson", "ujson", "json"]

    def test_backend_fallback(self) -> None:
        """Test fallback behavior when preferred backends are unavailable"""
        JSON._instance = None
        JSON._backend = None
        with patch.dict("sys.modules", {"orjson": None, "ujson": None}):
            json = JSON()
            assert json.backend() == "json"

    def test_explicit_backend(self) -> None:
        """Test using an explicitly provided backend"""
        backend = StandardJSONBackend()
        json = JSON(backend=backend)
        assert json.backend() == "json"

    def test_singleton_behavior(self) -> None:
        """Test that JSON class maintains singleton behavior"""
        json1 = JSON()
        json2 = JSON()
        assert json1._backend is json2._backend

    def test_class_methods(self) -> None:
        """Test class-level convenience methods"""
        data: Dict[str, Any] = COMPLEX_DICT
        serialized: str = JSON.dumps(data)
        deserialized: Dict[str, Any] = JSON.loads(serialized)
        assert deserialized == data


@pytest.mark.parametrize(
    "backend", [OrjsonBackend(), UjsonBackend(), StandardJSONBackend()]
)
def test_error_handling(backend: JSONBackend) -> None:
    """Test error handling for invalid JSON"""
    with pytest.raises(Exception):
        backend.loads("invalid json")

    with pytest.raises(Exception):
        backend.dumps(object())
