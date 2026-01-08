"""Route handlers for the time tracking application."""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
    jsonify,
)
from datetime import datetime, timedelta
from . import db
from .models import TimeEntry, LeaveDay, Settings
from .utils import (
    calculate_duration,
    calculate_weekly_stats,
    calculate_monthly_stats,
    get_week_bounds,
    get_month_bounds,
    export_time_entries_to_csv,
    get_time_entries_for_period,
    generate_calendar_data,
    parse_time_input,
)
from .config import (
    CONFIG_DEFAULTS,
    CONFIG_TYPES,
    CONFIG_DESCRIPTIONS,
    CONFIG_DISPLAY_NAMES,
    validate_config_value,
    normalize_bool_value,
    get_config_input_type,
    get_config_validation_bounds,
    get_config_select_options,
)

bp = Blueprint("main", __name__)


def get_open_entry():
    """Get the currently running timer entry if any."""
    # Find entry with is_active=True (don't restrict to today's date)
    # This handles cases where a timer was started late at night and is still running
    return (
        TimeEntry.query.filter_by(is_active=True)
        .order_by(TimeEntry.created_at.desc())
        .first()
    )


@bp.route("/api/timer/status")
def timer_status():
    """Get the current status of the timer."""
    entry = get_open_entry()
    if entry:
        is_paused = entry.last_pause_start_time is not None

        # Calculate elapsed time since start
        start_dt = datetime.combine(entry.date, entry.start_time)
        now = datetime.now()

        if is_paused:
            # If paused, elapsed time is fixed at the pause start time minus accumulated pauses
            # Actually simpler: elapsed = (pause_start - start) - previous_pauses
            current_duration_seconds = (
                entry.last_pause_start_time - start_dt
            ).total_seconds() - (entry.accumulated_pause_seconds or 0)
        else:
            # If running: elapsed = (now - start) - previous_pauses
            current_duration_seconds = (now - start_dt).total_seconds() - (
                entry.accumulated_pause_seconds or 0
            )

        return jsonify(
            {
                "active": True,
                "is_paused": is_paused,
                "start_time": entry.start_time.strftime("%H:%M:%S"),
                "elapsed_seconds": int(max(0, current_duration_seconds)),
                "description": entry.description,
            }
        )

    return jsonify({"active": False})


@bp.route("/api/timer/session-alert-check")
def session_alert_check():
    """Check if session alert should be shown."""
    # Get the alert feature flag
    alert_enabled = Settings.get_bool("alert_on_max_work_session", default=False)

    if not alert_enabled:
        return jsonify({"alert": False, "enabled": False})

    # Get current timer entry
    entry = get_open_entry()
    if not entry:
        return jsonify({"alert": False, "enabled": True, "reason": "no_active_timer"})

    # Don't alert if timer is paused
    if entry.last_pause_start_time is not None:
        return jsonify({"alert": False, "enabled": True, "reason": "timer_paused"})

    # Calculate current session duration in hours
    start_dt = datetime.combine(entry.date, entry.start_time)
    now = datetime.now()
    current_duration_seconds = max(
        0, (now - start_dt).total_seconds() - (entry.accumulated_pause_seconds or 0)
    )
    current_duration_hours = current_duration_seconds / 3600.0

    # Get the maximum session hours threshold
    max_session_hours = Settings.get_float("max_work_session_hours", default=10.0)

    # Alert if session exceeds 8 hours and is approaching the max threshold
    # We consider "approaching" as when session is > 8 hours
    if current_duration_hours > 8.0:
        return jsonify(
            {
                "alert": True,
                "enabled": True,
                "current_hours": round(current_duration_hours, 2),
                "max_hours": max_session_hours,
                "exceeded_standard": True,
            }
        )

    return jsonify(
        {
            "alert": False,
            "enabled": True,
            "current_hours": round(current_duration_hours, 2),
            "max_hours": max_session_hours,
        }
    )


