"""Tests for multi-day leave functionality."""

import pytest
from datetime import date
from src.waqt import create_app, db
from src.waqt.models import LeaveDay, Settings
from src.waqt.utils import (
    is_weekend,
    get_date_range,
    get_working_days_in_range,
    calculate_leave_hours,
)


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        # Set standard hours per day for testing
        Settings.set_setting("standard_hours_per_day", "8.0")
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


class TestWeekendDetection:
    """Tests for weekend detection utility."""

    def test_is_weekend_saturday(self):
        """Test that Saturday is detected as weekend."""
        # 2026-01-10 is a Saturday
        saturday = date(2026, 1, 10)
        assert is_weekend(saturday) is True

    def test_is_weekend_sunday(self):
        """Test that Sunday is detected as weekend."""
        # 2026-01-11 is a Sunday
        sunday = date(2026, 1, 11)
        assert is_weekend(sunday) is True

    def test_is_weekend_monday(self):
        """Test that Monday is not detected as weekend."""
        # 2026-01-12 is a Monday
        monday = date(2026, 1, 12)
        assert is_weekend(monday) is False

    def test_is_weekend_friday(self):
        """Test that Friday is not detected as weekend."""
        # 2026-01-09 is a Friday
        friday = date(2026, 1, 9)
        assert is_weekend(friday) is False


class TestDateRange:
    """Tests for date range generation."""

    def test_get_date_range_single_day(self):
        """Test date range for a single day."""
        start = date(2026, 1, 13)
        end = date(2026, 1, 13)
        result = get_date_range(start, end)
        assert len(result) == 1
        assert result[0] == start

    def test_get_date_range_week(self):
        """Test date range for a week."""
        # Monday to Sunday
        start = date(2026, 1, 12)  # Monday
        end = date(2026, 1, 18)  # Sunday
        result = get_date_range(start, end)
        assert len(result) == 7
        assert result[0] == start
        assert result[-1] == end

    def test_get_date_range_invalid(self):
        """Test date range with end before start."""
        start = date(2026, 1, 20)
        end = date(2026, 1, 10)
        result = get_date_range(start, end)
        assert len(result) == 0

    def test_get_date_range_month_crossing(self):
        """Test date range crossing month boundary."""
        start = date(2026, 1, 28)
        end = date(2026, 2, 3)
        result = get_date_range(start, end)
        assert len(result) == 7
        assert result[0] == start
        assert result[-1] == end


class TestWorkingDays:
    """Tests for working days calculation."""

    def test_get_working_days_full_week(self):
        """Test working days for a full week (Mon-Sun)."""
        # 2026-01-12 (Monday) to 2026-01-18 (Sunday)
        start = date(2026, 1, 12)
        end = date(2026, 1, 18)
        working_days = get_working_days_in_range(start, end)
        assert len(working_days) == 5  # Mon-Fri only

    def test_get_working_days_weekdays_only(self):
        """Test working days for weekdays only (Mon-Fri)."""
        # 2026-01-12 (Monday) to 2026-01-16 (Friday)
        start = date(2026, 1, 12)
        end = date(2026, 1, 16)
        working_days = get_working_days_in_range(start, end)
        assert len(working_days) == 5

    def test_get_working_days_weekend_only(self):
        """Test working days for weekend only."""
        # 2026-01-17 (Saturday) to 2026-01-18 (Sunday)
        start = date(2026, 1, 17)
        end = date(2026, 1, 18)
        working_days = get_working_days_in_range(start, end)
        assert len(working_days) == 0

    def test_get_working_days_two_weeks(self):
        """Test working days for two full weeks."""
        # 2026-01-12 (Monday) to 2026-01-25 (Sunday)
        start = date(2026, 1, 12)
        end = date(2026, 1, 25)
        working_days = get_working_days_in_range(start, end)
        assert len(working_days) == 10  # 5 days * 2 weeks


class TestLeaveHoursCalculation:
    """Tests for leave hours calculation."""

    def test_calculate_leave_hours_single_day(self, app):
        """Test leave hours for a single working day."""
        with app.app_context():
            # Monday
            start = date(2026, 1, 12)
            end = date(2026, 1, 12)
            result = calculate_leave_hours(start, end)
            
            assert result["total_days"] == 1
            assert result["working_days"] == 1
            assert result["weekend_days"] == 0
            assert result["working_hours"] == 8.0

    def test_calculate_leave_hours_weekend_day(self, app):
        """Test leave hours for a weekend day."""
        with app.app_context():
            # Saturday
            start = date(2026, 1, 17)
            end = date(2026, 1, 17)
            result = calculate_leave_hours(start, end)
            
            assert result["total_days"] == 1
            assert result["working_days"] == 0
            assert result["weekend_days"] == 1
            assert result["working_hours"] == 0.0

    def test_calculate_leave_hours_full_week(self, app):
        """Test leave hours for a full week."""
        with app.app_context():
            # Monday to Sunday
            start = date(2026, 1, 12)
            end = date(2026, 1, 18)
            result = calculate_leave_hours(start, end)
            
            assert result["total_days"] == 7
            assert result["working_days"] == 5
            assert result["weekend_days"] == 2
            assert result["working_hours"] == 40.0

    def test_calculate_leave_hours_spanning_weekend(self, app):
        """Test leave hours spanning a weekend."""
        with app.app_context():
            # Friday to Monday
            start = date(2026, 1, 16)  # Friday
            end = date(2026, 1, 19)    # Monday
            result = calculate_leave_hours(start, end)
            
            assert result["total_days"] == 4
            assert result["working_days"] == 2  # Friday and Monday
            assert result["weekend_days"] == 2  # Saturday and Sunday
            assert result["working_hours"] == 16.0


