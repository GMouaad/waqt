"""Business logic services for time tracking operations.

This module centralizes logic for starting, stopping, and updating time entries
to ensure consistency across CLI, WebApp, and MCP interfaces.
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, Any, Union
from .models import TimeEntry, LeaveDay
from .utils import calculate_duration, get_working_days_in_range

def add_time_entry(
    entry_date: date,
    start_time: time,
    end_time: time,
    description: str = "Work session",
    category_id: Optional[int] = None,
    pause_mode: str = "none",  # 'default', 'custom', 'none'
    pause_minutes: int = 0
) -> Dict[str, Any]:
    """
    Add a completed time entry with configurable pause handling.
    
    Args:
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
    from . import db
    from .models import Settings, Category
    
    # Calculate initial duration (handles midnight crossing)
    initial_duration_hours = calculate_duration(start_time, end_time)
    
    if initial_duration_hours <= 0:
        return {
            "success": False,
            "message": "End time must be after start time."
        }
        
    # Validate pause_mode
    valid_pause_modes = ["default", "custom", "none"]
    if pause_mode not in valid_pause_modes:
        return {
            "success": False,
            "message": f"Invalid pause mode '{pause_mode}'. Must be one of: {', '.join(valid_pause_modes)}."
        }
        
    if pause_mode == "custom" and pause_minutes < 0:
        return {
            "success": False,
            "message": "Pause duration must not be negative."
        }
        
    # Validate category if provided
    if category_id:
        category = db.session.get(Category, category_id)
        if not category:
             return {
                "success": False,
                "message": f"Category with ID {category_id} not found."
            }

    # Calculate pause deduction
    pause_seconds = 0
    if pause_mode == "default":
        default_pause = Settings.get_int("pause_duration_minutes", 45)
        pause_seconds = default_pause * 60
    elif pause_mode == "custom":
        pause_seconds = pause_minutes * 60
    # elif pause_mode == "none": pause_seconds = 0
    
    # Calculate final duration
    initial_seconds = initial_duration_hours * 3600
    final_seconds = max(0, initial_seconds - pause_seconds)
    final_duration_hours = final_seconds / 3600.0
    
    # Check for existing entries on this date (excluding active ones)
    existing_entries = TimeEntry.query.filter_by(
        date=entry_date, is_active=False
    ).all()

    if existing_entries:
        return {
            "success": False,
            "message": f"An entry already exists for {entry_date}. Only one entry per day is allowed."
        }

    entry = TimeEntry(
        date=entry_date,
        start_time=start_time,
        end_time=end_time,
        duration_hours=final_duration_hours,
        accumulated_pause_seconds=pause_seconds,
        is_active=False,
        description=description.strip() or "Work session",
        category_id=category_id
    )
    
    db.session.add(entry)
    db.session.commit()
    
    return {
        "success": True,
        "message": "Time entry added successfully",
        "entry": entry
    }


