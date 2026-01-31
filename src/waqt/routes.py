"""Route handlers for the time tracking application."""

import re
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
from .models import TimeEntry, LeaveDay, Settings, Category, Template
from .utils import (
    calculate_weekly_stats,
    calculate_monthly_stats,
    get_week_bounds,
    get_month_bounds,
    export_time_entries_to_csv,
    export_time_entries_to_json,
    export_time_entries_to_excel,
    get_time_entries_for_period,
    generate_calendar_data,
    parse_time_input,
)
from .services import (
    start_time_entry,
    end_time_entry,
    update_time_entry,
    add_time_entry,
    create_leave_requests,
    create_template,
    list_templates,
    get_template,
    delete_template,
    update_template,
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
from .logging import get_flask_logger

# Initialize logger for routes
logger = get_flask_logger()

HEX_COLOR_REGEX = r"^#(?:[0-9a-fA-F]{3}){1,2}$"

bp = Blueprint("main", __name__)


@bp.route("/categories", methods=["GET", "POST"])
def categories():
    """Manage time entry categories."""
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            code = request.form.get("code", "").strip() or None
            color = request.form.get("color", "").strip() or None
            description = request.form.get("description", "").strip() or None

            if not name:
                flash("Category name is required.", "error")
                return redirect(url_for("main.categories"))

            # Validate color format (Hex code)
            if color and not re.match(HEX_COLOR_REGEX, color):
                flash("Color must be a valid hex code (e.g., #FF0000).", "error")
                return redirect(url_for("main.categories"))

            # Check for duplicate name
            if Category.query.filter_by(name=name).first():
                flash("Category with this name already exists.", "error")
                return redirect(url_for("main.categories"))

            # Check for duplicate code
            if code and Category.query.filter_by(code=code).first():
                flash("Category with this code already exists.", "error")
                return redirect(url_for("main.categories"))

            category = Category(
                name=name, code=code, color=color, description=description
            )
            db.session.add(category)
            db.session.commit()

            flash("Category added successfully!", "success")
            return redirect(url_for("main.categories"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error adding category: {str(e)}", "error")
            return redirect(url_for("main.categories"))

    # GET request
    categories = Category.query.order_by(Category.name).all()
    return render_template("categories.html", categories=categories)


@bp.route("/categories/<int:id>/edit", methods=["POST"])
def edit_category(id):
    """Edit a category."""
    category = db.get_or_404(Category, id)
    try:
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip() or None
        color = request.form.get("color", "").strip() or None
        description = request.form.get("description", "").strip() or None

        if not name:
            flash("Category name is required.", "error")
            return redirect(url_for("main.categories"))

        # Validate color format (Hex code)
        if color and not re.match(HEX_COLOR_REGEX, color):
            flash("Color must be a valid hex code (e.g., #FF0000).", "error")
            return redirect(url_for("main.categories"))

        # Check for duplicates if name/code changed
        if name != category.name and Category.query.filter_by(name=name).first():
            flash("Category with this name already exists.", "error")
            return redirect(url_for("main.categories"))

        if (
            code
            and code != category.code
            and Category.query.filter_by(code=code).first()
        ):
            flash("Category with this code already exists.", "error")
            return redirect(url_for("main.categories"))

        category.name = name
        category.code = code
        category.color = color
        category.description = description

        db.session.commit()
        flash("Category updated successfully.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating category: {str(e)}", "error")

    return redirect(url_for("main.categories"))


@bp.route("/categories/<int:id>/delete", methods=["POST"])
def delete_category(id):
    """Delete a category."""
    category = db.get_or_404(Category, id)
    try:
        # Check if used in time entries
        if TimeEntry.query.filter_by(category_id=id).first():
            flash("Cannot delete category currently assigned to time entries.", "error")
            return redirect(url_for("main.categories"))

        db.session.delete(category)
        db.session.commit()
        flash("Category deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting category: {str(e)}", "error")

    return redirect(url_for("main.categories"))


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
        category_id = data.get("category_id")

        if category_id:
            try:
                category_id = int(category_id)
            except (ValueError, TypeError):
                return (
                    jsonify({"success": False, "message": "Invalid category ID"}),
                    400,
                )

        if not description:
            description = "Work"

        now = datetime.now()

        # Use shared service
        result = start_time_entry(
            db.session, now.date(), now.time(), description, category_id=category_id
        )

        if not result["success"]:
            # If it's a duplicate active timer error, we return 400.
            # (Though shared service logic is slightly different, checking date vs any active)
            # The service returns specific error types we can use.
            return jsonify({"success": False, "message": result["message"]}), 400

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

        # Use shared service
        # Note: shared service calculates effective end time based on pauses logic
        # which was originally taken from this route.
        result = end_time_entry(db.session, now.time(), entry.date)

        if not result["success"]:
            return jsonify({"success": False, "message": result["message"]}), 500

        db.session.commit()
        duration_hours = result["duration"]

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
            return (
                jsonify({"success": False, "message": "Date out of valid range"}),
                400,
            )
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format"}), 400

    try:
        # Get time entries for the day
        entries = (
            TimeEntry.query.filter_by(date=day_date)
            .order_by(TimeEntry.start_time)
            .all()
        )

        # Get leave for the day
        leave = LeaveDay.query.filter_by(date=day_date).first()

        # Calculate total hours
        total_hours = sum(e.duration_hours for e in entries)

        return jsonify(
            {
                "success": True,
                "date": date_str,
                "entries": [e.to_dict() for e in entries],
                "leave": leave.to_dict() if leave else None,
                "total_hours": round(total_hours, 2),
                "entry_count": len(entries),
                "has_entry": len(entries) > 0,
                "has_leave": leave is not None,
            }
        )
    except Exception:  # noqa: F841
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
            "weeks": [],
            "month_name": today.strftime("%B"),
            "year": today.year,
            "month": today.month,
            "prev_month": {"year": today.year, "month": today.month},
            "next_month": {"year": today.year, "month": today.month},
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
    default_pause = Settings.get_int("pause_duration_minutes", 45)

    if request.method == "POST":
        try:
            # Parse form data
            date_str = request.form.get("date")
            start_time_str = request.form.get("start_time")
            end_time_str = request.form.get("end_time")
            description = request.form.get("description", "").strip()
            category_id = request.form.get("category_id")

            # Parse category
            if category_id:
                try:
                    category_id = int(category_id)
                    if category_id == 0:
                        category_id = None
                except (ValueError, TypeError):
                    category_id = None
            else:
                category_id = None

            # Pause handling
            pause_mode = request.form.get("pause_mode", "default")
            custom_pause_str = request.form.get("custom_pause_minutes", "0")

            try:
                pause_minutes = int(custom_pause_str) if custom_pause_str else 0
                if pause_minutes < 0:
                    pause_minutes = 0
            except ValueError:
                pause_minutes = 0

            # Validate inputs
            if not all([date_str, start_time_str, end_time_str, description]):
                flash("All fields are required.", "error")
                return redirect(url_for("main.time_entry"))

            # Parse date and times
            date = datetime.strptime(date_str, "%Y-%m-%d").date()

            start_time = parse_time_input(start_time_str, time_format)
            end_time = parse_time_input(end_time_str, time_format)

            # Use shared service
            result = add_time_entry(
                db.session,
                entry_date=date,
                start_time=start_time,
                end_time=end_time,
                description=description,
                category_id=category_id,
                pause_mode=pause_mode,
                pause_minutes=pause_minutes,
            )

            if not result["success"]:
                flash(result["message"], "error")
                return redirect(url_for("main.time_entry"))

            # Handle Save as Template
            if request.form.get("save_as_template") == "on":
                template_name = request.form.get("new_template_name", "").strip()
                if template_name:
                    # Calculate duration
                    duration_minutes = None
                    # We have start_time and end_time objects

                    create_template_result = create_template(
                        db.session,
                        name=template_name,
                        start_time=start_time,
                        end_time=end_time,
                        pause_mode=pause_mode,
                        pause_minutes=pause_minutes,
                        category_id=category_id,
                        description=description,
                    )
                    if create_template_result["success"]:
                        flash(f"Template '{template_name}' saved.", "success")
                    else:
                        flash(
                            f"Warning: Could not save template: {create_template_result['message']}",
                            "warning",
                        )

            db.session.commit()
            entry = result["entry"]
            flash(
                f"Time entry added successfully! Duration: {entry.duration_hours:.2f} hours",
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
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    templates = list_templates(db.session)
    return render_template(
        "time_entry.html",
        today=datetime.now().date(),
        time_format=time_format,
        default_pause=default_pause,
        categories=categories,
        templates=templates,
    )


@bp.route("/time-entry/<int:entry_id>/edit", methods=["GET", "POST"])
def edit_time_entry(entry_id):
    """Edit an existing time entry."""
    entry = db.get_or_404(TimeEntry, entry_id)
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
            category_id = request.form.get("category_id")

            # Validate inputs
            if not all([start_time_str, end_time_str, description]):
                flash("All fields are required.", "error")
                return redirect(url_for("main.edit_time_entry", entry_id=entry_id))

            # Parse category
            category_raw = request.form.get("category_id")
            if category_raw in (None, ""):
                category_id = 0  # Explicitly clear category
            else:
                try:
                    category_id = int(category_raw)
                except (ValueError, TypeError):
                    category_id = None  # No change

            # Parse times
            start_time = parse_time_input(start_time_str, time_format)
            end_time = parse_time_input(end_time_str, time_format)

            # Use shared service
            result = update_time_entry(
                db.session,
                entry_id,
                start_time=start_time,
                end_time=end_time,
                description=description,
                category_id=category_id,
            )

            if not result["success"]:
                flash(result["message"], "error")
                return redirect(url_for("main.edit_time_entry", entry_id=entry_id))

            db.session.commit()
            entry = result["entry"]  # Get updated entry object

            flash(
                f"Time entry updated successfully! Duration: {entry.duration_hours:.2f} hours",
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
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return render_template(
        "edit_time_entry.html",
        entry=entry,
        time_format=time_format,
        categories=categories,
    )


@bp.route("/time-entry/<int:entry_id>/delete", methods=["POST"])
def delete_time_entry(entry_id):
    """Delete a time entry."""
    try:
        entry = db.get_or_404(TimeEntry, entry_id)
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
    from sqlalchemy.orm import joinedload

    entries = (
        TimeEntry.query.options(joinedload(TimeEntry.category))
        .filter(TimeEntry.date >= start_date, TimeEntry.date <= end_date)
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

    # Calculate category stats
    category_stats = {}
    for entry in entries:
        cat_name = entry.category.name if entry.category else "Uncategorized"
        cat_color = entry.category.color if entry.category else "#9ca3af"  # gray-400

        if cat_name not in category_stats:
            category_stats[cat_name] = {"hours": 0, "color": cat_color}

        category_stats[cat_name]["hours"] += entry.duration_hours

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
        category_stats=category_stats,
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

            # Create leave day records using shared utility
            result = create_leave_requests(
                db.session, start_date, end_date, leave_type, description
            )
            db.session.commit()

            created_count = result["created"]
            skipped_count = result["skipped"]

            # Provide detailed feedback
            if created_count == 1 and skipped_count == 0:
                flash(
                    f"{leave_type.capitalize()} leave added successfully!",
                    "success",
                )
            else:
                # Multi-day feedback
                msg_parts = []
                if created_count > 0:
                    msg_parts.append(f"{created_count} working days added")
                if skipped_count > 0:
                    msg_parts.append(f"{skipped_count} days skipped (duplicates)")
                if leave_stats["weekend_days"] > 0:
                    msg_parts.append(
                        f"excluded {leave_stats['weekend_days']} weekend days"
                    )

                details = ", ".join(msg_parts)
                flash(
                    f"{leave_type.capitalize()} leave processed! {details}. "
                    f"Total working hours: {leave_stats['working_hours']:.1f}h",
                    "success" if created_count > 0 else "warning",
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
        leave_day = db.get_or_404(LeaveDay, leave_id)
        db.session.delete(leave_day)
        db.session.commit()
        flash("Leave day deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting leave day: {str(e)}", "error")

    return redirect(url_for("main.leave"))


def _handle_export_request(export_format):
    """
    Handle export request for CSV, JSON, and Excel formats.

    Args:
        export_format: One of 'csv', 'json', 'excel'
    """
    try:
        # Get filter parameters
        period = request.args.get("period", "all")
        date_str = request.args.get("date", datetime.now().date().isoformat())

        # Parse the reference date
        try:
            ref_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
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

        # Generate content based on format
        if export_format == "csv":
            content = export_time_entries_to_csv(entries, start_date, end_date)
            mimetype = "text/csv"
            extension = "csv"
        elif export_format == "json":
            content = export_time_entries_to_json(entries, start_date, end_date)
            mimetype = "application/json"
            extension = "json"
        elif export_format == "excel":
            content = export_time_entries_to_excel(entries, start_date, end_date)
            mimetype = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            extension = "xlsx"
        else:
            flash(f"Unsupported export format: {export_format}", "error")
            return redirect(url_for("main.reports"))

        # Generate filename
        if start_date and end_date:
            filename = (
                f"time_entries_{start_date.strftime('%Y%m%d')}_"
                f"{end_date.strftime('%Y%m%d')}.{extension}"
            )
        else:
            filename = (
                f"time_entries_all_{datetime.now().strftime('%Y%m%d')}.{extension}"
            )

        # Return content as download
        return Response(
            content,
            mimetype=mimetype,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except IOError as e:
        # Handle file system errors
        flash(f"Error generating export file: {str(e)}", "error")
        return redirect(url_for("main.reports"))
    except Exception as e:
        # Log unexpected errors for debugging
        logger.error(
            f"Unexpected error during {export_format.upper()} export: {str(e)}",
            exc_info=True,
        )
        flash("An unexpected error occurred during export. Please try again.", "error")
        return redirect(url_for("main.reports"))


@bp.route("/export/csv")
def export_csv():
    """Export time entries to CSV format."""
    return _handle_export_request("csv")


@bp.route("/export/json")
def export_json():
    """Export time entries to JSON format."""
    return _handle_export_request("json")


@bp.route("/export/excel")
def export_excel():
    """Export time entries to Excel format."""
    return _handle_export_request("excel")


@bp.route("/import", methods=["POST"])
def import_data():
    """Import time entries from uploaded file (POST only, accessed via reports modal)."""
    from .services import import_time_entries
    from .utils import (
        detect_import_format,
        parse_time_entries_from_json,
        parse_time_entries_from_csv,
        parse_time_entries_from_excel,
    )
    import tempfile
    import os

    try:
        # Check if file was uploaded
        if "file" not in request.files:
            flash("No file uploaded.", "error")
            return redirect(url_for("main.reports"))

        file = request.files["file"]
        if file.filename == "":
            flash("No file selected.", "error")
            return redirect(url_for("main.reports"))

        # Get options from form
        import_format = request.form.get("format", "auto").lower()
        on_conflict = request.form.get("on_conflict", "skip").lower()
        dry_run = request.form.get("dry_run") == "on"
        auto_create_categories = request.form.get("auto_create_categories") != "off"

        # Validate file extension
        filename = file.filename.lower()
        allowed_extensions = {".csv", ".json", ".xlsx", ".xls"}
        file_ext = os.path.splitext(filename)[1]

        if file_ext not in allowed_extensions:
            flash(
                f"Unsupported file type '{file_ext}'. "
                f"Allowed: {', '.join(allowed_extensions)}",
                "error",
            )
            return redirect(url_for("main.reports"))

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            file.save(tmp_file.name)
            tmp_path = tmp_file.name

        try:
            # Perform import
            result = import_time_entries(
                db.session,
                file_path=tmp_path,
                import_format=import_format,
                on_conflict=on_conflict,
                auto_create_categories=auto_create_categories,
                include_leave_days=True,
                dry_run=dry_run,
            )

            if not dry_run and result["success"]:
                db.session.commit()

            # Build result message
            if result["success"]:
                if dry_run:
                    msg_type = "info"
                    msg = "Dry run completed. "
                else:
                    msg_type = "success"
                    msg = "Import completed successfully! "

                details = []
                if result["entries_imported"] > 0:
                    details.append(f"{result['entries_imported']} entries imported")
                if result["entries_updated"] > 0:
                    details.append(f"{result['entries_updated']} entries updated")
                if result["entries_skipped"] > 0:
                    details.append(f"{result['entries_skipped']} entries skipped")
                if result["leave_days_imported"] > 0:
                    details.append(
                        f"{result['leave_days_imported']} leave days imported"
                    )
                if result["categories_created"]:
                    details.append(
                        f"Categories created: {', '.join(result['categories_created'])}"
                    )

                msg += ". ".join(details) if details else "No entries to import."
                flash(msg, msg_type)

                # Show warnings
                for warning in result.get("warnings", [])[:5]:
                    flash(f"Warning: {warning}", "warning")

            else:
                flash("Import failed. Check errors below.", "error")
                for error in result.get("errors", [])[:5]:
                    flash(f"Error: {error}", "error")

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return redirect(url_for("main.reports"))

    except Exception as e:
        db.session.rollback()
        flash(f"Import error: {str(e)}", "error")
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


@bp.route("/templates")
def templates():
    """Manage time entry templates."""
    templates = list_templates(db.session)
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return render_template("templates.html", templates=templates, categories=categories)


@bp.route("/templates/create", methods=["POST"])
def create_template_route():
    """Create a new template."""
    try:
        name = request.form.get("name", "").strip()
        start_time_str = request.form.get("start_time")
        end_time_str = request.form.get("end_time")
        duration_str = request.form.get("duration_minutes")
        pause_mode = request.form.get("pause_mode", "default")
        pause_str = request.form.get("pause_minutes", "0")
        category_id = request.form.get("category_id") or None
        description = request.form.get("description", "").strip()
        is_default = request.form.get("is_default") == "on"

        if not name or not start_time_str:
            flash("Name and Start Time are required.", "error")
            return redirect(url_for("main.templates"))

        try:
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = (
                datetime.strptime(end_time_str, "%H:%M").time()
                if end_time_str
                else None
            )
        except ValueError:
            flash("Invalid time format.", "error")
            return redirect(url_for("main.templates"))

        duration_minutes = int(duration_str) if duration_str else None
        pause_minutes = int(pause_str) if pause_str else 0
        if category_id:
            category_id = int(category_id)

        result = create_template(
            db.session,
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

        if result["success"]:
            flash("Template created successfully.", "success")
        else:
            flash(f"Error: {result['message']}", "error")

        db.session.commit()  # Ensure commit happens if service didn't (service usually doesn't commit if passed session? wait, service implementation commits? let's check. create_template calls session.add but maybe not commit? I should check service)
        # Service implementation:
        #  session.add(template)
        #  try: session.commit() ...
        # So it handles commit. Good.

    except Exception as e:
        db.session.rollback()
        flash(f"Error creating template: {str(e)}", "error")

    return redirect(url_for("main.templates"))


@bp.route("/templates/<int:id>/delete", methods=["POST"])
def delete_template_route(id):
    """Delete a template."""
    result = delete_template(db.session, id)
    if result["success"]:
        flash("Template deleted.", "success")
    else:
        flash(f"Error: {result['message']}", "error")
    return redirect(url_for("main.templates"))


@bp.route("/templates/<int:id>/default", methods=["POST"])
def set_default_template_route(id):
    """Set a template as default."""
    try:
        # Clear existing default
        Template.query.update({Template.is_default: False})

        # Set new default
        template = db.get_or_404(Template, id)
        template.is_default = True
        db.session.commit()
        flash(f"Set '{template.name}' as default template.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error setting default template: {str(e)}", "error")

    return redirect(url_for("main.templates"))
