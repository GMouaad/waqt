"""MCP server for waqt time tracking application.

This module implements a Model Context Protocol (MCP) server that exposes
time tracking functionality to LLM applications, mirroring the CLI capabilities.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP

from .database import get_session, initialize_database
from .models import TimeEntry, LeaveDay, Settings
from .utils import (
    get_week_bounds,
    get_month_bounds,
    calculate_weekly_stats,
    calculate_monthly_stats,
    format_hours,
    export_time_entries_to_csv,
    export_time_entries_to_json,
    format_time,
    get_working_days_in_range,
    calculate_leave_hours,
)
from .services import (
    start_time_entry,
    end_time_entry,
    update_time_entry,
    add_time_entry,
    create_leave_requests,
)
from .config import (
    CONFIG_DEFAULTS,
    CONFIG_TYPES,
    CONFIG_DESCRIPTIONS,
    validate_config_value,
    normalize_bool_value,
)
from .logging import get_mcp_logger

# Initialize logger for MCP server
logger = get_mcp_logger()


# Initialize FastMCP server
mcp = FastMCP(
    name="waqt",
    instructions="""Waqt MCP Server

A Model Context Protocol server for time tracking functionality.
This server provides tools for tracking work hours, managing time entries,
and generating reports.

Available tools:
- start: Start time tracking for a day
- end: End time tracking for a day
- add_entry: Add a completed time entry with pause support
- edit_entry: Edit an existing time entry
- summary: Get time summary for week or month
- leave_request: Request multi-day leave (vacation/sick)
- list_entries: List time entries for a period
- export_entries: Export time entries to CSV format
- list_config: List all configuration settings
- get_config: Get a specific configuration setting
- set_config: Set a configuration setting

