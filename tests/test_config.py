"""Unit tests for the configuration management CLI commands."""

import pytest
from click.testing import CliRunner
from src.waqtracker import create_app, db
from src.waqtracker.models import Settings
from src.waqtracker.cli import cli


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
            ("standard_hours_per_week", "40"),
            ("weekly_hours", "40"),
            ("pause_duration_minutes", "45"),
            ("auto_end", "false"),
        ]
        for key, value in default_settings:
            Settings.set_setting(key, value)
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


def test_config_help(runner):
    """Test that the config help message displays correctly."""
    result = runner.invoke(cli, ["config", "--help"])
    assert result.exit_code == 0
    assert "Manage application configuration" in result.output
    assert "list" in result.output
    assert "get" in result.output
    assert "set" in result.output
    assert "reset" in result.output


def test_config_list_displays_all_settings(runner, app):
    """Test that config list displays all configuration settings."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "list"])
        assert result.exit_code == 0
        assert "Configuration Settings" in result.output
        assert "standard_hours_per_day" in result.output
        assert "standard_hours_per_week" in result.output
        assert "weekly_hours" in result.output
        assert "pause_duration_minutes" in result.output
        assert "auto_end" in result.output


def test_config_list_shows_default_values(runner, app):
    """Test that config list shows default values correctly."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "list"])
        assert result.exit_code == 0
        assert "Value: 8" in result.output
        assert "Value: 40" in result.output
        assert "Value: 45" in result.output
        assert "Value: false" in result.output


def test_config_get_existing_key(runner, app):
    """Test getting value of an existing configuration key."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "get", "weekly_hours"])
        assert result.exit_code == 0
        assert "weekly_hours" in result.output
        assert "Value: 40" in result.output


def test_config_get_nonexistent_key(runner, app):
    """Test getting value of a non-existent configuration key."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "get", "nonexistent_key"])
        assert result.exit_code != 0
        assert "Unknown configuration key" in result.output
        assert "Available configuration keys:" in result.output


def test_config_set_valid_value(runner, app):
    """Test setting a configuration value with valid input."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "set", "weekly_hours", "35"])
        assert result.exit_code == 0
        assert "Configuration updated!" in result.output
        assert "Old value: 40" in result.output
        assert "New value: 35" in result.output

        # Verify value was actually changed in the database
        value = Settings.get_setting("weekly_hours")
        assert value == "35"


def test_config_set_pause_duration(runner, app):
    """Test setting pause duration."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "set", "pause_duration_minutes", "60"])
        assert result.exit_code == 0
        assert "Configuration updated!" in result.output
        assert "New value: 60" in result.output

        # Verify value was actually changed in the database
        value = Settings.get_int("pause_duration_minutes")
        assert value == 60


def test_config_set_feature_flag_true(runner, app):
    """Test setting a feature flag to true."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "set", "auto_end", "true"])
        assert result.exit_code == 0
        assert "Configuration updated!" in result.output
        assert "New value: true" in result.output

        # Verify value was actually changed in the database
        value = Settings.get_bool("auto_end")
        assert value is True


def test_config_set_feature_flag_various_true_values(runner, app):
    """Test setting a feature flag with various true representations."""
    with app.app_context():
        for true_value in ["true", "1", "yes", "on", "True", "YES", "ON"]:
            result = runner.invoke(cli, ["config", "set", "auto_end", true_value])
            assert result.exit_code == 0
            assert "Configuration updated!" in result.output
            assert "New value: true" in result.output

            # Verify value
            value = Settings.get_bool("auto_end")
            assert value is True


def test_config_set_feature_flag_false(runner, app):
    """Test setting a feature flag to false."""
    with app.app_context():
        # First set it to true
        runner.invoke(cli, ["config", "set", "auto_end", "true"])

        # Now set it to false
        result = runner.invoke(cli, ["config", "set", "auto_end", "false"])
        assert result.exit_code == 0
        assert "Configuration updated!" in result.output
        assert "New value: false" in result.output

        # Verify value
        value = Settings.get_bool("auto_end")
        assert value is False


def test_config_set_nonexistent_key(runner, app):
    """Test setting a non-existent configuration key."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "set", "nonexistent_key", "value"])
        assert result.exit_code != 0
        assert "Unknown configuration key" in result.output


def test_config_set_invalid_weekly_hours_too_high(runner, app):
    """Test setting weekly hours to an invalid value (too high)."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "set", "weekly_hours", "200"])
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "Must be between" in result.output


def test_config_set_invalid_weekly_hours_negative(runner, app):
    """Test setting weekly hours to a negative value."""
    with app.app_context():
        # Note: Click interprets negative numbers as options, so we use 0 instead
        result = runner.invoke(cli, ["config", "set", "weekly_hours", "0"])
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "Must be between" in result.output


def test_config_set_invalid_pause_duration(runner, app):
    """Test setting pause duration to an invalid value."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "set", "pause_duration_minutes", "500"])
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "Must be between" in result.output


