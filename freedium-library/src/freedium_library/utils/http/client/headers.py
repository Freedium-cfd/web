import abc
from collections.abc import Iterator, Mapping
from typing import Any, Dict, List, Tuple, Union, cast


class AbstractHeaders(abc.ABC, Mapping[str, str]):
    """Abstract base class for HTTP headers."""

    @abc.abstractmethod
    def __getitem__(self, key: str) -> str:
        """Get a header value by name (case-insensitive)."""
        pass

    @abc.abstractmethod
    def __iter__(self) -> Iterator[str]:
        """Iterate over header names."""
        pass

    @abc.abstractmethod
    def __len__(self) -> int:
        """Get the number of unique headers."""
        pass


class Headers(AbstractHeaders):
    """
    A case-insensitive dictionary-like object for HTTP headers.

    It stores header keys in a case-insensitive manner.
    If multiple headers with the same name are provided, the last one is kept.
    """

    def __init__(
        self,
        headers: Union[
            Mapping[str, str], "Headers", List[Tuple[str, str]], None
        ] = None,
    ):
        self._headers: Dict[str, Tuple[str, str]] = {}
        if headers:
            if isinstance(headers, Mapping):
                for key, value in headers.items():
                    self._headers[key.lower()] = (key, str(value))
            else:
                for key, value in headers:
                    self._headers[key.lower()] = (key, str(value))

    def __getitem__(self, key: str) -> str:
        return self._headers[key.lower()][1]

    def __iter__(self) -> Iterator[str]:
        return (original_key for original_key, _ in self._headers.values())

    def __len__(self) -> int:
        return len(self._headers)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Mapping):
            return NotImplemented

        self_lower: Dict[str, str] = {}
        for k, v in cast(Iterator[Tuple[str, str]], self.items()):
            self_lower[k.lower()] = v
        other_lower: Dict[str, str] = {}
        for k, v in cast(Iterator[Tuple[str, str]], other.items()):
            other_lower[k.lower()] = v
        return self_lower == other_lower

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({dict(self.items())!r})"
