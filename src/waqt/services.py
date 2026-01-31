"""Business logic services for time tracking operations.

This module centralizes logic for starting, stopping, and updating time entries
to ensure consistency across CLI, WebApp, and MCP interfaces.

All service functions accept a SQLAlchemy Session as their first parameter.
The caller is responsible for session lifecycle (commit/rollback) via
the `database.get_session()` context manager.
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, Any, List
import logging
from sqlalchemy.orm import Session

from .models import TimeEntry, LeaveDay, Settings, Category, Template
from .utils import (
    calculate_duration,
    get_working_days_in_range,
    detect_import_format,
    parse_time_entries_from_json,
    parse_time_entries_from_csv,
    parse_time_entries_from_excel,
    validate_time_entry_data,
    validate_leave_day_data,
    normalize_date_string,
    normalize_time_string,
)

logger = logging.getLogger(__name__)


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
            "message": (
                f"Invalid pause mode '{pause_mode}'. "
                f"Must be one of: {', '.join(valid_pause_modes)}."
            ),
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
            "message": (
                f"An entry already exists for {entry_date}. "
                "Only one entry per day is allowed."
            ),
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


# =============================================================================
# Import Functions
# =============================================================================


def _resolve_category(
    session: Session,
    category_name: Optional[str],
    category_code: Optional[str],
    auto_create: bool,
) -> tuple[Optional[int], Optional[str]]:
    """
    Resolve category by code or name, optionally creating if not found.

    Args:
        session: SQLAlchemy session
        category_name: Category name from import data
        category_code: Category code from import data
        auto_create: Whether to create missing categories

    Returns:
        Tuple of (category_id or None, created_category_name or None)
    """
    if not category_name and not category_code:
        return None, None

    # Try to find by code first (more reliable for matching)
    if category_code:
        category = session.query(Category).filter_by(code=category_code).first()
        if category:
            return category.id, None

    # Try to find by name
    if category_name:
        category = session.query(Category).filter_by(name=category_name).first()
        if category:
            return category.id, None

    # Category not found - create if allowed
    if auto_create and category_name:
        # Generate code if not provided
        if not category_code:
            # Use first 6 chars, uppercase, alphanumeric only
            code_base = "".join(c for c in category_name.upper() if c.isalnum())[:6]
            category_code = code_base if code_base else "IMPORT"

            # Ensure code is unique
            existing = session.query(Category).filter_by(code=category_code).first()
            if existing:
                # Append number to make unique
                for i in range(1, 100):
                    new_code = f"{category_code[:5]}{i}"
                    if not session.query(Category).filter_by(code=new_code).first():
                        category_code = new_code
                        break

        new_category = Category(
            name=category_name,
            code=category_code,
            description=f"Auto-created during import on {datetime.now().date()}",
            is_active=True,
        )
        session.add(new_category)
        session.flush()  # Get the ID
        return new_category.id, category_name

    return None, None


def _check_duplicate_entry(
    session: Session,
    entry_date: date,
    start_time: time,
    end_time: time,
) -> Optional[TimeEntry]:
    """
    Check if a matching time entry already exists.

    Args:
        session: SQLAlchemy session
        entry_date: Date of the entry
        start_time: Start time
        end_time: End time

    Returns:
        Existing TimeEntry if found, None otherwise
    """
    return (
        session.query(TimeEntry)
        .filter_by(
            date=entry_date,
            start_time=start_time,
            end_time=end_time,
        )
        .first()
    )


def _check_duplicate_leave(
    session: Session,
    leave_date: date,
) -> Optional[LeaveDay]:
    """
    Check if a leave day already exists for this date.

    Args:
        session: SQLAlchemy session
        leave_date: Date to check

    Returns:
        Existing LeaveDay if found, None otherwise
    """
    return session.query(LeaveDay).filter_by(date=leave_date).first()


def import_time_entries(
    session: Session,
    file_path: str,
    import_format: str = "auto",
    on_conflict: str = "skip",
    auto_create_categories: bool = True,
    include_leave_days: bool = True,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Import time entries and leave days from a file.

    Args:
        session: SQLAlchemy session
        file_path: Path to the import file
        import_format: 'csv', 'json', 'excel', or 'auto' (auto-detect)
        on_conflict: How to handle duplicates:
            - 'skip': Skip duplicate entries (default)
            - 'overwrite': Update existing entries with imported data
            - 'duplicate': Create new entries regardless of duplicates
        auto_create_categories: Create missing categories automatically
        include_leave_days: Import leave days from JSON (if present)
        dry_run: Preview without saving changes

    Returns:
        Dictionary with:
        - success: bool
        - entries_imported: int
        - entries_skipped: int
        - entries_updated: int (for overwrite mode)
        - leave_days_imported: int
        - leave_days_skipped: int
        - categories_created: List[str]
        - errors: List[str]
        - warnings: List[str]
    """
    result = {
        "success": True,
        "entries_imported": 0,
        "entries_skipped": 0,
        "entries_updated": 0,
        "leave_days_imported": 0,
        "leave_days_skipped": 0,
        "categories_created": [],
        "errors": [],
        "warnings": [],
    }

    # Validate on_conflict option
    valid_conflict_modes = ["skip", "overwrite", "duplicate"]
    if on_conflict not in valid_conflict_modes:
        result["success"] = False
        result["errors"].append(
            f"Invalid on_conflict mode '{on_conflict}'. "
            f"Must be one of: {', '.join(valid_conflict_modes)}"
        )
        return result

    # Detect format if auto
    try:
        if import_format == "auto":
            import_format = detect_import_format(file_path)
    except ValueError as e:
        result["success"] = False
        result["errors"].append(str(e))
        return result

    # Read and parse file
    try:
        if import_format == "json":
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            parsed = parse_time_entries_from_json(content)
        elif import_format == "csv":
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            parsed = parse_time_entries_from_csv(content)
        elif import_format == "excel":
            with open(file_path, "rb") as f:
                content = f.read()
            parsed = parse_time_entries_from_excel(content)
        else:
            result["success"] = False
            result["errors"].append(f"Unsupported format: {import_format}")
            return result
    except (ValueError, OSError) as e:
        result["success"] = False
        result["errors"].append(f"Failed to read/parse file: {e}")
        return result

    entries_data = parsed.get("entries", [])
    leave_data = parsed.get("leave_days", [])

    # Process time entries
    for idx, entry_data in enumerate(entries_data, 1):
        # Validate entry
        is_valid, validation_errors = validate_time_entry_data(entry_data)
        if not is_valid:
            for err in validation_errors:
                result["errors"].append(f"Entry {idx}: {err}")
            result["entries_skipped"] += 1
            continue

        # Parse date and times
        entry_date = normalize_date_string(str(entry_data["date"]))
        start_time = normalize_time_string(str(entry_data["start_time"]))
        end_time = normalize_time_string(str(entry_data["end_time"]))

        if not entry_date or not start_time or not end_time:
            result["entries_skipped"] += 1
            continue

        # Check for duplicates
        existing = _check_duplicate_entry(session, entry_date, start_time, end_time)

        if existing:
            if on_conflict == "skip":
                result["entries_skipped"] += 1
                continue
            elif on_conflict == "overwrite":
                # Update existing entry
                existing.description = (
                    entry_data.get("description", "").strip() or existing.description
                )

                # Resolve category for update
                category_id, created_name = _resolve_category(
                    session,
                    entry_data.get("category"),
                    entry_data.get("category_code"),
                    auto_create_categories,
                )
                if created_name:
                    result["categories_created"].append(created_name)
                if category_id:
                    existing.category_id = category_id

                result["entries_updated"] += 1
                continue
            # else: on_conflict == "duplicate" - continue to create new

        # Resolve category
        category_id, created_name = _resolve_category(
            session,
            entry_data.get("category"),
            entry_data.get("category_code"),
            auto_create_categories,
        )
        if created_name:
            result["categories_created"].append(created_name)

        # Calculate duration
        duration_hours = calculate_duration(start_time, end_time)
        if duration_hours <= 0:
            result["warnings"].append(
                f"Entry {idx} ({entry_date}): Invalid time range, skipping"
            )
            result["entries_skipped"] += 1
            continue

        # Check for excessive duration
        if duration_hours > 16:
            result["warnings"].append(
                f"Entry {idx} ({entry_date}): Duration {duration_hours:.1f}h exceeds 16 hours"
            )

        # Create new entry
        if not dry_run:
            new_entry = TimeEntry(
                date=entry_date,
                start_time=start_time,
                end_time=end_time,
                duration_hours=duration_hours,
                description=entry_data.get("description", "").strip(),
                category_id=category_id,
                is_active=False,
                accumulated_pause_seconds=0,
            )
            session.add(new_entry)

        result["entries_imported"] += 1

    # Process leave days (JSON only)
    if include_leave_days and leave_data:
        for idx, leave_item in enumerate(leave_data, 1):
            # Validate leave day
            is_valid, validation_errors = validate_leave_day_data(leave_item)
            if not is_valid:
                for err in validation_errors:
                    result["errors"].append(f"Leave day {idx}: {err}")
                result["leave_days_skipped"] += 1
                continue

            leave_date = normalize_date_string(str(leave_item["date"]))
            if not leave_date:
                result["leave_days_skipped"] += 1
                continue

            # Check for duplicate leave
            existing_leave = _check_duplicate_leave(session, leave_date)
            if existing_leave:
                result["leave_days_skipped"] += 1
                continue

            # Create leave day
            if not dry_run:
                new_leave = LeaveDay(
                    date=leave_date,
                    leave_type=leave_item.get("leave_type", "").lower(),
                    description=leave_item.get("description", ""),
                )
                session.add(new_leave)

            result["leave_days_imported"] += 1

    # Remove duplicate category names
    result["categories_created"] = list(set(result["categories_created"]))

    # Set success based on whether any entries were imported
    if result["entries_imported"] == 0 and result["leave_days_imported"] == 0:
        if result["errors"]:
            result["success"] = False
        else:
            result["success"] = True  # No errors, but nothing to import
            result["warnings"].append("No new entries to import")

    return result


