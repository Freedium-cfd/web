import pytest

from freedium_library.utils import URLProcessor


class TestUnWwwify:
    @pytest.fixture
    def url_processor(self):
        return URLProcessor()

    def test_basic_www_removal(self, url_processor: URLProcessor):
        assert url_processor.un_wwwify("www.example.com") == "example.com"
        assert (
            url_processor.un_wwwify("https://www.example.com") == "https://example.com"
        )
        assert url_processor.un_wwwify("http://www.example.com") == "http://example.com"

    def test_non_www_urls(self, url_processor: URLProcessor):
        assert url_processor.un_wwwify("example.com") == "example.com"
        assert url_processor.un_wwwify("https://example.com") == "https://example.com"
        assert url_processor.un_wwwify("sub.example.com") == "sub.example.com"

    def test_urls_with_paths(self, url_processor: URLProcessor):
        assert url_processor.un_wwwify("www.example.com/path") == "example.com/path"
        assert (
            url_processor.un_wwwify("https://www.example.com/path")
            == "https://example.com/path"
        )
        assert (
            url_processor.un_wwwify("https://www.example.com/path/to/resource")
            == "https://example.com/path/to/resource"
        )

    def test_urls_with_query_params(self, url_processor: URLProcessor):
        assert (
            url_processor.un_wwwify("www.example.com?key=value")
            == "example.com?key=value"
        )
        assert (
            url_processor.un_wwwify("https://www.example.com?key=value")
            == "https://example.com?key=value"
        )
        assert (
            url_processor.un_wwwify("https://www.example.com/path?key=value&other=123")
            == "https://example.com/path?key=value&other=123"
        )

    def test_error_handling(self, url_processor: URLProcessor):
        with pytest.raises(ValueError):
            url_processor.un_wwwify("")

        with pytest.raises(TypeError):
            url_processor.un_wwwify(None)  # type: ignore

    def test_special_cases(self, url_processor: URLProcessor):
        assert url_processor.un_wwwify("www.www.example.com") == "www.example.com"
        assert url_processor.un_wwwify("wwww.example.com") == "wwww.example.com"
        assert url_processor.un_wwwify("example.www.com") == "example.www.com"


class TestUnquerifyUrl:
    @pytest.fixture
    def url_processor(self):
        return URLProcessor()

    def test_basic_query_removal(self, url_processor: URLProcessor):
        assert url_processor.unquerify_url("example.com?param=value") == "example.com"
        assert (
            url_processor.unquerify_url("https://example.com?param=value")
            == "https://example.com"
        )

    def test_multiple_query_params(self, url_processor: URLProcessor):
        assert url_processor.unquerify_url("example.com?p1=v1&p2=v2") == "example.com"
        assert (
            url_processor.unquerify_url("https://example.com?p1=v1&p2=v2")
            == "https://example.com"
        )

    def test_urls_without_query(self, url_processor: URLProcessor):
        assert url_processor.unquerify_url("example.com") == "example.com"
        assert (
            url_processor.unquerify_url("https://example.com") == "https://example.com"
        )

    def test_urls_with_paths(self, url_processor: URLProcessor):
        assert (
            url_processor.unquerify_url("example.com/path?param=value")
            == "example.com/path"
        )
        assert (
            url_processor.unquerify_url("https://example.com/path?param=value")
            == "https://example.com/path"
        )

    def test_trailing_slash_removal(self, url_processor: URLProcessor):
        assert (
            url_processor.unquerify_url("example.com/path/?param=value")
            == "example.com/path"
        )
        assert (
            url_processor.unquerify_url("https://example.com/?param=value")
            == "https://example.com"
        )

    def test_error_handling(self, url_processor: URLProcessor):
        ...
        # with pytest.raises(ValueError):
        #     url_processor.unquerify_url("")

        # with pytest.raises(TypeError):
        #     url_processor.unquerify_url(None)