def start_time_entry(
    entry_date: date,
    start_time: time,
    description: str = "Work session",
    category_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Start a new time entry.
    
    Args:
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
    from . import db
    from .models import Category
    
    # Validate category if provided
    if category_id:
        category = db.session.get(Category, category_id)
        if not category:
             return {
                "success": False,
                "message": f"Category with ID {category_id} not found."
            }
            
    # Check for open entries
    # Don't restrict to date - if you left one running yesterday, you should close it
    # But wait, existing CLI/MCP logic checks for open entries *on this date*.
    # WebApp checks for *any* open entry.
    # To standardize: WebApp logic is safer (one timer at a time globally).
    # However, CLI users might want to backfill yesterday while today runs.
    # Compromise: Check for open entry on *this* date to prevent duplicates for same day.
    # AND check for *active* entry generally to prevent multiple concurrent timers?
    #
    # Current implementations:
    # CLI: Checks open entries for *entry_date*.
    # MCP: Checks open entries for *entry_date*.
    # WebApp: Checks `get_open_entry()` (any active=True).
    #
    # Let's align with the safer WebApp approach: if ANY timer is active, warn user?
    # Or strict alignment with CLI/MCP for now to avoid breaking workflows?
    # CLI users might be annoyed if they can't backfill. 
    #
    # Let's stick to the specific date check to prevent *duplicate active entries for the same day*
    # which breaks the model. 
    
    open_entry = TimeEntry.query.filter_by(date=entry_date, is_active=True).first()
    if open_entry:
        return {
            "success": False,
            "message": f"There is already an active timer for {entry_date}.",
            "error_type": "duplicate_active"
        }

    # Create new entry
    entry = TimeEntry(
        date=entry_date,
        start_time=start_time,
        end_time=start_time, # Temporary
        duration_hours=0.0,
        is_active=True,
        description=description.strip() or "Work session",
        category_id=category_id
    )
    
    db.session.add(entry)
    db.session.commit()
    
    return {
        "success": True,
        "message": "Time tracking started",
        "entry": entry
    }

def end_time_entry(
    end_time: time,
    entry_date: date,
) -> Dict[str, Any]:
    """
    End an active time entry.
    
    Args:
        end_time: Stop time
        entry_date: Date of the entry to stop
        
    Returns:
        Dictionary with:
        - success: Boolean
        - message: Status message
        - entry: TimeEntry object
        - duration: Calculated duration
    """
    from . import db
    # Find most recent active entry for this date
    entry = TimeEntry.query.filter_by(date=entry_date, is_active=True)\
        .order_by(TimeEntry.created_at.desc()).first()
        
    if not entry:
        return {
            "success": False,
            "message": f"No active timer found for {entry_date}.",
            "error_type": "no_active_timer"
        }
        
    # Handle paused state (WebApp logic adoption)
    # If paused, we need to calculate effective duration properly
    # CLI/MCP used simple calculate_duration(start, end).
    # WebApp uses complicated pause math.
    #
    # Let's standardize on the smarter WebApp logic which respects pauses.
    # If last_pause_start_time is set, the work effectively stopped then.
    
    effective_end_dt = None
    if entry.last_pause_start_time:
        # User stopped while paused. End time = Pause start time.
        effective_end_dt = entry.last_pause_start_time
        # Reset pause to clean up
        entry.last_pause_start_time = None
    
    # If not paused, use provided end_time combined with date
    if not effective_end_dt:
        effective_end_dt = datetime.combine(entry_date, end_time)
        # Handle midnight crossing? calculate_duration does it.
        # But here we are explicit.
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
    
    db.session.commit()
    
    return {
        "success": True,
        "message": "Time tracking stopped",
        "entry": entry,
        "duration": duration_hours
    }

def update_time_entry(
    entry_id: int,
    start_time: Optional[time] = None,
    end_time: Optional[time] = None,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
    date_check: Optional[date] = None
) -> Dict[str, Any]:
    """
    Update an existing time entry.
    
    Args:
        entry_id: ID of entry to update
        start_time: New start time (optional)
        end_time: New end time (optional)
        description: New description (optional)
        category_id: New category ID (optional - None means no change, 0 means clear?)
                     For now let's assume if it's passed (even None if strictly typed, but here Optional)
                     we might need a way to clear it. 
                     Let's say -1 clears it, or we treat None as 'no change'.
                     Let's treat None as 'no change' for now to keep it simple.
        date_check: Optional date to verify against entry
        
    Returns:
        Dictionary with success/message/entry
    """
    from . import db
    from .models import Category
    
    entry = db.session.get(TimeEntry, entry_id)
    
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
        if category_id == 0: # Convention to clear category
             entry.category_id = None
        else:
             category = db.session.get(Category, category_id)
             if category:
                 entry.category_id = category_id
             else:
                 return {"success": False, "message": f"Category {category_id} not found."}
        
    # Recalculate duration if times changed
    # Note: editing overrides pause calculations currently.
    # If you edit start/end manually, we assume you know the exact bounds
    # and we reset pause logic usually? Or we blindly trust calculate_duration?
    # Existing CLI/MCP/WebApp logic uses calculate_duration(start, end) on edit.
    # This ignores accumulated_pause_seconds! 
    # This might be a bug or feature (simplification).
    # We will stick to existing behavior: Edit = Reset duration based on new bounds.
    
    if start_time or end_time:
        duration = calculate_duration(entry.start_time, entry.end_time)
        if duration <= 0:
            return {"success": False, "message": "End time must be after start time."}
        entry.duration_hours = duration
        
    db.session.commit()
    
    return {
        "success": True,
        "message": "Entry updated",
        "entry": entry
    }


def create_leave_requests(
    start_date: date,
    end_date: date,
    leave_type: str,
    description: str = "",
    db_session = None
) -> Dict[str, int]:
    """
    Create leave records for a date range, skipping duplicates and weekends.
    
    Args:
        start_date: Start date of leave
        end_date: End date of leave
        leave_type: Type of leave ('vacation' or 'sick')
        description: Description/notes
        db_session: Optional database session to use (defaults to global db.session)
        
    Returns:
        Dictionary with:
        - created: Number of records created
        - skipped: Number of records skipped (already existed)
        - weekend_days: Number of weekend days excluded
        - working_days: Total working days in range
    """
    from . import db
    session = db_session if db_session else db.session
    
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
            "working_days": 0
        }

    # Query existing leave days in the range to avoid duplicates
    existing_leaves = LeaveDay.query.filter(
        LeaveDay.date >= start_date,
        LeaveDay.date <= end_date
    ).all()
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

    return {
        "created": created_count,
        "skipped": skipped_count,
        "weekend_days": weekend_days,
        "working_days": len(working_days)
    }

