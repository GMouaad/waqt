"""Unit tests for the CLI interface."""

import pytest
from click.testing import CliRunner
from datetime import date, time
from src.waqtracker import create_app, db
from src.waqtracker.models import TimeEntry, LeaveDay
from src.waqtracker.cli import cli


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
def runner():
    """Create a CLI test runner."""
    return CliRunner()


def test_cli_help(runner):
    """Test that the CLI help message displays correctly."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Waqt - Time tracking CLI" in result.output
    assert "start" in result.output
    assert "end" in result.output
    assert "summary" in result.output
    assert "reference" in result.output


def test_cli_version(runner):
    """Test that the version command works."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "waqt" in result.output
    assert "0.1.0" in result.output


def test_start_command_basic(runner, app):
    """Test basic start command functionality."""
    with app.app_context():
        result = runner.invoke(cli, ["start", "--time", "09:00"])
        assert result.exit_code == 0
        assert "Time tracking started!" in result.output
        assert "09:00" in result.output

        # Verify entry was created in database
        entry = TimeEntry.query.first()
        assert entry is not None
        assert entry.start_time == time(9, 0)
        assert entry.duration_hours == 0.0  # Open entry marker


def test_start_command_with_description(runner, app):
    """Test start command with custom description."""
    with app.app_context():
        result = runner.invoke(
            cli,
            ["start", "--time", "09:00", "--description", "Morning work session"],
        )
        assert result.exit_code == 0
        assert "Time tracking started!" in result.output

        entry = TimeEntry.query.first()
        assert entry is not None
        assert entry.description == "Morning work session"


def test_start_command_with_date(runner, app):
    """Test start command with specific date."""
    with app.app_context():
        result = runner.invoke(
            cli, ["start", "--date", "2024-01-15", "--time", "09:00"]
        )
        assert result.exit_code == 0
        assert "2024-01-15" in result.output

        entry = TimeEntry.query.first()
        assert entry is not None
        assert entry.date == date(2024, 1, 15)


def test_start_command_invalid_time_format(runner, app):
    """Test start command with invalid time format."""
    with app.app_context():
        result = runner.invoke(cli, ["start", "--time", "invalid"])
        assert result.exit_code == 0
        assert "Invalid time format" in result.output


def test_start_command_invalid_date_format(runner, app):
    """Test start command with invalid date format."""
    with app.app_context():
        result = runner.invoke(cli, ["start", "--date", "invalid"])
        assert result.exit_code == 0
        assert "Invalid date format" in result.output


def test_start_command_duplicate(runner, app):
    """Test start command when entry already open."""
    with app.app_context():
        # Create first entry
        runner.invoke(cli, ["start", "--time", "09:00"])

        # Try to create another one
        result = runner.invoke(cli, ["start", "--time", "10:00"])
        assert result.exit_code == 0
        assert "already an open time entry" in result.output


def test_end_command_basic(runner, app):
    """Test basic end command functionality."""
    with app.app_context():
        # Start tracking
        runner.invoke(cli, ["start", "--time", "09:00"])

        # End tracking
        result = runner.invoke(cli, ["end", "--time", "17:00"])
        assert result.exit_code == 0
        assert "Time tracking ended!" in result.output
        assert "Duration:" in result.output

        # Verify entry was updated
        entry = TimeEntry.query.first()
        assert entry is not None
        assert entry.end_time == time(17, 0)
        assert entry.duration_hours == 8.0


def test_end_command_without_start(runner, app):
    """Test end command when no entry exists."""
    with app.app_context():
        result = runner.invoke(cli, ["end", "--time", "17:00"])
        assert result.exit_code == 0
        assert "No open time entry found" in result.output


def test_end_command_with_date(runner, app):
    """Test end command with specific date."""
    with app.app_context():
        # Start tracking
        runner.invoke(cli, ["start", "--date", "2024-01-15", "--time", "09:00"])

        # End tracking for the same date
        result = runner.invoke(cli, ["end", "--date", "2024-01-15", "--time", "17:00"])
        assert result.exit_code == 0
        assert "Time tracking ended!" in result.output


def test_summary_command_week(runner, app):
    """Test weekly summary command."""
    with app.app_context():
        # Create some test entries for the current date
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

        result = runner.invoke(cli, ["summary", "--period", "week"])
        assert result.exit_code == 0
        assert "Week Summary" in result.output
        assert "Total Hours" in result.output
        assert "Working Days" in result.output


def test_summary_command_month(runner, app):
    """Test monthly summary command."""
    with app.app_context():
        # Create some test entries for the current month
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

        result = runner.invoke(cli, ["summary", "--period", "month"])
        assert result.exit_code == 0
        assert "Month Summary" in result.output
        assert "Total Hours" in result.output


def test_summary_command_no_entries(runner, app):
    """Test summary command when no entries exist."""
    with app.app_context():
        result = runner.invoke(cli, ["summary"])
        assert result.exit_code == 0
        assert "No time entries found" in result.output


def test_sum_command_alias(runner, app):
    """Test that 'sum' is an alias for 'summary'."""
    with app.app_context():
        result = runner.invoke(cli, ["sum", "--period", "week"])
        assert result.exit_code == 0
        assert "Week Summary" in result.output


def test_reference_command(runner, app):
    """Test reference command (placeholder)."""
    with app.app_context():
        result = runner.invoke(cli, ["reference"])
        assert result.exit_code == 0
        assert "Waqt Reference" in result.output
        assert "placeholder" in result.output


def test_summary_with_leave_days(runner, app):
    """Test monthly summary with leave days."""
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

        result = runner.invoke(
            cli, ["summary", "--period", "month", "--date", "2024-01-15"]
        )
        assert result.exit_code == 0
        assert "Month Summary" in result.output
        assert "Leave Days" in result.output


def test_full_workflow(runner, app):
    """Test complete workflow: start -> end -> summary."""
    with app.app_context():
        # Start tracking
        result1 = runner.invoke(cli, ["start", "--time", "09:00"])
        assert result1.exit_code == 0
        assert "Time tracking started!" in result1.output

        # End tracking
        result2 = runner.invoke(cli, ["end", "--time", "17:00"])
        assert result2.exit_code == 0
        assert "Time tracking ended!" in result2.output
        assert "8:00" in result2.output  # Duration

        # View summary
        result3 = runner.invoke(cli, ["summary"])
        assert result3.exit_code == 0
        assert "Week Summary" in result3.output
        assert "Total Hours" in result3.output
