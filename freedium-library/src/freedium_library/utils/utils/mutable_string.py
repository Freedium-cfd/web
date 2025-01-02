from typing import List, Union


class MutableString:
    __slots__ = ("_string", "_string_list", "_is_dirty")

    def __init__(self, string: Union[str, "MutableString"]) -> None:
        self._string: str = str(string) if isinstance(string, MutableString) else string
        self._string_list: List[str] = list(self._string)
        self._is_dirty: bool = False

    @property
    def string(self) -> str:
        if self._is_dirty:
            self._string = "".join(self._string_list)
            self._is_dirty = False

        return self._string

    def _mark_dirty(self) -> None:
        self._is_dirty = True

    def __len__(self) -> int:
        return len(self._string_list)

    def pop(self, key: int) -> "MutableString":
        self._string_list.pop(key)
        self._mark_dirty()
        return self

    def encode(self, encoding: str) -> bytes:
        return self.string.encode(encoding, "surrogatepass")

    def insert(self, key: int, value: str) -> "MutableString":
        self._string_list.insert(key, value)
        self._mark_dirty()
        return self

    def __setitem__(self, key: Union[int, slice], value: str) -> None:
        self._string_list[key] = value
        self._mark_dirty()

    def __getitem__(self, key: int) -> str:
        return self._string_list[key]

    def __str__(self) -> str:
        return self.string

    def __repr__(self) -> str:
        return self.string

    def delete(self, start: int, length: int) -> None:
        del self._string_list[start : start + length]
