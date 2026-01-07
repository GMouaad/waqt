import pytest
from src.waqtracker.models import TimeEntry
from src.waqtracker import create_app, db

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

@pytest.fixture
def client(app):
    return app.test_client()

def test_start_timer_with_empty_description(client, app):
    # Test with empty string
    resp = client.post("/api/timer/start", json={"description": ""})
    assert resp.status_code == 200
    
    with app.app_context():
        entry = TimeEntry.query.first()
        assert entry.description == "Work"

def test_start_timer_with_whitespace_description(client, app):
    # Test with whitespace only
    resp = client.post("/api/timer/start", json={"description": "   "})
    assert resp.status_code == 200
    
    with app.app_context():
        # This will fail before fix if it currently allows whitespace
        entry = TimeEntry.query.first()
        assert entry.description == "Work"

def test_start_timer_with_no_description(client, app):
    # Test with no description field
    resp = client.post("/api/timer/start", json={})
    assert resp.status_code == 200
    
    with app.app_context():
        entry = TimeEntry.query.first()
        assert entry.description == "Work"
