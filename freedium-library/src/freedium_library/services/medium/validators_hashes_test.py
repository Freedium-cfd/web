import pytest

from freedium_library.container import Container
from freedium_library.services.medium.container import MediumContainer
from freedium_library.services.medium.validators import (
    _MediumServiceHashesValidator,  # type: ignore
)


class TestMediumServiceHashesValidator:
    @pytest.fixture
    def validator(self) -> _MediumServiceHashesValidator:
        Container().wire(modules=[__name__])
        MediumContainer().wire(modules=[__name__])
        return _MediumServiceHashesValidator()

    def test_is_valid(self, validator: _MediumServiceHashesValidator):
        assert validator.is_valid("515dd5a43948")
        assert validator.is_valid("c81e00f6320d")
        assert validator.is_valid("-515dd5a43948")
        assert not validator.is_valid("")
        assert not validator.is_valid("invalid")
        assert not validator.is_valid("12345")
        assert not validator.is_valid("zzzzzzzzzzz")

    def test_extract_hashes(self, validator: _MediumServiceHashesValidator):
        assert validator.extract_hashes("stop-wasting-your-life-27832c8f6644") == [
            "27832c8f6644"
        ]
        assert validator.extract_hashes("some-linux-commands-9dc802a10618") == [
            "9dc802a10618"
        ]

        assert validator.extract_hashes("515dd5a43948") == ["515dd5a43948"]
        assert validator.extract_hashes("c81e00f6320d") == ["c81e00f6320d"]

        assert validator.extract_hashes(
            "https://medium.com/macoclock/12-macos-apps-515dd5a43948"
        ) == ["515dd5a43948"]
        assert validator.extract_hashes("https://www.freedium.cfd/c81e00f6320d") == [
            "c81e00f6320d"
        ]

        assert validator.extract_hashes("") == []
        assert validator.extract_hashes("no-hash-here") == []
        assert validator.extract_hashes("invalid-hash-123") == []
        assert validator.extract_hashes("zzzzzzzzzzz") == []

        assert validator.extract_hashes(
            "https://medium.com/macoclock/the-11-craziest-and-most-advanced-macos-tips-tricks-ive-ever-seen-cd842ce3f0a3"
        ) == ["cd842ce3f0a3"]

        assert validator.extract_hashes(
            "https://medium.com/calendar/practicing-purposeful-productivity-ef976b89890e"
        ) == ["ef976b89890e"]

        assert validator.extract_hashes(
            "https://medium.com/@andreafeccomandi/how-to-use-the-self-fulfilling-prophecy-narrative-technique-2c7bf44edbdc"
        ) == ["2c7bf44edbdc"]

        assert validator.extract_hashes(
            "https://grigorkh.medium.com/native-lazy-loading-of-images-and-iframes-6931fe455632"
        ) == ["6931fe455632"]

        assert validator.extract_hashes(
            "codeium-best-free-alternative-for-github-copilot-5a010f74d3e1?subid1=20241023-0155-4648-992f-1316e4a9d771"
        ) == ["5a010f74d3e1", "1316e4a9d771"]

        assert validator.extract_hashes(
            "https://medium.com/dataman-in-ai/temporal-fusion-transformer-for-interpretable-time-series-predictions-4b439aa3d9bd"
        ) == ["4b439aa3d9bd"]

        assert validator.extract_hashes(
            "https://medium.com/dataman-in-ai/temporal-fusion-transformer-for-interpretable-time-series-predictions-4b439aa3d9bd+"
        ) == ["4b439aa3d9bd"]

        assert validator.extract_hashes(
            "https://medium.com/dataman-in-ai/temporal-fusion-transformer-for-interpretable-time-series-predictions-4b439aa3d9bd+fds"
        ) == ["4b439aa3d9bd"]

        assert validator.extract_hashes(
            "https://12ft.io/api/proxy?q=https%3A%2F%2Fednico.medium.com%2Fpkm-weekly-2024-05-26-6601694e4147"
        ) == ["6601694e4147"]

    def test_extract_multiple_hashes(self, validator: _MediumServiceHashesValidator):
        text = "first-515dd5a43948 second-c81e00f6320d"
        assert set(validator.extract_hashes(text)) == {"515dd5a43948", "c81e00f6320d"}

    def test_edge_cases(self, validator: _MediumServiceHashesValidator):
        assert validator.extract_hashes(None) == []  # type: ignore
        assert validator.extract_hashes("   ") == []
        assert validator.extract_hashes("abc123") == []
        assert validator.extract_hashes("12345678901234567890") == []
