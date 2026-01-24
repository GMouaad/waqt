"Tests for multi-day leave request functionality."

import pytest
from datetime import date, timedelta
from src.waqt import create_app, db
from src.waqt.models import LeaveDay
from src.waqt.utils import (
    is_weekend,
    get_date_range,
    get_working_days_in_range,
    calculate_leave_hours,
)
from click.testing import CliRunner


class TestWeekendDetection:
    def test_is_weekend_saturday(self):
        """Test that Saturday is identified as a weekend."""
        saturday = date(2026, 1, 10)  # Jan 10, 2026 is a Saturday
        assert is_weekend(saturday) is True

    def test_is_weekend_sunday(self):
        """Test that Sunday is identified as a weekend."""
        sunday = date(2026, 1, 11)  # Jan 11, 2026 is a Sunday
        assert is_weekend(sunday) is True

    def test_is_weekend_monday(self):
        """Test that Monday is not identified as a weekend."""
        monday = date(2026, 1, 12)  # Jan 12, 2026 is a Monday
        assert is_weekend(monday) is False

    def test_is_weekend_friday(self):
        """Test that Friday is not identified as a weekend."""
        friday = date(2026, 1, 9)  # Jan 9, 2026 is a Friday
        assert is_weekend(friday) is False


class TestDateRange:
    def test_get_date_range_single_day(self):
        """Test range for a single day."""
        start = date(2026, 1, 15)
        end = date(2026, 1, 15)
        result = get_date_range(start, end)
        assert len(result) == 1
        assert result[0] == start

    def test_get_date_range_week(self):
        """Test range for a full week (Mon-Sun)."""
        start = date(2026, 1, 12)  # Monday
        end = date(2026, 1, 18)  # Sunday
        result = get_date_range(start, end)
        assert len(result) == 7
        assert result[0] == start
        assert result[-1] == end

    def test_get_date_range_invalid(self):
        """Test range where start > end."""
        start = date(2026, 1, 15)
        end = date(2026, 1, 14)
        result = get_date_range(start, end)
        assert result == []

    def test_get_date_range_month_crossing(self):
        """Test range crossing month boundary."""
        start = date(2026, 1, 31)
        end = date(2026, 2, 1)
        result = get_date_range(start, end)
        assert len(result) == 2
        assert result[0] == date(2026, 1, 31)
        assert result[1] == date(2026, 2, 1)


class TestWorkingDays:
    def test_get_working_days_full_week(self):
        """Test working days in a full Mon-Sun week."""
        start = date(2026, 1, 12)  # Monday
        end = date(2026, 1, 18)  # Sunday
        result = get_working_days_in_range(start, end)
        assert len(result) == 5  # Mon-Fri
        assert date(2026, 1, 12) in result
        assert date(2026, 1, 16) in result
        assert date(2026, 1, 17) not in result  # Saturday
        assert date(2026, 1, 18) not in result  # Sunday

    def test_get_working_days_weekdays_only(self):
        """Test working days in a Mon-Fri range."""
        start = date(2026, 1, 12)  # Monday
        end = date(2026, 1, 16)  # Friday
        result = get_working_days_in_range(start, end)
        assert len(result) == 5

    def test_get_working_days_weekend_only(self):
        """Test working days in a Sat-Sun range."""
        start = date(2026, 1, 17)  # Saturday
        end = date(2026, 1, 18)  # Sunday
        result = get_working_days_in_range(start, end)
        assert len(result) == 0

    def test_get_working_days_two_weeks(self):
        """Test working days across two weeks."""
        start = date(2026, 1, 16)  # Friday
        end = date(2026, 1, 19)  # Monday
        result = get_working_days_in_range(start, end)
        assert len(result) == 2  # Friday and Monday
        assert date(2026, 1, 16) in result
        assert date(2026, 1, 19) in result


