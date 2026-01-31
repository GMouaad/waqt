from datetime import time, date
from waqt.models import Template, TimeEntry
from waqt.services import (
    create_template,
    list_templates,
    get_template,
    delete_template,
    apply_template,
    update_template,
)


def test_create_template(db_session):
    result = create_template(
        db_session,
        name="Morning Routine",
        start_time=time(9, 0),
        duration_minutes=60,
        description="Daily standup",
    )
    assert result["success"] is True

    template = db_session.query(Template).filter_by(name="Morning Routine").first()
    assert template is not None
    assert template.start_time == time(9, 0)
    assert template.duration_minutes == 60
    assert template.description == "Daily standup"


def test_create_duplicate_template(db_session):
    create_template(
        db_session, name="Duplicate", start_time=time(9, 0), duration_minutes=60
    )
    result = create_template(
        db_session, name="Duplicate", start_time=time(10, 0), duration_minutes=60
    )
    assert result["success"] is False
    assert "already exists" in result["message"]


def test_list_templates(db_session):
    create_template(db_session, name="T1", start_time=time(9, 0), duration_minutes=60)
    create_template(db_session, name="T2", start_time=time(10, 0), duration_minutes=60)

    templates = list_templates(db_session)
    # The session fixture usually commits or flushes?
    # Actually services commit themselves or caller commits?
    # Services take session and add. Caller commits.
    # But in test, create_template calls add.
    # list_templates calls query.all().
    # Should be visible in same session.

    # Filter by created names to avoid interference if any
    relevant = [t for t in templates if t.name in ["T1", "T2"]]
    assert len(relevant) == 2


def test_get_template(db_session):
    create_template(
        db_session, name="Target", start_time=time(9, 0), duration_minutes=60
    )

    t = get_template(db_session, "Target")
    assert t is not None
    assert t.name == "Target"

    t_none = get_template(db_session, "NonExistent")
    assert t_none is None


def test_delete_template(db_session):
    create_template(
        db_session, name="To Delete", start_time=time(9, 0), duration_minutes=60
    )
    t = get_template(db_session, "To Delete")

    result = delete_template(db_session, t.id)
    assert result["success"] is True

    t_deleted = get_template(db_session, "To Delete")
    assert t_deleted is None


def test_apply_template(db_session):
    create_template(
        db_session,
        name="Work Layout",
        start_time=time(9, 0),
        duration_minutes=120,
        description="Deep Work",
    )

    target_date = date(2025, 1, 1)
    result = apply_template(db_session, "Work Layout", target_date)
    assert result["success"] is True

    entry = db_session.query(TimeEntry).filter_by(date=target_date).first()
    assert entry is not None
    assert entry.start_time == time(9, 0)
    # End time should be start + 120m = 11:00
    assert entry.end_time == time(11, 0)
    assert entry.description == "Deep Work"


def test_apply_default_template(db_session):
    create_template(
        db_session,
        name="Default one",
        start_time=time(8, 0),
        is_default=True,
        duration_minutes=60,
    )

    target_date = date(2025, 1, 2)
    result = apply_template(db_session, target_date=target_date)  # No name provided
    assert result["success"] is True

    entry = db_session.query(TimeEntry).filter_by(date=target_date).first()
    assert entry is not None
    assert entry.start_time == time(8, 0)


def test_apply_template_overrides(db_session):
    create_template(
        db_session,
        name="Override Me",
        start_time=time(9, 0),
        description="Original",
        duration_minutes=60,
    )

    target_date = date(2025, 1, 3)
    result = apply_template(
        db_session,
        "Override Me",
        target_date,
        start_time=time(10, 0),
        description="Overridden",
    )
    assert result["success"] is True

    entry = db_session.query(TimeEntry).filter_by(date=target_date).first()
    assert entry.start_time == time(10, 0)
    assert entry.description == "Overridden"


def test_update_template(db_session):
    create_template(
        db_session, name="Old Name", start_time=time(9, 0), duration_minutes=60
    )
    t = get_template(db_session, "Old Name")

    result = update_template(db_session, t.id, name="New Name", duration_minutes=90)
    assert result["success"] is True

    t_updated = get_template(db_session, "New Name")
    assert t_updated is not None
    assert t_updated.duration_minutes == 90
    assert get_template(db_session, "Old Name") is None


def test_update_template_name_conflict(db_session):
    create_template(db_session, name="T1", start_time=time(9, 0), duration_minutes=60)
    create_template(db_session, name="T2", start_time=time(10, 0), duration_minutes=60)

    t1 = get_template(db_session, "T1")
    result = update_template(db_session, t1.id, name="T2")

    assert result["success"] is False
    assert "already exists" in result["message"]


def test_update_template_not_found(db_session):
    result = update_template(db_session, 999, name="New Name")
    assert result["success"] is False
    assert "not found" in result["message"]


def test_delete_template_not_found(db_session):
    result = delete_template(db_session, 999)
    assert result["success"] is False
    assert "not found" in result["message"]


def test_apply_template_not_found(db_session):
    result = apply_template(db_session, "NonExistent", date(2025, 1, 1))
    assert result["success"] is False
    assert "not found" in result["message"]


def test_apply_no_default_template(db_session):
    # Ensure no default exists
    result = apply_template(db_session, target_date=date(2025, 1, 1))
    assert result["success"] is False
    assert "No default template set" in result["message"]
