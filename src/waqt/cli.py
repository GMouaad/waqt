"""CLI interface for waqt time tracking application."""

import click
from datetime import datetime
from typing import Optional

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
    export_time_entries_to_excel,
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
from ._version import VERSION, GIT_SHA
from .config import (
    CONFIG_DEFAULTS,
    CONFIG_TYPES,
    CONFIG_DESCRIPTIONS,
    validate_config_value,
    normalize_bool_value,
)
from .updater import (
    check_for_updates,
    download_and_install_update,
    is_frozen,
)
from .logging import get_cli_logger

# Flag to track if database has been initialized this session
_db_initialized = False

# Global logger (initialized with verbose option)
_cli_logger = None


def ensure_db_initialized():
    """Ensure database is initialized before any command runs."""
    global _db_initialized
    if not _db_initialized:
        if _cli_logger:
            _cli_logger.debug("Initializing database")
        initialize_database()
        _db_initialized = True


@click.group()
@click.version_option(version=VERSION, prog_name="waqt")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging output")
@click.pass_context
def cli(ctx, verbose):
    """Waqt - Time tracking CLI for waqt application.

    A command-line interface for tracking work hours, managing time entries,
    and generating reports.
    """
    global _cli_logger
    _cli_logger = get_cli_logger(verbose=verbose)
    ctx.ensure_object(dict)
    ctx.obj["logger"] = _cli_logger
    _cli_logger.info("CLI started")
    ensure_db_initialized()


@cli.command()
@click.option(
    "--date",
    "-d",
    type=str,
    default=None,
    help="Date in YYYY-MM-DD format (default: today)",
)
@click.option(
    "--start",
    "-s",
    type=str,
    required=True,
    help="Start time in HH:MM format",
)
@click.option(
    "--end",
    "-e",
    type=str,
    required=True,
    help="End time in HH:MM format",
)
@click.option(
    "--description",
    "-desc",
    type=str,
    default="Work session",
    help="Description of the work session",
)
@click.option(
    "--pause",
    "-p",
    type=str,
    default="default",
    help="Pause mode: 'default', 'none', or minutes (e.g. '30', '45')",
)
def add(date: Optional[str], start: str, end: str, description: str, pause: str):
    """Add a completed time entry.

    Creates a past/completed time entry with start and end times.
    You can specify how to handle pauses:
    - --pause default: Use the configured default pause duration (default behavior)
    - --pause none: No pause deduction
    - --pause 30: Deduct specific minutes (e.g. 30)

    Examples:
        waqt add --start 09:00 --end 17:00
        waqt add -d 2024-01-15 -s 09:00 -e 17:30 --pause none
        waqt add -s 09:00 -e 18:00 --pause 45 --desc "Long day"
    """
    with get_session() as session:
        # Parse date
        if date:
            try:
                entry_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                click.echo(
                    click.style(
                        f"Error: Invalid date format '{date}'. Use YYYY-MM-DD.",
                        fg="red",
                    )
                )
                raise click.exceptions.Exit(1)
        else:
            entry_date = datetime.now().date()

        # Parse times
        try:
            start_time = datetime.strptime(start, "%H:%M").time()
            end_time = datetime.strptime(end, "%H:%M").time()
        except ValueError:
            click.echo(click.style("Error: Invalid time format. Use HH:MM.", fg="red"))
            raise click.exceptions.Exit(1)

        # Parse pause
        if pause.lower() == "default":
            pause_mode = "default"
            pause_minutes = 0
        elif pause.lower() == "none":
            pause_mode = "none"
            pause_minutes = 0
        else:
            try:
                pause_minutes = int(pause)
                pause_mode = "custom"
                if pause_minutes < 0:
                    raise ValueError
            except ValueError:
                click.echo(
                    click.style(
                        f"Error: Invalid pause value '{pause}'. "
                        "Use 'default', 'none', or a positive integer.",
                        fg="red",
                    )
                )
                raise click.exceptions.Exit(1)

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
            click.echo(click.style(f"Error: {result['message']}", fg="red"))
            raise click.exceptions.Exit(1)

        entry = result["entry"]
        click.echo(
            click.style("✓ Time entry added successfully!", fg="green", bold=True)
        )
        click.echo(f"Date: {entry_date}")
        click.echo(f"Time: {format_time(start_time)} - {format_time(end_time)}")
        click.echo(f"Duration: {format_hours(entry.duration_hours)}")
        if entry.accumulated_pause_seconds > 0:
            click.echo(f"Pause: {int(entry.accumulated_pause_seconds/60)} minutes")
        click.echo(f"Description: {description}")