class TestLeaveHoursCalculation:
    @pytest.fixture
    def app(self):
        app = create_app()
        app.config.update(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()

    def test_calculate_leave_hours_single_day(self, app):
        """Test stats for single working day."""
        with app.app_context():
            start = date(2026, 1, 15)  # Thursday
            result = calculate_leave_hours(start, start)
            assert result["total_days"] == 1
            assert result["working_days"] == 1
            assert result["weekend_days"] == 0
            assert result["working_hours"] == 8.0  # Default 8h

    def test_calculate_leave_hours_weekend_day(self, app):
        """Test stats for single weekend day."""
        with app.app_context():
            start = date(2026, 1, 17)  # Saturday
            result = calculate_leave_hours(start, start)
            assert result["total_days"] == 1
            assert result["working_days"] == 0
            assert result["weekend_days"] == 1
            assert result["working_hours"] == 0.0

    def test_calculate_leave_hours_full_week(self, app):
        """Test stats for Mon-Sun week."""
        with app.app_context():
            start = date(2026, 1, 12)  # Monday
            end = date(2026, 1, 18)  # Sunday
            result = calculate_leave_hours(start, end)
            assert result["total_days"] == 7
            assert result["working_days"] == 5
            assert result["weekend_days"] == 2
            assert result["working_hours"] == 40.0  # 5 * 8h

    def test_calculate_leave_hours_spanning_weekend(self, app):
        """Test stats for Fri-Mon range."""
        with app.app_context():
            start = date(2026, 1, 16)  # Friday
            end = date(2026, 1, 19)  # Monday
            result = calculate_leave_hours(start, end)
            assert result["total_days"] == 4
            assert result["working_days"] == 2  # Fri, Mon
            assert result["weekend_days"] == 2  # Sat, Sun
            assert result["working_hours"] == 16.0  # 2 * 8h


class TestMultiDayLeaveBackend:
    @pytest.fixture
    def app(self):
        app = create_app()
        app.config.update(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "WTF_CSRF_ENABLED": False,
            }
        )

        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def client(self, app):
        return app.test_client()

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

            # Check for success message
            assert (
                b"leave added successfully" in response.data
                or b"leave processed" in response.data
            )

            # Check that 5 leave records were created (Mon-Fri)
            leave_days = LeaveDay.query.all()
            assert len(leave_days) == 5

            # Verify data
            dates = sorted([l.date for l in leave_days])
            assert dates[0] == date(2026, 1, 12)  # Monday
            assert dates[-1] == date(2026, 1, 16)  # Friday
            assert all(l.leave_type == "vacation" for l in leave_days)

    def test_create_multi_day_leave_excludes_weekends(self, client, app):
        """Test that multi-day leave excludes weekends."""
        with app.app_context():
            # Request leave from Friday to Monday (4 calendar days)
            response = client.post(
                "/leave",
                data={
                    "start_date": "2026-01-16",  # Friday
                    "end_date": "2026-01-19",  # Monday
                    "leave_type": "vacation",
                    "description": "Long weekend",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200

            # Should create only 2 records (Friday and Monday)
            leave_days = LeaveDay.query.all()
            assert len(leave_days) == 2

            dates = sorted([l.date for l in leave_days])
            assert dates[0] == date(2026, 1, 16)  # Friday
            assert dates[1] == date(2026, 1, 19)  # Monday

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


class TestLeaveRequestCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def app(self):
        app = create_app()
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()

    def test_leave_request_cli_basic(self, runner, app):
        """Test CLI leave request basic functionality."""
        from src.waqt.cli import cli

        with app.app_context():
            result = runner.invoke(
                cli,
                [
                    "leave-request",
                    "--from",
                    "2026-01-12",
                    "--to",
                    "2026-01-16",
                    "--type",
                    "vacation",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            assert "Leave request created successfully" in result.output
            assert "Created 5 leave record(s)" in result.output

            # Verify DB
            assert LeaveDay.query.count() == 5

    def test_leave_request_cli_excludes_weekends(self, runner, app):
        """Test CLI excludes weekends."""
        from src.waqt.cli import cli

        with app.app_context():
            # Fri-Mon
            result = runner.invoke(
                cli,
                [
                    "leave-request",
                    "--from",
                    "2026-01-16",
                    "--to",
                    "2026-01-19",
                    "--type",
                    "vacation",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            assert "Created 2 leave record(s)" in result.output
            assert "Excluded 2 weekend day(s)" in result.output

            # Verify DB
            assert LeaveDay.query.count() == 2

    def test_leave_request_cli_weekend_only(self, runner, app):
        """Test CLI error on weekend-only request."""
        from src.waqt.cli import cli

        with app.app_context():
            result = runner.invoke(
                cli,
                [
                    "leave-request",
                    "--from",
                    "2026-01-17",  # Sat
                    "--to",
                    "2026-01-18",  # Sun
                ],
            )

            assert result.exit_code != 0
            assert "No working days in the selected range" in result.output

    def test_leave_request_cli_invalid_date_range(self, runner, app):
        """Test CLI error on invalid date range."""
        from src.waqt.cli import cli

        with app.app_context():
            result = runner.invoke(
                cli,
                [
                    "leave-request",
                    "--from",
                    "2026-01-18",
                    "--to",
                    "2026-01-12",
                ],
            )

            assert result.exit_code != 0
            assert "End date must be on or after start date" in result.output

    def test_leave_request_cli_cancel(self, runner, app):
        """Test cancelling request."""
        from src.waqt.cli import cli

        with app.app_context():
            result = runner.invoke(
                cli,
                [
                    "leave-request",
                    "--from",
                    "2026-01-12",
                    "--to",
                    "2026-01-12",
                ],
                input="n\n",
            )  # Say no

            assert result.exit_code == 0
            assert "Leave request cancelled" in result.output
            assert LeaveDay.query.count() == 0