Standard work schedule: 8 hours/day, 40 hours/week
Overtime is automatically calculated for hours beyond the standard.
""",
)


# Flag to track if database has been initialized
_db_initialized = False


def ensure_db_initialized():
    """Ensure database is initialized before any tool runs."""
    global _db_initialized
    if not _db_initialized:
        logger.debug("Initializing database for MCP server")
        initialize_database()
        _db_initialized = True


@mcp.tool()
def start(
    time: Optional[str] = None,
    date: Optional[str] = None,
    description: str = "Work session",
) -> Dict[str, Any]:
    """Start time tracking for the current or specified day.

    Creates a new time entry with the specified or current time as the start time.
    The entry will remain open until you call 'end'.

    Args:
        time: Start time in HH:MM format (e.g., "09:00"). Defaults to current time.
        date: Date in YYYY-MM-DD format (e.g., "2024-01-15"). Defaults to today.
        description: Description of the work session. Defaults to "Work session".

    Returns:
        Dictionary with status, message, and entry details.

    Examples:
        start()
        start(time="09:00")
        start(date="2024-01-15", time="09:30", description="Morning session")
    """
    ensure_db_initialized()

    with get_session() as session:
        # Parse date
        if date:
            try:
                entry_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Invalid date format '{date}'. Use YYYY-MM-DD.",
                }
        else:
            entry_date = datetime.now().date()

        # Parse time
        if time:
            try:
                start_time = datetime.strptime(time, "%H:%M").time()
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Invalid time format '{time}'. Use HH:MM.",
                }
        else:
            start_time = datetime.now().time()

        # Validate and normalize description
        description = description.strip() if description else ""
        if not description:
            description = "Work session"

        # Use shared service
        result = start_time_entry(session, entry_date, start_time, description)

        if not result["success"]:
            return {"status": "error", "message": result["message"]}

        _entry = result["entry"]  # noqa: F841 - extracted for clarity

        return {
            "status": "success",
            "message": "Time tracking started!",
            "entry": {
                "date": entry_date.isoformat(),
                "start_time": format_time(start_time),
                "description": description,
            },
        }


@mcp.tool()
def end(time: Optional[str] = None, date: Optional[str] = None) -> Dict[str, Any]:
    """End time tracking for the current or specified day.

    Closes the most recent open time entry by setting the end time and
    calculating the duration.

    Args:
        time: End time in HH:MM format (e.g., "17:30"). Defaults to current time.
        date: Date in YYYY-MM-DD format (e.g., "2024-01-15"). Defaults to today.

    Returns:
        Dictionary with status, message, and entry details including duration.

    Examples:
        end()
        end(time="17:30")
        end(date="2024-01-15", time="18:00")
    """
    ensure_db_initialized()

    with get_session() as session:
        # Parse date
        if date:
            try:
                entry_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Invalid date format '{date}'. Use YYYY-MM-DD.",
                }
        else:
            entry_date = datetime.now().date()

        # Parse time
        if time:
            try:
                end_time = datetime.strptime(time, "%H:%M").time()
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Invalid time format '{time}'. Use HH:MM.",
                }
        else:
            end_time = datetime.now().time()

        # Use shared service
        result = end_time_entry(session, end_time, entry_date)

        if not result["success"]:
            return {"status": "error", "message": result["message"]}

        entry = result["entry"]
        duration = result["duration"]

        return {
            "status": "success",
            "message": "Time tracking ended!",
            "entry": {
                "date": entry_date.isoformat(),
                "start_time": format_time(entry.start_time),
                "end_time": format_time(end_time),
                "duration": format_hours(duration),
                "duration_hours": duration,
                "description": entry.description,
            },
        }


@mcp.tool()
def add_entry(
    start: str,
    end: str,
    date: Optional[str] = None,
    description: str = "Work session",
    pause_mode: str = "none",
    pause_minutes: int = 0,
) -> Dict[str, Any]:
    """Add a completed time entry.

    Creates a past/completed time entry with start and end times.
    Supports flexible pause handling.

    Args:
        start: Start time in HH:MM format (e.g., "09:00").
        end: End time in HH:MM format (e.g., "17:30").
        date: Date in YYYY-MM-DD format. Defaults to today.
        description: Description of the work. Defaults to "Work session".
        pause_mode: How to handle pause: 'default', 'custom', or 'none'. Defaults to 'none'.
        pause_minutes: Custom pause duration in minutes (required if pause_mode='custom').

    Returns:
        Dictionary with status and entry details.

    Examples:
        add_entry(start="09:00", end="17:00")
        add_entry(start="09:00", end="17:30", pause_mode="default")
        add_entry(start="09:00", end="18:00", pause_mode="custom", pause_minutes=45)
    """
    ensure_db_initialized()

    with get_session() as session:
        # Parse date
        if date:
            try:
                entry_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Invalid date format '{date}'. Use YYYY-MM-DD.",
                }
        else:
            entry_date = datetime.now().date()

        # Parse times
        try:
            start_time = datetime.strptime(start, "%H:%M").time()
            end_time = datetime.strptime(end, "%H:%M").time()
        except ValueError:
            return {
                "status": "error",
                "message": "Invalid time format. Use HH:MM.",
            }

        # Use shared service
        result = add_time_entry(
            session,
            entry_date=entry_date,
            start_time=start_time,
            end_time=end_time,
            description=description,
            pause_mode=pause_mode,
            pause_minutes=pause_minutes,
        )

        if not result["success"]:
            return {"status": "error", "message": result["message"]}

        entry = result["entry"]

        return {
            "status": "success",
            "message": "Time entry added successfully!",
            "entry": {
                "date": entry_date.isoformat(),
                "start_time": format_time(entry.start_time),
                "end_time": format_time(entry.end_time),
                "duration": format_hours(entry.duration_hours),
                "duration_hours": entry.duration_hours,
                "pause_minutes": (
                    int(entry.accumulated_pause_seconds / 60)
                    if entry.accumulated_pause_seconds
                    else 0
                ),
                "description": entry.description,
            },
        }


@mcp.tool()
def edit_entry(
    date: str,
    entry_id: Optional[int] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Edit an existing time entry.

    Modify the details of a time entry for a specific date. You can update
    the start time, end time, and/or description. At least one field must
    be provided to update.

    If multiple entries exist for a date, use 'entry_id' (available from list_entries)
    to target a specific one.

    Args:
        date: Date of the entry in YYYY-MM-DD format (required).
        entry_id: ID of the entry to edit (optional, useful if multiple entries exist for the date).
        start: New start time in HH:MM format (optional).
        end: New end time in HH:MM format (optional).
        description: New description (optional).

    Returns:
        Dictionary with status and updated entry details.
    """
    ensure_db_initialized()

    with get_session() as session:
        # Parse date
        try:
            entry_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return {
                "status": "error",
                "message": f"Invalid date format '{date}'. Use YYYY-MM-DD.",
            }

        # Check if at least one field to update is provided
        if not any([start, end, description]):
            return {
                "status": "error",
                "message": (
                    "At least one field (start, end, or description) "
                    "must be provided to update."
                ),
            }

        # Prepare updates
        start_t = None
        if start:
            try:
                start_t = datetime.strptime(start, "%H:%M").time()
            except ValueError:
                return {"status": "error", "message": f"Invalid start time '{start}'."}

        end_t = None
        if end:
            try:
                end_t = datetime.strptime(end, "%H:%M").time()
            except ValueError:
                return {"status": "error", "message": f"Invalid end time '{end}'."}

        # If ID not provided, resolve it
        target_id = entry_id
        if not target_id:
            entries = (
                session.query(TimeEntry)
                .filter_by(date=entry_date, is_active=False)
                .order_by(TimeEntry.created_at.desc())
                .all()
            )
            if not entries:
                return {
                    "status": "error",
                    "message": f"No completed entry found for {date}.",
                }
            if len(entries) > 1:
                return {
                    "status": "error",
                    "message": f"Multiple entries found for {date}, please specify entry_id.",
                }
            target_id = entries[0].id

        # Use shared service
        result = update_time_entry(
            session,
            target_id,
            start_time=start_t,
            end_time=end_t,
            description=description,
            date_check=entry_date,
        )

        if not result["success"]:
            return {"status": "error", "message": result["message"]}

        entry = result["entry"]

        return {
            "status": "success",
            "message": "Time entry updated successfully!",
            "entry": {
                "id": entry.id,
                "date": entry.date.isoformat(),
                "start_time": format_time(entry.start_time),
                "end_time": format_time(entry.end_time),
                "duration": format_hours(entry.duration_hours),
                "description": entry.description,
            },
        }