@cli.command()
@click.option(
    "--time",
    "-t",
    type=str,
    default=None,
    help="Start time in HH:MM format (default: current time)",
)
@click.option(
    "--date",
    "-d",
    type=str,
    default=None,
    help="Date in YYYY-MM-DD format (default: today)",
)
@click.option(
    "--description",
    "-desc",
    type=str,
    default="Work session",
    help="Description of the work session",
)
def start(time: Optional[str], date: Optional[str], description: str):
    """Start time tracking for the current day.

    Creates a new time entry with the specified or current time as the start time.
    The entry will remain open until you run 'waqt end'.

    Examples:
        waqt start
        waqt start --time 09:00
        waqt start --date 2024-01-15 --time 09:30 --description "Morning session"
    """
    with get_session() as session:
        # Parse date
        if date:
            try:
                entry_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                click.echo(
                    click.style(
                        f"Error: Invalid date format '{date}'. Use YYYY-MM-DD.",
                        fg="red",
                    )
                )
                raise click.exceptions.Exit(1)
        else:
            entry_date = datetime.now().date()

        # Parse time
        if time:
            try:
                start_time = datetime.strptime(time, "%H:%M").time()
            except ValueError:
                click.echo(
                    click.style(
                        f"Error: Invalid time format '{time}'. Use HH:MM.", fg="red"
                    )
                )
                raise click.exceptions.Exit(1)
        else:
            start_time = datetime.now().time()

        # Validate and normalize description
        description = description.strip() if description else ""
        if not description:
            description = "Work session"

        # Use shared service
        result = start_time_entry(session, entry_date, start_time, description)

        if not result["success"]:
            click.echo(click.style(f"Error: {result['message']}", fg="red"))
            if result.get("error_type") == "duplicate_active":
                click.echo("Please run 'waqt end' first to close it.")
            raise click.exceptions.Exit(1)

        click.echo(click.style("✓ Time tracking started!", fg="green", bold=True))
        click.echo(f"Date: {entry_date}")
        click.echo(f"Start time: {format_time(start_time)}")
        click.echo(f"Description: {description}")
        click.echo("\nRun 'waqt end' when you're done to record the session duration.")


@cli.command()
@click.option(
    "--time",
    "-t",
    type=str,
    default=None,
    help="End time in HH:MM format (default: current time)",
)
@click.option(
    "--date",
    "-d",
    type=str,
    default=None,
    help="Date in YYYY-MM-DD format (default: today)",
)
def end(time: Optional[str], date: Optional[str]):
    """End time tracking for the current day.

    Closes the most recent open time entry by setting the end time and
    calculating the duration.

    Examples:
        waqt end
        waqt end --time 17:30
        waqt end --date 2024-01-15 --time 18:00
    """
    with get_session() as session:
        # Parse date
        if date:
            try:
                entry_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                click.echo(
                    click.style(
                        f"Error: Invalid date format '{date}'. Use YYYY-MM-DD.",
                        fg="red",
                    )
                )
                raise click.exceptions.Exit(1)
        else:
            entry_date = datetime.now().date()

        # Parse time
        if time:
            try:
                end_time = datetime.strptime(time, "%H:%M").time()
            except ValueError:
                click.echo(
                    click.style(
                        f"Error: Invalid time format '{time}'. Use HH:MM.", fg="red"
                    )
                )
                raise click.exceptions.Exit(1)
        else:
            end_time = datetime.now().time()

        # Use shared service
        result = end_time_entry(session, end_time, entry_date)

        if not result["success"]:
            click.echo(click.style(f"Error: {result['message']}", fg="red"))
            if result.get("error_type") == "no_active_timer":
                click.echo("Run 'waqt start' first to begin tracking time.")
            raise click.exceptions.Exit(1)

        entry = result["entry"]
        duration = result["duration"]

        click.echo(click.style("✓ Time tracking ended!", fg="green", bold=True))
        click.echo(f"Date: {entry_date}")
        click.echo(f"Start time: {format_time(entry.start_time)}")
        click.echo(f"End time: {format_time(end_time)}")
        click.echo(f"Duration: {format_hours(duration)}")
        click.echo(f"Description: {entry.description}")


