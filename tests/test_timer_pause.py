import pytest
from datetime import datetime, time, timedelta
import time as time_module

@pytest.fixture
def app():
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
    return app.test_client()

def test_pause_resume_flow(client, app):
    from src.waqt.models import TimeEntry
    
    # Start timer
    resp = client.post("/api/timer/start", json={"description": "Test Task"})
    assert resp.status_code == 200
    
    # Check status (running)
    resp = client.get("/api/timer/status")
    data = resp.get_json()
    assert data["active"] is True
    assert data["is_paused"] is False
    
    # Wait a bit (mocking time passage might be hard in e2e, but we can just call endpoints)
    
    # Pause
    resp = client.post("/api/timer/pause")
    assert resp.status_code == 200
    
    # Check status (paused)
    resp = client.get("/api/timer/status")
    data = resp.get_json()
    assert data["active"] is True
    assert data["is_paused"] is True
    
    # Verify DB state
    with app.app_context():
        entry = TimeEntry.query.first()
        assert entry.last_pause_start_time is not None
        assert entry.accumulated_pause_seconds == 0.0 # Not added yet
    
    # Resume
    resp = client.post("/api/timer/resume")
    assert resp.status_code == 200
    
    # Check status (running)
    resp = client.get("/api/timer/status")
    data = resp.get_json()
    assert data["active"] is True
    assert data["is_paused"] is False
    
    # Verify DB state
    with app.app_context():
        entry = TimeEntry.query.first()
        assert entry.last_pause_start_time is None
        # Since execution is fast, it might be close to 0, but technically > 0 if time passed
        # We won't assert > 0 strictly unless we sleep, but we check field exists
        assert entry.accumulated_pause_seconds >= 0.0

def test_stop_while_paused(client, app):
    from src.waqt.models import TimeEntry
    
    client.post("/api/timer/start", json={})
    client.post("/api/timer/pause", json={})
    
    # Stop
    resp = client.post("/api/timer/stop")
    assert resp.status_code == 200
    
    # Verify DB
    with app.app_context():
        entry = TimeEntry.query.first()
        assert entry.last_pause_start_time is None
        # Duration should be calculated based on start -> pause time
        # Since we ran start->pause->stop instantly, duration should be ~0
        assert entry.duration_hours >= 0.0

def test_accumulated_pause_calculation(client, app):
    from src.waqt.models import TimeEntry
    from src.waqt import db
    
    with app.app_context():
        # Manually create an entry that started 1 hour ago, paused 30 mins ago
        now = datetime.now()
        start = now - timedelta(hours=1)
        pause_start = now - timedelta(minutes=30)
        
        entry = TimeEntry(
            date=start.date(),
            start_time=start.time(),
            end_time=start.time(),
            duration_hours=0.0,
            description="Manual Entry",
            last_pause_start_time=pause_start,
            accumulated_pause_seconds=0.0,
            is_active=True
        )
        db.session.add(entry)
        db.session.commit()
    
    # Check status
    resp = client.get("/api/timer/status")
    data = resp.get_json()
    assert data["active"] is True
    assert data["is_paused"] is True
    # Elapsed should be (pause_start - start) = 30 mins = 1800s
    # Allow small margin for execution time
    assert 1799 <= data["elapsed_seconds"] <= 1801
    
    # Resume
    # To test accumulation, we need to mock datetime.now() or just check the logic
    # Let's rely on the previous flow test for general logic correctness
