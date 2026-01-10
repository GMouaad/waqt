"""Unit tests for the new MCP server features."""

import pytest
from datetime import date, time, timedelta


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    from src.waqt import create_app, db
    from src.waqt.models import Settings
    import src.waqt.mcp_server
    
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        # Ensure default settings exist
        Settings.set_setting("standard_hours_per_day", "8")
        Settings.set_setting("weekly_hours", "40")
        
        # Inject our test app into mcp_server global
        # This is more reliable than patching get_app in some contexts
        original_app = src.waqt.mcp_server._app
        src.waqt.mcp_server._app = app
        
        yield app
        
        # Restore original
        src.waqt.mcp_server._app = original_app
            
        db.session.remove()
        db.drop_all()

# --- edit_entry Tests ---

def test_edit_entry_basic(app):
    """Test editing a single entry."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import edit_entry
    
    with app.app_context():
        # Create an entry
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Original",
            is_active=False
        )
        db.session.add(entry)
        db.session.commit()

        # Edit it
        result = edit_entry(
            date="2024-01-15",
            start="10:00",
            description="Updated"
        )

        assert result["status"] == "success"
        assert result["entry"]["start_time"] == "10:00"
        assert result["entry"]["end_time"] == "17:00"
        assert result["entry"]["description"] == "Updated"
        # Duration should be recalculated: 10 to 17 is 7 hours
        assert result["entry"]["duration"] == "7:00"

        # Verify DB
        db_entry = TimeEntry.query.first()
        assert db_entry.start_time == time(10, 0)
        assert db_entry.description == "Updated"
        assert db_entry.duration_hours == 7.0

def test_edit_entry_by_id(app):
    """Test editing an entry by ID (useful when multiple exist)."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import edit_entry
    
    with app.app_context():
        # Create two entries for the same day
        entry1 = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(12, 0),
            duration_hours=3.0,
            description="Morning",
            is_active=False
        )
        entry2 = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(13, 0),
            end_time=time(17, 0),
            duration_hours=4.0,
            description="Afternoon",
            is_active=False
        )
        db.session.add(entry1)
        db.session.add(entry2)
        db.session.commit()
        
        target_id = entry2.id
        
        # Edit the second one specifically
        result = edit_entry(
            date="2024-01-15",
            entry_id=target_id,
            description="Updated Afternoon"
        )
        
        # Refresh session to force reload from DB
        db.session.expire_all()
        
        assert result["status"] == "success"
        assert result["entry"]["description"] == "Updated Afternoon"
        
        # Verify DB
        updated_entry = db.session.get(TimeEntry, target_id)
        assert updated_entry.description == "Updated Afternoon"
        
        # Verify other entry untouched
        other_entry = db.session.get(TimeEntry, entry1.id)
        assert other_entry.description == "Morning"