@cli.command()
@click.option(
    "--date",
    "-d",
    type=str,
    required=True,
    help="Date of the entry to edit in YYYY-MM-DD format",
)
@click.option(
    "--start",
    "-s",
    type=str,
    default=None,
    help="New start time in HH:MM format",
)
@click.option(
    "--end",
    "-e",
    type=str,
    default=None,
    help="New end time in HH:MM format",
)
@click.option(
    "--description",
    "--desc",
    type=str,
    default=None,
    help="New description",
)
def edit_entry(
    date: str,
    start: Optional[str],
    end: Optional[str],
    description: Optional[str],
):
    """Edit an existing time entry.

    Modify the details of a time entry for a specific date. You can update
    the start time, end time, and/or description. At least one field must
    be provided to update.

    Examples:
        waqt edit-entry --date 2026-01-08 --desc "Updated description"
        waqt edit-entry -d 2026-01-08 --start 09:00 --end 17:30
        waqt edit-entry -d 2026-01-08 -s 08:30 -e 17:00 --desc "Full day work"
    """
    with get_session() as session:
        # Parse date
        try:
            entry_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            click.echo(
                click.style(
                    f"Error: Invalid date format '{date}'. Use YYYY-MM-DD.",
                    fg="red",
                )
            )
            raise click.exceptions.Exit(1)

        # Check if at least one field to update is provided
        if not any([start, end, description]):
            click.echo(
                click.style(
                    "Error: At least one field must be provided to update.",
                    fg="red",
                )
            )
            click.echo(
                "Use --start, --end, or --description to specify what to change."
            )
            raise click.exceptions.Exit(1)

        # Find entries for this date (excluding active/open entries)
        entries = (
            session.query(TimeEntry)
            .filter_by(date=entry_date, is_active=False)
            .order_by(TimeEntry.created_at.desc())
            .all()
        )

        if not entries:
            click.echo(
                click.style(
                    f"Error: No completed time entry found for {entry_date}.",
                    fg="red",
                )
            )
            click.echo(
                "Note: Cannot edit entries that are currently active. "
                "Run 'waqt end' first."
            )
            raise click.exceptions.Exit(1)

        # Handle multiple entries per day (legacy case)
        if len(entries) > 1:
            click.echo(
                click.style(
                    f"⚠ Multiple entries found for {entry_date}:",
                    fg="yellow",
                    bold=True,
                )
            )
            click.echo()
            for idx, entry_item in enumerate(entries, 1):
                click.echo(
                    f"  {idx}. {format_time(entry_item.start_time)}-"
                    f"{format_time(entry_item.end_time)} "
                    f"({format_hours(entry_item.duration_hours)}) - {entry_item.description[:50]}"
                )
            click.echo()
            click.echo(
                "Please resolve multiple entries in UI or use ID-based editing "
                "(not available in CLI yet)."
            )

            if start:
                try:
                    start_filter = datetime.strptime(start, "%H:%M").time()
                    matching = [e for e in entries if e.start_time == start_filter]
                    if len(matching) == 1:
                        entry = matching[0]
                    else:
                        click.echo(
                            click.style(
                                "Error: Could not uniquely identify entry by start time.",
                                fg="red",
                            )
                        )
                        raise click.exceptions.Exit(1)
                except ValueError:
                    click.echo(
                        click.style(f"Error: Invalid time format '{start}'.", fg="red")
                    )
                    raise click.exceptions.Exit(1)
            else:
                click.echo(
                    click.style(
                        "Error: Multiple entries. Provide --start to select one.",
                        fg="red",
                    )
                )
                raise click.exceptions.Exit(1)
        else:
            entry = entries[0]

        # Store original values for display
        original_start = entry.start_time
        original_end = entry.end_time
        original_description = entry.description

        # Prepare updates
        start_t = None
        if start:
            try:
                parsed_start = datetime.strptime(start, "%H:%M").time()
                if entry.start_time != parsed_start:
                    start_t = parsed_start
            except ValueError:
                click.echo(
                    click.style(f"Error: Invalid time format '{start}'.", fg="red")
                )
                raise click.exceptions.Exit(1)

        end_t = None
        if end:
            try:
                end_t = datetime.strptime(end, "%H:%M").time()
            except ValueError:
                click.echo(
                    click.style(f"Error: Invalid time format '{end}'.", fg="red")
                )
                raise click.exceptions.Exit(1)

        # Use shared service
        result = update_time_entry(
            session,
            entry.id,
            start_time=start_t,
            end_time=end_t,
            description=description,
        )

        if not result["success"]:
            click.echo(click.style(f"Error: {result['message']}", fg="red"))
            raise click.exceptions.Exit(1)

        entry = result["entry"]

        # Display success message
        click.echo(
            click.style("✓ Time entry updated successfully!", fg="green", bold=True)
        )
        click.echo(f"Date: {entry_date}")

        if start:
            click.echo(
                f"Start time: {format_time(original_start)} → "
                f"{format_time(entry.start_time)}"
            )
        if end:
            click.echo(
                f"End time: {format_time(original_end)} → "
                f"{format_time(entry.end_time)}"
            )
        if start or end:
            click.echo(f"Duration: {format_hours(entry.duration_hours)}")
        if description:
            click.echo(f"Description: {original_description} → {entry.description}")


