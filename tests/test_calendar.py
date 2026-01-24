"""Tests for calendar functionality."""

import pytest
from datetime import date


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


def test_generate_calendar_data(app):
    """Test calendar data generation."""
    from src.waqt.utils import generate_calendar_data

    with app.app_context():
        # Generate calendar for January 2026
        calendar_data = generate_calendar_data(2026, 1)

        # Check basic structure
        assert "weeks" in calendar_data
        assert "month_name" in calendar_data
        assert "year" in calendar_data
        assert "month" in calendar_data
        assert "prev_month" in calendar_data
        assert "next_month" in calendar_data

        # Check month name
        assert calendar_data["month_name"] == "January"
        assert calendar_data["year"] == 2026
        assert calendar_data["month"] == 1

        # Check navigation
        assert calendar_data["prev_month"]["year"] == 2025
        assert calendar_data["prev_month"]["month"] == 12
        assert calendar_data["next_month"]["year"] == 2026
        assert calendar_data["next_month"]["month"] == 2

        # Check that we have weeks
        assert len(calendar_data["weeks"]) > 0

        # Each week should have 7 days
        for week in calendar_data["weeks"]:
            assert len(week) == 7


def test_calendar_with_entries(app):
    """Test calendar with time entries."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.utils import generate_calendar_data

    with app.app_context():
        # Add a time entry for January 15, 2026
        from datetime import time as datetime_time

        entry = TimeEntry(
            date=date(2026, 1, 15),
            start_time=datetime_time(9, 0),
            end_time=datetime_time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        db.session.add(entry)
        db.session.commit()

        # Generate calendar
        calendar_data = generate_calendar_data(2026, 1)

        # Find the day with entry
        found_day = None
        for week in calendar_data["weeks"]:
            for day in week:
                if day["is_current_month"] and day["day"] == 15:
                    found_day = day
                    break
            if found_day:
                break

        assert found_day is not None
        assert found_day["has_entry"] is True
        assert found_day["total_hours"] == 8.0
        assert found_day["entry_count"] == 1


def test_calendar_with_leave(app):
    """Test calendar with leave days."""
    from src.waqt.models import LeaveDay
    from src.waqt import db
    from src.waqt.utils import generate_calendar_data

    with app.app_context():
        # Add a vacation day for January 20, 2026
        leave = LeaveDay(
            date=date(2026, 1, 20), leave_type="vacation", description="Holiday"
        )
        db.session.add(leave)
        db.session.commit()

        # Generate calendar
        calendar_data = generate_calendar_data(2026, 1)

        # Find the day with leave
        found_day = None
        for week in calendar_data["weeks"]:
            for day in week:
                if day["is_current_month"] and day["day"] == 20:
                    found_day = day
                    break
            if found_day:
                break

        assert found_day is not None
        assert found_day["has_leave"] is True
        assert found_day["leave_type"] == "vacation"


def test_calendar_api_endpoint(client, app):
    """Test the calendar day details API endpoint."""
    from src.waqt.models import TimeEntry
    from src.waqt import db

    with app.app_context():
        from datetime import time as datetime_time

        # Add a time entry
        entry = TimeEntry(
            date=date(2026, 1, 15),
            start_time=datetime_time(9, 0),
            end_time=datetime_time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        db.session.add(entry)
        db.session.commit()

        # Test API endpoint
        response = client.get("/api/calendar/day/2026-01-15")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["date"] == "2026-01-15"
        assert data["has_entry"] is True
        assert data["entry_count"] == 1
        assert data["total_hours"] == 8.0


def test_calendar_api_endpoint_no_entry(client, app):
    """Test the calendar day details API endpoint for day without entries."""
    with app.app_context():
        # Test API endpoint for day without entries
        response = client.get("/api/calendar/day/2026-01-15")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["date"] == "2026-01-15"
        assert data["has_entry"] is False
        assert data["entry_count"] == 0
        assert data["total_hours"] == 0


def test_calendar_api_endpoint_invalid_date(client):
    """Test the calendar day details API endpoint with invalid date."""
    response = client.get("/api/calendar/day/invalid-date")
    assert response.status_code == 400

    data = response.get_json()
    assert data["success"] is False


def test_dashboard_includes_calendar(client):
    """Test that dashboard includes calendar data."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"calendar-section" in response.data
    assert b"Monthly Overview" in response.data
    assert b"calendar-grid" in response.data


def test_calendar_api_endpoint_out_of_range_date(client):
    """Test the calendar day details API endpoint with date out of valid range."""
    # Test year too far in the past
    response = client.get("/api/calendar/day/1800-01-01")
    assert response.status_code == 400

    data = response.get_json()
    assert data["success"] is False
    assert "out of valid range" in data["message"]

    # Test year too far in the future
    response = client.get("/api/calendar/day/2200-01-01")
    assert response.status_code == 400

    data = response.get_json()
    assert data["success"] is False
    assert "out of valid range" in data["message"]
