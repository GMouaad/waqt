"""Tests for import functionality."""

import pytest
import json
from datetime import date, time


from waqt.utils import (
    detect_import_format,
    normalize_time_string,
    normalize_date_string,
    parse_time_entries_from_json,
    parse_time_entries_from_csv,
    validate_time_entry_data,
    validate_leave_day_data,
)
from waqt.services import import_time_entries
from waqt.models import TimeEntry, LeaveDay, Category


class TestDetectImportFormat:
    """Tests for format detection from file extension."""

    def test_detect_csv(self, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.touch()
        assert detect_import_format(str(file_path)) == "csv"

    def test_detect_json(self, tmp_path):
        file_path = tmp_path / "test.json"
        file_path.touch()
        assert detect_import_format(str(file_path)) == "json"

    def test_detect_excel_xlsx(self, tmp_path):
        file_path = tmp_path / "test.xlsx"
        file_path.touch()
        assert detect_import_format(str(file_path)) == "excel"

    def test_detect_excel_xls(self, tmp_path):
        file_path = tmp_path / "test.xls"
        file_path.touch()
        assert detect_import_format(str(file_path)) == "excel"

    def test_unknown_format_raises(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.touch()
        with pytest.raises(ValueError, match="Cannot determine file format"):
            detect_import_format(str(file_path))

    def test_case_insensitive(self, tmp_path):
        file_path = tmp_path / "test.JSON"
        file_path.touch()
        assert detect_import_format(str(file_path)) == "json"


class TestNormalizeTimeString:
    """Tests for time string parsing."""

    def test_24_hour_format(self):
        result = normalize_time_string("14:30")
        assert result == time(14, 30)

    def test_24_hour_with_seconds(self):
        result = normalize_time_string("14:30:45")
        assert result == time(14, 30, 45)

    def test_12_hour_pm(self):
        result = normalize_time_string("02:30 PM")
        assert result == time(14, 30)

    def test_12_hour_am(self):
        result = normalize_time_string("09:00 AM")
        assert result == time(9, 0)

    def test_12_hour_no_space(self):
        result = normalize_time_string("02:30PM")
        assert result == time(14, 30)

    def test_invalid_returns_none(self):
        assert normalize_time_string("not a time") is None
        assert normalize_time_string("") is None
        assert normalize_time_string(None) is None

    def test_strips_whitespace(self):
        result = normalize_time_string("  14:30  ")
        assert result == time(14, 30)


class TestNormalizeDateString:
    """Tests for date string parsing."""

    def test_iso_format(self):
        result = normalize_date_string("2026-01-15")
        assert result == date(2026, 1, 15)

    def test_slash_ymd(self):
        result = normalize_date_string("2026/01/15")
        assert result == date(2026, 1, 15)

    def test_european_format(self):
        result = normalize_date_string("15/01/2026")
        assert result == date(2026, 1, 15)

    def test_european_dash(self):
        result = normalize_date_string("15-01-2026")
        assert result == date(2026, 1, 15)

    def test_invalid_returns_none(self):
        assert normalize_date_string("not a date") is None
        assert normalize_date_string("") is None
        assert normalize_date_string(None) is None

    def test_strips_whitespace(self):
        result = normalize_date_string("  2026-01-15  ")
        assert result == date(2026, 1, 15)


class TestValidateTimeEntryData:
    """Tests for time entry validation."""

    def test_valid_entry(self):
        entry = {
            "date": "2026-01-15",
            "start_time": "09:00",
            "end_time": "17:00",
        }
        is_valid, errors = validate_time_entry_data(entry)
        assert is_valid is True
        assert errors == []

    def test_missing_date(self):
        entry = {
            "start_time": "09:00",
            "end_time": "17:00",
        }
        is_valid, errors = validate_time_entry_data(entry)
        assert is_valid is False
        assert any("date" in err.lower() for err in errors)

    def test_missing_start_time(self):
        entry = {
            "date": "2026-01-15",
            "end_time": "17:00",
        }
        is_valid, errors = validate_time_entry_data(entry)
        assert is_valid is False
        assert any("start_time" in err for err in errors)

    def test_missing_end_time(self):
        entry = {
            "date": "2026-01-15",
            "start_time": "09:00",
        }
        is_valid, errors = validate_time_entry_data(entry)
        assert is_valid is False
        assert any("end_time" in err for err in errors)

    def test_invalid_date_format(self):
        entry = {
            "date": "not-a-date",
            "start_time": "09:00",
            "end_time": "17:00",
        }
        is_valid, errors = validate_time_entry_data(entry)
        assert is_valid is False
        assert any("date" in err.lower() for err in errors)

    def test_negative_duration_error(self):
        entry = {
            "date": "2026-01-15",
            "start_time": "09:00",
            "end_time": "17:00",
            "duration_hours": -5.0,
        }
        is_valid, errors = validate_time_entry_data(entry)
        assert is_valid is False
        assert any("negative" in err.lower() for err in errors)


class TestValidateLeaveDayData:
    """Tests for leave day validation."""

    def test_valid_vacation(self):
        leave = {
            "date": "2026-01-20",
            "leave_type": "vacation",
        }
        is_valid, errors = validate_leave_day_data(leave)
        assert is_valid is True
        assert errors == []

    def test_valid_sick(self):
        leave = {
            "date": "2026-01-20",
            "leave_type": "sick",
        }
        is_valid, errors = validate_leave_day_data(leave)
        assert is_valid is True

    def test_missing_date(self):
        leave = {
            "leave_type": "vacation",
        }
        is_valid, errors = validate_leave_day_data(leave)
        assert is_valid is False
        assert any("date" in err.lower() for err in errors)

    def test_missing_leave_type(self):
        leave = {
            "date": "2026-01-20",
        }
        is_valid, errors = validate_leave_day_data(leave)
        assert is_valid is False
        assert any("leave_type" in err for err in errors)

    def test_invalid_leave_type(self):
        leave = {
            "date": "2026-01-20",
            "leave_type": "holiday",
        }
        is_valid, errors = validate_leave_day_data(leave)
        assert is_valid is False
        assert any("leave_type" in err for err in errors)


class TestParseTimeEntriesFromJson:
    """Tests for JSON parsing."""

    def test_parse_standard_format(self):
        content = json.dumps(
            {
                "period": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
                "entries": [
                    {
                        "date": "2026-01-15",
                        "start_time": "09:00:00",
                        "end_time": "17:00:00",
                        "description": "Work session",
                    }
                ],
                "leave_days": [],
            }
        )
        result = parse_time_entries_from_json(content)
        assert len(result["entries"]) == 1
        assert result["entries"][0]["date"] == "2026-01-15"

    def test_parse_with_leave_days(self):
        content = json.dumps(
            {
                "entries": [],
                "leave_days": [
                    {
                        "date": "2026-01-20",
                        "leave_type": "vacation",
                    }
                ],
            }
        )
        result = parse_time_entries_from_json(content)
        assert len(result["leave_days"]) == 1
        assert result["leave_days"][0]["leave_type"] == "vacation"

    def test_parse_array_format(self):
        """Support old format where JSON is just an array of entries."""
        content = json.dumps(
            [{"date": "2026-01-15", "start_time": "09:00", "end_time": "17:00"}]
        )
        result = parse_time_entries_from_json(content)
        assert len(result["entries"]) == 1

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_time_entries_from_json("not json")


class TestParseTimeEntriesFromCsv:
    """Tests for CSV parsing."""

    def test_parse_basic_csv(self):
        content = (
            "Date,Day of Week,Start Time,End Time,Duration (Hours),Duration (HH:MM)"
            ",Description,Category,Overtime,Created At\n"
            "2026-01-15,Wednesday,09:00,17:00,8.00,8:00,Work session,Development,0.00,"
            "2026-01-15T09:00:00\n"
        )
        result = parse_time_entries_from_csv(content)
        assert len(result["entries"]) == 1
        assert result["entries"][0]["date"] == "2026-01-15"
        assert result["entries"][0]["category"] == "Development"

    def test_parse_csv_without_category(self):
        """CSV without Category column should still work."""
        content = (
            "Date,Day of Week,Start Time,End Time,Duration (Hours),Duration (HH:MM)"
            ",Description,Overtime,Created At\n"
            "2026-01-15,Wednesday,09:00,17:00,8.00,8:00,Work session,0.00,"
            "2026-01-15T09:00:00\n"
        )
        result = parse_time_entries_from_csv(content)
        assert len(result["entries"]) == 1
        assert "category" not in result["entries"][0]

    def test_skips_summary_rows(self):
        content = (
            "Date,Day of Week,Start Time,End Time,Duration (Hours),Duration (HH:MM)"
            ",Description,Overtime,Created At\n"
            "2026-01-15,Wednesday,09:00,17:00,8.00,8:00,Work session,0.00,"
            "2026-01-15T09:00:00\n\n"
            "Summary Statistics\n"
            "Period,2026-01-15 to 2026-01-15\n"
            "Total Entries,1\n"
        )
        result = parse_time_entries_from_csv(content)
        assert len(result["entries"]) == 1

    def test_empty_csv_raises(self):
        content = (
            "Date,Day of Week,Start Time,End Time,Duration (Hours),Duration (HH:MM)"
            ",Description,Overtime,Created At\n"
        )
        with pytest.raises(ValueError, match="no valid time entries"):
            parse_time_entries_from_csv(content)


class TestImportTimeEntries:
    """Integration tests for the import_time_entries service function."""

    @pytest.fixture
    def json_file(self, tmp_path):
        """Create a temporary JSON file for testing."""
        content = {
            "entries": [
                {
                    "date": "2026-02-01",
                    "start_time": "09:00:00",
                    "end_time": "17:00:00",
                    "description": "Test entry",
                    "category": "Testing",
                }
            ],
            "leave_days": [
                {
                    "date": "2026-02-05",
                    "leave_type": "vacation",
                    "description": "Day off",
                }
            ],
        }
        file_path = tmp_path / "import_test.json"
        file_path.write_text(json.dumps(content))
        return str(file_path)

    def test_import_creates_entries(self, db_session, json_file):
        """Test that import creates time entries."""
        result = import_time_entries(
            db_session,
            file_path=json_file,
            import_format="auto",
            on_conflict="skip",
            auto_create_categories=True,
            dry_run=False,
        )

        assert result["success"] is True
        assert result["entries_imported"] == 1
        assert result["leave_days_imported"] == 1

        # Verify entry was created
        entry = db_session.query(TimeEntry).filter_by(date=date(2026, 2, 1)).first()
        assert entry is not None
        assert entry.description == "Test entry"

        # Verify leave day was created
        leave = db_session.query(LeaveDay).filter_by(date=date(2026, 2, 5)).first()
        assert leave is not None
        assert leave.leave_type == "vacation"

    def test_import_auto_creates_category(self, db_session, json_file):
        """Test that import creates missing categories."""
        # Ensure category doesn't exist
        existing = db_session.query(Category).filter_by(name="Testing").first()
        if existing:
            db_session.delete(existing)
            db_session.commit()

        result = import_time_entries(
            db_session,
            file_path=json_file,
            auto_create_categories=True,
            dry_run=False,
        )

        assert "Testing" in result["categories_created"]

        # Verify category was created
        category = db_session.query(Category).filter_by(name="Testing").first()
        assert category is not None

    def test_import_dry_run_no_changes(self, db_session, json_file):
        """Test that dry run doesn't create entries."""
        result = import_time_entries(
            db_session,
            file_path=json_file,
            dry_run=True,
        )

        assert result["success"] is True
        assert result["entries_imported"] == 1  # Counted but not saved

        # Verify no entry was created
        entry = db_session.query(TimeEntry).filter_by(date=date(2026, 2, 1)).first()
        assert entry is None

    def test_import_skip_duplicates(self, db_session, json_file):
        """Test that duplicate entries are skipped."""
        # First import
        import_time_entries(db_session, file_path=json_file, dry_run=False)

        # Second import with same data
        result = import_time_entries(
            db_session,
            file_path=json_file,
            on_conflict="skip",
            dry_run=False,
        )

        assert result["entries_skipped"] >= 1
        assert result["entries_imported"] == 0

    def test_import_overwrite_duplicates(self, db_session, tmp_path):
        """Test that overwrite mode updates existing entries."""
        # Create initial entry
        entry = TimeEntry(
            date=date(2026, 7, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Original description",
            is_active=False,
        )
        db_session.add(entry)
        db_session.commit()

        # Import with updated description
        import_content = {
            "entries": [
                {
                    "date": "2026-07-01",
                    "start_time": "09:00:00",
                    "end_time": "17:00:00",  # Same end time to match duplicate detection
                    "description": "Updated description",
                }
            ]
        }
        import_file = tmp_path / "overwrite.json"
        import_file.write_text(json.dumps(import_content))

        result = import_time_entries(
            db_session,
            file_path=str(import_file),
            on_conflict="overwrite",
            dry_run=False,
        )

        assert result["success"] is True
        assert result["entries_updated"] >= 1

        # Verify entry was updated (description, not end_time - that's part of duplicate key)
        updated = db_session.query(TimeEntry).filter_by(date=date(2026, 7, 1)).first()
        assert updated.description == "Updated description"

    def test_import_duplicate_mode(self, db_session, tmp_path):
        """Test that duplicate mode creates new entries even if duplicates exist."""
        # Create initial entry
        entry = TimeEntry(
            date=date(2026, 8, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            duration_hours=3.0,
            description="First session",
            is_active=False,
        )
        db_session.add(entry)
        db_session.commit()

        # Import with same start time
        import_content = {
            "entries": [
                {
                    "date": "2026-08-01",
                    "start_time": "09:00:00",
                    "end_time": "12:00:00",
                    "description": "Duplicate session",
                }
            ]
        }
        import_file = tmp_path / "duplicate.json"
        import_file.write_text(json.dumps(import_content))

        result = import_time_entries(
            db_session,
            file_path=str(import_file),
            on_conflict="duplicate",
            dry_run=False,
        )

        assert result["success"] is True
        assert result["entries_imported"] >= 1

        # Verify 2 entries now exist
        entries = db_session.query(TimeEntry).filter_by(date=date(2026, 8, 1)).all()
        assert len(entries) == 2

    def test_import_without_auto_create_categories(self, db_session, tmp_path):
        """Test that categories are not created when auto_create is disabled."""
        import_content = {
            "entries": [
                {
                    "date": "2026-09-01",
                    "start_time": "09:00:00",
                    "end_time": "17:00:00",
                    "category": "NonExistentCategory",
                }
            ]
        }
        import_file = tmp_path / "no_auto_cat.json"
        import_file.write_text(json.dumps(import_content))

        result = import_time_entries(
            db_session,
            file_path=str(import_file),
            auto_create_categories=False,
            dry_run=False,
        )

        assert result["success"] is True
        # Entry should be imported but without category
        entry = db_session.query(TimeEntry).filter_by(date=date(2026, 9, 1)).first()
        assert entry is not None
        assert entry.category_id is None


class TestNormalizeEdgeCases:
    """Additional edge case tests for date/time normalization."""

    def test_time_midnight(self):
        result = normalize_time_string("00:00")
        assert result == time(0, 0)

    def test_time_noon(self):
        result = normalize_time_string("12:00 PM")
        assert result == time(12, 0)

    def test_time_midnight_am(self):
        result = normalize_time_string("12:00 AM")
        assert result == time(0, 0)

    def test_time_lowercase_am_pm(self):
        result = normalize_time_string("03:30pm")
        assert result == time(15, 30)

    def test_date_us_format(self):
        """Test US format MM/DD/YYYY."""
        result = normalize_date_string("01/15/2026")
        # Could be interpreted as DD/MM/YYYY or MM/DD/YYYY depending on logic
        assert result is not None

    def test_date_short_year(self):
        """Test short year format."""
        result = normalize_date_string("2026-1-5")
        assert result == date(2026, 1, 5)


class TestExportImportRoundTrip:
    """End-to-end tests verifying export → import compatibility."""

    @pytest.fixture
    def app(self):
        """Create and configure a test app instance."""
        from waqt import create_app, db as flask_db

        app = create_app()
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

        with app.app_context():
            flask_db.create_all()
            yield app
            flask_db.session.remove()
            flask_db.drop_all()

    def test_json_roundtrip(self, app, tmp_path):
        """Test that JSON export can be re-imported correctly."""
        from waqt.utils import export_time_entries_to_json
        from waqt.models import TimeEntry, Category
        from waqt.services import import_time_entries
        from waqt import db

        with app.app_context():
            # Create test data
            cat = Category(name="RoundTrip", code="RT")
            db.session.add(cat)
            db.session.flush()

            entry = TimeEntry(
                date=date(2026, 3, 15),
                start_time=time(9, 0),
                end_time=time(17, 30),
                duration_hours=8.5,
                description="Round trip test entry",
                category_id=cat.id,
                is_active=False,
            )
            db.session.add(entry)
            db.session.commit()

            # Export to JSON
            entries = TimeEntry.query.filter_by(date=date(2026, 3, 15)).all()
            json_content = export_time_entries_to_json(
                entries, date(2026, 3, 1), date(2026, 3, 31)
            )

            # Verify export content
            exported = json.loads(json_content)
            assert len(exported["entries"]) == 1
            assert exported["entries"][0]["category"] == "RoundTrip"

            # Clear the original data
            TimeEntry.query.filter_by(date=date(2026, 3, 15)).delete()
            Category.query.filter_by(name="RoundTrip").delete()
            db.session.commit()

            # Verify data is cleared
            assert TimeEntry.query.filter_by(date=date(2026, 3, 15)).first() is None

            # Import the exported JSON
            json_file = tmp_path / "roundtrip.json"
            json_file.write_text(json_content)

            result = import_time_entries(
                db.session,
                file_path=str(json_file),
                import_format="json",
                auto_create_categories=True,
                dry_run=False,
            )

            assert result["success"] is True
            assert result["entries_imported"] == 1

            # Verify the imported entry matches original
            imported_entry = TimeEntry.query.filter_by(date=date(2026, 3, 15)).first()
            assert imported_entry is not None
            assert imported_entry.start_time == time(9, 0)
            assert imported_entry.end_time == time(17, 30)
            assert imported_entry.description == "Round trip test entry"
            assert imported_entry.category is not None
            assert imported_entry.category.name == "RoundTrip"

    def test_csv_roundtrip(self, app, tmp_path):
        """Test that CSV export can be re-imported correctly."""
        from waqt.utils import export_time_entries_to_csv
        from waqt.models import TimeEntry
        from waqt.services import import_time_entries
        from waqt import db

        with app.app_context():
            # Create test data
            entry = TimeEntry(
                date=date(2026, 4, 10),
                start_time=time(8, 30),
                end_time=time(16, 0),
                duration_hours=7.5,
                description="CSV round trip test",
                is_active=False,
            )
            db.session.add(entry)
            db.session.commit()

            # Export to CSV
            entries = TimeEntry.query.filter_by(date=date(2026, 4, 10)).all()
            csv_content = export_time_entries_to_csv(
                entries, date(2026, 4, 1), date(2026, 4, 30)
            )

            # Clear the original data
            TimeEntry.query.filter_by(date=date(2026, 4, 10)).delete()
            db.session.commit()

            # Import the exported CSV
            csv_file = tmp_path / "roundtrip.csv"
            csv_file.write_text(csv_content)

            result = import_time_entries(
                db.session,
                file_path=str(csv_file),
                import_format="csv",
                dry_run=False,
            )

            assert result["success"] is True
            assert result["entries_imported"] == 1

            # Verify the imported entry matches original
            imported_entry = TimeEntry.query.filter_by(date=date(2026, 4, 10)).first()
            assert imported_entry is not None
            assert imported_entry.start_time == time(8, 30)
            assert imported_entry.end_time == time(16, 0)
            assert imported_entry.description == "CSV round trip test"

    def test_roundtrip_with_multiple_entries(self, app, tmp_path):
        """Test round-trip with multiple entries and categories."""
        from waqt.utils import export_time_entries_to_json
        from waqt.models import TimeEntry, Category
        from waqt.services import import_time_entries
        from waqt import db

        with app.app_context():
            # Create categories
            cat1 = Category(name="Project A")
            cat2 = Category(name="Project B")
            db.session.add_all([cat1, cat2])
            db.session.flush()

            # Create multiple entries
            entries_to_create = [
                TimeEntry(
                    date=date(2026, 5, 1),
                    start_time=time(9, 0),
                    end_time=time(12, 0),
                    duration_hours=3.0,
                    description="Morning session",
                    category_id=cat1.id,
                    is_active=False,
                ),
                TimeEntry(
                    date=date(2026, 5, 1),
                    start_time=time(13, 0),
                    end_time=time(17, 0),
                    duration_hours=4.0,
                    description="Afternoon session",
                    category_id=cat2.id,
                    is_active=False,
                ),
                TimeEntry(
                    date=date(2026, 5, 2),
                    start_time=time(8, 0),
                    end_time=time(16, 0),
                    duration_hours=8.0,
                    description="Full day",
                    category_id=cat1.id,
                    is_active=False,
                ),
            ]
            db.session.add_all(entries_to_create)
            db.session.commit()

            # Export
            entries = TimeEntry.query.filter(
                TimeEntry.date >= date(2026, 5, 1),
                TimeEntry.date <= date(2026, 5, 2),
            ).all()
            json_content = export_time_entries_to_json(
                entries, date(2026, 5, 1), date(2026, 5, 2)
            )

            # Clear data
            TimeEntry.query.filter(
                TimeEntry.date >= date(2026, 5, 1),
                TimeEntry.date <= date(2026, 5, 2),
            ).delete()
            Category.query.filter(
                Category.name.in_(["Project A", "Project B"])
            ).delete()
            db.session.commit()

            # Import
            json_file = tmp_path / "multi_roundtrip.json"
            json_file.write_text(json_content)

            result = import_time_entries(
                db.session,
                file_path=str(json_file),
                auto_create_categories=True,
                dry_run=False,
            )

            assert result["success"] is True
            assert result["entries_imported"] == 3

            # Verify all entries imported
            imported = TimeEntry.query.filter(
                TimeEntry.date >= date(2026, 5, 1),
                TimeEntry.date <= date(2026, 5, 2),
            ).all()
            assert len(imported) == 3

            # Verify categories were recreated
            assert "Project A" in result["categories_created"]
            assert "Project B" in result["categories_created"]

    def test_roundtrip_preserves_duration(self, app, tmp_path):
        """Test that duration is correctly calculated on import."""
        from waqt.utils import export_time_entries_to_json
        from waqt.models import TimeEntry
        from waqt.services import import_time_entries
        from waqt import db

        with app.app_context():
            # Create entry with specific duration
            entry = TimeEntry(
                date=date(2026, 6, 15),
                start_time=time(9, 15),
                end_time=time(17, 45),
                duration_hours=8.5,  # 9:15 to 17:45 = 8.5 hours
                description="Duration test",
                is_active=False,
            )
            db.session.add(entry)
            db.session.commit()

            original_duration = entry.duration_hours

            # Export and re-import
            entries = TimeEntry.query.filter_by(date=date(2026, 6, 15)).all()
            json_content = export_time_entries_to_json(
                entries, date(2026, 6, 1), date(2026, 6, 30)
            )

            TimeEntry.query.filter_by(date=date(2026, 6, 15)).delete()
            db.session.commit()

            json_file = tmp_path / "duration_test.json"
            json_file.write_text(json_content)

            import_time_entries(db.session, file_path=str(json_file), dry_run=False)

            # Verify duration matches
            imported = TimeEntry.query.filter_by(date=date(2026, 6, 15)).first()
            assert imported is not None
            # Allow tiny float diff
            assert abs(imported.duration_hours - original_duration) < 0.01
