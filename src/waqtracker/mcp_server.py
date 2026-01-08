"""MCP server for waqtracker time tracking application.

This module implements a Model Context Protocol (MCP) server that exposes
time tracking functionality to LLM applications, mirroring the CLI capabilities.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP

from . import create_app, db
from .models import TimeEntry, LeaveDay
from .utils import (
    get_week_bounds,
    get_month_bounds,
    calculate_weekly_stats,
    calculate_monthly_stats,
    calculate_duration,
    format_hours,
    export_time_entries_to_csv,
    get_time_entries_for_period,
    format_time,
)


# Initialize FastMCP server
mcp = FastMCP(
    name="waqtracker",
    instructions="""Waqt MCP Server

A Model Context Protocol server for time tracking functionality.
This server provides tools for tracking work hours, managing time entries,
and generating reports.

Available tools:
- start: Start time tracking for a day
- end: End time tracking for a day
- summary: Get time summary for week or month
- export_entries: Export time entries to CSV format
- list_entries: List time entries for a period

Standard work schedule: 8 hours/day, 40 hours/week
Overtime is automatically calculated for hours beyond the standard.
""",
)


# Global app instance for the MCP server, initialized lazily
_app = None

def get_app():
    """Get or create the Flask app instance."""
    global _app
    if _app is None:
        _app = create_app()
    return _app


def _get_open_entry_for_date(entry_date):
    """Get the most recent open time entry for a specific date.
    
    Open entries are identified by:
    - is_active == True
    
    Args:
        entry_date: Date to check for open entries
    
    Returns:
        TimeEntry object if found, None otherwise
    """
    return (
        TimeEntry.query.filter_by(date=entry_date, is_active=True)
        .order_by(TimeEntry.created_at.desc())
        .first()
    )


def _has_open_entry_for_date(entry_date):
    """Check if there's an open time entry for a specific date.
    
    Args:
        entry_date: Date to check
    
    Returns:
        Boolean indicating if an open entry exists
    """
    return _get_open_entry_for_date(entry_date) is not None


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
    app = get_app()
    with app.app_context():
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

        # Check if there's already an open entry for this date
        if _has_open_entry_for_date(entry_date):
            return {
                "status": "error",
                "message": f"There's already an open time entry for {entry_date}. "
                "Please call 'end' first to close it.",
            }

        # Create a new entry
        entry = TimeEntry(
            date=entry_date,
            start_time=start_time,
            end_time=start_time,  # Marker: same as start_time for open entries
            duration_hours=0.0,  # Marker: 0.0 for open entries
            is_active=True,
            description=description,
        )

        db.session.add(entry)
        db.session.commit()

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
    app = get_app()
    with app.app_context():
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

        # Find the most recent open entry for this date
        open_entry = _get_open_entry_for_date(entry_date)

        if not open_entry:
            return {
                "status": "error",
                "message": f"No open time entry found for {entry_date}. "
                "Call 'start' first to begin tracking time.",
            }

        # Calculate duration
        duration = calculate_duration(open_entry.start_time, end_time)

        # Update the entry
        open_entry.end_time = end_time
        open_entry.duration_hours = duration
        open_entry.is_active = False
        db.session.commit()

        return {
            "status": "success",
            "message": "Time tracking ended!",
            "entry": {
                "date": entry_date.isoformat(),
                "start_time": format_time(open_entry.start_time),
                "end_time": format_time(end_time),
                "duration": format_hours(duration),
                "duration_hours": duration,
                "description": open_entry.description,
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
    app = get_app()
    with app.app_context():
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
            TimeEntry.query.filter(TimeEntry.date >= start_date)
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
                LeaveDay.query.filter(LeaveDay.date >= start_date)
                .filter(LeaveDay.date <= end_date)
                .all()
            )
            stats = calculate_monthly_stats(entries, leave_days)

        # Format recent entries
        recent_entries = []
        for entry in entries[-5:]:  # Last 5 entries
            recent_entries.append({
                "date": entry.date.isoformat(),
                "start_time": format_time(entry.start_time),
                "end_time": format_time(entry.end_time),
                "duration": format_hours(entry.duration_hours),
                "duration_hours": entry.duration_hours,
                "description": entry.description,
                "has_overtime": entry.duration_hours > 8.0,
            })

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
    app = get_app()
    with app.app_context():
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
        entries = get_time_entries_for_period(start_date, end_date)

        # Apply limit if specified
        if limit and limit > 0:
            entries = entries[-limit:]  # Get most recent entries

        # Format entries
        formatted_entries = []
        for entry in entries:
            formatted_entries.append({
                "id": entry.id,
                "date": entry.date.isoformat(),
                "day_of_week": entry.date.strftime("%A"),
                "start_time": format_time(entry.start_time),
                "end_time": format_time(entry.end_time),
                "duration": format_hours(entry.duration_hours),
                "duration_hours": entry.duration_hours,
                "description": entry.description,
                "is_open": entry.duration_hours == 0.0,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
            })

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
    """Export time entries to CSV format.
    
    Export time tracking data for use in spreadsheet applications.
    Returns the CSV content as a string.
    
    Args:
        period: Export period: "week", "month", or "all". Defaults to "all".
        date: Reference date in YYYY-MM-DD format. Defaults to today.
        export_format: Export format. Currently only "csv" is supported.
    
    Returns:
        Dictionary with status, metadata, and CSV content.
    
    Examples:
        export_entries()
        export_entries(period="week")
        export_entries(period="month", date="2024-01-15")
    """
    app = get_app()
    with app.app_context():
        # Validate format
        if export_format.lower() != "csv":
            return {
                "status": "error",
                "message": f"Unsupported format '{export_format}'. Only 'csv' is supported.",
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
        entries = get_time_entries_for_period(start_date, end_date)

        if not entries:
            return {
                "status": "success",
                "message": "No time entries found to export.",
                "count": 0,
                "csv_content": "",
            }

        # Generate CSV content
        csv_content = export_time_entries_to_csv(entries, start_date, end_date)

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
            "csv_content": csv_content,
        }

        if start_date and end_date:
            result["start_date"] = start_date.isoformat()
            result["end_date"] = end_date.isoformat()

        return result


def main():
    """Main entry point for the MCP server.
    
    Runs the MCP server using stdio transport for communication
    with MCP clients.
    """
    import asyncio
    
    async def run_server():
        """Run the MCP server asynchronously."""
        await mcp.run_stdio_async()
    
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
