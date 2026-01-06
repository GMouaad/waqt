"""Utility functions for time tracking calculations."""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from .models import TimeEntry, LeaveDay


def calculate_daily_overtime(duration_hours: float, standard_hours: float = 8.0) -> float:
    """
    Calculate overtime hours for a single day.
    
    Args:
        duration_hours: Total hours worked in the day
        standard_hours: Standard work hours per day (default: 8)
    
    Returns:
        Overtime hours (0 if no overtime)
    """
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


def calculate_weekly_stats(entries: List[TimeEntry], standard_hours: float = 40.0) -> Dict:
    """
    Calculate weekly statistics from time entries.
    
    Args:
        entries: List of TimeEntry objects for the week
        standard_hours: Standard work hours per week (default: 40)
    
    Returns:
        Dictionary with total_hours, overtime, and working_days
    """
    total_hours = sum(entry.duration_hours for entry in entries)
    overtime = max(0, total_hours - standard_hours)
    working_days = len(set(entry.date for entry in entries))
    
    return {
        'total_hours': round(total_hours, 2),
        'overtime': round(overtime, 2),
        'working_days': working_days,
        'standard_hours': standard_hours
    }


def calculate_monthly_stats(entries: List[TimeEntry], leave_days: List[LeaveDay]) -> Dict:
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
    vacation_days = len([l for l in leave_days if l.leave_type == 'vacation'])
    sick_days = len([l for l in leave_days if l.leave_type == 'sick'])
    
    # Calculate expected hours (working_days * 8)
    expected_hours = working_days * 8.0
    overtime = max(0, total_hours - expected_hours)
    
    return {
        'total_hours': round(total_hours, 2),
        'overtime': round(overtime, 2),
        'working_days': working_days,
        'vacation_days': vacation_days,
        'sick_days': sick_days,
        'expected_hours': expected_hours
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
