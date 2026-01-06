# Usage Guide

This guide explains how to use the Time Tracker application to manage your work hours, overtime, and leave days.

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
   python run.py
   ```

3. Open your browser to `http://localhost:5000`

### Stopping the Server

Press `Ctrl+C` in the terminal where the application is running.

## Dashboard Overview

The dashboard is your home page and shows:

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
- **Time Entry**: Log work hours
- **Leave**: Manage vacation and sick days
- **Reports**: View weekly and monthly summaries

## Tracking Work Hours

### Adding a Time Entry

1. Click **"Add Time Entry"** from the dashboard or navigation menu

2. Fill in the form:
   - **Date**: The date you worked (defaults to today)
   - **Start Time**: When you started work (e.g., 09:00)
   - **End Time**: When you finished work (e.g., 17:30)
   - **Description**: What you worked on (e.g., "Developed login feature")

3. Click **"Save Entry"**

The system automatically calculates:
- Duration in hours
- Daily overtime (hours beyond 8)
- Weekly overtime (hours beyond 40 for the week)

### Example Time Entry

```
Date: 2026-01-06
Start Time: 09:00
End Time: 18:00
Description: Fixed bug #123 and updated documentation

Result: 9 hours total, 1 hour overtime
```

### Editing Time Entries

Currently, entries are permanent once saved. To correct an entry:
1. Note the incorrect entry details
2. Add a correcting entry with negative hours if needed
3. Or manually edit the database file `time_tracker.db` (advanced users)

### Best Practices for Time Entries

- **Be Specific**: Use clear descriptions (e.g., "Client meeting - Project X" not just "Meeting")
- **Log Daily**: Enter time at the end of each workday while it's fresh
- **Include Breaks**: If you track breaks separately, note them in the description
- **Multiple Entries**: You can add multiple entries per day for different activities

## Managing Leave Days

### Recording Vacation Days

1. Navigate to **"Leave"** in the menu

2. Select the leave type: **Vacation**

3. Enter:
   - **Start Date**: First day of vacation
   - **End Date**: Last day of vacation
   - **Description**: Optional notes (e.g., "Summer vacation")

4. Click **"Submit"**

### Recording Sick Leave

1. Navigate to **"Leave"** in the menu

2. Select the leave type: **Sick Leave**

3. Enter:
   - **Date**: The sick day
   - **Description**: Optional notes (e.g., "Doctor's appointment")

4. Click **"Submit"**

### Viewing Leave History

The Leave page shows:
- All recorded vacation days
- All sick leave days
- Total days for each type
- Calendar view of leave (if implemented)

### Leave Day Examples

**Single Vacation Day:**
```
Type: Vacation
Start Date: 2026-01-15
End Date: 2026-01-15
Description: Personal day
```

**Week-Long Vacation:**
```
Type: Vacation
Start Date: 2026-07-01
End Date: 2026-07-05
Description: Summer holiday
```

## Viewing Reports

### Weekly Reports

1. Go to **"Reports"** → **"Weekly Overview"**

2. View statistics:
   - Total hours worked
   - Standard hours target (40)
   - Overtime hours
   - Daily breakdown
   - Average hours per day

3. Navigate between weeks using date selectors

### Monthly Reports

1. Go to **"Reports"** → **"Monthly Overview"**

2. View aggregated data:
   - Total hours for the month
   - Total overtime
   - Days worked
   - Average hours per day
   - Week-by-week breakdown

### Activity Log

View all time entries with filtering options:
- Filter by date range
- Filter by description keywords
- Sort by date or duration
- Export options (if implemented)

## Understanding Overtime Calculations

### Standard Work Schedule

The Time Tracker uses these defaults:
- **Standard Day**: 8 hours
- **Standard Week**: 40 hours (Monday-Friday)

### Daily Overtime

Overtime is calculated for each day:
```
Daily Overtime = Total Hours - 8 hours
```

**Example:**
- Work 9.5 hours → 1.5 hours overtime
- Work 7 hours → 0 hours overtime (no negative overtime)

### Weekly Overtime

Weekly overtime considers the full week:
```
Weekly Overtime = Total Weekly Hours - 40 hours
```

**Example Week:**
```
Monday:    8 hours
Tuesday:   9 hours
Wednesday: 8 hours
Thursday:  10 hours
Friday:    7 hours
-----------------------
Total:     42 hours
Overtime:  2 hours
```

### Overtime Tracking

- Overtime accumulates and is displayed in reports
- Daily and weekly overtime are tracked separately
- Use reports to see overtime trends over time

## Common Workflows

### Daily Routine

**End of Workday:**
1. Open Time Tracker
2. Click "Add Time Entry"
3. Enter today's date, start/end times, and description
4. Save entry
5. Check dashboard to see weekly progress

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
from app import create_app, db
from app.models import TimeEntry
from datetime import datetime, time

app = create_app()
with app.app_context():
    entry = TimeEntry(
        date=datetime.now().date(),
        start_time=time(9, 0),
        end_time=time(17, 0),
        duration_hours=8.0,
        description="Automated entry"
    )
    db.session.add(entry)
    db.session.commit()
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
3. See the project [README](../README.md) for quick reference
4. Open an issue on GitHub: https://github.com/GMouaad/time-tracker/issues

## What's Next?

- Explore all features systematically
- Develop a daily routine for time tracking
- Review reports regularly for insights
- Customize descriptions to match your workflow
- Back up your data regularly

Happy time tracking! 📊⏰
