"""Unit tests for CSV export functionality."""

import pytest
import csv
import io
from datetime import date, time
from click.testing import CliRunner
from src.waqt import create_app, db
from src.waqt.models import TimeEntry
from src.waqt.utils import export_time_entries_to_csv
from src.waqt.cli import cli


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


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_entries(app):
    """Create sample time entries for testing."""
    with app.app_context():
        entries = [
            TimeEntry(
                date=date(2024, 1, 15),
                start_time=time(9, 0),
                end_time=time(17, 0),
                duration_hours=8.0,
                description="Regular work day",
            ),
            TimeEntry(
                date=date(2024, 1, 16),
                start_time=time(9, 0),
                end_time=time(18, 0),
                duration_hours=9.0,
                description="Overtime day",
            ),
            TimeEntry(
                date=date(2024, 1, 17),
                start_time=time(10, 0),
                end_time=time(16, 0),
                duration_hours=6.0,
                description="Short day",
            ),
        ]
        for entry in entries:
            db.session.add(entry)
        db.session.commit()
        return entries


def test_export_time_entries_to_csv_basic(app, sample_entries):
    """Test basic CSV export functionality."""
    with app.app_context():
        entries = TimeEntry.query.all()
        csv_content = export_time_entries_to_csv(entries)

        assert csv_content is not None
        assert len(csv_content) > 0
        assert "Date" in csv_content
        assert "Start Time" in csv_content
        assert "End Time" in csv_content
        assert "Duration (Hours)" in csv_content
        assert "Description" in csv_content
        assert "Overtime" in csv_content


def test_export_csv_contains_data(app, sample_entries):
    """Test that CSV export contains actual data."""
    with app.app_context():
        entries = TimeEntry.query.all()
        csv_content = export_time_entries_to_csv(entries)

        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        # Check we have the correct number of rows
        assert len(rows) >= 3

        # Check data in rows
        assert rows[0]["Date"] == "2024-01-15"
        assert rows[0]["Start Time"] == "09:00"
        assert rows[0]["End Time"] == "17:00"
        assert rows[0]["Duration (Hours)"] == "8.00"
        assert rows[0]["Description"] == "Regular work day"
        assert rows[0]["Overtime"] == "0.00"

        # Check overtime is calculated correctly
        assert rows[1]["Overtime"] == "1.00"  # 9 hours - 8 hours = 1 hour


def test_export_csv_summary_statistics(app, sample_entries):
    """Test that CSV export includes summary statistics."""
    with app.app_context():
        entries = TimeEntry.query.all()
        csv_content = export_time_entries_to_csv(
            entries, start_date=date(2024, 1, 15), end_date=date(2024, 1, 17)
        )

        assert "Summary Statistics" in csv_content
        assert "Total Entries" in csv_content
        assert "Total Hours" in csv_content
        assert "Working Days" in csv_content
        assert "Total Overtime" in csv_content
        assert "2024-01-15 to 2024-01-17" in csv_content


def test_export_csv_multiple_entries_same_day(app):
    """Test CSV export with multiple entries for the same day."""
    with app.app_context():
        # Create multiple entries for the same day
        entries = [
            TimeEntry(
                date=date(2024, 1, 15),
                start_time=time(9, 0),
                end_time=time(12, 0),
                duration_hours=3.0,
                description="Morning session",
            ),
            TimeEntry(
                date=date(2024, 1, 15),
                start_time=time(13, 0),
                end_time=time(18, 0),
                duration_hours=5.0,
                description="Afternoon session",
            ),
            TimeEntry(
                date=date(2024, 1, 15),
                start_time=time(19, 0),
                end_time=time(21, 0),
                duration_hours=2.0,
                description="Evening session",
            ),
        ]
        for entry in entries:
            db.session.add(entry)
        db.session.commit()

        all_entries = TimeEntry.query.all()
        csv_content = export_time_entries_to_csv(all_entries)

        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        # All three entries should be present
        assert len(rows) >= 3

        # Overtime should be calculated based on total daily hours (3+5+2=10, so 2 hours overtime)
        # All entries for the same day should show the same overtime value
        day_entries = [r for r in rows if r["Date"] == "2024-01-15"]
        assert len(day_entries) == 3

        # All entries for the same day should have the same overtime (2.00 hours)
        for entry in day_entries:
            assert entry["Overtime"] == "2.00"

        # Verify total overtime in summary
        assert "Total Overtime,2.00" in csv_content or "Total Overtime,2.0" in csv_content


def test_export_csv_all_entries_period(app, sample_entries):
    """Test that CSV export shows 'All time entries' when no date range given."""
    with app.app_context():
        entries = TimeEntry.query.all()
        csv_content = export_time_entries_to_csv(entries)

        assert "Summary Statistics" in csv_content
        assert "All time entries" in csv_content


def test_export_csv_route_success(client, app, sample_entries):
    """Test CSV export via Flask route."""
    with app.app_context():
        response = client.get("/export/csv?period=all")

        assert response.status_code == 200
        assert response.mimetype == "text/csv"
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        assert "time_entries" in response.headers["Content-Disposition"]

        # Check content
        csv_content = response.data.decode("utf-8")
        assert "Date" in csv_content
        assert "2024-01-15" in csv_content


def test_export_csv_route_week_period(client, app, sample_entries):
    """Test CSV export for a specific week."""
    with app.app_context():
        response = client.get("/export/csv?period=week&date=2024-01-15")

        assert response.status_code == 200
        assert response.mimetype == "text/csv"


