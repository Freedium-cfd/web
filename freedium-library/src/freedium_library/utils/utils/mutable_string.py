from typing import List, Union, overload


class MutableString:
    __slots__ = ("_string", "_string_list")

    def __init__(self, string: Union[str, "MutableString"]) -> None:
        self._string: str = str(string) if isinstance(string, MutableString) else string
        self._string_list: List[str] = list(self._string)

    @property
    def string(self) -> str:
        return "".join(self._string_list)

    def __len__(self) -> int:
        return len(self._string_list)

    def pop(self, key: int) -> "MutableString":
        self._string_list.pop(key)
        return self

    def encode(self, encoding: str) -> bytes:
        return self.string.encode(encoding, "surrogatepass")

    def insert(self, key: int, value: str) -> "MutableString":
        if key < 0 or key > len(self._string_list):
            raise IndexError("string index out of range")
        self._string_list.insert(key, value)
        return self

    def __setitem__(self, key: Union[int, slice], value: str) -> None:
        self._string_list[key] = value

    @overload
    def __getitem__(self, key: int) -> str: ...

    @overload
    def __getitem__(self, key: slice) -> List[str]: ...

    def __getitem__(self, key: Union[int, slice]) -> Union[str, List[str]]:
        return self._string_list[key]

    def __str__(self) -> str:
        return self.string

    def __repr__(self) -> str:
        return self.string

    def delete(self, start: int, length: int) -> None:
        if start < 0 or start >= len(self._string_list):
            raise IndexError("string index out of range")
        del self._string_list[start : start + length]
