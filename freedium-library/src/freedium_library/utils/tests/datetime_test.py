from datetime import datetime
from typing import Tuple

import pytest
from freezegun import freeze_time

from freedium_library.utils.datetime import DateTimeUtils


@pytest.fixture
def fixed_datetime() -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0)


@freeze_time("2024-01-01 12:00:00")
def test_current_time() -> None:
    # Should return current time when no input is provided
    result = DateTimeUtils.to_milliseconds()
    expected = 1704110400000  # 2024-01-01 12:00:00 UTC in milliseconds
    assert result == expected


def test_string_input() -> None:
    # Test various string formats
    cases: list[Tuple[str, int]] = [
        ("2024-01-01 12:00:00", 1704110400000),
        ("2024-01-01T12:00:00Z", 1704110400000),
        ("2024-01-01", 1704067200000),  # Start of day
    ]

    for input_str, expected in cases:
        assert DateTimeUtils.to_milliseconds(input_str) == expected


def test_datetime_input(fixed_datetime: datetime) -> None:
    result = DateTimeUtils.to_milliseconds(fixed_datetime)
    expected = 1704110400000  # 2024-01-01 12:00:00 UTC
    assert result == expected


def test_timezone_handling() -> None:
    dt_str: str = "2024-01-01 12:00:00"

    utc_result = DateTimeUtils.to_milliseconds(dt_str, tz="UTC")
    est_result = DateTimeUtils.to_milliseconds(dt_str, tz="America/New_York")

    # When it's 12:00 in EST, it's 17:00 in UTC (EST+5)
    assert est_result == utc_result + (5 * 3600 * 1000)


def test_invalid_inputs() -> None:
    invalid_inputs: list[str] = [
        "not a date",
        "2024-13-01",  # Invalid month
        "2024-01-32",  # Invalid day
    ]

    for invalid_input in invalid_inputs:
        with pytest.raises(ValueError):
            DateTimeUtils.to_milliseconds(invalid_input)


def test_comprehensive_timezone_handling() -> None:
    dt_str: str = "2024-01-01 12:00:00"

    # Test various timezone offsets
    tokyo_result = DateTimeUtils.to_milliseconds(dt_str, tz="Asia/Tokyo")
    utc_result = DateTimeUtils.to_milliseconds(dt_str, tz="UTC")
    la_result = DateTimeUtils.to_milliseconds(dt_str, tz="America/Los_Angeles")

    # Tokyo is UTC+9, LA is UTC-8
    assert tokyo_result == utc_result - (9 * 3600 * 1000)
    assert la_result == utc_result + (8 * 3600 * 1000)


def test_dst_handling() -> None:
    # Test during DST period (July)
    summer_dt: str = "2024-07-01 12:00:00"
    ny_summer = DateTimeUtils.to_milliseconds(summer_dt, tz="America/New_York")
    utc_summer = DateTimeUtils.to_milliseconds(summer_dt, tz="UTC")

    # During DST, NY is UTC-4
    assert ny_summer == utc_summer + (4 * 3600 * 1000)

    # Test outside DST period (January)
    winter_dt: str = "2024-01-01 12:00:00"
    ny_winter = DateTimeUtils.to_milliseconds(winter_dt, tz="America/New_York")
    utc_winter = DateTimeUtils.to_milliseconds(winter_dt, tz="UTC")

    # Outside DST, NY is UTC-5
    assert ny_winter == utc_winter + (5 * 3600 * 1000)


def test_timezone_aware_string_input() -> None:
    cases: list[Tuple[str, str, int]] = [
        # ISO format with timezone
        (
            "2024-01-01T12:00:00+09:00",
            "UTC",
            1704078000000,
        ),  # Tokyo time converted to UTC
        (
            "2024-01-01T12:00:00-05:00",
            "UTC",
            1704128400000,
        ),  # EST time converted to UTC
        # Named timezone in string
        ("2024-01-01T12:00:00-00:00", "UTC", 1704110400000),
    ]

    for input_str, target_tz, expected in cases:
        assert int(DateTimeUtils.to_milliseconds(input_str, tz=target_tz)) == int(
            expected
        )


def test_date_boundary_cases() -> None:
    # Test date boundary cases across timezones
    dt_str: str = "2024-01-01 00:00:00"

    tokyo = DateTimeUtils.to_milliseconds(dt_str, tz="Asia/Tokyo")
    la = DateTimeUtils.to_milliseconds(dt_str, tz="America/Los_Angeles")

    # When it's midnight in Tokyo, it's still previous day in LA
    assert la - tokyo == 17 * 3600 * 1000  # 17 hours difference
