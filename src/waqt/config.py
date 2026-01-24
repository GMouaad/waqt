"""Configuration management utilities shared between CLI and UI."""

# Configuration defaults and validation rules
CONFIG_DEFAULTS = {
    "standard_hours_per_day": "8",
    "weekly_hours": "40",
    "pause_duration_minutes": "45",
    "auto_end": "false",
    "alert_on_max_work_session": "false",
    "max_work_session_hours": "10",
    "time_format": "24",
}

# Configuration value types for automatic type handling
CONFIG_TYPES = {
    "standard_hours_per_day": "float",
    "weekly_hours": "float",
    "pause_duration_minutes": "int",
    "auto_end": "bool",
    "alert_on_max_work_session": "bool",
    "max_work_session_hours": "float",
    "time_format": "text",
}

CONFIG_DESCRIPTIONS = {
    "standard_hours_per_day": "Standard working hours per day (default: 8)",
    "weekly_hours": "Expected weekly working hours (default: 40)",
    "pause_duration_minutes": "Default pause/break duration in minutes (default: 45)",
    "auto_end": "Feature flag: Auto-end work session after 8h 45m (default: false)",
    "alert_on_max_work_session": "Feature flag: Alert when session exceeds 8 hours and approaches max limit (default: false)",
    "max_work_session_hours": "Maximum work session hours threshold for alerts (default: 10)",
    "time_format": "Time display format: 24-hour (HH:MM) or 12-hour (hh:MM AM/PM) (default: 24)",
}

CONFIG_VALIDATORS = {
    "standard_hours_per_day": lambda v: 0 < float(v) <= 24,
    "weekly_hours": lambda v: 0 < float(v) <= 168,
    "pause_duration_minutes": lambda v: 0 <= int(v) <= 480,
    "auto_end": lambda v: isinstance(v, str)
    and v.lower() in ("true", "false", "1", "0", "yes", "no", "on", "off"),
    "alert_on_max_work_session": lambda v: isinstance(v, str)
    and v.lower() in ("true", "false", "1", "0", "yes", "no", "on", "off"),
    "max_work_session_hours": lambda v: 1 <= float(v) <= 24,
    "time_format": lambda v: isinstance(v, str) and v in ("12", "24"),
}

CONFIG_VALIDATION_MESSAGES = {
    "standard_hours_per_day": "Must be greater than 0 and at most 24 hours",
    "weekly_hours": "Must be greater than 0 and at most 168 hours",
    "pause_duration_minutes": "Must be between 0 and 480 minutes (8 hours)",
    "auto_end": "Must be a boolean value (true/false, yes/no, 1/0, on/off)",
    "alert_on_max_work_session": "Must be a boolean value (true/false, yes/no, 1/0, on/off)",
    "max_work_session_hours": "Must be between 1 and 24 hours",
    "time_format": "Must be either '12' for 12-hour format or '24' for 24-hour format",
}

# Display names for UI (user-friendly labels)
CONFIG_DISPLAY_NAMES = {
    "standard_hours_per_day": "Standard Hours Per Day",
    "weekly_hours": "Weekly Hours",
    "pause_duration_minutes": "Pause Duration (minutes)",
    "auto_end": "Auto-End Work Session",
    "alert_on_max_work_session": "Alert on Max Work Session",
    "max_work_session_hours": "Max Work Session Hours",
    "time_format": "Time Display Format",
}


def validate_config_value(key, value):
    """
    Validate a configuration value.

    Args:
        key: Configuration key
        value: Value to validate

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if key not in CONFIG_DEFAULTS:
        return False, f"Unknown configuration key '{key}'"

    validator = CONFIG_VALIDATORS.get(key)
    if validator:
        try:
            if not validator(value):
                validation_msg = CONFIG_VALIDATION_MESSAGES.get(
                    key, "Value validation failed"
                )
                return False, validation_msg
        except (ValueError, TypeError) as e:
            validation_msg = CONFIG_VALIDATION_MESSAGES.get(
                key, "Value validation failed"
            )
            return False, f"{validation_msg}: {str(e)}"

    return True, None


def normalize_bool_value(value):
    """
    Normalize boolean values to 'true' or 'false' strings.

    Args:
        value: String value to normalize

    Returns:
        str: 'true' or 'false'
    """
    if isinstance(value, str):
        return "true" if value.lower() in ("true", "1", "yes", "on") else "false"
    return "false"


def get_config_input_type(key):
    """
    Get the HTML input type for a configuration key.

    Args:
        key: Configuration key

    Returns:
        str: HTML input type ('number', 'checkbox', 'text', 'select')
    """
    if key == "time_format":
        return "select"
    config_type = CONFIG_TYPES.get(key, "text")
    if config_type == "bool":
        return "checkbox"
    elif config_type in ("int", "float"):
        return "number"
    return "text"


def get_config_validation_bounds(key):
    """
    Get min/max validation bounds for numeric configuration fields.

    Args:
        key: Configuration key

    Returns:
        dict: Dictionary with 'min' and 'max' keys, or empty dict for non-numeric fields
    """
    bounds = {
        "standard_hours_per_day": {"min": "0.1", "max": "24"},
        "weekly_hours": {"min": "0.1", "max": "168"},
        "pause_duration_minutes": {"min": "0", "max": "480"},
        "max_work_session_hours": {"min": "1", "max": "24"},
    }
    return bounds.get(key, {})


def get_config_select_options(key):
    """
    Get select dropdown options for configuration fields.

    Args:
        key: Configuration key

    Returns:
        list: List of tuples (value, label) for select options, or empty list
    """
    options = {
        "time_format": [
            ("24", "24-hour (HH:MM) - e.g., 13:30"),
            ("12", "12-hour (hh:MM AM/PM) - e.g., 01:30 PM"),
        ],
    }
    return options.get(key, [])
