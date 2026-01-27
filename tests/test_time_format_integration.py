from datetime import datetime, time


def test_submit_time_entry_12_hour_format(app):
    """Test submitting a time entry using 12-hour format."""
    from waqt.models import TimeEntry, Settings

    client = app.test_client()

    with app.app_context():
        # Set 12-hour format preference
        Settings.set_setting("time_format", "12")

        # Submit entry with 12-hour format
        response = client.post(
            "/time-entry",
            data={
                "date": "2024-01-01",
                "start_time": "02:30 PM",
                "end_time": "05:30 PM",
                "description": "Afternoon work",
                "pause_mode": "none",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Time entry added successfully" in response.data

        # Verify storage
        entry = TimeEntry.query.filter_by(description="Afternoon work").first()
        assert entry is not None
        assert entry.start_time == time(14, 30)
        assert entry.end_time == time(17, 30)
        assert entry.duration_hours == 3.0


def test_submit_time_entry_24_hour_format_fallback(app):
    """Test submitting 24-hour format even when 12-hour is configured (fallback)."""
    from waqt.models import TimeEntry, Settings

    client = app.test_client()

    with app.app_context():
        # Set 12-hour format preference
        Settings.set_setting("time_format", "12")

        # Submit entry with 24-hour format
        response = client.post(
            "/time-entry",
            data={
                "date": "2024-01-02",
                "start_time": "14:30",
                "end_time": "17:30",
                "description": "Fallback work",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Time entry added successfully" in response.data

        # Verify storage
        entry = TimeEntry.query.filter_by(description="Fallback work").first()
        assert entry is not None
        assert entry.start_time == time(14, 30)
        assert entry.end_time == time(17, 30)


def test_edit_time_entry_format_handling(app):
    """Test editing a time entry using mixed formats."""
    from waqt.models import TimeEntry, Settings
    from waqt import db

    client = app.test_client()

    with app.app_context():
        # Create initial entry
        entry = TimeEntry(
            date=datetime(2024, 1, 3).date(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            duration_hours=3.0,
            description="Original",
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

        # Set 12-hour format preference
        Settings.set_setting("time_format", "12")

        # Edit using 12-hour format
        response = client.post(
            f"/time-entry/{entry_id}/edit",
            data={
                "start_time": "01:00 PM",
                "end_time": "04:00 PM",
                "description": "Edited 12h",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Time entry updated successfully" in response.data

        updated_entry = db.session.get(TimeEntry, entry_id)
        assert updated_entry.start_time == time(13, 0)
        assert updated_entry.end_time == time(16, 0)
        assert updated_entry.description == "Edited 12h"

        # Now edit using 24-hour format (fallback)
        response = client.post(
            f"/time-entry/{entry_id}/edit",
            data={
                "start_time": "10:00",
                "end_time": "11:00",
                "description": "Edited 24h",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Time entry updated successfully" in response.data

        updated_entry = db.session.get(TimeEntry, entry_id)
        assert updated_entry.start_time == time(10, 0)
        assert updated_entry.end_time == time(11, 0)
        assert updated_entry.description == "Edited 24h"