def test_config_set_invalid_pause_duration_negative(runner, app):
    """Test setting pause duration to an invalid value (below minimum)."""
    with app.app_context():
        # Note: Click interprets negative numbers as options, so we test -1 using quotes
        result = runner.invoke(cli, ["config", "set", "pause_duration_minutes", "--", "-5"])
        # This will still be caught by validation since -5 < 0
        assert result.exit_code != 0


def test_config_set_invalid_feature_flag(runner, app):
    """Test setting a feature flag to an invalid value."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "set", "auto_end", "invalid"])
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "boolean" in result.output


def test_config_reset_to_default(runner, app):
    """Test resetting a configuration value to default."""
    with app.app_context():
        # First change the value
        runner.invoke(cli, ["config", "set", "weekly_hours", "35"])

        # Now reset it
        result = runner.invoke(cli, ["config", "reset", "weekly_hours"])
        assert result.exit_code == 0
        assert "Configuration reset to default!" in result.output
        assert "Old value: 35" in result.output
        assert "Default value: 40" in result.output

        # Verify value was reset in the database
        value = Settings.get_setting("weekly_hours")
        assert value == "40"


def test_config_reset_feature_flag(runner, app):
    """Test resetting a feature flag to default."""
    with app.app_context():
        # First change the value
        runner.invoke(cli, ["config", "set", "auto_end", "true"])

        # Now reset it
        result = runner.invoke(cli, ["config", "reset", "auto_end"])
        assert result.exit_code == 0
        assert "Configuration reset to default!" in result.output
        assert "Default value: false" in result.output

        # Verify value was reset
        value = Settings.get_bool("auto_end")
        assert value is False


def test_config_reset_nonexistent_key(runner, app):
    """Test resetting a non-existent configuration key."""
    with app.app_context():
        result = runner.invoke(cli, ["config", "reset", "nonexistent_key"])
        assert result.exit_code != 0
        assert "Unknown configuration key" in result.output


def test_settings_get_int_method(app):
    """Test the Settings.get_int() helper method."""
    with app.app_context():
        Settings.set_setting("test_int", "42")
        value = Settings.get_int("test_int")
        assert value == 42
        assert isinstance(value, int)


def test_settings_get_float_method(app):
    """Test the Settings.get_float() helper method."""
    with app.app_context():
        Settings.set_setting("test_float", "3.14")
        value = Settings.get_float("test_float")
        assert value == 3.14
        assert isinstance(value, float)


def test_settings_get_bool_method(app):
    """Test the Settings.get_bool() helper method."""
    with app.app_context():
        # Test various true values
        for true_val in ["true", "True", "1", "yes", "on"]:
            Settings.set_setting("test_bool", true_val)
            assert Settings.get_bool("test_bool") is True

        # Test various false values
        for false_val in ["false", "False", "0", "no", "off"]:
            Settings.set_setting("test_bool", false_val)
            assert Settings.get_bool("test_bool") is False


def test_settings_get_all_settings(app):
    """Test the Settings.get_all_settings() method."""
    with app.app_context():
        all_settings = Settings.get_all_settings()
        assert isinstance(all_settings, dict)
        assert "weekly_hours" in all_settings
        assert "pause_duration_minutes" in all_settings
        assert "auto_end" in all_settings
        assert all_settings["weekly_hours"] == "40"


def test_config_list_marks_non_default_values(runner, app):
    """Test that config list marks non-default values with asterisk."""
    with app.app_context():
        # Change a value from default
        runner.invoke(cli, ["config", "set", "weekly_hours", "35"])

        result = runner.invoke(cli, ["config", "list"])
        assert result.exit_code == 0
        # Should show the asterisk marker for non-default values
        assert "Indicates non-default value" in result.output


def test_config_workflow_set_get_reset(runner, app):
    """Test complete workflow: set -> get -> reset."""
    with app.app_context():
        # Set a value
        result1 = runner.invoke(cli, ["config", "set", "pause_duration_minutes", "30"])
        assert result1.exit_code == 0
        assert "Configuration updated!" in result1.output

        # Get the value
        result2 = runner.invoke(cli, ["config", "get", "pause_duration_minutes"])
        assert result2.exit_code == 0
        assert "Value: 30" in result2.output

        # Reset the value
        result3 = runner.invoke(cli, ["config", "reset", "pause_duration_minutes"])
        assert result3.exit_code == 0
        assert "Configuration reset to default!" in result3.output

        # Verify it's back to default
        result4 = runner.invoke(cli, ["config", "get", "pause_duration_minutes"])
        assert result4.exit_code == 0
        assert "Value: 45" in result4.output
