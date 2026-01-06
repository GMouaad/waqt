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
    format_hours,
)


def get_app():
    """Create and return the Flask app instance."""
    app = create_app()
    return app


@click.group()
@click.version_option(version="0.1.0", prog_name="waqt")
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
    app = get_app()
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
                return
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
                return
        else:
            start_time = datetime.now().time()

        # Check if there's already an open entry for this date
        # Open entries have duration_hours == 0.0
        open_entries = TimeEntry.query.filter_by(
            date=entry_date, duration_hours=0.0
        ).all()

        if open_entries:
            click.echo(
                click.style(
                    f"Warning: There's already an open time entry for {entry_date}.",
                    fg="yellow",
                )
            )
            click.echo("Please run 'waqt end' first to close it.")
            return

        # Create a new entry with only start time (end_time will be None initially)
        # We'll store a placeholder value and update it on end
        # For now, we'll use start_time as end_time temporarily
        entry = TimeEntry(
            date=entry_date,
            start_time=start_time,
            end_time=start_time,  # Temporary placeholder
            duration_hours=0.0,  # Will be calculated on end
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
    app = get_app()
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
                return
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
                return
        else:
            end_time = datetime.now().time()

        # Find the most recent entry for today with duration 0
        # (our marker for open entries)
        open_entry = (
            TimeEntry.query.filter_by(date=entry_date)
            .filter_by(duration_hours=0.0)
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
            return

        # Calculate duration
        from .utils import calculate_duration

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
    app = get_app()
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
                return
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

        # Query leave days for the period
        leave_days = (
            LeaveDay.query.filter(LeaveDay.date >= start_date)
            .filter(LeaveDay.date <= end_date)
            .all()
        )

        # Calculate statistics
        if period.lower() == "week":
            stats = calculate_weekly_stats(entries)
        else:
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

                # Show leave days
                if leave_days:
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
def sum(period: str, date: Optional[str]):
    """Alias for 'summary' command."""
    ctx = click.get_current_context()
    ctx.invoke(summary, period=period, date=date)


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


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
