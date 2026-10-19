import pytest

from freedium_library.utils.url import escape_html, normalize_url


@pytest.mark.parametrize(
    "inp,expected",
    [
        ("https:/example.com/foo", "https://example.com/foo"),
        ("https://example.com/foo", "https://example.com/foo"),
        ("http:/example.com/foo", "http://example.com/foo"),
        ("http://example.com/foo", "http://example.com/foo"),
        ("example.com/foo", "https://example.com/foo"),
        ("  https:/nytimes.com/art  ", "https://nytimes.com/art"),
    ],
)
def test_normalize_url(inp: str, expected: str):
    assert normalize_url(inp) == expected


def test_escape_html():
    assert escape_html('Hello <world> & "friends"') == "Hello &lt;world&gt; &amp; &quot;friends&quot;"
