"""Business logic services for time tracking operations.

This module centralizes logic for starting, stopping, and updating time entries
to ensure consistency across CLI, WebApp, and MCP interfaces.

All service functions accept a SQLAlchemy Session as their first parameter.
The caller is responsible for session lifecycle (commit/rollback) via
the `database.get_session()` context manager.
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from .models import TimeEntry, LeaveDay, Settings, Category
from .utils import calculate_duration, get_working_days_in_range


def add_time_entry(
    session: Session,
    entry_date: date,
    start_time: time,
    end_time: time,
    description: str = "Work session",
    category_id: Optional[int] = None,
    pause_mode: str = "none",  # 'default', 'custom', 'none'
    pause_minutes: int = 0,
) -> Dict[str, Any]:
    """
    Add a completed time entry with configurable pause handling.

    Args:
        session: SQLAlchemy session
        entry_date: Date of work
        start_time: Start time
        end_time: End time
        description: Work description
        category_id: Optional category ID
        pause_mode: How to handle pause ('default', 'custom', 'none')
        pause_minutes: Custom pause duration in minutes (used if pause_mode='custom')

    Returns:
        Dictionary with:
        - success: Boolean
        - message: Status message
        - entry: TimeEntry object (if successful)
    """
    # Calculate initial duration (handles midnight crossing)
    initial_duration_hours = calculate_duration(start_time, end_time)

    if initial_duration_hours <= 0:
        return {"success": False, "message": "End time must be after start time."}

    # Validate pause_mode
    valid_pause_modes = ["default", "custom", "none"]
    if pause_mode not in valid_pause_modes:
        return {
            "success": False,
            "message": f"Invalid pause mode '{pause_mode}'. Must be one of: {', '.join(valid_pause_modes)}.",
        }

    if pause_mode == "custom" and pause_minutes < 0:
        return {"success": False, "message": "Pause duration must not be negative."}

    # Validate category if provided
    if category_id:
        category = session.get(Category, category_id)
        if not category:
            return {
                "success": False,
                "message": f"Category with ID {category_id} not found.",
            }

    # Calculate pause deduction
    pause_seconds = 0
    if pause_mode == "default":
        default_pause = Settings.get_int_with_session(
            session, "pause_duration_minutes", 45
        )
        pause_seconds = default_pause * 60
    elif pause_mode == "custom":
        pause_seconds = pause_minutes * 60
    # elif pause_mode == "none": pause_seconds = 0

    # Calculate final duration
    initial_seconds = initial_duration_hours * 3600
    final_seconds = max(0, initial_seconds - pause_seconds)
    final_duration_hours = final_seconds / 3600.0

    # Check for existing entries on this date (excluding active ones)
    existing_entries = (
        session.query(TimeEntry).filter_by(date=entry_date, is_active=False).all()
    )

    if existing_entries:
        return {
            "success": False,
            "message": f"An entry already exists for {entry_date}. Only one entry per day is allowed.",
        }

    entry = TimeEntry(
        date=entry_date,
        start_time=start_time,
        end_time=end_time,
        duration_hours=final_duration_hours,
        accumulated_pause_seconds=pause_seconds,
        is_active=False,
        description=description.strip() or "Work session",
        category_id=category_id,
    )

    session.add(entry)
    # Note: Commit is handled by the caller's context manager

    return {"success": True, "message": "Time entry added successfully", "entry": entry}


def start_time_entry(
    session: Session,
    entry_date: date,
    start_time: time,
    description: str = "Work session",
    category_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Start a new time entry.

    Args:
        session: SQLAlchemy session
        entry_date: Date of work
        start_time: Start time
        description: Work description
        category_id: Optional category ID

    Returns:
        Dictionary with:
        - success: Boolean
        - message: Status message
        - entry: TimeEntry object (if successful)
    """
    # Validate category if provided
    if category_id:
        category = session.get(Category, category_id)
        if not category:
            return {
                "success": False,
                "message": f"Category with ID {category_id} not found.",
            }

    # Check for open entries on this date
    open_entry = (
        session.query(TimeEntry).filter_by(date=entry_date, is_active=True).first()
    )

    if open_entry:
        return {
            "success": False,
            "message": f"There is already an active timer for {entry_date}.",
            "error_type": "duplicate_active",
        }

    # Create new entry
    entry = TimeEntry(
        date=entry_date,
        start_time=start_time,
        end_time=start_time,  # Temporary
        duration_hours=0.0,
        is_active=True,
        description=description.strip() or "Work session",
        category_id=category_id,
    )

    session.add(entry)
    # Note: Commit is handled by the caller's context manager

    return {"success": True, "message": "Time tracking started", "entry": entry}


