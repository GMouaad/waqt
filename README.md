# Time Tracker

A portable Python time tracking application for managing work hours, overtime, vacation days, sick leaves, and work activities.

## Project Overview

This is a self-contained Flask-based time tracking application with no external services required. All data is stored locally in SQLite, making it completely portable and easy to run anywhere.

## Documentation

- **[Installation Guide](docs/installation.md)** - Detailed installation instructions, prerequisites, and troubleshooting
- **[Usage Guide](docs/usage.md)** - Complete guide on how to use the application, workflows, and best practices

## Features

- **Work Hours Tracking**: Track daily work hours (8 hours/day, 40 hours/week standard)
- **Overtime Calculation**: Automatically calculate overtime hours
- **Vacation Days**: Track and manage vacation days
- **Sick Leaves**: Record sick leave days
- **Work Activities**: Log detailed work activities and tasks
- **Reports**: View weekly and monthly overtime summaries


## Technology Stack

- **Backend**: Flask (Python 3.8+)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript
- **Portable**: No external services required

## Installation

For detailed installation instructions including troubleshooting, see the **[Installation Guide](docs/installation.md)**.

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/GMouaad/time-tracker.git
cd time-tracker
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python init_db.py
```

5. Run the application:
```bash
python run.py
```

6. Open your browser and navigate to `http://localhost:5000`

**Alternative:** Use the quick start scripts:
- Linux/macOS: `./start.sh`
- Windows: `start.bat`

## Usage

For detailed usage instructions, workflows, and examples, see the **[Usage Guide](docs/usage.md)**.

### Quick Overview

### Track Work Hours
1. Navigate to the dashboard
2. Click "Add Time Entry"
3. Enter date, start time, end time, and description
4. The system automatically calculates overtime

### View Reports
- **Weekly Overview**: See total hours and overtime for each week
- **Monthly Overview**: View monthly summaries
- **Activity Log**: Browse all recorded activities

### Manage Leave
- Record vacation days with start/end dates
- Log sick leave days
- View remaining vacation balance

## Project Structure

```
time-tracker/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── models.py            # Database models
│   ├── routes.py            # Application routes
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS, images
├── docs/                    # Documentation
│   ├── installation.md      # Installation guide
│   └── usage.md            # Usage guide
├── tests/                   # Unit tests
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
└── README.md               # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.