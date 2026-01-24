"""Database models for time tracking application.

These models use standalone SQLAlchemy (via database.py Base) and are
compatible with both Flask-SQLAlchemy and direct SQLAlchemy usage.
"""

import logging
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, Time, 
    DateTime, Text, ForeignKey
)
from sqlalchemy.orm import relationship, Session
from typing import Optional, Dict, Any, List

from .database import Base

logger = logging.getLogger(__name__)


class Category(Base):
    """Model for time entry categories."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=True)
    color = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship defined in TimeEntry

    def __repr__(self):
        return f"<Category {self.name}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "color": self.color,
            "description": self.description,
            "is_active": self.is_active,
        }


class TimeEntry(Base):
    """Model for tracking work time entries."""

    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_hours = Column(Float, nullable=False)
    accumulated_pause_seconds = Column(Float, default=0.0)
    last_pause_start_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False)
    description = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    category = relationship("Category", backref="time_entries")

    def __repr__(self):
        return f"<TimeEntry {self.date} - {self.duration_hours}h>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        # Import here to avoid circular imports
        from .utils import format_time
        
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "start_time": format_time(self.start_time),
            "end_time": format_time(self.end_time),
            "duration_hours": self.duration_hours,
            "description": self.description,
            "category": self.category.to_dict() if self.category else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LeaveDay(Base):
    """Model for tracking vacation and sick leave days."""

    __tablename__ = "leave_days"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    leave_type = Column(String(20), nullable=False)  # 'vacation' or 'sick'
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<LeaveDay {self.date} - {self.leave_type}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "leave_type": self.leave_type,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Settings(Base):
    """Model for application settings."""

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(String(200), nullable=False)

    def __repr__(self):
        return f"<Settings {self.key}={self.value}>"

    # ---------------------------------------------------------------------------
    # Session-based methods (new pattern)
    # ---------------------------------------------------------------------------

    @staticmethod
    def get_setting_with_session(
        session: Session, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Get a setting value by key using explicit session."""
        setting = session.query(Settings).filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set_setting_with_session(session: Session, key: str, value: str) -> None:
        """Set a setting value using explicit session (caller commits)."""
        setting = session.query(Settings).filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = Settings(key=key, value=str(value))
            session.add(setting)

    @staticmethod
    def get_all_settings_with_session(session: Session) -> Dict[str, str]:
        """Get all settings as a dictionary using explicit session."""
        settings = session.query(Settings).all()
        return {s.key: s.value for s in settings}

    @staticmethod
    def get_int_with_session(
        session: Session, key: str, default: Optional[int] = None
    ) -> Optional[int]:
        """Get a setting value as integer using explicit session."""
        value = Settings.get_setting_with_session(session, key, str(default) if default else None)
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
    def get_float_with_session(
        session: Session, key: str, default: Optional[float] = None
    ) -> Optional[float]:
        """Get a setting value as float using explicit session."""
        value = Settings.get_setting_with_session(session, key, str(default) if default else None)
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
    def get_bool_with_session(
        session: Session, key: str, default: bool = False
    ) -> bool:
        """Get a setting value as boolean using explicit session."""
        value = Settings.get_setting_with_session(session, key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    # ---------------------------------------------------------------------------
    # Legacy methods (for backward compatibility with Flask routes)
    # These detect Flask context and use appropriate session
    # ---------------------------------------------------------------------------

    @staticmethod
    def _get_flask_session():
        """Try to get Flask-SQLAlchemy session if in Flask context."""
        try:
            from flask import has_app_context
            if has_app_context():
                from . import db
                return db.session
        except ImportError:
            pass
        return None

    @staticmethod
    def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value by key."""
        flask_session = Settings._get_flask_session()
        if flask_session is not None:
            return Settings.get_setting_with_session(flask_session, key, default)
        from .database import get_session
        with get_session() as session:
            return Settings.get_setting_with_session(session, key, default)

    @staticmethod
    def set_setting(key: str, value: str) -> None:
        """Set a setting value."""
        flask_session = Settings._get_flask_session()
        if flask_session is not None:
            Settings.set_setting_with_session(flask_session, key, value)
            flask_session.commit()
            return
        from .database import get_session
        with get_session() as session:
            Settings.set_setting_with_session(session, key, value)

    @staticmethod
    def update_setting(key: str, value: str) -> None:
        """Update a setting value without committing (for atomic transactions)."""
        flask_session = Settings._get_flask_session()
        if flask_session is not None:
            Settings.set_setting_with_session(flask_session, key, value)
            # Don't commit - caller handles transaction
            return
        Settings.set_setting(key, value)

    @staticmethod
    def get_all_settings() -> Dict[str, str]:
        """Get all settings as a dictionary."""
        flask_session = Settings._get_flask_session()
        if flask_session is not None:
            return Settings.get_all_settings_with_session(flask_session)
        from .database import get_session
        with get_session() as session:
            return Settings.get_all_settings_with_session(session)

    @staticmethod
    def get_int(key: str, default: Optional[int] = None) -> Optional[int]:
        """Get a setting value as integer."""
        flask_session = Settings._get_flask_session()
        if flask_session is not None:
            return Settings.get_int_with_session(flask_session, key, default)
        from .database import get_session
        with get_session() as session:
            return Settings.get_int_with_session(session, key, default)

    @staticmethod
    def get_float(key: str, default: Optional[float] = None) -> Optional[float]:
        """Get a setting value as float."""
        flask_session = Settings._get_flask_session()
        if flask_session is not None:
            return Settings.get_float_with_session(flask_session, key, default)
        from .database import get_session
        with get_session() as session:
            return Settings.get_float_with_session(session, key, default)

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """Get a setting value as boolean."""
        flask_session = Settings._get_flask_session()
        if flask_session is not None:
            return Settings.get_bool_with_session(flask_session, key, default)
        from .database import get_session
        with get_session() as session:
            return Settings.get_bool_with_session(session, key, default)
