import pytest

from freedium_library.utils.utils.mutable_string import MutableString


def test_init():
    # Test basic string initialization
    ms = MutableString("hello")
    assert str(ms) == "hello"

    # Test initialization from another MutableString
    ms2 = MutableString(ms)
    assert str(ms2) == "hello"

    # Test empty string
    ms3 = MutableString("")
    assert str(ms3) == ""


def test_string_property():
    ms = MutableString("test")
    ms._string_list[0] = "b"
    ms._mark_dirty()
    assert ms.string == "best"


def test_len():
    ms = MutableString("hello")
    assert len(ms) == 5
    assert len(MutableString("")) == 0


def test_pop():
    ms = MutableString("hello")
    ms.pop(0)
    assert str(ms) == "ello"

    with pytest.raises(IndexError):
        ms.pop(10)


def test_encode():
    ms = MutableString("hello")
    assert ms.encode("utf-8") == b"hello"

    # Test unicode
    ms = MutableString("hello 🌍")
    assert ms.encode("utf-8").decode("utf-8") == "hello 🌍"


def test_insert():
    ms = MutableString("hello")
    ms.insert(0, "x")
    assert str(ms) == "xhello"

    ms.insert(len(ms), "y")
    assert str(ms) == "xhelloy"

    with pytest.raises(IndexError):
        ms.insert(100, "z")


def test_setitem():
    ms = MutableString("hello")
    ms[0] = "j"
    assert str(ms) == "jello"

    # Test slice
    ms[1:4] = "a"
    assert str(ms) == "jao"


def test_getitem():
    ms = MutableString("hello")
    assert ms[0] == "h"

    with pytest.raises(IndexError):
        _ = ms[10]


def test_delete():
    ms = MutableString("hello")
    ms.delete(1, 2)
    assert str(ms) == "hlo"

    with pytest.raises(IndexError):
        ms.delete(10, 1)