@mcp.tool()
def summary(period: str = "week", date: Optional[str] = None) -> Dict[str, Any]:
    """Summarize tracked time for the specified period.

    Displays statistics including total hours, overtime, working days,
    and leave days for the week or month.

    Args:
        period: Summary period, either "week" or "month". Defaults to "week".
        date: Reference date in YYYY-MM-DD format. Defaults to today.

    Returns:
        Dictionary with status, period information, statistics, and recent entries.

    Examples:
        summary()
        summary(period="month")
        summary(period="week", date="2024-01-15")
    """
    ensure_db_initialized()

    with get_session() as session:
        # Validate period
        if period.lower() not in ["week", "month"]:
            return {
                "status": "error",
                "message": f"Invalid period '{period}'. Use 'week' or 'month'.",
            }

        # Parse date
        if date:
            try:
                ref_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Invalid date format '{date}'. Use YYYY-MM-DD.",
                }
        else:
            ref_date = datetime.now().date()

        if period.lower() == "week":
            start_date, end_date = get_week_bounds(ref_date)
            period_name = "Week"
        else:
            start_date, end_date = get_month_bounds(ref_date)
            period_name = "Month"

        # Query time entries for the period
        entries = (
            session.query(TimeEntry)
            .filter(TimeEntry.date >= start_date)
            .filter(TimeEntry.date <= end_date)
            .order_by(TimeEntry.date)
            .all()
        )

        # Calculate statistics
        if period.lower() == "week":
            stats = calculate_weekly_stats(entries)
        else:
            # Query leave days for monthly statistics
            leave_days = (
                session.query(LeaveDay)
                .filter(LeaveDay.date >= start_date)
                .filter(LeaveDay.date <= end_date)
                .all()
            )
            stats = calculate_monthly_stats(entries, leave_days)

        # Format recent entries
        recent_entries = []
        for entry in entries[-5:]:  # Last 5 entries
            recent_entries.append(
                {
                    "date": entry.date.isoformat(),
                    "start_time": format_time(entry.start_time),
                    "end_time": format_time(entry.end_time),
                    "duration": format_hours(entry.duration_hours),
                    "duration_hours": entry.duration_hours,
                    "description": entry.description,
                    "has_overtime": entry.duration_hours > 8.0,
                }
            )

        result = {
            "status": "success",
            "period": period_name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "statistics": {
                "total_hours": stats["total_hours"],
                "total_hours_formatted": format_hours(stats["total_hours"]),
                "working_days": stats["working_days"],
                "overtime": stats["overtime"],
                "overtime_formatted": format_hours(stats["overtime"]),
            },
            "recent_entries": recent_entries,
            "has_entries": len(entries) > 0,
        }

        # Add period-specific stats
        if period.lower() == "week":
            result["statistics"]["standard_hours"] = stats["standard_hours"]
        else:
            result["statistics"]["expected_hours"] = stats["expected_hours"]
            result["statistics"]["vacation_days"] = stats.get("vacation_days", 0)
            result["statistics"]["sick_days"] = stats.get("sick_days", 0)

        return result


