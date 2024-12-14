from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from loguru import logger


class JSONBackend(ABC):
    @abstractmethod
    def dumps(self, obj: Any, pretty: bool = False) -> str:
        pass

    @abstractmethod
    def loads(self, string: str) -> Any:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(backend='{self.name}')"

    def __str__(self) -> str:
        return f"JSON Backend: {self.name}"


class OrjsonBackend(JSONBackend):
    def __init__(self):
        import orjson

        self._orjson = orjson

    def dumps(self, obj: Any, pretty: bool = False) -> str:
        opts = self._orjson.OPT_INDENT_2 if pretty else None
        return self._orjson.dumps(obj, option=opts).decode("utf-8")

    def loads(self, string: str) -> Any:
        return self._orjson.loads(string)

    @property
    def name(self) -> str:
        return "orjson"


class UjsonBackend(JSONBackend):
    def __init__(self):
        import ujson

        self._ujson = ujson

    def dumps(self, obj: Any, pretty: bool = False) -> str:
        return self._ujson.dumps(obj, indent=2 if pretty else 0)

    def loads(self, string: str) -> Any:
        return self._ujson.loads(string)

    @property
    def name(self) -> str:
        return "ujson"


class StandardJSONBackend(JSONBackend):
    def __init__(self):
        import json

        self._json = json

    def dumps(self, obj: Any, pretty: bool = False) -> str:
        return self._json.dumps(obj, indent=2 if pretty else None)

    def loads(self, string: str) -> Any:
        return self._json.loads(string)

    @property
    def name(self) -> str:
        return "json"


class JSON:
    _instance: Optional[Type["JSON"]] = None
    _backend: Optional[JSONBackend] = None

    def __init__(self, backend: Optional[JSONBackend] = None) -> None:
        if backend:
            JSON._backend = backend
        elif not JSON._backend:
            JSON._backend = JSON._get_best_backend()

    @classmethod
    def _ensure_backend(cls) -> None:
        if cls._backend is None:
            cls._backend = cls._get_best_backend()

    @classmethod
    def dumps(cls, obj: Any, pretty: bool = False) -> str:
        cls._ensure_backend()
        return cls._backend.dumps(obj, pretty)  # type: ignore

    @classmethod
    def loads(cls, string: str) -> Any:
        cls._ensure_backend()
        return cls._backend.loads(string)  # type: ignore

    @classmethod
    def backend(cls) -> str:
        cls._ensure_backend()
        return cls._backend.name  # type: ignore

    @classmethod
    def _get_best_backend(cls) -> JSONBackend:
        backends = [
            (OrjsonBackend, "orjson"),
            (UjsonBackend, "ujson"),
            (StandardJSONBackend, "json"),
        ]

        for backend_class, module_name in backends:
            try:
                __import__(module_name)
                logger.debug(f"Using {module_name} as JSON backend")
                return backend_class()
            except ImportError:
                continue

        logger.warning("No JSON backend found, using standard JSON backend")
        return StandardJSONBackend()


json_instance = JSON()
json = json_instance
