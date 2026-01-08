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
2. Fill in the required fields:
   - **Date**: Select the date for this entry
   - **Start Time**: When you started working (e.g., 09:00)
   - **End Time**: When you finished working (e.g., 17:00)
   - **Description**: What you worked on
3. Click **"Save Entry"**
4. The entry will appear in your recent entries list

**Note**: The system enforces one entry per day. If you try to add another entry for a date that already has one, you'll receive an error message asking you to edit the existing entry instead.

### Editing a Time Entry

You can edit any completed time entry to correct mistakes or update information.

**Via UI:**
1. Go to the **Dashboard** or **Reports** page
2. Find the entry you want to edit in the table
3. Click the blue **"Edit"** button next to the entry
4. Update any of the following fields:
   - **Start Time**: Adjust the start time
   - **End Time**: Adjust the end time
   - **Description**: Update what you worked on
5. Click **"Update Entry"**
6. The duration will be automatically recalculated

**Via CLI:**
```bash
# Edit only the description
waqt edit-entry --date 2026-01-08 --desc "Updated work description"

# Edit times
waqt edit-entry --date 2026-01-08 --start 08:30 --end 17:30

# Edit all fields at once
waqt edit-entry -d 2026-01-08 -s 08:00 -e 18:00 --desc "Full day development work"
```

**Important Notes:**
- You cannot edit an active timer. Stop the timer first using the **"Stop"** button or `waqt end` command
- The date field cannot be changed. If you need to move an entry to a different date, delete it and create a new one
- Duration is automatically recalculated when you change start or end times
- For legacy cases where multiple entries exist for one day, the CLI will prompt you to specify which entry to edit using the `--start` parameter for selection

**Command Options:**
- `--date` or `-d`: Date of the entry to edit (YYYY-MM-DD format, **required**)
- `--start` or `-s`: New start time (HH:MM format)
- `--end` or `-e`: New end time (HH:MM format)
- `--description` or `--desc`: New description text
- At least one field (start, end, or description) must be provided

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

## Configuration

The application supports various configuration options to customize its behavior. All settings are stored in the database and can be managed using the CLI.

### Viewing Configuration

To see all available configuration options:

```bash
waqt config list
```

To view a specific setting:

```bash
waqt config get <setting_name>
```

### Available Settings

#### Standard Work Hours
- **`standard_hours_per_day`**: Number of hours considered standard work per day (default: 8)
- **`weekly_hours`**: Expected weekly working hours (default: 40)

#### Timer Settings
- **`pause_duration_minutes`**: Default pause/break duration in minutes (default: 45)
- **`auto_end`**: Feature flag to auto-end work session after 8h 45m (default: false)

#### Session Alert Settings
- **`alert_on_max_work_session`**: Enable alerts when work sessions exceed 8 hours and approach the maximum limit (default: false)
- **`max_work_session_hours`**: Maximum work session hours threshold for alerts (default: 10)

### Modifying Settings

To change a setting:

```bash
waqt config set <setting_name> <value>
```

Examples:

```bash
# Enable session alerts
waqt config set alert_on_max_work_session true

# Set maximum session threshold to 12 hours
waqt config set max_work_session_hours 12

# Change weekly hours target
waqt config set weekly_hours 35
```

### Resetting Settings

To reset a setting to its default value:

```bash
waqt config reset <setting_name>
```

### Session Alert Feature

The session alert feature helps prevent excessive work sessions by showing a warning banner in the UI when:
1. The feature is enabled (`alert_on_max_work_session` is `true`)
2. An active timer has been running for more than 8 hours
3. The session is approaching the configured maximum threshold

**How it works:**
- The alert appears automatically in the dashboard when conditions are met
- It shows current session hours and the maximum recommended threshold
- Users can dismiss the alert, but it will reappear on the next check (every 60 seconds)
- The alert only shows when the UI is open and a session is actively running
- Pausing the timer hides the alert

**Use case:** In some countries, labor laws prohibit working more than 10 hours in a single session. This feature helps users stay compliant by providing timely reminders.

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
3. See the project [README](../README.md) for quick reference
4. Open an issue on GitHub: https://github.com/GMouaad/waqt/issues

## What's Next?

- Explore all features systematically
- Develop a daily routine for time tracking
- Review reports regularly for insights
- Customize descriptions to match your workflow
- Back up your data regularly

Happy time tracking! 📊⏰
