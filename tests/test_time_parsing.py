import pytest
from datetime import time


def test_parse_time_input_24_hour():
    """Test parsing 24-hour format."""
    from src.waqt.utils import parse_time_input

    assert parse_time_input("14:30", "24") == time(14, 30)
    assert parse_time_input("09:15", "24") == time(9, 15)
    assert parse_time_input("00:00", "24") == time(0, 0)
    assert parse_time_input("23:59", "24") == time(23, 59)


def test_parse_time_input_12_hour():
    """Test parsing 12-hour format."""
    from src.waqt.utils import parse_time_input

    assert parse_time_input("02:30 PM", "12") == time(14, 30)
    assert parse_time_input("09:15 AM", "12") == time(9, 15)
    assert parse_time_input("12:00 PM", "12") == time(12, 0)
    assert parse_time_input("12:00 AM", "12") == time(0, 0)


def test_parse_time_input_12_hour_case_insensitive():
    """Test case-insensitivity for 12-hour format."""
    from src.waqt.utils import parse_time_input

    assert parse_time_input("02:30 pm", "12") == time(14, 30)
    assert parse_time_input("09:15 am", "12") == time(9, 15)
    assert parse_time_input("02:30 Pm", "12") == time(14, 30)


def test_parse_time_input_12_hour_fallback():
    """Test fallback to 24-hour parsing if 12-hour fails."""
    from src.waqt.utils import parse_time_input

    # This simulates a case where user might enter 24h format even if setting is 12h
    # or if the input doesn't match the strict AM/PM pattern
    assert parse_time_input("14:30", "12") == time(14, 30)


def test_parse_time_input_invalid():
    """Test invalid inputs raise ValueError."""
    from src.waqt.utils import parse_time_input

    with pytest.raises(ValueError):
        parse_time_input("invalid", "24")

    with pytest.raises(ValueError):
        parse_time_input("25:00", "24")

    with pytest.raises(ValueError):
        parse_time_input("invalid", "12")


def test_parse_time_input_default_format():
    """Test default format is 24-hour."""
    from src.waqt.utils import parse_time_input

    assert parse_time_input("14:30") == time(14, 30)