@cli.command()
@click.option(
    "--period",
    "-p",
    type=click.Choice(["week", "month"], case_sensitive=False),
    default="week",
    help="Summary period (default: week)",
)
@click.option(
    "--date",
    "-d",
    type=str,
    default=None,
    help="Date for the period in YYYY-MM-DD format (default: today)",
)
def summary(period: str, date: Optional[str]):
    """Summarize tracked time for the current week or month.

    Displays statistics including total hours, overtime, working days,
    and leave days for the specified period.

    Examples:
        waqt summary
        waqt summary --period month
        waqt sum -p week -d 2024-01-15
    """
    with get_session() as session:
        # Parse date
        if date:
            try:
                ref_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                click.echo(
                    click.style(
                        f"Error: Invalid date format '{date}'. Use YYYY-MM-DD.",
                        fg="red",
                    )
                )
                raise click.exceptions.Exit(1)
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
            # Query leave days only for monthly statistics
            leave_days = (
                session.query(LeaveDay)
                .filter(LeaveDay.date >= start_date)
                .filter(LeaveDay.date <= end_date)
                .all()
            )
            stats = calculate_monthly_stats(entries, leave_days)

        # Display summary
        click.echo(
            click.style(
                f"\n{period_name} Summary: {start_date} to {end_date}",
                fg="cyan",
                bold=True,
            )
        )
        click.echo("=" * 50)

        if not entries:
            click.echo(
                click.style("No time entries found for this period.", fg="yellow")
            )
        else:
            click.echo(f"Total Hours: {format_hours(stats['total_hours'])}")
            click.echo(f"Working Days: {stats['working_days']}")

            if period.lower() == "week":
                click.echo(f"Standard Hours: {format_hours(stats['standard_hours'])}")
                click.echo(
                    f"Overtime: {format_hours(stats['overtime'])}",
                )
                if stats["overtime"] > 0:
                    click.echo(
                        click.style(
                            f"  ⚠ {format_hours(stats['overtime'])} overtime hours",
                            fg="yellow",
                        )
                    )
            else:
                click.echo(f"Expected Hours: {format_hours(stats['expected_hours'])}")
                click.echo(f"Overtime: {format_hours(stats['overtime'])}")
                if stats["overtime"] > 0:
                    click.echo(
                        click.style(
                            f"  ⚠ {format_hours(stats['overtime'])} overtime hours",
                            fg="yellow",
                        )
                    )

                # Show leave days (only available for monthly summary)
                if stats.get("vacation_days", 0) > 0 or stats.get("sick_days", 0) > 0:
                    click.echo("\nLeave Days:")
                    click.echo(f"  Vacation: {stats['vacation_days']}")
                    click.echo(f"  Sick: {stats['sick_days']}")

        # Show recent entries
        if entries:
            click.echo("\n" + click.style("Recent Entries:", fg="cyan"))
            click.echo("-" * 50)
            for entry in entries[-5:]:  # Show last 5 entries
                overtime_marker = " ⚠" if entry.duration_hours > 8.0 else ""
                click.echo(
                    f"{entry.date} | {format_time(entry.start_time)}-"
                    f"{format_time(entry.end_time)} | "
                    f"{format_hours(entry.duration_hours)}{overtime_marker} | "
                    f"{entry.description[:40]}"
                )

        click.echo()


# Create alias for summary command
cli.add_command(summary, "sum")


@cli.command()
def reference():
    """Display reference information and documentation.

    [Placeholder for future expansion]

    This command will provide quick reference documentation for time tracking
    workflows, shortcuts, and best practices.
    """
    click.echo(click.style("\n📚 Waqt Reference", fg="cyan", bold=True))
    click.echo("=" * 50)
    click.echo("\nThis command is a placeholder for future expansion.")
    click.echo("\nPlanned features:")
    click.echo("  • Quick reference guide for time tracking")
    click.echo("  • Common workflows and examples")
    click.echo("  • Keyboard shortcuts and tips")
    click.echo("  • Configuration options")
    click.echo("\nFor now, use 'waqt --help' to see available commands.")
    click.echo()