def test_edit_entry_multiple_error(app):
    """Test error when editing date with multiple entries without ID."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import edit_entry
    
    with app.app_context():
        entry1 = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(12, 0),
            duration_hours=3.0,
            description="Morning",
            is_active=False
        )
        entry2 = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(13, 0),
            end_time=time(17, 0),
            duration_hours=4.0,
            description="Afternoon",
            is_active=False
        )
        db.session.add(entry1)
        db.session.add(entry2)
        db.session.commit()

        result = edit_entry(date="2024-01-15", description="Fail")
        
        assert result["status"] == "error"
        assert "Multiple entries found" in result["message"]

def test_edit_active_entry_error(app):
    """Test error when trying to edit an active entry."""
    from src.waqt.models import TimeEntry
    from src.waqt import db
    from src.waqt.mcp_server import edit_entry
    
    with app.app_context():
        entry = TimeEntry(
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(9, 0),
            duration_hours=0.0,
            description="Active",
            is_active=True
        )
        db.session.add(entry)
        db.session.commit()

        result = edit_entry(date="2024-01-15", description="Try edit")
        
        assert result["status"] == "error"
        # Since we filter by is_active=False to find the ID, we won't find it if it's active
        assert "No completed entry found" in result["message"]

# --- leave_request Tests ---

def test_leave_request_basic(app):
    """Test creating a leave request."""
    from src.waqt.models import LeaveDay
    from src.waqt.mcp_server import leave_request
    
    with app.app_context():
        # Request leave for Mon-Fri
        result = leave_request(
            start_date="2024-01-15", # Monday
            end_date="2024-01-19",   # Friday
            leave_type="vacation",
            description="Holiday"
        )

        assert result["status"] == "success"
        assert result["summary"]["total_days"] == 5
        assert result["summary"]["working_days"] == 5
        
        # Check DB
        leaves = LeaveDay.query.all()
        assert len(leaves) == 5
        assert all(l.leave_type == "vacation" for l in leaves)

def test_leave_request_weekend_exclusion(app):
    """Test that weekends are excluded."""
    from src.waqt.models import LeaveDay
    from src.waqt.mcp_server import leave_request
    
    with app.app_context():
        # Request leave Fri-Mon (Fri, Sat, Sun, Mon)
        result = leave_request(
            start_date="2024-01-19", # Friday
            end_date="2024-01-22",   # Monday
            leave_type="sick"
        )

        assert result["status"] == "success"
        assert result["summary"]["total_days"] == 4
        assert result["summary"]["working_days"] == 2 # Fri and Mon
        assert result["summary"]["weekend_days"] == 2 # Sat and Sun
        
        leaves = LeaveDay.query.all()
        assert len(leaves) == 2
        dates = sorted([l.date for l in leaves])
        assert dates[0] == date(2024, 1, 19)
        assert dates[1] == date(2024, 1, 22)

def test_leave_request_invalid_dates(app):
    """Test error with invalid dates."""
    from src.waqt.mcp_server import leave_request
    
    with app.app_context():
        result = leave_request(
            start_date="2024-01-20", 
            end_date="2024-01-19" # End before start
        )
        assert result["status"] == "error"
        assert "End date must be on or after" in result["message"]

def test_leave_request_prevents_duplicates(app):
    """Test that duplicate leave records are skipped."""
    from src.waqt.models import LeaveDay
    from src.waqt.mcp_server import leave_request
    
    with app.app_context():
        # First request: Mon-Wed
        result1 = leave_request(
            start_date="2024-01-15",
            end_date="2024-01-17",
            leave_type="vacation"
        )
        assert result1["status"] == "success"
        assert result1["summary"]["created_days"] == 3

        # Second request overlapping: Tue-Thu
        # Tue (16) and Wed (17) are duplicates, Thu (18) is new
        result2 = leave_request(
            start_date="2024-01-16",
            end_date="2024-01-18",
            leave_type="sick"
        )
        assert result2["status"] == "success"
        assert result2["summary"]["created_days"] == 1
        assert result2["summary"]["skipped_days"] == 2
        
        # Verify total records: 3 from first + 1 from second = 4
        leaves = LeaveDay.query.all()
        assert len(leaves) == 4
        
        # Verify types preserved (skipped ones shouldn't change type)
        tue_leave = LeaveDay.query.filter_by(date=date(2024, 1, 16)).first()
        assert tue_leave.leave_type == "vacation" # Should remain vacation

# --- Config Tests ---

def test_get_set_config(app):
    """Test getting and setting configuration."""
    from src.waqt.mcp_server import get_config, set_config
    
    with app.app_context():
        # Initial check
        res = get_config("weekly_hours")
        assert res["status"] == "success"
        assert res["value"] == "40" # Default string value

        # Set new value
        res = set_config("weekly_hours", "35")
        assert res["status"] == "success"
        assert res["new_value"] == "35"
        
        # Verify persistence
        res = get_config("weekly_hours")
        assert res["value"] == "35"

def test_set_config_validation(app):
    """Test validation when setting config."""
    from src.waqt.mcp_server import set_config
    
    with app.app_context():
        # Invalid boolean
        res = set_config("auto_end", "maybe")
        assert res["status"] == "error"
        assert "Invalid value" in res["message"]

        # Valid boolean
        res = set_config("auto_end", "true")
        assert res["status"] == "success"
        assert res["new_value"] == "true" # Normalized

def test_list_config(app):
    """Test listing all configuration."""
    from src.waqt.mcp_server import list_config
    
    with app.app_context():
        res = list_config()
        assert res["status"] == "success"
        assert res["count"] > 0
        
        # Check structure
        keys = [item["key"] for item in res["settings"]]
        assert "weekly_hours" in keys
        assert "standard_hours_per_day" in keys