@mcp.tool()
def leave_request(
    start_date: str,
    end_date: str,
    leave_type: str = "vacation",
    description: str = "",
) -> Dict[str, Any]:
    """Request multi-day leave with automatic working hours calculation.

    Creates leave records for all working days (Monday-Friday) in the specified
    date range, automatically excluding weekends.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        leave_type: Type of leave ('vacation' or 'sick'). Defaults to 'vacation'.
        description: Description or notes for the leave.

    Returns:
        Dictionary with status and summary of created leave.
    """
    ensure_db_initialized()

    with get_session() as session:
        # Parse dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return {
                "status": "error",
                "message": f"Invalid start date format '{start_date}'. Use YYYY-MM-DD.",
            }

        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return {
                "status": "error",
                "message": f"Invalid end date format '{end_date}'. Use YYYY-MM-DD.",
            }

        if end < start:
            return {
                "status": "error",
                "message": "End date must be on or after start date.",
            }

        if leave_type.lower() not in ["vacation", "sick"]:
            return {
                "status": "error",
                "message": f"Invalid leave type '{leave_type}'. Use 'vacation' or 'sick'.",
            }

        # Calculate leave statistics
        leave_stats = calculate_leave_hours(start, end)
        working_days = get_working_days_in_range(start, end)

        if not working_days:
            return {
                "status": "error",
                "message": "No working days in the selected range (only weekends).",
            }

        # Create leave records
        try:
            result = create_leave_requests(
                session,
                start,
                end,
                leave_type.lower(),
                description.strip() if description else "",
            )

            created_count = result["created"]
            skipped_count = result["skipped"]

            message = (
                f"Leave request created successfully! ({created_count} days created"
            )
            if skipped_count > 0:
                message += f", {skipped_count} skipped as duplicates)"
            else:
                message += ")"

            return {
                "status": "success",
                "message": message,
                "summary": {
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "total_days": leave_stats["total_days"],
                    "working_days": leave_stats["working_days"],
                    "weekend_days": leave_stats["weekend_days"],
                    "created_days": created_count,
                    "skipped_days": skipped_count,
                    "working_hours": format_hours(leave_stats["working_hours"]),
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error creating leave records: {str(e)}",
            }


@mcp.tool()
def list_entries(
    period: str = "week",
    date: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """List time entries for the specified period.

    Retrieves all time entries for a week, month, or all entries.

    Args:
        period: Period filter: "week", "month", or "all". Defaults to "week".
        date: Reference date in YYYY-MM-DD format. Defaults to today.
        limit: Maximum number of entries to return. If None, returns all.

    Returns:
        Dictionary with status, period information, and list of entries.

    Examples:
        list_entries()
        list_entries(period="month")
        list_entries(period="all", limit=10)
    """
    ensure_db_initialized()

    with get_session() as session:
        # Validate period
        if period.lower() not in ["week", "month", "all"]:
            return {
                "status": "error",
                "message": f"Invalid period '{period}'. Use 'week', 'month', or 'all'.",
            }

        # Parse date if provided
        if date:
            try:
                ref_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Invalid date format '{date}'. Use YYYY-MM-DD.",
                }
        else:
            ref_date = datetime.now().date()

        # Determine date range
        if period.lower() == "week":
            start_date, end_date = get_week_bounds(ref_date)
        elif period.lower() == "month":
            start_date, end_date = get_month_bounds(ref_date)
        else:
            start_date = None
            end_date = None

        # Query entries
        if start_date and end_date:
            entries = (
                session.query(TimeEntry)
                .filter(TimeEntry.date >= start_date)
                .filter(TimeEntry.date <= end_date)
                .order_by(TimeEntry.date)
                .all()
            )
        else:
            entries = session.query(TimeEntry).order_by(TimeEntry.date).all()

        # Apply limit if specified
        if limit and limit > 0:
            entries = entries[-limit:]  # Get most recent entries

        # Format entries
        formatted_entries = []
        for entry in entries:
            formatted_entries.append(
                {
                    "id": entry.id,
                    "date": entry.date.isoformat(),
                    "day_of_week": entry.date.strftime("%A"),
                    "start_time": format_time(entry.start_time),
                    "end_time": format_time(entry.end_time),
                    "duration": format_hours(entry.duration_hours),
                    "duration_hours": entry.duration_hours,
                    "description": entry.description,
                    "is_open": entry.duration_hours == 0.0,
                    "created_at": (
                        entry.created_at.isoformat() if entry.created_at else None
                    ),
                }
            )

        result = {
            "status": "success",
            "period": period,
            "count": len(formatted_entries),
            "entries": formatted_entries,
        }

        if start_date and end_date:
            result["start_date"] = start_date.isoformat()
            result["end_date"] = end_date.isoformat()

        return result


@mcp.tool()
def export_entries(
    period: str = "all",
    date: Optional[str] = None,
    export_format: str = "csv",
) -> Dict[str, Any]:
    """Export time entries to CSV or JSON format.

    Export time tracking data for use in external applications.
    Returns the content as a string.

    Args:
        period: Export period: "week", "month", or "all". Defaults to "all".
        date: Reference date in YYYY-MM-DD format. Defaults to today.
        export_format: Export format. Supported: "csv", "json". Defaults to "csv".

    Returns:
        Dictionary with status, metadata, and content.

    Examples:
        export_entries()
        export_entries(export_format="json")
        export_entries(period="week")
        export_entries(period="month", date="2024-01-15")
    """
    ensure_db_initialized()

    with get_session() as session:
        # Validate format
        if export_format.lower() not in ["csv", "json"]:
            return {
                "status": "error",
                "message": (
                    f"Unsupported format '{export_format}'. "
                    "Only 'csv' and 'json' are supported."
                ),
            }

        # Validate period
        if period.lower() not in ["week", "month", "all"]:
            return {
                "status": "error",
                "message": f"Invalid period '{period}'. Use 'week', 'month', or 'all'.",
            }

        # Parse reference date
        if date:
            try:
                ref_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Invalid date format '{date}'. Use YYYY-MM-DD.",
                }
        else:
            ref_date = datetime.now().date()

        # Determine date range based on period
        if period.lower() == "week":
            start_date, end_date = get_week_bounds(ref_date)
            period_name = f"week_{start_date}"
        elif period.lower() == "month":
            start_date, end_date = get_month_bounds(ref_date)
            period_name = f"month_{start_date.strftime('%Y-%m')}"
        else:
            start_date = None
            end_date = None
            period_name = "all"

        # Query entries
        if start_date and end_date:
            entries = (
                session.query(TimeEntry)
                .filter(TimeEntry.date >= start_date)
                .filter(TimeEntry.date <= end_date)
                .order_by(TimeEntry.date)
                .all()
            )
        else:
            entries = session.query(TimeEntry).order_by(TimeEntry.date).all()

        if not entries:
            result = {
                "status": "success",
                "message": "No time entries found to export.",
                "count": 0,
                "content": "",
            }
            if export_format.lower() == "csv":
                result["csv_content"] = ""
            return result

        # Generate content
        if export_format.lower() == "json":
            content = export_time_entries_to_json(entries, start_date, end_date)
        else:
            content = export_time_entries_to_csv(entries, start_date, end_date)

        # Calculate total hours
        total_hours = sum(entry.duration_hours for entry in entries)

        result = {
            "status": "success",
            "message": "Export successful!",
            "count": len(entries),
            "total_hours": total_hours,
            "total_hours_formatted": format_hours(total_hours),
            "period": period_name,
            "format": export_format,
            "content": content,
        }

        # Keep csv_content for backward compatibility if format is csv
        if export_format.lower() == "csv":
            result["csv_content"] = content

        if start_date and end_date:
            result["start_date"] = start_date.isoformat()
            result["end_date"] = end_date.isoformat()

        return result


