"""Unit tests for the time tracker application."""

import pytest
from datetime import time, date


@pytest.fixture
def app():
    """Create and configure a test app instance."""
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
    """Create a test client for the app."""
    return app.test_client()


def test_app_creation(app):
    """Test that the app is created successfully."""
    assert app is not None
    assert app.config["TESTING"] is True


def test_calculate_duration():
    """Test duration calculation between two times."""
    from src.waqt.utils import calculate_duration

    start = time(9, 0)
    end = time(17, 0)
    duration = calculate_duration(start, end)
    assert duration == 8.0

    # Test with minutes
    start = time(9, 30)
    end = time(17, 45)
    duration = calculate_duration(start, end)
    assert duration == 8.25


def test_calculate_daily_overtime():
    """Test overtime calculation."""
    from src.waqt.utils import calculate_daily_overtime

    # No overtime
    overtime = calculate_daily_overtime(8.0, standard_hours=8.0)
    assert overtime == 0.0

    # With overtime
    overtime = calculate_daily_overtime(10.0, standard_hours=8.0)
    assert overtime == 2.0

    # Under standard hours
    overtime = calculate_daily_overtime(6.0, standard_hours=8.0)
    assert overtime == 0.0


def test_get_week_bounds():
    """Test getting week boundaries."""
    from src.waqt.utils import get_week_bounds

    # Monday
    test_date = date(2024, 1, 1)  # This is a Monday
    start, end = get_week_bounds(test_date)
    assert start.weekday() == 0  # Monday
    assert end.weekday() == 6  # Sunday
    assert (end - start).days == 6


def test_index_route(client):
    """Test the index/dashboard route."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_time_entry_form(client):
    """Test the time entry form page."""
    response = client.get("/time-entry")
    assert response.status_code == 200
    assert b"Add Time Entry" in response.data


def test_reports_page(client):
    """Test the reports page."""
    response = client.get("/reports")
    assert response.status_code == 200
    assert b"Reports" in response.data


def test_leave_page(client):
    """Test the leave management page."""
    response = client.get("/leave")
    assert response.status_code == 200
    assert b"Leave Management" in response.data


def test_create_time_entry(app):
    """Test creating a time entry in the database."""
    from src.waqt.models import TimeEntry
    from src.waqt import db

    with app.app_context():
        entry = TimeEntry(
            date=date(2024, 1, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        db.session.add(entry)
        db.session.commit()

        # Verify it was saved
        saved_entry = TimeEntry.query.first()
        assert saved_entry is not None
        assert saved_entry.description == "Test work"
        assert saved_entry.duration_hours == 8.0


def test_create_leave_day(app):
    """Test creating a leave day in the database."""
    from src.waqt.models import LeaveDay
    from src.waqt import db

    with app.app_context():
        leave = LeaveDay(
            date=date(2024, 1, 15), leave_type="vacation", description="Family vacation"
        )
        db.session.add(leave)
        db.session.commit()

        # Verify it was saved
        saved_leave = LeaveDay.query.first()
        assert saved_leave is not None
        assert saved_leave.leave_type == "vacation"
        assert saved_leave.description == "Family vacation"


def test_settings_model(app):
    """Test the settings model."""
    from src.waqt.models import Settings

    with app.app_context():
        # Set a setting
        Settings.set_setting("test_key", "test_value")

        # Get the setting
        value = Settings.get_setting("test_key")
        assert value == "test_value"

        # Get non-existent setting with default
        value = Settings.get_setting("nonexistent", "default")
        assert value == "default"


def test_edit_time_entry_page(client, app):
    """Test the edit time entry page."""
    from src.waqt.models import TimeEntry
    from src.waqt import db

    with app.app_context():
        # Create a test entry
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
            is_active=False,
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    # Access the edit page
    response = client.get(f"/time-entry/{entry_id}/edit")
    assert response.status_code == 200
    assert b"Edit Time Entry" in response.data
    assert b"Test work" in response.data


def test_edit_time_entry_post(client, app):
    """Test editing a time entry via POST."""
    from src.waqt.models import TimeEntry
    from src.waqt import db

    with app.app_context():
        # Create a test entry
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Original description",
            is_active=False,
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    # Edit the entry
    response = client.post(
        f"/time-entry/{entry_id}/edit",
        data={
            "start_time": "08:30",
            "end_time": "17:30",
            "description": "Updated description",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Time entry updated successfully!" in response.data

    # Verify changes in database
    with app.app_context():
        updated_entry = db.session.get(TimeEntry, entry_id)
        assert updated_entry.start_time == time(8, 30)
        assert updated_entry.end_time == time(17, 30)
        assert updated_entry.duration_hours == 9.0
        assert updated_entry.description == "Updated description"


def test_prevent_duplicate_entries(client, app):
    """Test that creating a duplicate entry for the same date is prevented."""
    from src.waqt.models import TimeEntry
    from src.waqt import db

    with app.app_context():
        # Create a test entry
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="First entry",
            is_active=False,
        )
        db.session.add(entry)
        db.session.commit()

    # Try to create another entry for the same date
    response = client.post(
        "/time-entry",
        data={
            "date": "2024-01-15",
            "start_time": "10:00",
            "end_time": "18:00",
            "description": "Duplicate entry",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"An entry already exists" in response.data
    assert b"Only one entry per day is allowed" in response.data

    # Verify only one entry exists
    with app.app_context():
        entries = TimeEntry.query.filter_by(date=date(2024, 1, 15)).all()
        assert len(entries) == 1
        assert entries[0].description == "First entry"


def test_edit_time_entry_invalid_time(client, app):
    """Test editing a time entry with times that would result in very long duration."""
    from src.waqt.models import TimeEntry
    from src.waqt import db

    with app.app_context():
        # Create a test entry
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
            is_active=False,
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    # Edit with times that cross midnight (17:00 to 09:00 = 16 hours)
    # This should actually succeed because calculate_duration handles midnight crossing
    response = client.post(
        f"/time-entry/{entry_id}/edit",
        data={
            "start_time": "17:00",
            "end_time": "09:00",
            "description": "Night shift",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Time entry updated successfully!" in response.data

    # Verify entry was updated with 16 hour duration (crossing midnight)
    with app.app_context():
        updated_entry = db.session.get(TimeEntry, entry_id)
        assert updated_entry.start_time == time(17, 0)
        assert updated_entry.end_time == time(9, 0)
        assert updated_entry.duration_hours == 16.0  # 17:00 to 09:00 next day


def test_edit_active_timer_prevented(client, app):
    """Test that editing an active timer is prevented."""
    from src.waqt.models import TimeEntry
    from src.waqt import db

    with app.app_context():
        # Create an active entry (timer running)
        entry = TimeEntry(
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(9, 0),
            duration_hours=0.0,
            description="Active work",
            is_active=True,
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    # Try to access the edit page
    response = client.get(f"/time-entry/{entry_id}/edit", follow_redirects=True)
    assert response.status_code == 200
    assert b"Cannot edit an active timer" in response.data
    assert b"Please stop the timer before editing" in response.data

    # Verify we're redirected to dashboard
    assert b"Dashboard" in response.data

    # Verify entry was not changed
    with app.app_context():
        unchanged_entry = db.session.get(TimeEntry, entry_id)
        assert unchanged_entry.is_active is True
        assert unchanged_entry.start_time == time(9, 0)
