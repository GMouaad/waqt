"""CLI interface for waqtracker time tracking application."""

import click
from datetime import datetime
from typing import Optional
from . import create_app, db
from .models import TimeEntry, LeaveDay, Settings
from .utils import (
    get_week_bounds,
    get_month_bounds,
    calculate_weekly_stats,
    calculate_monthly_stats,
    calculate_duration,
    format_hours,
    export_time_entries_to_csv,
    get_time_entries_for_period,
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


@click.group()
@click.version_option(version=VERSION, prog_name="waqt")
def cli():
    """Waqt - Time tracking CLI for waqtracker application.

    A command-line interface for tracking work hours, managing time entries,
    and generating reports.
    """
    pass


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
    app = create_app()
    with app.app_context():
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

        # Check if there's already an open entry for this date
        # Open entries are identified by is_active=True
        open_entries = TimeEntry.query.filter_by(date=entry_date, is_active=True).all()

        if open_entries:
            click.echo(
                click.style(
                    f"Error: There's already an open time entry for {entry_date}.",
                    fg="red",
                )
            )
            click.echo("Please run 'waqt end' first to close it.")
            raise click.exceptions.Exit(1)

        # Create a new entry with start time
        # end_time is set to start_time as a temporary marker for open entries
        # duration_hours is 0.0 to indicate this entry is not yet complete
        # The 'waqt end' command will update these values
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

        click.echo(click.style("✓ Time tracking started!", fg="green", bold=True))
        click.echo(f"Date: {entry_date}")
        click.echo(f"Start time: {start_time.strftime('%H:%M')}")
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
    app = create_app()
    with app.app_context():
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

        # Find the most recent entry for this date that is still open
        # Open entries have is_active=True
        open_entry = (
            TimeEntry.query.filter_by(date=entry_date, is_active=True)
            .order_by(TimeEntry.created_at.desc())
            .first()
        )

        if not open_entry:
            click.echo(
                click.style(
                    f"Error: No open time entry found for {entry_date}.", fg="red"
                )
            )
            click.echo("Run 'waqt start' first to begin tracking time.")
            raise click.exceptions.Exit(1)

        # Calculate duration
        duration = calculate_duration(open_entry.start_time, end_time)

        # Update the entry
        open_entry.end_time = end_time
        open_entry.duration_hours = duration
        open_entry.is_active = False
        db.session.commit()

        click.echo(click.style("✓ Time tracking ended!", fg="green", bold=True))
        click.echo(f"Date: {entry_date}")
        click.echo(f"Start time: {open_entry.start_time.strftime('%H:%M')}")
        click.echo(f"End time: {end_time.strftime('%H:%M')}")
        click.echo(f"Duration: {format_hours(duration)}")
        click.echo(f"Description: {open_entry.description}")


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
    app = create_app()
    with app.app_context():
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
            TimeEntry.query.filter_by(date=entry_date, is_active=False)
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
            for idx, entry in enumerate(entries, 1):
                click.echo(
                    f"  {idx}. {entry.start_time.strftime('%H:%M')}-"
                    f"{entry.end_time.strftime('%H:%M')} "
                    f"({format_hours(entry.duration_hours)}) - {entry.description[:50]}"
                )
            click.echo()
            click.echo(
                "Note: The system now enforces one entry per day. "
                "Please delete the extra entries manually."
            )
            click.echo(
                "You can use the UI to delete entries, or specify --start to select."
            )

            # If start time provided, try to match it
            if start:
                try:
                    start_time = datetime.strptime(start, "%H:%M").time()
                    matching = [e for e in entries if e.start_time == start_time]
                    if len(matching) == 1:
                        entry = matching[0]
                        click.echo(
                            f"\nMatching entry by start time: "
                            f"{entry.start_time.strftime('%H:%M')}"
                        )
                    else:
                        click.echo(
                            click.style(
                                f"Error: Could not uniquely identify entry by start time.",
                                fg="red",
                            )
                        )
                        raise click.exceptions.Exit(1)
                except ValueError:
                    click.echo(
                        click.style(
                            f"Error: Invalid time format '{start}'. Use HH:MM.",
                            fg="red",
                        )
                    )
                    raise click.exceptions.Exit(1)
            else:
                raise click.exceptions.Exit(1)
        else:
            entry = entries[0]

        # Store original values for display
        original_start = entry.start_time
        original_end = entry.end_time
        original_description = entry.description

        # Parse and update start time if provided
        if start:
            try:
                entry.start_time = datetime.strptime(start, "%H:%M").time()
            except ValueError:
                click.echo(
                    click.style(
                        f"Error: Invalid time format '{start}'. Use HH:MM.",
                        fg="red",
                    )
                )
                raise click.exceptions.Exit(1)

        # Parse and update end time if provided
        if end:
            try:
                entry.end_time = datetime.strptime(end, "%H:%M").time()
            except ValueError:
                click.echo(
                    click.style(
                        f"Error: Invalid time format '{end}'. Use HH:MM.", fg="red"
                    )
                )
                raise click.exceptions.Exit(1)

        # Update description if provided
        if description:
            entry.description = description.strip()
            if not entry.description:
                click.echo(click.style("Error: Description cannot be empty.", fg="red"))
                raise click.exceptions.Exit(1)

        # Recalculate duration if times were changed
        if start or end:
            duration = calculate_duration(entry.start_time, entry.end_time)
            if duration <= 0:
                click.echo(
                    click.style("Error: End time must be after start time.", fg="red")
                )
                raise click.exceptions.Exit(1)
            entry.duration_hours = duration

        # Commit changes
        db.session.commit()

        # Display success message
        click.echo(
            click.style("✓ Time entry updated successfully!", fg="green", bold=True)
        )
        click.echo(f"Date: {entry_date}")

        if start:
            click.echo(
                f"Start time: {original_start.strftime('%H:%M')} → "
                f"{entry.start_time.strftime('%H:%M')}"
            )
        if end:
            click.echo(
                f"End time: {original_end.strftime('%H:%M')} → "
                f"{entry.end_time.strftime('%H:%M')}"
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
    app = create_app()
    with app.app_context():
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
            TimeEntry.query.filter(TimeEntry.date >= start_date)
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
                LeaveDay.query.filter(LeaveDay.date >= start_date)
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
                    f"{entry.date} | {entry.start_time.strftime('%H:%M')}-"
                    f"{entry.end_time.strftime('%H:%M')} | "
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
    help="Output file path (default: time_entries_<period>_<date>.csv)",
)
@click.option(
    "--format",
    "-f",
    "export_format",
    type=click.Choice(["csv"], case_sensitive=False),
    default="csv",
    help="Export format (default: csv)",
)
def export(period: str, date: Optional[str], output: Optional[str], export_format: str):
    """Export time entries to CSV file.

    Export your time tracking data to a CSV file for use in spreadsheet
    applications like Excel or Google Sheets. You can export by week, month,
    or all entries.

    Examples:
        waqt export
        waqt export --period week
        waqt export --period month --date 2024-01-15
        waqt export --output my_time_entries.csv
        waqt export -p week -o weekly_report.csv
    """
    app = create_app()
    with app.app_context():
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

        # Query entries using utility function
        entries = get_time_entries_for_period(start_date, end_date)

        if not entries:
            click.echo(click.style("No time entries found to export.", fg="yellow"))
            raise click.exceptions.Exit(0)

        # Generate CSV content
        csv_content = export_time_entries_to_csv(entries, start_date, end_date)

        # Determine output filename
        if output:
            output_file = output
        else:
            timestamp = datetime.now().strftime("%Y%m%d")
            output_file = f"time_entries_{period_name}_{timestamp}.csv"

        # Write to file
        try:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                f.write(csv_content)

            click.echo(click.style("✓ Export successful!", fg="green", bold=True))
            click.echo(f"File: {output_file}")
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
    app = create_app()
    with app.app_context():
        all_settings = Settings.get_all_settings()

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
    app = create_app()
    with app.app_context():
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

        value = Settings.get_setting(key, CONFIG_DEFAULTS[key])
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
    app = create_app()
    with app.app_context():
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
        old_value = Settings.get_setting(key, CONFIG_DEFAULTS[key])

        # Set the new value
        Settings.set_setting(key, value)

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
    app = create_app()
    with app.app_context():
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
        old_value = Settings.get_setting(key, default_value)

        # Set to default value
        Settings.set_setting(key, default_value)

        click.echo(
            click.style("✓ Configuration reset to default!", fg="green", bold=True)
        )
        click.echo(f"Key: {key}")
        click.echo(f"Old value: {old_value}")
        click.echo(f"Default value: {default_value}")
        click.echo()


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


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
