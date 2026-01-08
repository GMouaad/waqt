"""Utility functions for time tracking calculations."""

import csv
import io
from datetime import datetime, timedelta, date, time as datetime_time
from typing import List, Dict, Tuple, Optional
from .models import TimeEntry, LeaveDay, Settings


def is_weekend(check_date: date) -> bool:
    """
    Check if a given date falls on a weekend (Saturday or Sunday).
    
    Args:
        check_date: Date to check
        
    Returns:
        True if the date is Saturday (5) or Sunday (6), False otherwise
    """
    return check_date.weekday() in (5, 6)


def get_date_range(start_date: date, end_date: date) -> List[date]:
    """
    Generate a list of dates between start_date and end_date (inclusive).
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        
    Returns:
        List of date objects from start_date to end_date
    """
    if start_date > end_date:
        return []
    
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    return date_list


def get_working_days_in_range(start_date: date, end_date: date) -> List[date]:
    """
    Get all working days (excluding weekends) in a date range.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        
    Returns:
        List of date objects that are working days (Monday-Friday)
    """
    all_dates = get_date_range(start_date, end_date)
    return [d for d in all_dates if not is_weekend(d)]


def calculate_leave_hours(start_date: date, end_date: date) -> Dict:
    """
    Calculate leave statistics for a date range.
    
    Args:
        start_date: Start date of leave
        end_date: End date of leave
        
    Returns:
        Dictionary with:
        - total_days: Total calendar days in range
        - working_days: Number of working days (excluding weekends)
        - weekend_days: Number of weekend days
        - working_hours: Total working hours (working_days * standard_hours_per_day)
    """
    # Generate date range once and reuse it
    all_dates = get_date_range(start_date, end_date)
    working_days_list = [d for d in all_dates if not is_weekend(d)]
    
    total_days = len(all_dates)
    working_days = len(working_days_list)
    weekend_days = total_days - working_days
    
    # Get standard hours per day from settings
    standard_hours_per_day = get_standard_hours_per_day()
    working_hours = working_days * standard_hours_per_day
    
    return {
        "total_days": total_days,
        "working_days": working_days,
        "weekend_days": weekend_days,
        "working_hours": working_hours,
    }


def format_time(time_obj: Optional[datetime_time], time_format: Optional[str] = None) -> str:
    """
    Format a time object according to the user's preferred time format.
    
    Args:
        time_obj: datetime.time object to format. If None, returns an empty string.
        time_format: Time format preference ('12' or '24'). If None, reads from settings.
    
    Returns:
        Formatted time string (e.g., '13:30' or '01:30 PM'), or empty string if time_obj is None
    """
    if time_obj is None:
        return ""
    
    if time_format is None:
        time_format = Settings.get_setting("time_format", "24")
    
    if time_format == "12":
        # Convert to 12-hour format with AM/PM
        hour = time_obj.hour
        minute = time_obj.minute
        am_pm = "AM" if hour < 12 else "PM"
        
        # Convert hour to 12-hour format
        display_hour = hour % 12
        if display_hour == 0:
            display_hour = 12
        
        return f"{display_hour:d}:{minute:02d} {am_pm}"
    else:
        # Default to 24-hour format
        return time_obj.strftime("%H:%M")


def get_standard_hours_per_day() -> float:
    """Get the configured standard hours per day from settings."""
    return Settings.get_float("standard_hours_per_day", 8.0)


def get_standard_hours_per_week() -> float:
    """Get the configured standard hours per week from settings."""
    return Settings.get_float("weekly_hours", 40.0)


def calculate_daily_overtime(
    duration_hours: float, standard_hours: Optional[float] = None
) -> float:
    """
    Calculate overtime hours for a single day.

    Args:
        duration_hours: Total hours worked in the day
        standard_hours: Standard work hours per day (default: from settings or 8)

    Returns:
        Overtime hours (0 if no overtime)
    """
    if standard_hours is None:
        standard_hours = get_standard_hours_per_day()
    return max(0, duration_hours - standard_hours)


def calculate_duration(start_time: datetime.time, end_time: datetime.time) -> float:
    """
    Calculate duration in hours between two times.

    Args:
        start_time: Start time
        end_time: End time

    Returns:
        Duration in hours
    """
    # Convert times to datetime for calculation
    today = datetime.today().date()
    start = datetime.combine(today, start_time)
    end = datetime.combine(today, end_time)

    # Handle case where end time is before start time (crosses midnight)
    if end < start:
        end += timedelta(days=1)

    duration = end - start
    return duration.total_seconds() / 3600  # Convert to hours


def get_week_bounds(date: datetime.date) -> Tuple[datetime.date, datetime.date]:
    """
    Get the start (Monday) and end (Sunday) dates of the week containing the given date.

    Args:
        date: Any date in the week

    Returns:
        Tuple of (week_start, week_end)
    """
    # Find Monday of the week
    week_start = date - timedelta(days=date.weekday())
    # Find Sunday of the week
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def get_month_bounds(date: datetime.date) -> Tuple[datetime.date, datetime.date]:
    """
    Get the first and last dates of the month containing the given date.

    Args:
        date: Any date in the month

    Returns:
        Tuple of (month_start, month_end)
    """
    month_start = date.replace(day=1)
    # Get last day of month
    if date.month == 12:
        month_end = date.replace(day=31)
    else:
        next_month = date.replace(month=date.month + 1, day=1)
        month_end = next_month - timedelta(days=1)
    return month_start, month_end


