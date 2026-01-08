"""Database models for time tracking application."""

import logging
from datetime import datetime, timezone
from . import db

logger = logging.getLogger(__name__)


def _format_time_for_dict(time_obj):
    """Helper to format time for dictionary serialization."""
    # Import here to avoid circular imports
    from .utils import format_time
    return format_time(time_obj)


class TimeEntry(db.Model):
    """Model for tracking work time entries."""

    __tablename__ = "time_entries"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration_hours = db.Column(db.Float, nullable=False)
    accumulated_pause_seconds = db.Column(db.Float, default=0.0)
    last_pause_start_time = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<TimeEntry {self.date} - {self.duration_hours}h>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "start_time": _format_time_for_dict(self.start_time),
            "end_time": _format_time_for_dict(self.end_time),
            "duration_hours": self.duration_hours,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }


class LeaveDay(db.Model):
    """Model for tracking vacation and sick leave days."""

    __tablename__ = "leave_days"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    leave_type = db.Column(db.String(20), nullable=False)  # 'vacation' or 'sick'
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<LeaveDay {self.date} - {self.leave_type}>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "leave_type": self.leave_type,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }


class Settings(db.Model):
    """Model for application settings."""

    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<Settings {self.key}={self.value}>"

    @staticmethod
    def get_setting(key, default=None):
        """Get a setting value by key."""
        setting = Settings.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set_setting(key, value):
        """Set a setting value."""
        setting = Settings.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = Settings(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()

    @staticmethod
    def update_setting(key, value):
        """Update a setting value without committing (for atomic transactions)."""
        setting = Settings.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = Settings(key=key, value=str(value))
            db.session.add(setting)

    @staticmethod
    def get_all_settings():
        """Get all settings as a dictionary."""
        settings = Settings.query.all()
        return {s.key: s.value for s in settings}

    @staticmethod
    def get_int(key, default=None):
        """Get a setting value as integer."""
        value = Settings.get_setting(key, default)
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Failed to convert setting '{key}' value '{value}' to int: {e}. "
                f"Returning default: {default}"
            )
            return default

    @staticmethod
    def get_float(key, default=None):
        """Get a setting value as float."""
        value = Settings.get_setting(key, default)
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Failed to convert setting '{key}' value '{value}' to float: {e}. "
                f"Returning default: {default}"
            )
            return default

    @staticmethod
    def get_bool(key, default=False):
        """Get a setting value as boolean."""
        value = Settings.get_setting(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
