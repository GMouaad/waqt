"""Route handlers for the time tracking application."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify
from datetime import datetime, timedelta
from . import db
from .models import TimeEntry, LeaveDay
from .utils import (
    calculate_duration,
    calculate_weekly_stats,
    calculate_monthly_stats,
    get_week_bounds,
    get_month_bounds,
    export_time_entries_to_csv,
    get_time_entries_for_period,
)

bp = Blueprint("main", __name__)


def get_open_entry():
    """Get the currently running timer entry if any."""
    today = datetime.now().date()
    # Find entry with duration=0 AND end_time=start_time (marker for open entry)
    return (
        TimeEntry.query.filter_by(date=today, duration_hours=0.0)
        .filter(TimeEntry.end_time == TimeEntry.start_time)
        .order_by(TimeEntry.created_at.desc())
        .first()
    )


@bp.route("/api/timer/status")
def timer_status():
    """Get the current status of the timer."""
    entry = get_open_entry()
    if entry:
        # Calculate elapsed time since start
        start_dt = datetime.combine(entry.date, entry.start_time)
        elapsed_seconds = (datetime.now() - start_dt).total_seconds()
        
        return jsonify({
            "active": True,
            "start_time": entry.start_time.strftime("%H:%M:%S"),
            "elapsed_seconds": int(elapsed_seconds),
            "description": entry.description
        })
    
    return jsonify({"active": False})


@bp.route("/api/timer/start", methods=["POST"])
def start_timer():
    """Start a new timer."""
    try:
        # Check if already running
        if get_open_entry():
            return jsonify({"success": False, "message": "Timer already running"}), 400
            
        data = request.get_json() or {}
        description = data.get("description", "Work")
        
        now = datetime.now()
        
        entry = TimeEntry(
            date=now.date(),
            start_time=now.time(),
            end_time=now.time(),  # Marker for open entry
            duration_hours=0.0,   # Marker for open entry
            description=description
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Timer started",
            "start_time": now.strftime("%H:%M:%S")
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@bp.route("/api/timer/stop", methods=["POST"])
def stop_timer():
    """Stop the current timer."""
    try:
        entry = get_open_entry()
        if not entry:
            return jsonify({"success": False, "message": "No active timer"}), 400
            
        now = datetime.now()
        end_time = now.time()
        
        # Calculate duration
        duration = calculate_duration(entry.start_time, end_time)
        
        entry.end_time = end_time
        entry.duration_hours = duration
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Timer stopped",
            "duration": duration
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@bp.route("/")
def index():
    """Dashboard - show overview of recent entries and current week stats."""
    today = datetime.now().date()
    week_start, week_end = get_week_bounds(today)

    # Get current week entries
    week_entries = (
        TimeEntry.query.filter(TimeEntry.date >= week_start, TimeEntry.date <= week_end)
        .order_by(TimeEntry.date.desc())
        .all()
    )

    # Calculate weekly stats
    weekly_stats = calculate_weekly_stats(week_entries)

    # Get recent entries (last 7 days)
    week_ago = today - timedelta(days=7)
    recent_entries = (
        TimeEntry.query.filter(TimeEntry.date >= week_ago)
        .order_by(TimeEntry.date.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "dashboard.html",
        recent_entries=recent_entries,
        weekly_stats=weekly_stats,
        current_date=today,
    )


@bp.route("/time-entry", methods=["GET", "POST"])
def time_entry():
    """Add or view time entries."""
    if request.method == "POST":
        try:
            # Parse form data
            date_str = request.form.get("date")
            start_time_str = request.form.get("start_time")
            end_time_str = request.form.get("end_time")
            description = request.form.get("description", "").strip()

            # Validate inputs
            if not all([date_str, start_time_str, end_time_str, description]):
                flash("All fields are required.", "error")
                return redirect(url_for("main.time_entry"))

            # Parse date and times
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            # Calculate duration
            duration = calculate_duration(start_time, end_time)

            if duration <= 0:
                flash("End time must be after start time.", "error")
                return redirect(url_for("main.time_entry"))

            # Create new entry
            entry = TimeEntry(
                date=date,
                start_time=start_time,
                end_time=end_time,
                duration_hours=duration,
                description=description,
            )

            db.session.add(entry)
            db.session.commit()

            flash(
                f"Time entry added successfully! Duration: {duration:.2f} hours",
                "success",
            )
            return redirect(url_for("main.index"))

        except ValueError as e:
            flash(f"Invalid date or time format: {str(e)}", "error")
            return redirect(url_for("main.time_entry"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding time entry: {str(e)}", "error")
            return redirect(url_for("main.time_entry"))

    # GET request - show form
    return render_template("time_entry.html", today=datetime.now().date())


@bp.route("/time-entry/<int:entry_id>/delete", methods=["POST"])
def delete_time_entry(entry_id):
    """Delete a time entry."""
    try:
        entry = TimeEntry.query.get_or_404(entry_id)
        db.session.delete(entry)
        db.session.commit()
        flash("Time entry deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting time entry: {str(e)}", "error")

    return redirect(url_for("main.index"))


@bp.route("/reports")
def reports():
    """View weekly and monthly reports."""
    today = datetime.now().date()

    # Get selected period from query params
    period = request.args.get("period", "week")
    date_str = request.args.get("date", today.isoformat())

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        selected_date = today

    if period == "week":
        start_date, end_date = get_week_bounds(selected_date)
    else:  # month
        start_date, end_date = get_month_bounds(selected_date)

    # Get entries for the period
    entries = (
        TimeEntry.query.filter(TimeEntry.date >= start_date, TimeEntry.date <= end_date)
        .order_by(TimeEntry.date.desc())
        .all()
    )

    # Get leave days for the period
    leave_days = (
        LeaveDay.query.filter(LeaveDay.date >= start_date, LeaveDay.date <= end_date)
        .order_by(LeaveDay.date.desc())
        .all()
    )

    # Calculate stats
    if period == "week":
        stats = calculate_weekly_stats(entries)
    else:
        stats = calculate_monthly_stats(entries, leave_days)

    # Group entries by date
    entries_by_date = {}
    for entry in entries:
        date_key = entry.date.isoformat()
        if date_key not in entries_by_date:
            entries_by_date[date_key] = []
        entries_by_date[date_key].append(entry)

    return render_template(
        "reports.html",
        period=period,
        start_date=start_date,
        end_date=end_date,
        selected_date=selected_date,
        entries=entries,
        entries_by_date=entries_by_date,
        leave_days=leave_days,
        stats=stats,
        timedelta=timedelta,
    )


@bp.route("/leave", methods=["GET", "POST"])
def leave():
    """Manage vacation and sick leave days."""
    if request.method == "POST":
        try:
            # Parse form data
            date_str = request.form.get("date")
            leave_type = request.form.get("leave_type")
            description = request.form.get("description", "").strip()

            # Validate inputs
            if not all([date_str, leave_type]):
                flash("Date and leave type are required.", "error")
                return redirect(url_for("main.leave"))

            if leave_type not in ["vacation", "sick"]:
                flash("Invalid leave type.", "error")
                return redirect(url_for("main.leave"))

            # Parse date
            date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Create new leave day
            leave_day = LeaveDay(
                date=date, leave_type=leave_type, description=description
            )

            db.session.add(leave_day)
            db.session.commit()

            flash(f"{leave_type.capitalize()} leave added successfully!", "success")
            return redirect(url_for("main.leave"))

        except ValueError as e:
            flash(f"Invalid date format: {str(e)}", "error")
            return redirect(url_for("main.leave"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding leave: {str(e)}", "error")
            return redirect(url_for("main.leave"))

    # GET request - show form and list
    # Get all leave days, ordered by date
    all_leave = LeaveDay.query.order_by(LeaveDay.date.desc()).all()

    # Calculate totals for current year
    current_year = datetime.now().year
    year_leave = [leave for leave in all_leave if leave.date.year == current_year]
    vacation_count = len(
        [leave for leave in year_leave if leave.leave_type == "vacation"]
    )
    sick_count = len([leave for leave in year_leave if leave.leave_type == "sick"])

    return render_template(
        "leave.html",
        leave_days=all_leave,
        vacation_count=vacation_count,
        sick_count=sick_count,
        current_year=current_year,
        today=datetime.now().date(),
    )


@bp.route("/leave/<int:leave_id>/delete", methods=["POST"])
def delete_leave(leave_id):
    """Delete a leave day."""
    try:
        leave_day = LeaveDay.query.get_or_404(leave_id)
        db.session.delete(leave_day)
        db.session.commit()
        flash("Leave day deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting leave day: {str(e)}", "error")

    return redirect(url_for("main.leave"))


@bp.route("/export/csv")
def export_csv():
    """Export time entries to CSV format."""
    try:
        # Get filter parameters
        period = request.args.get("period", "all")
        date_str = request.args.get("date", datetime.now().date().isoformat())

        # Parse the reference date
        try:
            ref_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            # Log the error and fallback to current date
            flash(
                f"Invalid date format '{date_str}', using current date instead.",
                "warning",
            )
            ref_date = datetime.now().date()

        # Determine date range based on period
        if period == "week":
            start_date, end_date = get_week_bounds(ref_date)
        elif period == "month":
            start_date, end_date = get_month_bounds(ref_date)
        else:
            # Export all entries
            start_date = None
            end_date = None

        # Query entries using utility function
        entries = get_time_entries_for_period(start_date, end_date)

        if not entries:
            flash("No time entries found to export.", "warning")
            return redirect(url_for("main.reports"))

        # Generate CSV content
        csv_content = export_time_entries_to_csv(entries, start_date, end_date)

        # Generate filename
        if start_date and end_date:
            filename = (
                f"time_entries_{start_date.strftime('%Y%m%d')}_"
                f"{end_date.strftime('%Y%m%d')}.csv"
            )
        else:
            filename = f"time_entries_all_{datetime.now().strftime('%Y%m%d')}.csv"

        # Return CSV as download
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except IOError as e:
        # Handle file system errors
        flash(f"Error writing CSV file: {str(e)}", "error")
        return redirect(url_for("main.reports"))
    except Exception as e:
        # Log unexpected errors for debugging
        import logging
        logging.error(f"Unexpected error during CSV export: {str(e)}", exc_info=True)
        flash("An unexpected error occurred during export. Please try again.", "error")
        return redirect(url_for("main.reports"))