# =============================================================================
# Template Functions
# =============================================================================


def create_template(
    session: Session,
    name: str,
    start_time: time,
    end_time: Optional[time] = None,
    duration_minutes: Optional[int] = None,
    pause_mode: str = "default",
    pause_minutes: int = 0,
    category_id: Optional[int] = None,
    description: str = "Work session",
    is_default: bool = False,
) -> Dict[str, Any]:
    """
    Create a new time entry template.

    Args:
        session: SQLAlchemy session
        name: Template name (must be unique)
        start_time: Start time
        end_time: End time (optional if duration set)
        duration_minutes: Duration in minutes (optional if end_time set)
        pause_mode: Pause behavior ('default', 'custom', 'none')
        pause_minutes: Custom pause duration in minutes
        category_id: Category ID
        description: Template description
        is_default: Set as default template

    Returns:
        Dictionary with status and created template details
    """
    try:
        # validate inputs
        if not end_time and not duration_minutes:
            return {
                "success": False,
                "message": "Either end_time or duration_minutes must be provided",
            }

        # Check uniqueness
        existing = session.query(Template).filter(Template.name == name).first()
        if existing:
            return {
                "success": False,
                "message": f"Template with name '{name}' already exists",
            }

        # Handle default preference
        if is_default:
            _clear_default_template(session)

        # Create template
        template = Template(
            name=name,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            pause_mode=pause_mode,
            pause_minutes=pause_minutes,
            category_id=category_id,
            description=description,
            is_default=is_default,
        )
        session.add(template)
        session.commit()

        return {
            "success": True,
            "message": f"Template '{name}' created successfully",
            "template": template.to_dict(),
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating template: {e}")
        return {"success": False, "message": f"Error creating template: {str(e)}"}


def get_template(session: Session, name: str) -> Optional[Template]:
    """Get a template by name."""
    return session.query(Template).filter(Template.name == name).first()


def get_template_by_id(session: Session, template_id: int) -> Optional[Template]:
    """Get a template by ID."""
    return session.query(Template).filter(Template.id == template_id).first()


def list_templates(session: Session) -> List[Template]:
    """List all templates ordered by name."""
    return session.query(Template).order_by(Template.name).all()


def update_template(session: Session, template_id: int, **kwargs) -> Dict[str, Any]:
    """Update an existing template."""
    try:
        template = session.query(Template).filter(Template.id == template_id).first()
        if not template:
            return {"success": False, "message": "Template not found"}

        if "name" in kwargs and kwargs["name"] != template.name:
            # Check for naming conflict
            existing = (
                session.query(Template).filter(Template.name == kwargs["name"]).first()
            )
            if existing:
                return {
                    "success": False,
                    "message": f"Template with name '{kwargs['name']}' already exists",
                }
            template.name = kwargs["name"]

        if "is_default" in kwargs:
            if kwargs["is_default"] and not template.is_default:
                _clear_default_template(session)
            template.is_default = kwargs["is_default"]

        # Update other fields
        fields = [
            "start_time",
            "end_time",
            "duration_minutes",
            "pause_mode",
            "pause_minutes",
            "category_id",
            "description",
        ]
        for field in fields:
            if field in kwargs:
                setattr(template, field, kwargs[field])

        session.commit()
        return {
            "success": True,
            "message": "Template updated successfully",
            "template": template.to_dict(),
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating template: {e}")
        return {"success": False, "message": f"Error updating template: {str(e)}"}


def delete_template(session: Session, template_id: int) -> Dict[str, Any]:
    """Delete a template."""
    try:
        template = session.query(Template).filter(Template.id == template_id).first()
        if not template:
            return {"success": False, "message": "Template not found"}

        session.delete(template)
        session.commit()
        return {"success": True, "message": "Template deleted successfully"}
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting template: {e}")
        return {"success": False, "message": f"Error deleting template: {str(e)}"}


def apply_template(
    session: Session,
    template_name: Optional[str] = None,
    target_date: Optional[date] = None,
    **overrides,
) -> Dict[str, Any]:
    """
    Apply a template to create a time entry for a specific date.

    Args:
        session: SQLAlchemy session
        template_name: Name of template to apply (uses default if None)
        target_date: Date to apply to (default: today)
        **overrides: Optional overrides for start_time, description, etc.
    """
    try:
        target_date = target_date or date.today()

        if template_name:
            template = get_template(session, template_name)
            if not template:
                return {
                    "success": False,
                    "message": f"Template '{template_name}' not found",
                }
        else:
            # Get default template
            template = (
                session.query(Template).filter(Template.is_default.is_(True)).first()
            )
            if not template:
                return {
                    "success": False,
                    "message": "No default template set and no name provided",
                }

        # Calculate parameters
        start_time = overrides.get("start_time", template.start_time)
        description = overrides.get("description", template.description)
        category_id = overrides.get("category_id", template.category_id)

        # Calculate end time
        if template.end_time:
            # If end_time is set in template, we try to respect it.
            # However, if user overrides start_time, we might want to shift block.
            # Using template's calculation logic.
            end_time = template.get_end_time(start_time_ref=start_time)
        elif template.duration_minutes:
            # Calculate from duration
            # We calculate end time from duration manually here
            end_time = template.get_end_time(start_time_ref=start_time)
        else:
            return {
                "success": False,
                "message": "Template is invalid (no end time or duration)",
            }

        # Check for duplicate
        existing = _check_duplicate_entry(session, target_date, start_time, end_time)
        if existing:
            return {
                "success": False,
                "message": f"Time entry already exists for {target_date} overlapping this time",
            }

        # Call add_time_entry
        result = add_time_entry(
            session=session,
            entry_date=target_date,
            start_time=start_time,
            end_time=end_time,
            description=description,
            category_id=category_id,
            pause_mode=template.pause_mode,
            pause_minutes=overrides.get("pause_minutes", template.pause_minutes),
        )

        if result["success"]:
            result["message"] = f"Applied template '{template.name}' to {target_date}"

        return result

    except Exception as e:
        session.rollback()
        logger.error(f"Error applying template: {e}")
        return {"success": False, "message": f"Error applying template: {str(e)}"}


def _clear_default_template(session: Session):
    """Unset is_default for all templates."""
    session.query(Template).filter(Template.is_default.is_(True)).update(
        {"is_default": False}
    )
    session.commit()