@cli.command()
@click.option(
    "--period",
    "-p",
    type=click.Choice(["week", "month", "all"], case_sensitive=False),
    default="all",
    help="Export period: week, month, or all entries (default: all)",
)
@click.option(
    "--date",
    "-d",
    type=str,
    default=None,
    help="Reference date for week/month in YYYY-MM-DD format (default: today)",
)
@click.option(
    "--output",
    "-o",
    type=str,
    default=None,
    help="Output file path (default: time_entries_<period>_<date>.<ext>)",
)
@click.option(
    "--format",
    "-f",
    "export_format",
    type=click.Choice(["csv", "json", "excel"], case_sensitive=False),
    default="csv",
    help="Export format (default: csv)",
)
def export(period: str, date: Optional[str], output: Optional[str], export_format: str):
    """Export time entries to CSV, JSON or Excel file.

    Export your time tracking data to a file for external use.
    You can export by week, month, or all entries.

    Examples:
        waqt export
        waqt export --format json
        waqt export --period week --format excel
        waqt export --output my_report.xlsx
    """
    with get_session() as session:
        # Parse reference date
        if date:
            try:
                ref_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                click.echo(
                    click.style(
                        f"Error: Invalid date format '{date}'. Use YYYY-MM-DD.",
                        fg="red",
                    )
                )
                raise click.exceptions.Exit(1)
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

        # Query entries using utility function (needs session-based version)
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
            click.echo(click.style("No time entries found to export.", fg="yellow"))
            raise click.exceptions.Exit(0)

        # Generate content based on format
        if export_format.lower() == "json":
            content = export_time_entries_to_json(entries, start_date, end_date)
            default_ext = "json"
            mode = "w"
            encoding = "utf-8"
        elif export_format.lower() in ("excel", "xlsx"):
            content = export_time_entries_to_excel(entries, start_date, end_date)
            default_ext = "xlsx"
            mode = "wb"
            encoding = None
        else:  # csv
            content = export_time_entries_to_csv(entries, start_date, end_date)
            default_ext = "csv"
            mode = "w"
            encoding = "utf-8"

        # Determine output filename
        if output:
            output_file = output
        else:
            timestamp = datetime.now().strftime("%Y%m%d")
            output_file = f"time_entries_{period_name}_{timestamp}.{default_ext}"

        # Write to file
        try:
            if mode == "wb":
                with open(output_file, mode) as f:
                    f.write(content)
            else:
                with open(output_file, mode, encoding=encoding) as f:
                    f.write(content)

            click.echo(click.style("✓ Export successful!", fg="green", bold=True))
            click.echo(f"File: {output_file}")
            click.echo(f"Format: {export_format.upper()}")
            click.echo(f"Entries exported: {len(entries)}")

            if start_date and end_date:
                click.echo(f"Period: {start_date} to {end_date}")

            total_hours = sum(entry.duration_hours for entry in entries)
            click.echo(f"Total hours: {format_hours(total_hours)}")

        except IOError as e:
            click.echo(click.style(f"Error writing to file: {str(e)}", fg="red"))
            raise click.exceptions.Exit(1)


# Configuration management commands
@cli.group()
def config():
    """Manage application configuration settings.

    Configuration options control various aspects of time tracking behavior,
    including standard work hours, break durations, and feature flags.
    All settings are stored persistently in the database.
    """
    pass


@config.command("list")
def config_list():
    """Display all configuration options and their current values.

    Shows all configuration settings with their current values, descriptions,
    and default values. Settings marked with (*) indicate they are using
    non-default values.

    Examples:
        waqt config list
    """
    with get_session() as session:
        all_settings = Settings.get_all_settings_with_session(session)

        click.echo(click.style("\n⚙️  Configuration Settings", fg="cyan", bold=True))
        click.echo("=" * 70)

        # Sort by key for consistent display
        for key in sorted(CONFIG_DEFAULTS.keys()):
            current_value = all_settings.get(key, CONFIG_DEFAULTS[key])
            default_value = CONFIG_DEFAULTS[key]
            description = CONFIG_DESCRIPTIONS.get(key, "No description available")

            # Mark non-default values
            marker = " *" if current_value != default_value else ""

            click.echo(f"\n{click.style(key, fg='green', bold=True)}{marker}")
            click.echo(f"  Value: {current_value}")
            click.echo(f"  Default: {default_value}")
            click.echo(f"  Description: {description}")

        click.echo("\n" + "=" * 70)
        click.echo("* Indicates non-default value")
        click.echo()