def test_export_csv_route_month_period(client, app, sample_entries):
    """Test CSV export for a specific month."""
    with app.app_context():
        response = client.get("/export/csv?period=month&date=2024-01-15")

        assert response.status_code == 200
        assert response.mimetype == "text/csv"


def test_export_csv_route_no_entries(client, app):
    """Test CSV export when no entries exist."""
    with app.app_context():
        response = client.get("/export/csv?period=all", follow_redirects=True)

        # Should redirect with warning message
        assert response.status_code == 200
        assert b"No time entries found" in response.data


def test_export_csv_route_invalid_date(client, app, sample_entries):
    """Test CSV export with invalid date format via web route."""
    with app.app_context():
        # Request with invalid date should fallback to current date with warning
        response = client.get(
            "/export/csv?period=week&date=invalid-date", follow_redirects=False
        )

        # Should still succeed but with fallback behavior
        # Since we can't easily check flash messages without following redirects,
        # we verify it doesn't crash
        assert response.status_code in [200, 302]


def test_cli_export_command_basic(runner, app, sample_entries, tmp_path):
    """Test basic CLI export command."""
    with app.app_context():
        output_file = tmp_path / "test_export.csv"

        result = runner.invoke(cli, ["export", "--output", str(output_file)])

        assert result.exit_code == 0
        assert "Export successful!" in result.output
        assert output_file.exists()

        # Verify file content
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Date" in content
            assert "2024-01-15" in content


def test_cli_export_command_week(runner, app, sample_entries, tmp_path):
    """Test CLI export for a specific week."""
    with app.app_context():
        output_file = tmp_path / "weekly_export.csv"

        result = runner.invoke(
            cli,
            [
                "export",
                "--period",
                "week",
                "--date",
                "2024-01-15",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert "Export successful!" in result.output
        assert output_file.exists()


def test_cli_export_command_month(runner, app, sample_entries, tmp_path):
    """Test CLI export for a specific month."""
    with app.app_context():
        output_file = tmp_path / "monthly_export.csv"

        result = runner.invoke(
            cli,
            [
                "export",
                "--period",
                "month",
                "--date",
                "2024-01-15",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert "Export successful!" in result.output
        assert output_file.exists()


def test_cli_export_command_default_filename(runner, app, sample_entries):
    """Test CLI export with default filename generation."""
    with app.app_context():
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["export"])

            assert result.exit_code == 0
            assert "Export successful!" in result.output
            assert "time_entries" in result.output


def test_cli_export_command_no_entries(runner, app):
    """Test CLI export when no entries exist."""
    with app.app_context():
        result = runner.invoke(cli, ["export"])

        assert result.exit_code == 0
        assert "No time entries found" in result.output


def test_cli_export_command_invalid_date(runner, app):
    """Test CLI export with invalid date format."""
    with app.app_context():
        result = runner.invoke(cli, ["export", "--date", "invalid-date"])

        assert result.exit_code != 0
        assert "Invalid date format" in result.output


def test_cli_export_command_format_option(runner, app, sample_entries, tmp_path):
    """Test CLI export with format option."""
    with app.app_context():
        output_file = tmp_path / "formatted_export.csv"

        result = runner.invoke(
            cli, ["export", "--format", "csv", "--output", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()


def test_export_csv_special_characters(app):
    """Test CSV export with special characters in descriptions."""
    with app.app_context():
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description='Work on "project", with commas, and quotes',
        )
        db.session.add(entry)
        db.session.commit()

        entries = TimeEntry.query.all()
        csv_content = export_time_entries_to_csv(entries)

        # CSV should properly escape special characters
        assert csv_content is not None
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        # Description should be properly parsed despite special characters
        assert '"project"' in rows[0]["Description"]


def test_export_csv_empty_entries_list(app):
    """Test CSV export with empty entries list."""
    with app.app_context():
        csv_content = export_time_entries_to_csv([])

        # Should return CSV with headers but no data rows
        assert "Date" in csv_content
        assert "Start Time" in csv_content
        
        # Should not have summary section for empty entries
        # Use csv.reader to count actual rows
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) == 1  # Just the header row
        assert "Date" in rows[0]  # Verify it's the header


def test_export_includes_all_fields(app, sample_entries):
    """Test that export includes all required fields."""
    with app.app_context():
        entries = TimeEntry.query.all()
        csv_content = export_time_entries_to_csv(entries)

        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        # Check all required fields are present
        required_fields = [
            "Date",
            "Day of Week",
            "Start Time",
            "End Time",
            "Duration (Hours)",
            "Duration (HH:MM)",
            "Description",
            "Overtime",
            "Created At",
        ]

        for field in required_fields:
            assert field in rows[0].keys()


def test_export_day_of_week_format(app, sample_entries):
    """Test that day of week is properly formatted."""
    with app.app_context():
        entries = TimeEntry.query.all()
        csv_content = export_time_entries_to_csv(entries)

        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        # 2024-01-15 is a Monday
        assert rows[0]["Day of Week"] == "Monday"


def test_export_duration_formats(app, sample_entries):
    """Test that both duration formats are included."""
    with app.app_context():
        entries = TimeEntry.query.all()
        csv_content = export_time_entries_to_csv(entries)

        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        # Check both duration formats
        assert rows[0]["Duration (Hours)"] == "8.00"
        assert rows[0]["Duration (HH:MM)"] == "8:00"

        # Check 9 hours
        assert rows[1]["Duration (Hours)"] == "9.00"
        assert rows[1]["Duration (HH:MM)"] == "9:00"
