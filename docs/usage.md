# Usage Guide

This guide explains how to use the Time Tracker application to manage your work hours, overtime, and leave days.

## Running the Application

### Starting the Server

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

## Dashboard Overview

The dashboard is your home page and shows:

- **Current Week Stats**: Total hours worked this week, overtime hours accumulated
- **Recent Entries**: Last 10 time entries
- **Quick Actions**: Add Time Entry, View Reports, Manage Leave

## Tracking Work Hours

### Adding a Time Entry

1. Click **"Add Time Entry"** from the dashboard or navigation menu
2. Fill in the form:
   - **Date**: The date you worked (defaults to today)
   - **Start Time**: When you started work (e.g., 09:00)
   - **End Time**: When you finished work (e.g., 17:30)
   - **Description**: What you worked on
3. Click **"Save Entry"**

The system automatically calculates:
- Duration in hours
- Daily overtime (hours beyond 8)
- Weekly overtime (hours beyond 40 for the week)

## Managing Leave Days

### Recording Vacation Days

1. Navigate to **"Leave"** in the menu
2. Select the leave type: **Vacation**
3. Enter start date, end date, and optional description
4. Click **"Submit"**

### Recording Sick Leave

1. Navigate to **"Leave"** in the menu
2. Select the leave type: **Sick Leave**
3. Enter the date and optional description
4. Click **"Submit"**

## Viewing Reports

### Weekly Reports

1. Go to **"Reports"** → **"Weekly Overview"**
2. View statistics: Total hours worked, overtime hours, daily breakdown
3. Navigate between weeks using date selectors

### Monthly Reports

1. Go to **"Reports"** → **"Monthly Overview"**
2. View aggregated data: Total hours, total overtime, days worked, weekly breakdown

## Understanding Overtime Calculations

### Standard Work Schedule

- **Standard Day**: 8 hours
- **Standard Week**: 40 hours (Monday-Friday)

### Daily Overtime

```
Daily Overtime = Total Hours - 8 hours
```

### Weekly Overtime

```
Weekly Overtime = Total Weekly Hours - 40 hours
```

## Tips and Best Practices

- **Log daily**: Don't wait until the end of the week
- **Be specific**: Use clear descriptions for activities
- **Review weekly**: Check your hours every Friday
- **Backup regularly**: Copy `time_tracker.db` to a safe location

For more detailed information and advanced usage, see the project documentation.