@config.command("get")
@click.argument("key")
def config_get(key: str):
    """Get the value of a specific configuration option.

    Displays the current value of the specified configuration key.

    Examples:
        waqt config get weekly_hours
        waqt config get auto_end
    """
    with get_session() as session:
        if key not in CONFIG_DEFAULTS:
            click.echo(
                click.style(
                    f"Error: Unknown configuration key '{key}'.",
                    fg="red",
                )
            )
            click.echo("\nAvailable configuration keys:")
            for k in sorted(CONFIG_DEFAULTS.keys()):
                click.echo(f"  - {k}")
            raise click.exceptions.Exit(1)

        value = Settings.get_setting_with_session(session, key, CONFIG_DEFAULTS[key])
        description = CONFIG_DESCRIPTIONS.get(key, "No description available")

        click.echo(click.style(f"\n{key}", fg="green", bold=True))
        click.echo(f"Value: {value}")
        click.echo(f"Description: {description}")
        click.echo()


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration option to a new value.

    Updates the specified configuration key with the provided value.
    The value will be validated before being saved.

    Examples:
        waqt config set weekly_hours 35
        waqt config set pause_duration_minutes 60
        waqt config set auto_end true
    """
    with get_session() as session:
        if key not in CONFIG_DEFAULTS:
            click.echo(
                click.style(
                    f"Error: Unknown configuration key '{key}'.",
                    fg="red",
                )
            )
            click.echo("\nAvailable configuration keys:")
            for k in sorted(CONFIG_DEFAULTS.keys()):
                click.echo(f"  - {k}")
            raise click.exceptions.Exit(1)

        # Validate the value using shared validation logic
        is_valid, error_message = validate_config_value(key, value)
        if not is_valid:
            click.echo(
                click.style(
                    f"Error: Invalid value for '{key}'.",
                    fg="red",
                )
            )
            click.echo(f"{error_message}")
            raise click.exceptions.Exit(1)

        # Normalize boolean values for all boolean type configs
        if CONFIG_TYPES.get(key) == "bool":
            value = normalize_bool_value(value)

        # Get old value for display
        old_value = Settings.get_setting_with_session(
            session, key, CONFIG_DEFAULTS[key]
        )

        # Set the new value
        Settings.set_setting_with_session(session, key, value)

        click.echo(click.style("✓ Configuration updated!", fg="green", bold=True))
        click.echo(f"Key: {key}")
        click.echo(f"Old value: {old_value}")
        click.echo(f"New value: {value}")
        click.echo()


@config.command("reset")
@click.argument("key")
def config_reset(key: str):
    """Reset a configuration option to its default value.

    Restores the specified configuration key to its default value.

    Examples:
        waqt config reset weekly_hours
        waqt config reset auto_end
    """
    with get_session() as session:
        if key not in CONFIG_DEFAULTS:
            click.echo(
                click.style(
                    f"Error: Unknown configuration key '{key}'.",
                    fg="red",
                )
            )
            click.echo("\nAvailable configuration keys:")
            for k in sorted(CONFIG_DEFAULTS.keys()):
                click.echo(f"  - {k}")
            raise click.exceptions.Exit(1)

        default_value = CONFIG_DEFAULTS[key]
        old_value = Settings.get_setting_with_session(session, key, default_value)

        # Set to default value
        Settings.set_setting_with_session(session, key, default_value)

        click.echo(
            click.style("✓ Configuration reset to default!", fg="green", bold=True)
        )
        click.echo(f"Key: {key}")
        click.echo(f"Old value: {old_value}")
        click.echo(f"Default value: {default_value}")
        click.echo()


@cli.command()
@click.option(
    "--from",
    "start_date",
    type=str,
    required=True,
    help="Start date in YYYY-MM-DD format",
)
@click.option(
    "--to",
    "end_date",
    type=str,
    required=True,
    help="End date in YYYY-MM-DD format",
)
@click.option(
    "--type",
    "-t",
    "leave_type",
    type=click.Choice(["vacation", "sick"], case_sensitive=False),
    default="vacation",
    help="Type of leave (default: vacation)",
)
@click.option(
    "--description",
    "--desc",
    type=str,
    default="",
    help="Description or notes for the leave",
)
def leave_request(start_date: str, end_date: str, leave_type: str, description: str):
    """Request multi-day leave with automatic working hours calculation.

    Creates leave records for all working days (Monday-Friday) in the specified
    date range, automatically excluding weekends. Useful for requesting vacation
    or sick leave spanning multiple days.

    Examples:
        waqt leave-request --from 2026-01-13 --to 2026-01-17
        waqt leave-request --from 2026-01-13 --to 2026-01-19 --type vacation
        waqt leave-request --from 2026-01-20 --to 2026-01-24 --type sick --desc "Medical leave"
    """
    with get_session() as session:
        # Parse dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            click.echo(
                click.style(
                    f"Error: Invalid start date format '{start_date}'. Use YYYY-MM-DD.",
                    fg="red",
                )
            )
            raise click.exceptions.Exit(1)

        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            click.echo(
                click.style(
                    f"Error: Invalid end date format '{end_date}'. Use YYYY-MM-DD.",
                    fg="red",
                )
            )
            raise click.exceptions.Exit(1)

        # Validate date range
        if end < start:
            click.echo(
                click.style(
                    "Error: End date must be on or after start date.",
                    fg="red",
                )
            )
            raise click.exceptions.Exit(1)

        # Calculate leave statistics
        leave_stats = calculate_leave_hours(start, end)
        working_days = get_working_days_in_range(start, end)

        # Check if there are any working days
        if not working_days:
            click.echo(
                click.style(
                    "⚠ No working days in the selected range (only weekends).",
                    fg="yellow",
                    bold=True,
                )
            )
            click.echo("Please select a range that includes at least one weekday.")
            raise click.exceptions.Exit(1)

        # Display preview
        click.echo(click.style("\n📅 Leave Request Summary", fg="cyan", bold=True))
        click.echo("=" * 50)
        click.echo(f"Start Date: {start.strftime('%Y-%m-%d (%A)')}")
        click.echo(f"End Date: {end.strftime('%Y-%m-%d (%A)')}")
        click.echo(f"Leave Type: {leave_type.capitalize()}")
        if description:
            click.echo(f"Description: {description}")
        click.echo()
        click.echo(f"Total Days: {leave_stats['total_days']}")
        click.echo(f"Working Days: {leave_stats['working_days']} (Mon-Fri)")
        if leave_stats["weekend_days"] > 0:
            click.echo(
                click.style(
                    f"Weekend Days: {leave_stats['weekend_days']} (excluded)",
                    fg="yellow",
                )
            )
        click.echo(f"Working Hours: {format_hours(leave_stats['working_hours'])}")
        click.echo()

        # Confirm before creating
        if not click.confirm("Create leave records for these dates?"):
            click.echo("Leave request cancelled.")
            raise click.exceptions.Exit(0)

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

            click.echo(
                click.style(
                    "✓ Leave request created successfully!",
                    fg="green",
                    bold=True,
                )
            )
            click.echo(f"Created {created_count} leave record(s)")
            if skipped_count > 0:
                click.echo(f"Skipped {skipped_count} duplicate record(s)")

            if leave_stats["weekend_days"] > 0:
                click.echo(f"Excluded {leave_stats['weekend_days']} weekend day(s)")
            click.echo()

        except Exception as e:
            click.echo(
                click.style(
                    f"Error creating leave records: {str(e)}",
                    fg="red",
                )
            )
            raise click.exceptions.Exit(1)


@cli.command()
def version():
    """Display version information.

    Shows the current version number and git commit SHA.
    Useful for debugging and checking if updates are available.

    Examples:
        waqt version
    """
    click.echo(click.style(f"\nwaqt version {VERSION}", fg="cyan", bold=True))
    if GIT_SHA and GIT_SHA != "unknown":
        # Show short SHA (first 7 characters)
        short_sha = GIT_SHA[:7] if len(GIT_SHA) > 7 else GIT_SHA
        click.echo(f"Git commit: {short_sha}")

    # Show frozen status
    if is_frozen():
        click.echo("Running as: frozen executable (PyInstaller)")
    else:
        click.echo("Running as: Python source")

    click.echo()


@cli.group(invoke_without_command=True)
@click.pass_context
def update(ctx):
    """Check for updates and self-update the waqt executable.

    Update commands allow you to check for and install new versions of waqt.
    Self-update only works for frozen executables (installed via install.sh).
    If running from source, use 'git pull' and 'uv pip install -e .' instead.
    """
    # If no subcommand is provided, default to 'install'
    if ctx.invoked_subcommand is None:
        ctx.invoke(update_install, yes=False, prerelease=False)


@update.command("check")
@click.option(
    "--prerelease",
    is_flag=True,
    help="Check for prerelease (dev) versions instead of stable releases",
)
def update_check(prerelease: bool):
    """Check for available updates without installing.

    Queries GitHub Releases to see if a newer version is available.
    By default checks stable releases; use --prerelease for dev versions.

    Examples:
        waqt update check
        waqt update check --prerelease
    """
    click.echo(click.style("\n🔍 Checking for updates...", fg="cyan"))
    click.echo(f"Current version: {VERSION}")

    channel = "prerelease (dev)" if prerelease else "stable"
    click.echo(f"Channel: {channel}")
    click.echo()

    try:
        update_info = check_for_updates(timeout=10, prerelease=prerelease)

        if update_info:
            new_version = update_info["version"]
            click.echo(
                click.style(f"✓ Update available: {new_version}", fg="green", bold=True)
            )
            click.echo(f"Release URL: {update_info['url']}")
            click.echo()
            click.echo("To install the update, run:")
            if prerelease:
                click.echo(
                    click.style("  waqt update install --prerelease", fg="yellow")
                )
            else:
                click.echo(click.style("  waqt update install", fg="yellow"))
        else:
            click.echo(click.style("✓ You are running the latest version", fg="green"))

        click.echo()

    except Exception as e:
        click.echo(click.style(f"❌ Error checking for updates: {e}", fg="red"))
        raise click.exceptions.Exit(1)


@update.command("install")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt and install immediately",
)
@click.option(
    "--prerelease",
    is_flag=True,
    help="Install prerelease (dev) version instead of stable release",
)
def update_install(yes: bool, prerelease: bool):
    """Download and install the latest version.

    Downloads the latest release from GitHub and replaces the current
    executable. Only works for frozen executables (PyInstaller builds).

    Examples:
        waqt update install
        waqt update install --yes
        waqt update install --prerelease
    """
    # Check if running as frozen executable
    if not is_frozen():
        click.echo(
            click.style(
                "\n❌ Self-update is only available for frozen executables", fg="red"
            )
        )
        click.echo()
        click.echo("You are running waqt from source.")
        click.echo("To update, use:")
        click.echo(click.style("  cd <waqt-repo-directory>", fg="yellow"))
        click.echo(click.style("  git pull", fg="yellow"))
        click.echo(click.style("  uv pip install -e .", fg="yellow"))
        click.echo()
        raise click.exceptions.Exit(1)

    click.echo(click.style("\n🔍 Checking for updates...", fg="cyan"))
    click.echo(f"Current version: {VERSION}")

    channel = "prerelease (dev)" if prerelease else "stable"
    click.echo(f"Channel: {channel}")
    click.echo()

    try:
        update_info = check_for_updates(timeout=10, prerelease=prerelease)

        if not update_info:
            click.echo(
                click.style("✓ You are already running the latest version", fg="green")
            )
            click.echo()
            return

        new_version = update_info["version"]
        click.echo(
            click.style(f"Update available: {new_version}", fg="green", bold=True)
        )
        click.echo(f"Release URL: {update_info['url']}")
        click.echo()

        # Confirm installation unless --yes flag is set
        if not yes:
            if not click.confirm(f"Do you want to install version {new_version}?"):
                click.echo("Update cancelled.")
                return

        # Perform the update
        click.echo()
        download_and_install_update(update_info)

        click.echo()
        click.echo(
            click.style("Update complete! Please restart waqt.", fg="green", bold=True)
        )
        click.echo()

    except Exception as e:
        click.echo(click.style(f"\n❌ Error during update: {e}", fg="red"))
        raise click.exceptions.Exit(1)


@cli.command()
@click.option(
    "--port",
    "-p",
    type=int,
    default=5555,
    help="Port to run the web server on (default: 5555)",
)
@click.option(
    "--host",
    "-h",
    type=str,
    default="127.0.0.1",
    help="Host to bind the web server to (default: 127.0.0.1)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Run in debug mode (not recommended for production)",
)
def ui(port: int, host: str, debug: bool):
    """Start the web UI for interactive time tracking.

    Launches the Flask web application that provides a graphical interface
    for managing time entries, viewing reports, and configuring settings.

    Examples:
        waqt ui
        waqt ui --port 8080
        waqt ui --host 0.0.0.0 --port 8000
        waqt ui --debug
    """
    # Import Flask app factory only when needed (for 'ui' command)
    from . import create_app

    click.echo(
        click.style("\n🚀 Starting waqt web application...", fg="cyan", bold=True)
    )
    click.echo(f"Access the application at: http://{host}:{port}")
    click.echo("\nPress Ctrl+C to stop the server.")
    click.echo("-" * 50)
    click.echo()

    try:
        app = create_app()
        app.run(debug=debug, host=host, port=port)
    except Exception as e:
        click.echo(click.style(f"\n❌ Error starting application: {e}", fg="red"))
        click.echo("\nPlease check that:")
        click.echo(f"  - Port {port} is not already in use")
        click.echo("  - You have write permissions in the current directory")
        click.echo("  - All required dependencies are available")
        raise click.exceptions.Exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
