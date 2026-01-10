"""Tests for time format functionality."""

import pytest
from datetime import time


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    from src.waqt import create_app, db
    
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


def test_format_time_24_hour(app):
    """Test time formatting with 24-hour format."""
    from src.waqt.models import Settings
    from src.waqt.utils import format_time
    
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
    from src.waqt.models import Settings
    from src.waqt.utils import format_time
    
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
    from src.waqt.utils import format_time
    
    with app.app_context():
        # Don't set any time_format setting
        time_obj = time(14, 30)
        formatted = format_time(time_obj)
        assert formatted == "14:30"


def test_format_time_with_explicit_format(app):
    """Test format_time with explicit format parameter."""
    from src.waqt.utils import format_time
    
    with app.app_context():
        # Test with explicit 24-hour format
        time_obj = time(15, 30)
        formatted = format_time(time_obj, "24")
        assert formatted == "15:30"
        
        # Test with explicit 12-hour format
        formatted = format_time(time_obj, "12")
        assert formatted == "3:30 PM"


def test_format_time_with_none(app):
    """Test format_time with None input for defensive programming."""
    from src.waqt.utils import format_time
    
    with app.app_context():
        # Test with None time_obj
        formatted = format_time(None)
        assert formatted == ""
        
        # Test with None and explicit format
        formatted = format_time(None, "12")
        assert formatted == ""
        
        formatted = format_time(None, "24")
        assert formatted == ""


def test_time_format_setting_validation(app):
    """Test that time_format setting validates correctly."""
    with app.app_context():
        from src.waqt.config import validate_config_value
        
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


def test_format_time_jinja_filter_registered(app):
    """Test that the format_time Jinja filter is properly registered."""
    with app.app_context():
        # Check that the filter is registered in the Jinja environment
        assert 'format_time' in app.jinja_env.filters


def test_format_time_jinja_filter_in_template(app, client):
    """Test that format_time filter works in template rendering."""
    from src.waqt.models import Settings, TimeEntry
    from src.waqt import db
    from datetime import date
    
    with app.app_context():
        # Set time format to 12-hour
        Settings.set_setting("time_format", "12")
        
        # Create a test time entry
        entry = TimeEntry(
            date=date.today(),
            start_time=time(9, 30),
            end_time=time(17, 45),
            duration_hours=8.25,
            description="Test entry"
        )
        db.session.add(entry)
        db.session.commit()
        
        # Get the dashboard page
        response = client.get("/")
        assert response.status_code == 200
        
        # Check that times are displayed in 12-hour format
        assert b"9:30 AM" in response.data
        assert b"5:45 PM" in response.data
        
        # Change to 24-hour format
        Settings.set_setting("time_format", "24")
        
        # Get the dashboard page again
        response = client.get("/")
        assert response.status_code == 200
        
        # Check that times are displayed in 24-hour format
        assert b"09:30" in response.data
        assert b"17:45" in response.data


def test_format_time_in_reports_page(app, client):
    """Test that format_time filter works correctly in reports page."""
    from src.waqt.models import Settings, TimeEntry
    from src.waqt import db
    from datetime import date
    
    with app.app_context():
        # Set time format to 12-hour
        Settings.set_setting("time_format", "12")
        
        # Create a test time entry
        entry = TimeEntry(
            date=date.today(),
            start_time=time(14, 15),
            end_time=time(18, 30),
            duration_hours=4.25,
            description="Report test entry"
        )
        db.session.add(entry)
        db.session.commit()
        
        # Get the reports page
        response = client.get("/reports")
        assert response.status_code == 200
        
        # Check that times are displayed in 12-hour format
        assert b"2:15 PM" in response.data
        assert b"6:30 PM" in response.data
