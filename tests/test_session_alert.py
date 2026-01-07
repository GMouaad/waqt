"""Tests for session alert feature."""

import pytest
import json
from datetime import datetime, timedelta
from src.waqtracker import create_app, db
from src.waqtracker.models import TimeEntry, Settings


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        # Initialize default settings
        Settings.set_setting("alert_on_max_work_session", "false")
        Settings.set_setting("max_work_session_hours", "10")
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


def test_session_alert_disabled_by_default(client, app):
    """Test that session alert is disabled by default."""
    response = client.get("/api/timer/session-alert-check")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["alert"] is False
    assert data["enabled"] is False


def test_session_alert_no_active_timer(client, app):
    """Test that no alert is shown when there's no active timer."""
    with app.app_context():
        Settings.set_setting("alert_on_max_work_session", "true")
    
    response = client.get("/api/timer/session-alert-check")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["alert"] is False
    assert data["enabled"] is True
    assert data["reason"] == "no_active_timer"


def test_session_alert_paused_timer(client, app):
    """Test that no alert is shown when timer is paused."""
    with app.app_context():
        Settings.set_setting("alert_on_max_work_session", "true")
        
        # Create an active entry that's paused
        now = datetime.now()
        entry = TimeEntry(
            date=now.date(),
            start_time=now.time(),
            end_time=now.time(),
            duration_hours=0.0,
            is_active=True,
            last_pause_start_time=now,
            description="Test Work"
        )
        db.session.add(entry)
        db.session.commit()
    
    response = client.get("/api/timer/session-alert-check")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["alert"] is False
    assert data["enabled"] is True
    assert data["reason"] == "timer_paused"


def test_session_alert_under_8_hours(client, app):
    """Test that no alert is shown when session is under 8 hours."""
    with app.app_context():
        Settings.set_setting("alert_on_max_work_session", "true")
        
        # Create an active entry started 7 hours ago
        now = datetime.now()
        start_time = (now - timedelta(hours=7)).time()
        entry = TimeEntry(
            date=now.date(),
            start_time=start_time,
            end_time=now.time(),
            duration_hours=0.0,
            is_active=True,
            description="Test Work"
        )
        db.session.add(entry)
        db.session.commit()
    
    response = client.get("/api/timer/session-alert-check")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["alert"] is False
    assert data["enabled"] is True
    assert "current_hours" in data
    assert data["current_hours"] < 8.0


def test_session_alert_over_8_hours(client, app):
    """Test that alert is shown when session exceeds 8 hours."""
    with app.app_context():
        Settings.set_setting("alert_on_max_work_session", "true")
        Settings.set_setting("max_work_session_hours", "10")
        
        # Create an active entry started 9 hours ago
        now = datetime.now()
        start_dt = now - timedelta(hours=9)
        entry = TimeEntry(
            date=start_dt.date(),
            start_time=start_dt.time(),
            end_time=now.time(),
            duration_hours=0.0,
            is_active=True,
            description="Test Work"
        )
        db.session.add(entry)
        db.session.commit()
    
    response = client.get("/api/timer/session-alert-check")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["alert"] is True
    assert data["enabled"] is True
    assert data["exceeded_standard"] is True
    assert "current_hours" in data
    assert data["current_hours"] > 8.0
    assert data["max_hours"] == 10.0


def test_session_alert_with_pauses(client, app):
    """Test that alert calculation accounts for pauses."""
    with app.app_context():
        Settings.set_setting("alert_on_max_work_session", "true")
        
        # Create an active entry started 10 hours ago with 2.5 hours of pauses
        # So actual work time is 7.5 hours, should not alert
        now = datetime.now()
        start_dt = now - timedelta(hours=10)
        entry = TimeEntry(
            date=start_dt.date(),
            start_time=start_dt.time(),
            end_time=now.time(),
            duration_hours=0.0,
            is_active=True,
            accumulated_pause_seconds=2.5 * 3600,  # 2.5 hours in seconds
            description="Test Work"
        )
        db.session.add(entry)
        db.session.commit()
    
    response = client.get("/api/timer/session-alert-check")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    # Should not alert because actual work time is 7.5 hours (10 - 2.5)
    assert data["alert"] is False
    assert data["enabled"] is True
    assert "current_hours" in data
    assert data["current_hours"] < 8.0


def test_session_alert_custom_threshold(client, app):
    """Test that custom threshold is respected."""
    with app.app_context():
        Settings.set_setting("alert_on_max_work_session", "true")
        Settings.set_setting("max_work_session_hours", "12")
        
        # Create an active entry started 9 hours ago
        now = datetime.now()
        start_dt = now - timedelta(hours=9)
        entry = TimeEntry(
            date=start_dt.date(),
            start_time=start_dt.time(),
            end_time=now.time(),
            duration_hours=0.0,
            is_active=True,
            description="Test Work"
        )
        db.session.add(entry)
        db.session.commit()
    
    response = client.get("/api/timer/session-alert-check")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["alert"] is True
    assert data["enabled"] is True
    assert data["max_hours"] == 12.0
