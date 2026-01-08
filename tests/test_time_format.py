"""Tests for time format functionality."""

import pytest
from datetime import time
from src.waqtracker import create_app, db
from src.waqtracker.models import Settings
from src.waqtracker.utils import format_time


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_format_time_24_hour(app):
    """Test time formatting with 24-hour format."""
    with app.app_context():
        # Set time format to 24-hour
        Settings.set_setting("time_format", "24")
        
        # Test morning time
        time_obj = time(9, 30)
        formatted = format_time(time_obj)
        assert formatted == "09:30"
        
        # Test afternoon time
        time_obj = time(14, 45)
        formatted = format_time(time_obj)
        assert formatted == "14:45"
        
        # Test midnight
        time_obj = time(0, 0)
        formatted = format_time(time_obj)
        assert formatted == "00:00"
        
        # Test noon
        time_obj = time(12, 0)
        formatted = format_time(time_obj)
        assert formatted == "12:00"


def test_format_time_12_hour(app):
    """Test time formatting with 12-hour format."""
    with app.app_context():
        # Set time format to 12-hour
        Settings.set_setting("time_format", "12")
        
        # Test morning time (single digit hour)
        time_obj = time(9, 30)
        formatted = format_time(time_obj)
        assert formatted == "9:30 AM"
        
        # Test afternoon time (single digit hour)
        time_obj = time(14, 45)
        formatted = format_time(time_obj)
        assert formatted == "2:45 PM"
        
        # Test midnight
        time_obj = time(0, 0)
        formatted = format_time(time_obj)
        assert formatted == "12:00 AM"
        
        # Test noon
        time_obj = time(12, 0)
        formatted = format_time(time_obj)
        assert formatted == "12:00 PM"
        
        # Test 1 PM
        time_obj = time(13, 0)
        formatted = format_time(time_obj)
        assert formatted == "1:00 PM"
        
        # Test 11 PM
        time_obj = time(23, 59)
        formatted = format_time(time_obj)
        assert formatted == "11:59 PM"


def test_format_time_default_24_hour(app):
    """Test that default format is 24-hour when no setting exists."""
    with app.app_context():
        # Don't set any time_format setting
        time_obj = time(14, 30)
        formatted = format_time(time_obj)
        assert formatted == "14:30"


def test_format_time_with_explicit_format(app):
    """Test format_time with explicit format parameter."""
    with app.app_context():
        # Test with explicit 24-hour format
        time_obj = time(15, 30)
        formatted = format_time(time_obj, "24")
        assert formatted == "15:30"
        
        # Test with explicit 12-hour format
        formatted = format_time(time_obj, "12")
        assert formatted == "3:30 PM"


def test_time_format_setting_validation(app):
    """Test that time_format setting validates correctly."""
    with app.app_context():
        from src.waqtracker.config import validate_config_value
        
        # Valid values
        is_valid, error = validate_config_value("time_format", "12")
        assert is_valid is True
        assert error is None
        
        is_valid, error = validate_config_value("time_format", "24")
        assert is_valid is True
        assert error is None
        
        # Invalid values
        is_valid, error = validate_config_value("time_format", "13")
        assert is_valid is False
        assert error is not None
        
        is_valid, error = validate_config_value("time_format", "invalid")
        assert is_valid is False
        assert error is not None
