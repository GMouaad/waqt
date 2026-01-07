# Usage Guide

This guide explains how to use the Waqt application to manage your work hours, overtime, and leave days.

## Table of Contents

1. [Running the Application](#running-the-application)
2. [Dashboard Overview](#dashboard-overview)
3. [Tracking Work Hours](#tracking-work-hours)
4. [Managing Leave Days](#managing-leave-days)
5. [Viewing Reports](#viewing-reports)
6. [Understanding Overtime Calculations](#understanding-overtime-calculations)
7. [Common Workflows](#common-workflows)
8. [Tips and Best Practices](#tips-and-best-practices)

## Running the Application

### Starting the Server

If you haven't installed the application yet, see the [Installation Guide](installation.md).

**Using the quick start script:**

Linux/macOS:
```bash
./start.sh
```

Windows:
```bash
start.bat
```

**Manual start:**

1. Activate virtual environment:
   - Linux/macOS: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`

2. Run the application:
   ```bash
   python -m waqtracker.wsgi
   ```

3. Open your browser to `http://localhost:5555`

### Stopping the Server

Press `Ctrl+C` in the terminal where the application is running.

## Dashboard Timer

The dashboard now features a one-click timer for seamless time tracking.

### Starting the Timer
1. On the Dashboard, click **"▶ Start Timer"**.
2. The timer will begin counting up immediately.
3. The status indicator will pulse green to show tracking is active.
4. By default, the entry description is set to "Work".

### Pausing and Resuming
- **Pause**: Click **"⏸ Pause"** if you need to take a break. This stops the current entry in the database and updates the status indicator to orange.
- **Resume**: Click **"▶ Resume"** to start a new entry. The timer will continue from where it left off visually (by starting a new session).

### Stopping the Timer
- Click **"■ Stop"** when you are finished with your work session.
- The entry will be saved to the database.
- The dashboard will automatically refresh to show your new entry in the "Recent Time Entries" table.

## Dashboard Overview

The dashboard is your home page and shows:

- **Timer Control Panel**: Quick-start and manage your current work session.
- **Current Week Stats**: 
  - Total hours worked this week
  - Overtime hours accumulated
  - Standard hours target (40 hours/week)

- **Recent Entries**: 
  - Last 10 time entries
  - Quick view of recent work activities

- **Quick Actions**:
  - Add Time Entry
  - View Reports
  - Manage Leave

### Navigation Menu

- **Dashboard**: Overview and recent activity
- **Time Entry**: Log work hours manually
- **Leave**: Manage vacation and sick days
- **Reports**: View weekly and monthly summaries

## Tracking Work Hours

### Using the Timer (Recommended)
The easiest way to track time is using the **Dashboard Timer**. It automatically records your start and end times with a single click.

### Adding a Time Entry Manually
1. Click **"Add Time Entry"** from the dashboard or navigation menu
...
## Common Workflows

### Daily Routine

**Start of Workday:**
1. Open Waqt dashboard.
2. Click **"▶ Start Timer"**.

**During the Day:**
1. Use **"⏸ Pause"** and **"▶ Resume"** for breaks.

**End of Workday:**
1. Click **"■ Stop"**.
2. Verify the entries in the "Recent Time Entries" table.
3. Check dashboard to see weekly progress.

### Weekly Review

**Friday Afternoon or Monday Morning:**
1. Navigate to Reports → Weekly Overview
2. Review total hours and overtime
3. Verify all days are logged
4. Add any missing entries

### Monthly Review

**End of Month:**
1. Go to Reports → Monthly Overview
2. Review total hours and overtime for the month
3. Check leave days taken
4. Compare with expected work hours
5. Plan upcoming vacation days

### Leave Planning

**Before Taking Time Off:**
1. Go to Leave section
2. Record vacation days in advance
3. Check remaining vacation balance
4. Ensure no conflicts with work entries

### Project Time Tracking

**Tracking Multiple Projects:**
1. Use clear project names in descriptions
2. Example: "[Project Alpha] Implemented user authentication"
3. Filter activity log by project name
4. Calculate project-specific hours manually or use reports

## Tips and Best Practices

### Consistency

- **Log daily**: Don't wait until the end of the week
- **Use templates**: Keep common descriptions in a note for copy-paste
- **Set reminders**: Add a daily reminder to log time

### Description Guidelines

Good descriptions include:
- Project or task name
- Specific activity
- Ticket/issue numbers if applicable

**Good examples:**
- "Project X - Fixed login bug (#145)"
- "Client meeting - Q1 planning"
- "Code review for pull request #89"

**Poor examples:**
- "Work"
- "Coding"
- "Meeting"

### Accuracy

- **Round appropriately**: Round to nearest 15 or 30 minutes
- **Include setup time**: Count environment setup, meetings, etc.
- **Track breaks**: Note if your times include lunch breaks
- **Be honest**: Accurate tracking helps with planning

### Data Management

- **Backup regularly**: Copy `time_tracker.db` to a safe location
- **Version control**: Keep backups when making changes
- **Export data**: Periodically export reports for records

### Timezone Considerations

- The application uses your local system time
- Be consistent with timezone when traveling
- Note timezone in descriptions if working across zones

### Performance

- Database stays fast even with thousands of entries
- Archive old entries annually if needed (manual process)
- Regular SQLite maintenance helps (vacuum command)

## Advanced Usage

### Custom Reports

While the application provides standard reports, you can:
1. Access `time_tracker.db` with SQLite tools
2. Write custom SQL queries for specific insights
3. Export data to CSV for analysis in Excel/spreadsheets

### Database Queries (Advanced)

Example queries using `sqlite3` command-line tool:

```bash
# Open database
sqlite3 time_tracker.db

# Get all entries for a specific project
SELECT date, duration_hours, description 
FROM time_entries 
WHERE description LIKE '%Project X%';

# Calculate overtime by month
SELECT strftime('%Y-%m', date) as month, 
       SUM(duration_hours) as total_hours,
       SUM(duration_hours) - (COUNT(DISTINCT date) * 8) as overtime
FROM time_entries
GROUP BY month;
```

### Automation

You can automate time entry creation with scripts:

```python
from waqtracker import create_app, db
from waqtracker.models import TimeEntry
from datetime import datetime, time
```

## Troubleshooting

### Time Entry Issues

**Problem**: Can't add time entry

**Solutions**:
- Check date format is valid
- Ensure end time is after start time
- Verify description isn't too long
- Check database isn't locked

### Report Not Updating

**Problem**: Reports show old data

**Solutions**:
- Refresh the page (Ctrl+F5)
- Restart the application
- Check entries are saved (view dashboard)
- Clear browser cache

### Data Recovery

**Problem**: Accidentally closed without saving

**Solution**:
- Unfortunately, unsaved time entries are lost
- Get in the habit of clicking Save immediately
- Consider the autosave feature (future enhancement)

## Getting Help

If you need assistance:

1. Check this usage guide thoroughly
2. Review the [Installation Guide](installation.md) for setup issues
3. See the project [Home Page](index.md) for quick reference
4. Open an issue on GitHub: https://github.com/GMouaad/waqt/issues

## What's Next?

- Explore all features systematically
- Develop a daily routine for time tracking
- Review reports regularly for insights
- Customize descriptions to match your workflow
- Back up your data regularly

Happy time tracking! 📊⏰
