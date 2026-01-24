"""Unit tests for the MCP server interface."""

import pytest
from datetime import date, time


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


def test_start_basic(app):
    """Test basic start functionality via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt.mcp_server import start

    with app.app_context():
        result = start(time="09:00", description="Test work")

        assert result["status"] == "success"
        assert "Time tracking started!" in result["message"]
        assert result["entry"]["start_time"] == "09:00"
        assert result["entry"]["description"] == "Test work"

        # Verify entry was created in database
        entry = TimeEntry.query.first()
        assert entry is not None
        assert entry.start_time == time(9, 0)
        assert entry.duration_hours == 0.0


def test_start_with_date(app):
    """Test start with specific date via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt.mcp_server import start

    with app.app_context():
        result = start(date="2024-01-15", time="09:00")

        assert result["status"] == "success"
        assert result["entry"]["date"] == "2024-01-15"

        entry = TimeEntry.query.first()
        assert entry.date == date(2024, 1, 15)


def test_start_invalid_time_format(app):
    """Test start with invalid time format."""
    from src.waqt.mcp_server import start

    with app.app_context():
        result = start(time="invalid")

        assert result["status"] == "error"
        assert "Invalid time format" in result["message"]


def test_start_invalid_date_format(app):
    """Test start with invalid date format."""
    from src.waqt.mcp_server import start

    with app.app_context():
        result = start(date="invalid")

        assert result["status"] == "error"
        assert "Invalid date format" in result["message"]


def test_start_duplicate_entry(app):
    """Test start when entry already open."""
    from src.waqt.mcp_server import start

    with app.app_context():
        # Create first entry
        start(time="09:00")

        # Try to create another one
        result = start(time="10:00")

        assert result["status"] == "error"
        assert "There is already an active timer" in result["message"]


def test_end_basic(app):
    """Test basic end functionality via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt.mcp_server import start, end

    with app.app_context():
        # Start tracking
        start(time="09:00")

        # End tracking
        result = end(time="17:00")

        assert result["status"] == "success"
        assert "Time tracking ended!" in result["message"]
        assert result["entry"]["start_time"] == "09:00"
        assert result["entry"]["end_time"] == "17:00"
        assert result["entry"]["duration"] == "8:00"
        assert result["entry"]["duration_hours"] == 8.0

        # Verify entry was updated
        entry = TimeEntry.query.first()
        assert entry.end_time == time(17, 0)
        assert entry.duration_hours == 8.0


def test_end_without_start(app):
    """Test end when no open entry exists."""
    from src.waqt.mcp_server import end

    with app.app_context():
        result = end(time="17:00")

        assert result["status"] == "error"
        assert "No active timer found" in result["message"]


def test_end_with_date(app):
    """Test end with specific date."""
    from src.waqt.mcp_server import start, end

    with app.app_context():
        # Start tracking
        start(date="2024-01-15", time="09:00")

        # End tracking for the same date
        result = end(date="2024-01-15", time="17:00")

        assert result["status"] == "success"
        assert result["entry"]["date"] == "2024-01-15"


def test_end_invalid_time_format(app):
    """Test end with invalid time format."""
    from src.waqt.mcp_server import end

    with app.app_context():
        result = end(time="invalid")

        assert result["status"] == "error"
        assert "Invalid time format" in result["message"]


def test_summary_week(app):
    """Test weekly summary via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import summary

    with app.app_context():
        # Create test entries for the current date
        today = date.today()
        entry1 = TimeEntry(
            date=today,
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work 1",
        )
        entry2 = TimeEntry(
            date=today,
            start_time=time(9, 0),
            end_time=time(18, 0),
            duration_hours=9.0,
            description="Test work 2",
        )
        db.session.add(entry1)
        db.session.add(entry2)
        db.session.commit()

        result = summary(period="week")

        assert result["status"] == "success"
        assert result["period"] == "Week"
        assert "start_date" in result
        assert "end_date" in result
        assert result["statistics"]["total_hours"] == 17.0
        assert result["statistics"]["working_days"] == 1
        assert result["has_entries"] is True
        assert len(result["recent_entries"]) == 2


def test_summary_month(app):
    """Test monthly summary via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import summary

    with app.app_context():
        # Create test entry
        today = date.today()
        entry = TimeEntry(
            date=today,
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        db.session.add(entry)
        db.session.commit()

        result = summary(period="month")

        assert result["status"] == "success"
        assert result["period"] == "Month"
        assert result["statistics"]["total_hours"] == 8.0
        assert "expected_hours" in result["statistics"]
        assert "vacation_days" in result["statistics"]
        assert "sick_days" in result["statistics"]


def test_summary_invalid_period(app):
    """Test summary with invalid period."""
    from src.waqt.mcp_server import summary

    with app.app_context():
        result = summary(period="invalid")

        assert result["status"] == "error"
        assert "Invalid period" in result["message"]


def test_summary_no_entries(app):
    """Test summary when no entries exist."""
    from src.waqt.mcp_server import summary

    with app.app_context():
        result = summary(period="week")

        assert result["status"] == "success"
        assert result["has_entries"] is False
        assert len(result["recent_entries"]) == 0


def test_summary_with_date(app):
    """Test summary with specific date."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import summary

    with app.app_context():
        # Create test entry
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        db.session.add(entry)
        db.session.commit()

        result = summary(period="week", date="2024-01-15")

        assert result["status"] == "success"
        assert "2024-01-15" in result["start_date"]


