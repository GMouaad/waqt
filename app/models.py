"""Database models for time tracking application."""
from datetime import datetime, timezone
from . import db


class TimeEntry(db.Model):
    """Model for tracking work time entries."""
    
    __tablename__ = 'time_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration_hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<TimeEntry {self.date} - {self.duration_hours}h>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'duration_hours': self.duration_hours,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }


class LeaveDay(db.Model):
    """Model for tracking vacation and sick leave days."""
    
    __tablename__ = 'leave_days'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    leave_type = db.Column(db.String(20), nullable=False)  # 'vacation' or 'sick'
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<LeaveDay {self.date} - {self.leave_type}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'leave_type': self.leave_type,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }


class Settings(db.Model):
    """Model for application settings."""
    
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=False)
    
    def __repr__(self):
        return f'<Settings {self.key}={self.value}>'
    
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
