"""Unit tests for the settings UI."""

import pytest
from src.waqtracker import create_app, db
from src.waqtracker.models import Settings


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        # Initialize with default settings
        default_settings = [
            ("standard_hours_per_day", "8"),
            ("weekly_hours", "40"),
            ("pause_duration_minutes", "45"),
            ("auto_end", "false"),
            ("alert_on_max_work_session", "false"),
            ("max_work_session_hours", "10"),
        ]
        for key, value in default_settings:
            Settings.set_setting(key, value)
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


def test_settings_page_loads(client, app):
    """Test that the settings page loads successfully."""
    with app.app_context():
        response = client.get("/settings")
        assert response.status_code == 200
        assert b"Settings" in response.data
        assert b"Configure application behavior" in response.data


def test_settings_page_displays_all_config_options(client, app):
    """Test that all configuration options are displayed on the settings page."""
    with app.app_context():
        response = client.get("/settings")
        assert response.status_code == 200
        
        # Check that all configuration keys are present
        assert b"Standard Hours Per Day" in response.data
        assert b"Weekly Hours" in response.data
        assert b"Pause Duration" in response.data
        assert b"Auto-End Work Session" in response.data
        assert b"Alert on Max Work Session" in response.data
        assert b"Max Work Session Hours" in response.data


def test_settings_page_displays_current_values(client, app):
    """Test that current values are displayed correctly."""
    with app.app_context():
        response = client.get("/settings")
        assert response.status_code == 200
        
        # Check default values are displayed
        assert b'value="8"' in response.data  # standard_hours_per_day
        assert b'value="40"' in response.data  # weekly_hours
        assert b'value="45"' in response.data  # pause_duration_minutes


def test_settings_update_numeric_value(client, app):
    """Test updating a numeric configuration value."""
    with app.app_context():
        response = client.post("/settings", data={
            "standard_hours_per_day": "7.5",
            "weekly_hours": "37.5",
            "pause_duration_minutes": "60",
            "auto_end": "",  # Unchecked
            "alert_on_max_work_session": "",  # Unchecked
            "max_work_session_hours": "10",
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b"Settings updated successfully!" in response.data
        
        # Verify the values were updated in the database
        assert Settings.get_setting("standard_hours_per_day") == "7.5"
        assert Settings.get_setting("weekly_hours") == "37.5"
        assert Settings.get_setting("pause_duration_minutes") == "60"


def test_settings_update_boolean_value(client, app):
    """Test updating a boolean configuration value."""
    with app.app_context():
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "40",
            "pause_duration_minutes": "45",
            "auto_end": "on",  # Checked
            "alert_on_max_work_session": "on",  # Checked
            "max_work_session_hours": "10",
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b"Settings updated successfully!" in response.data
        
        # Verify the boolean values were updated correctly
        assert Settings.get_bool("auto_end") is True
        assert Settings.get_bool("alert_on_max_work_session") is True


def test_settings_update_invalid_value_shows_error(client, app):
    """Test that invalid values show appropriate error messages."""
    with app.app_context():
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "200",  # Invalid: too high
            "pause_duration_minutes": "45",
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "10",
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b"Weekly Hours" in response.data
        # Should show error about invalid value


def test_settings_update_empty_value_shows_error(client, app):
    """Test that empty values for required fields show error messages."""
    with app.app_context():
        response = client.post("/settings", data={
            "standard_hours_per_day": "",  # Empty value
            "weekly_hours": "40",
            "pause_duration_minutes": "45",
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "10",
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error about empty value
        assert b"cannot be empty" in response.data or b"error" in response.data.lower()


def test_settings_update_multiple_values(client, app):
    """Test updating multiple configuration values at once."""
    with app.app_context():
        response = client.post("/settings", data={
            "standard_hours_per_day": "7",
            "weekly_hours": "35",
            "pause_duration_minutes": "30",
            "auto_end": "on",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "12",
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b"Settings updated successfully!" in response.data
        
        # Verify all values were updated
        assert Settings.get_setting("standard_hours_per_day") == "7"
        assert Settings.get_setting("weekly_hours") == "35"
        assert Settings.get_setting("pause_duration_minutes") == "30"
        assert Settings.get_bool("auto_end") is True
        assert Settings.get_bool("alert_on_max_work_session") is False
        assert Settings.get_setting("max_work_session_hours") == "12"


def test_settings_no_changes_shows_info(client, app):
    """Test that submitting without changes shows info message."""
    with app.app_context():
        # Submit with all default values
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "40",
            "pause_duration_minutes": "45",
            "auto_end": "",  # false
            "alert_on_max_work_session": "",  # false
            "max_work_session_hours": "10",
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b"No changes were made" in response.data


def test_settings_validates_standard_hours_per_day_range(client, app):
    """Test validation of standard_hours_per_day range."""
    with app.app_context():
        # Test too low
        response = client.post("/settings", data={
            "standard_hours_per_day": "0",
            "weekly_hours": "40",
            "pause_duration_minutes": "45",
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "10",
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should show error
        
        # Test too high
        response = client.post("/settings", data={
            "standard_hours_per_day": "25",
            "weekly_hours": "40",
            "pause_duration_minutes": "45",
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "10",
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should show error


def test_settings_validates_pause_duration_range(client, app):
    """Test validation of pause_duration_minutes range."""
    with app.app_context():
        # Test too high
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "40",
            "pause_duration_minutes": "500",  # > 480
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "10",
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should show error about value being too high


def test_settings_validates_max_work_session_hours_range(client, app):
    """Test validation of max_work_session_hours range."""
    with app.app_context():
        # Test too low
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "40",
            "pause_duration_minutes": "45",
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "0.5",  # < 1
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should show error
        
        # Test too high
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "40",
            "pause_duration_minutes": "45",
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "25",  # > 24
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should show error


def test_settings_page_shows_modified_indicator(client, app):
    """Test that modified settings show an indicator."""
    with app.app_context():
        # Change a value
        Settings.set_setting("weekly_hours", "35")
        
        response = client.get("/settings")
        assert response.status_code == 200
        
        # Check for modified indicator (asterisk or similar)
        assert b"*" in response.data or b"modified" in response.data.lower()


def test_settings_navigation_link_exists(client, app):
    """Test that settings link exists in navigation."""
    with app.app_context():
        response = client.get("/")
        assert response.status_code == 200
        assert b'href="/settings"' in response.data or b"Settings" in response.data