def test_list_entries_week(app):
    """Test list entries for a week via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import list_entries

    with app.app_context():
        # Create test entries
        today = date.today()
        for i in range(3):
            entry = TimeEntry(
                date=today,
                start_time=time(9, 0),
                end_time=time(17, 0),
                duration_hours=8.0,
                description=f"Test work {i+1}",
            )
            db.session.add(entry)
        db.session.commit()

        result = list_entries(period="week")

        assert result["status"] == "success"
        assert result["period"] == "week"
        assert result["count"] == 3
        assert len(result["entries"]) == 3
        assert "start_date" in result
        assert "end_date" in result


def test_list_entries_month(app):
    """Test list entries for a month via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import list_entries

    with app.app_context():
        # Create test entry
        today = date.today()
        entry = TimeEntry(
            date=today,
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        db.session.add(entry)
        db.session.commit()

        result = list_entries(period="month")

        assert result["status"] == "success"
        assert result["period"] == "month"
        assert result["count"] == 1


def test_list_entries_all(app):
    """Test list all entries via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import list_entries

    with app.app_context():
        # Create test entries
        today = date.today()
        for i in range(5):
            entry = TimeEntry(
                date=today,
                start_time=time(9, 0),
                end_time=time(17, 0),
                duration_hours=8.0,
                description=f"Test work {i+1}",
            )
            db.session.add(entry)
        db.session.commit()

        result = list_entries(period="all")

        assert result["status"] == "success"
        assert result["period"] == "all"
        assert result["count"] == 5


def test_list_entries_with_limit(app):
    """Test list entries with limit via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import list_entries

    with app.app_context():
        # Create test entries
        today = date.today()
        for i in range(10):
            entry = TimeEntry(
                date=today,
                start_time=time(9, 0),
                end_time=time(17, 0),
                duration_hours=8.0,
                description=f"Test work {i+1}",
            )
            db.session.add(entry)
        db.session.commit()

        result = list_entries(period="all", limit=3)

        assert result["status"] == "success"
        assert result["count"] == 3
        assert len(result["entries"]) == 3


def test_list_entries_invalid_period(app):
    """Test list entries with invalid period."""
    from src.waqt.mcp_server import list_entries

    with app.app_context():
        result = list_entries(period="invalid")

        assert result["status"] == "error"
        assert "Invalid period" in result["message"]


def test_list_entries_details(app):
    """Test that list entries includes all details."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import list_entries

    with app.app_context():
        # Create test entry
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        db.session.add(entry)
        db.session.commit()

        result = list_entries(period="all")

        assert result["status"] == "success"
        entry_data = result["entries"][0]
        assert entry_data["date"] == "2024-01-15"
        assert entry_data["day_of_week"] == "Monday"
        assert entry_data["start_time"] == "09:00"
        assert entry_data["end_time"] == "17:00"
        assert entry_data["duration"] == "8:00"
        assert entry_data["duration_hours"] == 8.0
        assert entry_data["description"] == "Test work"
        assert entry_data["is_open"] is False


def test_export_entries_basic(app):
    """Test basic export via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import export_entries

    with app.app_context():
        # Create test entries
        today = date.today()
        for i in range(3):
            entry = TimeEntry(
                date=today,
                start_time=time(9, 0),
                end_time=time(17, 0),
                duration_hours=8.0,
                description=f"Test work {i+1}",
            )
            db.session.add(entry)
        db.session.commit()

        result = export_entries(period="all")

        assert result["status"] == "success"
        assert "Export successful!" in result["message"]
        assert result["count"] == 3
        assert result["total_hours"] == 24.0
        assert result["format"] == "csv"
        assert "csv_content" in result
        assert len(result["csv_content"]) > 0
        assert "Date" in result["csv_content"]


def test_export_entries_week(app):
    """Test export for a week via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import export_entries

    with app.app_context():
        # Create test entry
        today = date.today()
        entry = TimeEntry(
            date=today,
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        db.session.add(entry)
        db.session.commit()

        result = export_entries(period="week")

        assert result["status"] == "success"
        assert result["count"] == 1
        assert "start_date" in result
        assert "end_date" in result


def test_export_entries_month(app):
    """Test export for a month via MCP."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import export_entries

    with app.app_context():
        # Create test entry
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        db.session.add(entry)
        db.session.commit()

        result = export_entries(period="month", date="2024-01-15")

        assert result["status"] == "success"
        assert "2024-01" in result["period"]


def test_export_entries_no_entries(app):
    """Test export when no entries exist."""
    from src.waqt.mcp_server import export_entries

    with app.app_context():
        result = export_entries(period="all")

        assert result["status"] == "success"
        assert "No time entries found" in result["message"]
        assert result["count"] == 0
        assert result["csv_content"] == ""


def test_export_entries_json_format(app):
    """Test export with JSON format."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import export_entries
    import json

    with app.app_context():
        # Create test entries
        today = date.today()
        entry = TimeEntry(
            date=today,
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        db.session.add(entry)
        db.session.commit()

        result = export_entries(period="all", export_format="json")

        assert result["status"] == "success"
        assert result["format"] == "json"
        assert "content" in result

        # Verify JSON content
        data = json.loads(result["content"])
        assert "entries" in data
        assert len(data["entries"]) == 1
        assert data["entries"][0]["description"] == "Test work"


def test_export_entries_invalid_format(app):
    """Test export with invalid format."""
    from src.waqt.mcp_server import export_entries

    with app.app_context():
        result = export_entries(export_format="xml")

        assert result["status"] == "error"
        assert "Unsupported format" in result["message"]


def test_export_entries_invalid_period(app):
    """Test export with invalid period."""
    from src.waqt.mcp_server import export_entries

    with app.app_context():
        result = export_entries(period="invalid")

        assert result["status"] == "error"
        assert "Invalid period" in result["message"]


def test_export_entries_csv_content(app):
    """Test that export CSV content is properly formatted."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import export_entries

    with app.app_context():
        # Create test entry
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        db.session.add(entry)
        db.session.commit()

        result = export_entries(period="all")

        csv_content = result["csv_content"]
        assert "2024-01-15" in csv_content
        assert "Monday" in csv_content
        assert "09:00" in csv_content
        assert "17:00" in csv_content
        assert "Test work" in csv_content
        assert "Summary Statistics" in csv_content


def test_full_workflow(app):
    """Test complete workflow via MCP: start -> end -> summary -> list -> export."""
    from src.waqt.mcp_server import start, end, summary, list_entries, export_entries

    with app.app_context():
        # Start tracking
        result1 = start(time="09:00", description="Morning work")
        assert result1["status"] == "success"

        # End tracking
        result2 = end(time="17:00")
        assert result2["status"] == "success"
        assert result2["entry"]["duration"] == "8:00"

        # Get summary
        result3 = summary(period="week")
        assert result3["status"] == "success"
        assert result3["statistics"]["total_hours"] == 8.0

        # List entries
        result4 = list_entries(period="all")
        assert result4["status"] == "success"
        assert result4["count"] == 1

        # Export entries
        result5 = export_entries(period="all")
        assert result5["status"] == "success"
        assert result5["count"] == 1
        assert "Morning work" in result5["csv_content"]


def test_overtime_detection(app):
    """Test that overtime is properly detected in summary."""
    with app.app_context():
        # Create multiple entries in the same week to exceed 40 hours
        from datetime import timedelta
        from src.waqt.utils import get_week_bounds
        from src.waqt.models import TimeEntry
        from src.waqt import db
        from src.waqt.mcp_server import summary

        today = date.today()
        week_start, week_end = get_week_bounds(today)

        # Add 5 days of 9 hours each = 45 hours total, 5 hours overtime
        # Make sure they're all in the current week
        for i in range(5):
            entry_date = week_start + timedelta(days=i)
            entry = TimeEntry(
                date=entry_date,
                start_time=time(9, 0),
                end_time=time(18, 0),
                duration_hours=9.0,
                description=f"Overtime work day {i+1}",
            )
            db.session.add(entry)
        db.session.commit()

        result = summary(period="week")

        assert result["status"] == "success"
        assert result["statistics"]["total_hours"] == 45.0
        assert result["statistics"]["overtime"] == 5.0
        # Check that at least one entry has overtime marker (9 hours > 8)
        assert any(entry["has_overtime"] for entry in result["recent_entries"])


def test_monthly_summary_with_leave_days(app):
    """Test monthly summary with leave days."""
    from src.waqt.models import TimeEntry, LeaveDay
    from src.waqt import db
    from src.waqt.mcp_server import summary

    with app.app_context():
        # Create test entry
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work",
        )
        # Create leave days
        leave1 = LeaveDay(
            date=date(2024, 1, 16), leave_type="vacation", description="Vacation"
        )
        leave2 = LeaveDay(date=date(2024, 1, 17), leave_type="sick", description="Sick")
        db.session.add(entry)
        db.session.add(leave1)
        db.session.add(leave2)
        db.session.commit()

        result = summary(period="month", date="2024-01-15")

        assert result["status"] == "success"
        assert result["statistics"]["vacation_days"] == 1
        assert result["statistics"]["sick_days"] == 1