class TestMultiDayLeaveBackend:
    """Tests for multi-day leave backend functionality."""

    def test_create_multi_day_leave_request(self, client, app):
        """Test creating a multi-day leave request via UI."""
        with app.app_context():
            # Request leave from Monday to Friday
            response = client.post(
                "/leave",
                data={
                    "start_date": "2026-01-12",
                    "end_date": "2026-01-16",
                    "leave_type": "vacation",
                    "description": "Winter vacation",
                },
                follow_redirects=True,
            )
            
            # Should redirect back to leave page
            assert response.status_code == 200
            
            # Check that 5 leave records were created (Mon-Fri)
            leave_days = LeaveDay.query.all()
            assert len(leave_days) == 5
            
            # Verify dates are correct
            dates = sorted([ld.date for ld in leave_days])
            assert dates[0] == date(2026, 1, 12)  # Monday
            assert dates[-1] == date(2026, 1, 16)  # Friday
            
            # Verify all have same type and description
            for ld in leave_days:
                assert ld.leave_type == "vacation"
                assert ld.description == "Winter vacation"

    def test_create_multi_day_leave_excludes_weekends(self, client, app):
        """Test that multi-day leave excludes weekends."""
        with app.app_context():
            # Request leave from Friday to Monday (4 calendar days)
            response = client.post(
                "/leave",
                data={
                    "start_date": "2026-01-16",  # Friday
                    "end_date": "2026-01-19",    # Monday
                    "leave_type": "vacation",
                    "description": "Long weekend",
                },
                follow_redirects=True,
            )
            
            assert response.status_code == 200
            
            # Should create only 2 records (Friday and Monday)
            leave_days = LeaveDay.query.all()
            assert len(leave_days) == 2
            
            # Verify no weekend dates
            dates = [ld.date for ld in leave_days]
            assert date(2026, 1, 16) in dates  # Friday
            assert date(2026, 1, 19) in dates  # Monday
            assert date(2026, 1, 17) not in dates  # Saturday
            assert date(2026, 1, 18) not in dates  # Sunday

    def test_create_single_day_leave_backward_compatible(self, client, app):
        """Test that single-day leave still works (backward compatibility)."""
        with app.app_context():
            # Old format: just "date" field
            response = client.post(
                "/leave",
                data={
                    "date": "2026-01-15",
                    "leave_type": "sick",
                    "description": "Doctor appointment",
                },
                follow_redirects=True,
            )
            
            assert response.status_code == 200
            
            # Should create 1 record
            leave_days = LeaveDay.query.all()
            assert len(leave_days) == 1
            assert leave_days[0].date == date(2026, 1, 15)
            assert leave_days[0].leave_type == "sick"


class TestLeaveRequestCLI:
    """Tests for leave-request CLI command."""

    def test_leave_request_cli_basic(self, app):
        """Test basic leave request via CLI."""
        from click.testing import CliRunner
        from src.waqt.cli import cli

        with app.app_context():
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "leave-request",
                    "--from", "2026-01-12",
                    "--to", "2026-01-16",
                    "--type", "vacation",
                    "--desc", "Winter break",
                ],
                input="y\n",  # Confirm the request
            )

            assert result.exit_code == 0
            assert "Leave Request Summary" in result.output
            assert "Working Days: 5" in result.output
            assert "✓ Leave request created successfully!" in result.output

            # Verify records created
            leave_days = LeaveDay.query.all()
            assert len(leave_days) == 5

    def test_leave_request_cli_excludes_weekends(self, app):
        """Test that CLI leave request excludes weekends."""
        from click.testing import CliRunner
        from src.waqt.cli import cli

        with app.app_context():
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "leave-request",
                    "--from", "2026-01-16",  # Friday
                    "--to", "2026-01-19",    # Monday
                    "--type", "sick",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            assert "Working Days: 2" in result.output
            assert "Weekend Days: 2 (excluded)" in result.output

            # Verify only working days created
            leave_days = LeaveDay.query.all()
            assert len(leave_days) == 2

    def test_leave_request_cli_weekend_only(self, app):
        """Test CLI with weekend-only range."""
        from click.testing import CliRunner
        from src.waqt.cli import cli

        with app.app_context():
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "leave-request",
                    "--from", "2026-01-17",  # Saturday
                    "--to", "2026-01-18",    # Sunday
                ],
            )

            assert result.exit_code == 1
            assert "No working days in the selected range" in result.output

    def test_leave_request_cli_invalid_date_range(self, app):
        """Test CLI with invalid date range (end before start)."""
        from click.testing import CliRunner
        from src.waqt.cli import cli

        with app.app_context():
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "leave-request",
                    "--from", "2026-01-20",
                    "--to", "2026-01-10",
                ],
            )

            assert result.exit_code == 1
            assert "End date must be on or after start date" in result.output

    def test_leave_request_cli_cancel(self, app):
        """Test cancelling leave request in CLI."""
        from click.testing import CliRunner
        from src.waqt.cli import cli

        with app.app_context():
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "leave-request",
                    "--from", "2026-01-12",
                    "--to", "2026-01-16",
                ],
                input="n\n",  # Cancel the request
            )

            assert result.exit_code == 0
            assert "Leave request cancelled" in result.output

            # Verify no records created
            leave_days = LeaveDay.query.all()
            assert len(leave_days) == 0
