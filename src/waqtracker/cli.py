"""CLI interface for waqtracker time tracking application."""

import click
from datetime import datetime
from typing import Optional
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
)
from ._version import VERSION


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

        # Check if there's already an open entry for this date
        # Open entries are identified by:
        # - duration_hours == 0.0 and end_time == start_time
        # This is a marker for entries waiting to be closed with 'waqt end'
        open_entries = (
            TimeEntry.query.filter_by(date=entry_date, duration_hours=0.0)
            .filter(TimeEntry.end_time == TimeEntry.start_time)
            .all()
        )

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
        # Open entries have: duration_hours == 0.0 AND end_time == start_time
        open_entry = (
            TimeEntry.query.filter_by(date=entry_date, duration_hours=0.0)
            .filter(TimeEntry.end_time == TimeEntry.start_time)
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
        db.session.commit()

        click.echo(click.style("✓ Time tracking ended!", fg="green", bold=True))
        click.echo(f"Date: {entry_date}")
        click.echo(f"Start time: {open_entry.start_time.strftime('%H:%M')}")
        click.echo(f"End time: {end_time.strftime('%H:%M')}")
        click.echo(f"Duration: {format_hours(duration)}")
        click.echo(f"Description: {open_entry.description}")


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
    type=click.Choice(["csv"], case_sensitive=False),
    default="csv",
    help="Export format (default: csv)",
)
def export(period: str, date: Optional[str], output: Optional[str], format: str):
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
            click.echo(
                click.style("No time entries found to export.", fg="yellow")
            )
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
            click.echo(
                click.style(f"Error writing to file: {str(e)}", fg="red")
            )
            raise click.exceptions.Exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