@mcp.tool()
def import_entries(
    content: str,
    import_format: str = "json",
    on_conflict: str = "skip",
    auto_create_categories: bool = True,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Import time entries from JSON or CSV content.

    Import time tracking data from a string containing JSON or CSV content.
    Useful for restoring backups or migrating data.

    Args:
        content: The JSON or CSV content to import (as a string).
        import_format: Format of the content: "json" or "csv". Defaults to "json".
        on_conflict: How to handle duplicate entries: "skip", "overwrite", or
            "duplicate". Defaults to "skip".
        auto_create_categories: Create categories that don't exist. Defaults to True.
        dry_run: Preview import without making changes. Defaults to False.

    Returns:
        Dictionary with status, import statistics, and any warnings/errors.

    Examples:
        import_entries(content='{"entries": [...]}')
        import_entries(content=csv_data, import_format="csv")
        import_entries(content=json_data, dry_run=True)
    """
    ensure_db_initialized()

    import tempfile
    import os
    from .services import import_time_entries

    # Validate format
    if import_format.lower() not in ["json", "csv"]:
        return {
            "status": "error",
            "message": (
                f"Unsupported format '{import_format}'. "
                "Only 'json' and 'csv' are supported."
            ),
        }

    # Validate on_conflict
    if on_conflict.lower() not in ["skip", "overwrite", "duplicate"]:
        return {
            "status": "error",
            "message": (
                f"Invalid on_conflict value '{on_conflict}'. "
                "Use 'skip', 'overwrite', or 'duplicate'."
            ),
        }

    if not content or not content.strip():
        return {
            "status": "error",
            "message": "Content is empty. Provide JSON or CSV content to import.",
        }

    with get_session() as session:
        # Create temp file to leverage the shared import_time_entries service
        suffix = f".{import_format.lower()}"
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=suffix, encoding="utf-8"
            ) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            result = import_time_entries(
                session,
                file_path=tmp_path,
                import_format=import_format.lower(),
                on_conflict=on_conflict.lower(),
                auto_create_categories=auto_create_categories,
                include_leave_days=True,
                dry_run=dry_run,
            )

            if not result["success"]:
                return {
                    "status": "error",
                    "message": "; ".join(result["errors"]) or "Import failed",
                }

            # Build message
            action = "Would import" if dry_run else "Imported"
            parts = []
            if result["entries_imported"]:
                parts.append(f"{result['entries_imported']} entries")
            if result["entries_updated"]:
                parts.append(f"updated {result['entries_updated']}")
            if result["entries_skipped"]:
                parts.append(f"skipped {result['entries_skipped']} duplicates")
            if result["leave_days_imported"]:
                parts.append(f"{result['leave_days_imported']} leave days")

            message = f"{action}: {', '.join(parts)}." if parts else "No entries found."

            return {
                "status": "success",
                "message": message,
                "dry_run": dry_run,
                "entries_imported": result["entries_imported"],
                "entries_updated": result["entries_updated"],
                "entries_skipped": result["entries_skipped"],
                "leave_days_imported": result["leave_days_imported"],
                "categories_created": result["categories_created"],
                "errors": result["errors"][:5],
                "warnings": result.get("warnings", [])[:5],
            }

        except ValueError as e:
            return {"status": "error", "message": f"Parse error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Import failed: {str(e)}"}
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)


@mcp.tool()
def list_config() -> Dict[str, Any]:
    """Display all configuration options and their current values.

    Returns a dictionary of all configuration settings with their
    current values, descriptions, and default values.

    Returns:
        Dictionary with status and settings.
    """
    ensure_db_initialized()

    with get_session() as session:
        all_settings = Settings.get_all_settings_with_session(session)

        settings_list = []
        for key in sorted(CONFIG_DEFAULTS.keys()):
            current_value = all_settings.get(key, CONFIG_DEFAULTS[key])
            default_value = CONFIG_DEFAULTS[key]
            description = CONFIG_DESCRIPTIONS.get(key, "No description available")

            settings_list.append(
                {
                    "key": key,
                    "value": current_value,
                    "default": default_value,
                    "description": description,
                    "is_default": current_value == default_value,
                }
            )

        return {
            "status": "success",
            "count": len(settings_list),
            "settings": settings_list,
        }


@mcp.tool()
def get_config(key: str) -> Dict[str, Any]:
    """Get the value of a specific configuration option.

    Args:
        key: Configuration key (e.g., 'weekly_hours', 'auto_end')

    Returns:
        Dictionary with status and setting details.
    """
    ensure_db_initialized()

    with get_session() as session:
        if key not in CONFIG_DEFAULTS:
            return {
                "status": "error",
                "message": f"Unknown configuration key '{key}'.",
                "available_keys": list(CONFIG_DEFAULTS.keys()),
            }

        value = Settings.get_setting_with_session(session, key, CONFIG_DEFAULTS[key])
        description = CONFIG_DESCRIPTIONS.get(key, "No description available")

        return {
            "status": "success",
            "key": key,
            "value": value,
            "description": description,
        }


@mcp.tool()
def set_config(key: str, value: str) -> Dict[str, Any]:
    """Set a configuration option to a new value.

    Updates the specified configuration key with the provided value.
    The value will be validated before being saved.

    Args:
        key: Configuration key (e.g., 'weekly_hours')
        value: New value to set

    Returns:
        Dictionary with status, message, and updated setting details.
    """
    ensure_db_initialized()

    with get_session() as session:
        if key not in CONFIG_DEFAULTS:
            return {
                "status": "error",
                "message": f"Unknown configuration key '{key}'.",
                "available_keys": list(CONFIG_DEFAULTS.keys()),
            }

        # Validate the value
        is_valid, error_message = validate_config_value(key, value)
        if not is_valid:
            return {
                "status": "error",
                "message": f"Invalid value for '{key}': {error_message}",
            }

        # Normalize boolean values
        if CONFIG_TYPES.get(key) == "bool":
            value = normalize_bool_value(value)

        # Get old value for reporting
        old_value = Settings.get_setting_with_session(
            session, key, CONFIG_DEFAULTS[key]
        )

        # Set the new value
        Settings.set_setting_with_session(session, key, value)

        return {
            "status": "success",
            "message": f"Configuration '{key}' updated successfully.",
            "key": key,
            "old_value": old_value,
            "new_value": value,
        }


def main():
    """Main entry point for the MCP server.

    Runs the MCP server using stdio transport for communication
    with MCP clients.
    """
    import asyncio

    logger.info("Starting MCP server")

    # Initialize database before starting server
    ensure_db_initialized()

    async def run_server():
        """Run the MCP server asynchronously."""
        await mcp.run_stdio_async()

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