@bp.route("/api/timer/start", methods=["POST"])
def start_timer():
    """Start a new timer."""
    try:
        # Check if already running
        if get_open_entry():
            return jsonify({"success": False, "message": "Timer already running"}), 400

        data = request.get_json() or {}
        description = data.get("description", "").strip()
        if not description:
            description = "Work"

        now = datetime.now()

        entry = TimeEntry(
            date=now.date(),
            start_time=now.time(),
            end_time=now.time(),  # Marker for open entry
            duration_hours=0.0,  # Marker for open entry
            is_active=True,
            description=description,
        )

        db.session.add(entry)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Timer started",
                "start_time": now.strftime("%H:%M:%S"),
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@bp.route("/api/timer/pause", methods=["POST"])
def pause_timer():
    """Pause the current timer."""
    try:
        entry = get_open_entry()
        if not entry:
            return jsonify({"success": False, "message": "No active timer"}), 400

        if entry.last_pause_start_time:
            return jsonify({"success": False, "message": "Timer already paused"}), 400

        entry.last_pause_start_time = datetime.now()
        db.session.commit()

        return jsonify({"success": True, "message": "Timer paused"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@bp.route("/api/timer/resume", methods=["POST"])
def resume_timer():
    """Resume the paused timer."""
    try:
        entry = get_open_entry()
        if not entry:
            return jsonify({"success": False, "message": "No active timer"}), 400

        if not entry.last_pause_start_time:
            return jsonify({"success": False, "message": "Timer is not paused"}), 400

        # Calculate how long we were paused
        pause_duration = (datetime.now() - entry.last_pause_start_time).total_seconds()

        # Add to accumulated pauses
        entry.accumulated_pause_seconds = (
            entry.accumulated_pause_seconds or 0
        ) + pause_duration

        # Clear pause start time to indicate running
        entry.last_pause_start_time = None

        db.session.commit()

        return jsonify({"success": True, "message": "Timer resumed"})

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

        # If stopped while paused, effective end time is when it was paused
        if entry.last_pause_start_time:
            # We don't add the current incomplete pause to accumulated_pause_seconds
            # because the work effectively stopped at the beginning of the pause.
            effective_end_dt = entry.last_pause_start_time
            # Reset pause state to clean up (though not strictly necessary if we are closing)
            entry.last_pause_start_time = None
        else:
            effective_end_dt = now

        end_time = effective_end_dt.time()

        # Calculate duration: (End - Start) - Pauses
        # Note: calculate_duration returns hours. We need to handle the pause subtraction.
        # Let's calculate raw duration in seconds first
        start_dt = datetime.combine(entry.date, entry.start_time)

        # Handle midnight crossing for end time if needed (though effective_end_dt has date)
        # But TimeEntry stores date and time separately. `entry.date` is the start date.
        # effective_end_dt might be on the next day.

        total_elapsed_seconds = (effective_end_dt - start_dt).total_seconds()
        actual_work_seconds = total_elapsed_seconds - (
            entry.accumulated_pause_seconds or 0
        )

        duration_hours = actual_work_seconds / 3600.0

        entry.end_time = end_time
        entry.duration_hours = duration_hours
        entry.is_active = False

        db.session.commit()

        return jsonify(
            {"success": True, "message": "Timer stopped", "duration": duration_hours}
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@bp.route("/api/calendar/day/<date_str>")
def get_day_details(date_str):
    """Get details for a specific day including time entries and leave."""
    try:
        day_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Validate date is within reasonable range
        if day_date.year < 1900 or day_date.year > 2100:
            return jsonify({"success": False, "message": "Date out of valid range"}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format"}), 400
    
    try:
        # Get time entries for the day
        entries = TimeEntry.query.filter_by(date=day_date).order_by(TimeEntry.start_time).all()
        
        # Get leave for the day
        leave = LeaveDay.query.filter_by(date=day_date).first()
        
        # Calculate total hours
        total_hours = sum(e.duration_hours for e in entries)
        
        return jsonify({
            "success": True,
            "date": date_str,
            "entries": [e.to_dict() for e in entries],
            "leave": leave.to_dict() if leave else None,
            "total_hours": round(total_hours, 2),
            "entry_count": len(entries),
            "has_entry": len(entries) > 0,
            "has_leave": leave is not None
        })
    except Exception as e:
        return jsonify({"success": False, "message": "Database error occurred"}), 500


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

    # Generate calendar data for the current month
    try:
        calendar_data = generate_calendar_data(today.year, today.month)
    except Exception:
        # Provide empty calendar structure as fallback
        calendar_data = {
            'weeks': [],
            'month_name': today.strftime('%B'),
            'year': today.year,
            'month': today.month,
            'prev_month': {'year': today.year, 'month': today.month},
            'next_month': {'year': today.year, 'month': today.month}
        }

    return render_template(
        "dashboard.html",
        recent_entries=recent_entries,
        weekly_stats=weekly_stats,
        current_date=today,
        calendar_data=calendar_data,
    )


@bp.route("/time-entry", methods=["GET", "POST"])
def time_entry():
    """Add or view time entries."""
    time_format = Settings.get_setting("time_format", "24")

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
            
            start_time = parse_time_input(start_time_str, time_format)
            end_time = parse_time_input(end_time_str, time_format)

            # Calculate duration
            duration = calculate_duration(start_time, end_time)

            if duration <= 0:
                flash("End time must be after start time.", "error")
                return redirect(url_for("main.time_entry"))

            # Check for existing entries on this date (excluding active ones)
            existing_entries = TimeEntry.query.filter_by(
                date=date, is_active=False
            ).all()

            if existing_entries:
                flash(
                    f"An entry already exists for {date}. "
                    "Only one entry per day is allowed. Please edit the existing entry instead.",
                    "error",
                )
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
    return render_template("time_entry.html", today=datetime.now().date(), time_format=time_format)


@bp.route("/time-entry/<int:entry_id>/edit", methods=["GET", "POST"])
def edit_time_entry(entry_id):
    """Edit an existing time entry."""
    entry = TimeEntry.query.get_or_404(entry_id)
    time_format = Settings.get_setting("time_format", "24")

    # Prevent editing of active timers to avoid data corruption and
    # keep behavior consistent with the CLI.
    if entry.is_active:
        flash(
            "Cannot edit an active timer. Please stop the timer before editing.",
            "error",
        )
        return redirect(url_for("main.index"))

    if request.method == "POST":
        try:
            # Parse form data
            start_time_str = request.form.get("start_time")
            end_time_str = request.form.get("end_time")
            description = request.form.get("description", "").strip()

            # Validate inputs
            if not all([start_time_str, end_time_str, description]):
                flash("All fields are required.", "error")
                return redirect(url_for("main.edit_time_entry", entry_id=entry_id))

            # Parse times
            start_time = parse_time_input(start_time_str, time_format)
            end_time = parse_time_input(end_time_str, time_format)

            # Calculate duration
            duration = calculate_duration(start_time, end_time)

            if duration <= 0:
                flash("End time must be after start time.", "error")
                return redirect(url_for("main.edit_time_entry", entry_id=entry_id))

            # Update entry
            entry.start_time = start_time
            entry.end_time = end_time
            entry.duration_hours = duration
            entry.description = description

            db.session.commit()

            flash(
                f"Time entry updated successfully! Duration: {duration:.2f} hours",
                "success",
            )
            return redirect(url_for("main.index"))

        except ValueError as e:
            flash(f"Invalid time format: {str(e)}", "error")
            return redirect(url_for("main.edit_time_entry", entry_id=entry_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating time entry: {str(e)}", "error")
            return redirect(url_for("main.edit_time_entry", entry_id=entry_id))

    # GET request - show form with existing data
    return render_template("edit_time_entry.html", entry=entry, time_format=time_format)


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
            # Import here to avoid circular imports
            from .utils import get_working_days_in_range, calculate_leave_hours

            # Parse form data - support both single day and multi-day formats
            single_date_str = request.form.get("date")
            start_date_str = request.form.get("start_date")
            end_date_str = request.form.get("end_date")
            leave_type = request.form.get("leave_type")
            description = request.form.get("description", "").strip()

            # Validate leave type first
            if not leave_type:
                flash("Leave type is required.", "error")
                return redirect(url_for("main.leave"))

            if leave_type not in ["vacation", "sick"]:
                flash("Invalid leave type.", "error")
                return redirect(url_for("main.leave"))

            # Determine if single-day or multi-day request
            if single_date_str:
                # Single day format (backward compatibility)
                start_date = datetime.strptime(single_date_str, "%Y-%m-%d").date()
                end_date = start_date
            elif start_date_str and end_date_str:
                # Multi-day format
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            else:
                flash("Please provide either a date or a date range.", "error")
                return redirect(url_for("main.leave"))

            # Validate date range
            if end_date < start_date:
                flash("End date must be on or after start date.", "error")
                return redirect(url_for("main.leave"))

            # Get working days in range (excludes weekends)
            working_days = get_working_days_in_range(start_date, end_date)

            if not working_days:
                flash(
                    "No working days in the selected range (only weekends). "
                    "Please select a range that includes at least one weekday.",
                    "warning",
                )
                return redirect(url_for("main.leave"))

            # Calculate leave statistics
            leave_stats = calculate_leave_hours(start_date, end_date)

            # Create leave day records for each working day
            created_count = 0
            for leave_date in working_days:
                leave_day = LeaveDay(
                    date=leave_date, leave_type=leave_type, description=description
                )
                db.session.add(leave_day)
                created_count += 1

            db.session.commit()

            # Provide detailed feedback
            if created_count == 1:
                flash(
                    f"{leave_type.capitalize()} leave added successfully!",
                    "success",
                )
            else:
                # Multi-day feedback
                weekend_msg = (
                    f" (excluded {leave_stats['weekend_days']} weekend days)"
                    if leave_stats["weekend_days"] > 0
                    else ""
                )
                flash(
                    f"{leave_type.capitalize()} leave added successfully! "
                    f"{created_count} working days added{weekend_msg}. "
                    f"Total working hours: {leave_stats['working_hours']:.1f}h",
                    "success",
                )

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
        standard_hours_per_day=Settings.get_float("standard_hours_per_day", 8.0),
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


@bp.route("/settings", methods=["GET", "POST"])
def settings():
    """View and manage application settings."""
    if request.method == "POST":
        try:
            # Get all current settings first
            all_settings = Settings.get_all_settings()

            # Track if any changes were made
            changes_made = False
            errors = []
            updates = []  # Store updates to apply after validation

            # First pass: Validate all values
            for key in CONFIG_DEFAULTS.keys():
                config_type = CONFIG_TYPES.get(key)

                # Get current value first
                current_value = all_settings.get(key, CONFIG_DEFAULTS[key])

                # Get the new value from form
                if config_type == "bool":
                    # Checkbox: checked = "on", unchecked = not in form
                    new_value = "true" if request.form.get(key) == "on" else "false"
                else:
                    # Check if field is in the form at all
                    if key not in request.form:
                        # Field not provided - use current value
                        new_value = current_value
                    else:
                        # Field provided - validate even if empty
                        new_value = request.form.get(key, "").strip()
                        if not new_value:
                            errors.append(
                                f"{CONFIG_DISPLAY_NAMES.get(key, key)}: Value cannot be empty"
                            )
                            continue

                # Skip if value hasn't changed
                if new_value == current_value:
                    continue

                # Validate the new value
                is_valid, error_message = validate_config_value(key, new_value)
                if not is_valid:
                    errors.append(
                        f"{CONFIG_DISPLAY_NAMES.get(key, key)}: {error_message}"
                    )
                    continue

                # Normalize boolean values
                if config_type == "bool":
                    new_value = normalize_bool_value(new_value)

                # Store for later update
                updates.append((key, new_value))
                changes_made = True

            # If validation passed, apply all updates atomically
            if not errors and updates:
                for key, value in updates:
                    Settings.update_setting(key, value)
                db.session.commit()

            # Show appropriate flash message
            if errors:
                for error in errors:
                    flash(error, "error")
                if changes_made and not updates:
                    # Had changes but all failed validation
                    flash("No settings were updated due to validation errors.", "error")
            elif changes_made:
                flash("Settings updated successfully!", "success")
            else:
                flash("No changes were made.", "info")

            return redirect(url_for("main.settings"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating settings: {str(e)}", "error")
            return redirect(url_for("main.settings"))

    # GET request - show settings form
    all_settings = Settings.get_all_settings()

    # Prepare settings data for template
    settings_data = []
    for key in sorted(CONFIG_DEFAULTS.keys()):
        current_value = all_settings.get(key, CONFIG_DEFAULTS[key])
        default_value = CONFIG_DEFAULTS[key]

        setting_dict = {
            "key": key,
            "display_name": CONFIG_DISPLAY_NAMES.get(key, key),
            "current_value": current_value,
            "default_value": default_value,
            "description": CONFIG_DESCRIPTIONS.get(key, ""),
            "type": CONFIG_TYPES.get(key, "text"),
            "input_type": get_config_input_type(key),
            "is_modified": current_value != default_value,
        }

        # Add validation bounds for numeric fields
        bounds = get_config_validation_bounds(key)
        if bounds:
            setting_dict.update(bounds)

        # Add select options for dropdown fields
        options = get_config_select_options(key)
        if options:
            setting_dict["options"] = options

        settings_data.append(setting_dict)

    return render_template(
        "settings.html",
        settings_data=settings_data,
    )
