"""Tests for the Timer API."""

import pytest
import json
from datetime import datetime, time, date
from src.waqt import create_app, db
from src.waqt.models import TimeEntry

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

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

def test_timer_lifecycle(client, app):
    """Test start, status, and stop timer lifecycle."""
    
    # 1. Check initial status (inactive)
    response = client.get("/api/timer/status")
    data = json.loads(response.data)
    assert data["active"] is False
    
    # 2. Start Timer
    response = client.post("/api/timer/start", json={"description": "Test Work"})
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["success"] is True
    
    # 3. Check status (active)
    response = client.get("/api/timer/status")
    data = json.loads(response.data)
    assert data["active"] is True
    assert data["description"] == "Test Work"
    assert "start_time" in data
    
    # 4. Stop Timer
    # Wait a bit or mock time? For simple integration test, immediate stop is fine.
    response = client.post("/api/timer/stop")
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["success"] is True
    assert "duration" in data
    
    # 5. Check status (inactive)
    response = client.get("/api/timer/status")
    data = json.loads(response.data)
    assert data["active"] is False

    # 6. Verify entry in DB
    with app.app_context():
        entry = TimeEntry.query.first()
        assert entry is not None
        assert entry.description == "Test Work"
        assert entry.duration_hours >= 0.0

def test_start_timer_when_already_active(client):
    """Test starting a timer when one is already active."""
    client.post("/api/timer/start", json={"description": "First"})
    response = client.post("/api/timer/start", json={"description": "Second"})
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["success"] is False
    assert "already running" in data["message"]

def test_stop_timer_when_none_active(client):
    """Test stopping a timer when none is active."""
    response = client.post("/api/timer/stop")
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["success"] is False
    assert "No active timer" in data["message"]