def end_time_entry(
    session: Session,
    end_time: time,
    entry_date: date,
) -> Dict[str, Any]:
    """
    End an active time entry.

    Args:
        session: SQLAlchemy session
        end_time: Stop time
        entry_date: Date of the entry to stop

    Returns:
        Dictionary with:
        - success: Boolean
        - message: Status message
        - entry: TimeEntry object
        - duration: Calculated duration
    """
    # Find most recent active entry for this date
    entry = (
        session.query(TimeEntry)
        .filter_by(date=entry_date, is_active=True)
        .order_by(TimeEntry.created_at.desc())
        .first()
    )

    if not entry:
        return {
            "success": False,
            "message": f"No active timer found for {entry_date}.",
            "error_type": "no_active_timer",
        }

    # Handle paused state
    effective_end_dt = None
    if entry.last_pause_start_time:
        # User stopped while paused. End time = Pause start time.
        effective_end_dt = entry.last_pause_start_time
        # Reset pause to clean up
        entry.last_pause_start_time = None

    # If not paused, use provided end_time combined with date
    if not effective_end_dt:
        effective_end_dt = datetime.combine(entry_date, end_time)
        # Handle midnight crossing
        start_dt = datetime.combine(entry_date, entry.start_time)
        if effective_end_dt < start_dt:
            effective_end_dt += timedelta(days=1)

    # Calculate duration in hours, subtracting accumulated pauses
    start_dt = datetime.combine(entry.date, entry.start_time)
    total_elapsed = (effective_end_dt - start_dt).total_seconds()
    actual_work_seconds = total_elapsed - (entry.accumulated_pause_seconds or 0)
    duration_hours = max(0, actual_work_seconds / 3600.0)

    # Update entry
    entry.end_time = effective_end_dt.time()
    entry.duration_hours = duration_hours
    entry.is_active = False

    # Note: Commit is handled by the caller's context manager

    return {
        "success": True,
        "message": "Time tracking stopped",
        "entry": entry,
        "duration": duration_hours,
    }


def update_time_entry(
    session: Session,
    entry_id: int,
    start_time: Optional[time] = None,
    end_time: Optional[time] = None,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
    date_check: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Update an existing time entry.

    Args:
        session: SQLAlchemy session
        entry_id: ID of entry to update
        start_time: New start time (optional)
        end_time: New end time (optional)
        description: New description (optional)
        category_id: New category ID (optional). If None, the category is not
                     changed. If 0, the category is cleared. For any other
                     positive value, the entry is associated with the given
                     category if it exists.
        date_check: Optional date to verify against entry

    Returns:
        Dictionary with success status, message, and updated entry.
    """
    entry = session.get(TimeEntry, entry_id)

    if not entry:
        return {"success": False, "message": f"Entry {entry_id} not found."}

    if date_check and entry.date != date_check:
        return {"success": False, "message": f"Entry {entry_id} date mismatch."}

    if entry.is_active:
        return {"success": False, "message": "Cannot edit active timer."}

    # Update fields
    if start_time:
        entry.start_time = start_time
    if end_time:
        entry.end_time = end_time
    if description:
        entry.description = description.strip()

    if category_id is not None:
        if category_id == 0:  # Convention to clear category
            entry.category_id = None
        else:
            category = session.get(Category, category_id)
            if category:
                entry.category_id = category_id
            else:
                return {
                    "success": False,
                    "message": f"Category {category_id} not found.",
                }

    # Recalculate duration if times changed
    if start_time or end_time:
        duration = calculate_duration(entry.start_time, entry.end_time)
        if duration <= 0:
            return {"success": False, "message": "End time must be after start time."}
        entry.duration_hours = duration

    # Note: Commit is handled by the caller's context manager

    return {"success": True, "message": "Entry updated", "entry": entry}


def create_leave_requests(
    session: Session,
    start_date: date,
    end_date: date,
    leave_type: str,
    description: str = "",
) -> Dict[str, int]:
    """
    Create leave records for a date range, skipping duplicates and weekends.

    Args:
        session: SQLAlchemy session
        start_date: Start date of leave
        end_date: End date of leave
        leave_type: Type of leave ('vacation' or 'sick')
        description: Description/notes

    Returns:
        Dictionary with:
        - created: Number of records created
        - skipped: Number of records skipped (already existed)
        - weekend_days: Number of weekend days excluded
        - working_days: Total working days in range
    """
    # Get working days (excludes weekends)
    working_days = get_working_days_in_range(start_date, end_date)

    # Calculate stats for return
    all_days_count = (end_date - start_date).days + 1
    weekend_days = all_days_count - len(working_days)

    if not working_days:
        return {
            "created": 0,
            "skipped": 0,
            "weekend_days": weekend_days,
            "working_days": 0,
        }

    # Query existing leave days in the range to avoid duplicates
    existing_leaves = (
        session.query(LeaveDay)
        .filter(LeaveDay.date >= start_date, LeaveDay.date <= end_date)
        .all()
    )
    existing_dates = {leave.date for leave in existing_leaves}

    created_count = 0
    skipped_count = 0

    for leave_date in working_days:
        if leave_date in existing_dates:
            skipped_count += 1
            continue

        leave_day = LeaveDay(
            date=leave_date,
            leave_type=leave_type,
            description=description,
        )
        session.add(leave_day)
        created_count += 1

    # Note: Commit is handled by the caller's context manager

    return {
        "created": created_count,
        "skipped": skipped_count,
        "weekend_days": weekend_days,
        "working_days": len(working_days),
    }
