import pytest
from datetime import datetime, time
from src.waqt.models import TimeEntry
from src.waqt.routes import get_open_entry
from src.waqt import create_app, db

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_manual_entry_confused_as_active_timer(app):
    with app.app_context():
        # Create a "manual" entry with 0 duration (start=end)
        # This simulates a user manually logging a very short task or just entering data
        # without using the timer start/stop flow.
        today = datetime.now().date()
        now_time = datetime.now().time()
        
        entry = TimeEntry(
            date=today,
            start_time=now_time,
            end_time=now_time,
            duration_hours=0.0,
            description="Manual 0-duration entry"
        )
        db.session.add(entry)
        db.session.commit()
        
        # Now check if get_open_entry thinks this is an active timer
        active_entry = get_open_entry()
        
        # The manual entry should NOT be picked up as active
        assert active_entry is None
        
    # Verify that a real active timer IS picked up
    with app.test_client() as client:
        client.post("/api/timer/start", json={"description": "Real Timer"})
        
    with app.app_context():
        active_entry = get_open_entry()
        assert active_entry is not None
        assert active_entry.description == "Real Timer"
        assert active_entry.is_active is True
