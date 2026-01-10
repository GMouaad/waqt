"""Unit tests for the settings UI."""

import pytest


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    from src.waqt import create_app, db
    from src.waqt.models import Settings
    
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
    from src.waqt.models import Settings
    
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
    from src.waqt.models import Settings
    
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
        # Verify specific error message appears
        assert b"Weekly Hours: Must be greater than 0 and at most 168 hours" in response.data


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
        # Should show specific error about empty value for the field
        assert b"Standard Hours Per Day: Value cannot be empty" in response.data


def test_settings_empty_values_for_all_numeric_fields(client, app):
    """Test that empty values for all required numeric fields show error messages."""
    with app.app_context():
        # Test empty weekly_hours
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "",  # Empty value
            "pause_duration_minutes": "45",
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "10",
        }, follow_redirects=True)
        assert b"Weekly Hours: Value cannot be empty" in response.data
        
        # Test empty pause_duration_minutes
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "40",
            "pause_duration_minutes": "",  # Empty value
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "10",
        }, follow_redirects=True)
        assert b"Pause Duration (minutes): Value cannot be empty" in response.data
        
        # Test empty max_work_session_hours
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "40",
            "pause_duration_minutes": "45",
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "",  # Empty value
        }, follow_redirects=True)
        assert b"Max Work Session Hours: Value cannot be empty" in response.data


def test_settings_update_multiple_values(client, app):
    """Test updating multiple configuration values at once."""
    from src.waqt.models import Settings
    
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
        assert b"Standard Hours Per Day: Must be greater than 0 and at most 24 hours" in response.data
        
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
        assert b"Standard Hours Per Day: Must be greater than 0 and at most 24 hours" in response.data


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
        assert b"Pause Duration (minutes): Must be between 0 and 480 minutes (8 hours)" in response.data


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
        assert b"Max Work Session Hours: Must be between 1 and 24 hours" in response.data
        
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
        assert b"Max Work Session Hours: Must be between 1 and 24 hours" in response.data


def test_settings_page_shows_modified_indicator(client, app):
    """Test that modified settings show an indicator."""
    from src.waqt.models import Settings
    
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
        # Check for both href and Settings text in navigation
        assert b'href="/settings"' in response.data
        assert b"Settings" in response.data


def test_settings_page_displays_time_format_dropdown(client, app):
    """Test that time_format select dropdown is displayed with correct options."""
    with app.app_context():
        response = client.get("/settings")
        assert response.status_code == 200
        
        # Check that Time Display Format is present
        assert b"Time Display Format" in response.data
        
        # Check that the select dropdown exists
        assert b'name="time_format"' in response.data
        assert b'id="time_format"' in response.data
        
        # Check that both options are present
        assert b"24-hour (HH:MM)" in response.data
        assert b"12-hour (hh:MM AM/PM)" in response.data
        assert b'value="24"' in response.data
        assert b'value="12"' in response.data


def test_settings_time_format_update(client, app):
    """Test updating the time_format value via the settings page POST request."""
    from src.waqt.models import Settings
    
    with app.app_context():
        # Initially, time_format should be default (24)
        assert Settings.get_setting("time_format", "24") == "24"
        
        # Update to 12-hour format
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "40",
            "pause_duration_minutes": "45",
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "10",
            "time_format": "12",
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b"Settings updated successfully!" in response.data
        
        # Verify the value was updated in the database
        assert Settings.get_setting("time_format") == "12"
        
        # Update back to 24-hour format
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "40",
            "pause_duration_minutes": "45",
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "10",
            "time_format": "24",
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b"Settings updated successfully!" in response.data
        assert Settings.get_setting("time_format") == "24"


def test_settings_time_format_shows_selected_value(client, app):
    """Test that the dropdown shows the currently selected time format value correctly."""
    from src.waqt.models import Settings
    
    with app.app_context():
        # Set to 12-hour format
        Settings.set_setting("time_format", "12")
        
        response = client.get("/settings")
        assert response.status_code == 200
        
        # Check that 12 is selected
        assert b'value="12" selected' in response.data
        
        # Set to 24-hour format
        Settings.set_setting("time_format", "24")
        
        response = client.get("/settings")
        assert response.status_code == 200
        
        # Check that 24 is selected
        assert b'value="24" selected' in response.data


def test_settings_time_format_validation(client, app):
    """Test that time_format only accepts valid values (12 or 24)."""
    from src.waqt.models import Settings
    
    with app.app_context():
        # Test invalid value
        response = client.post("/settings", data={
            "standard_hours_per_day": "8",
            "weekly_hours": "40",
            "pause_duration_minutes": "45",
            "auto_end": "",
            "alert_on_max_work_session": "",
            "max_work_session_hours": "10",
            "time_format": "invalid",
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b"Time Display Format:" in response.data
        
        # The setting should not have been updated
        # (should still be default or previous valid value)
        time_format = Settings.get_setting("time_format", "24")
        assert time_format in ["12", "24"]