def calculate_weekly_stats(
    entries: List[TimeEntry], standard_hours: Optional[float] = None
) -> Dict:
    """
    Calculate weekly statistics from time entries.

    Args:
        entries: List of TimeEntry objects for the week
        standard_hours: Standard work hours per week (default: from settings or 40)

    Returns:
        Dictionary with total_hours, overtime, and working_days
    """
    if standard_hours is None:
        standard_hours = get_standard_hours_per_week()
    total_hours = sum(entry.duration_hours for entry in entries)
    overtime = max(0, total_hours - standard_hours)
    working_days = len(set(entry.date for entry in entries))

    return {
        "total_hours": round(total_hours, 2),
        "overtime": round(overtime, 2),
        "working_days": working_days,
        "standard_hours": standard_hours,
    }


def calculate_monthly_stats(
    entries: List[TimeEntry], leave_days: List[LeaveDay]
) -> Dict:
    """
    Calculate monthly statistics from time entries and leave days.

    Args:
        entries: List of TimeEntry objects for the month
        leave_days: List of LeaveDay objects for the month

    Returns:
        Dictionary with comprehensive monthly statistics
    """
    total_hours = sum(entry.duration_hours for entry in entries)
    working_days = len(set(entry.date for entry in entries))

    # Count leave days by type
    vacation_days = len(
        [leave for leave in leave_days if leave.leave_type == "vacation"]
    )
    sick_days = len([leave for leave in leave_days if leave.leave_type == "sick"])

    # Calculate expected hours using configured standard hours per day
    standard_hours_per_day = get_standard_hours_per_day()
    expected_hours = working_days * standard_hours_per_day
    overtime = max(0, total_hours - expected_hours)

    return {
        "total_hours": round(total_hours, 2),
        "overtime": round(overtime, 2),
        "working_days": working_days,
        "vacation_days": vacation_days,
        "sick_days": sick_days,
        "expected_hours": expected_hours,
    }


def format_hours(hours: float) -> str:
    """
    Format hours as HH:MM string.

    Args:
        hours: Hours as a float

    Returns:
        Formatted string like "8:30"
    """
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h}:{m:02d}"


def get_time_entries_for_period(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[TimeEntry]:
    """
    Get time entries for a specific date range.

    Note: If both start_date and end_date are None, all time entries
    in the database will be returned. For large datasets, this may
    impact performance. Consider providing a date range for better
    performance.

    Args:
        start_date: Optional start date (inclusive). If provided without
                   end_date, only start_date filtering is applied.
        end_date: Optional end date (inclusive). If provided without
                 start_date, only end_date filtering is applied.

    Returns:
        List of TimeEntry objects, ordered by date ascending
    """
    query = TimeEntry.query
    if start_date and end_date:
        query = query.filter(TimeEntry.date >= start_date, TimeEntry.date <= end_date)
    elif start_date:
        # Support filtering from start_date onwards
        query = query.filter(TimeEntry.date >= start_date)
    elif end_date:
        # Support filtering up to end_date
        query = query.filter(TimeEntry.date <= end_date)
    return query.order_by(TimeEntry.date.asc()).all()


def export_time_entries_to_csv(
    entries: List[TimeEntry],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> str:
    """
    Export time entries to CSV format.

    Args:
        entries: List of TimeEntry objects to export
        start_date: Optional start date for the export period
        end_date: Optional end date for the export period

    Returns:
        CSV content as a string
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    headers = [
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
    writer.writerow(headers)

    # Calculate daily totals for overtime (aggregate entries by date)
    daily_totals = {}
    for entry in entries:
        if entry.date not in daily_totals:
            daily_totals[entry.date] = 0.0
        daily_totals[entry.date] += entry.duration_hours

    # Calculate daily overtime based on aggregated totals
    daily_overtime = {}
    for date_key, total_hours in daily_totals.items():
        daily_overtime[date_key] = calculate_daily_overtime(total_hours)

    # Write data rows
    for entry in entries:
        # Get the overtime for this entry's day
        overtime = daily_overtime[entry.date]

        row = [
            entry.date.isoformat(),
            entry.date.strftime("%A"),
            format_time(entry.start_time),
            format_time(entry.end_time),
            f"{entry.duration_hours:.2f}",
            format_hours(entry.duration_hours),
            entry.description,
            f"{overtime:.2f}",
            entry.created_at.isoformat() if entry.created_at else "",
        ]
        writer.writerow(row)

    # Add summary statistics if there are entries
    if entries:
        writer.writerow([])  # Empty row
        writer.writerow(["Summary Statistics"])

        # Format period display
        if start_date and end_date:
            period_str = f"{start_date} to {end_date}"
        else:
            period_str = "All time entries"

        writer.writerow(["Period", period_str])
        writer.writerow(["Total Entries", len(entries)])
        total_hours = sum(entry.duration_hours for entry in entries)
        writer.writerow(["Total Hours", f"{total_hours:.2f}"])
        writer.writerow(["Total Hours (HH:MM)", format_hours(total_hours)])
        working_days = len(set(entry.date for entry in entries))
        writer.writerow(["Working Days", working_days])
        # Calculate total overtime from daily overtime values
        total_overtime = sum(daily_overtime.values())
        writer.writerow(["Total Overtime", f"{total_overtime:.2f}"])

    return output.getvalue()
