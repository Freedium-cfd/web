from datetime import datetime, timedelta

from freedium_library.utils.time import get_unix_ms


def test_get_unix_ms_returns_current_time_ms() -> None:
    before = datetime.now() - timedelta(seconds=1)
    value = get_unix_ms()
    after = datetime.now() + timedelta(seconds=1)

    assert isinstance(value, int)
    assert before.timestamp() * 1000 <= value <= after.timestamp() * 1000
