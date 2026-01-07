# Copilot Instructions for Waqt App

## Project Overview
This repository contains a portable Python time tracking application built with Flask and SQLite. The app helps users track work hours, overtime, vacation days, sick leaves, and work activities without requiring any external services.

## Repository Purpose and Context

### Primary Goals
- **Time Tracking**: Enable users to log daily work hours and activities
- **Overtime Management**: Automatically calculate and track overtime hours
- **Leave Management**: Track vacation days and sick leaves
- **Reporting**: Provide weekly and monthly summaries of work hours
- **Portability**: Single-file SQLite database, no external dependencies

### Architecture Philosophy
- **Simple and Portable**: Self-contained Flask application
- **No External Services**: All data stored locally in SQLite
- **User-Friendly**: Clean, intuitive web interface
- **Standards-Based**: 8 hours/day, 40 hours/week work schedule


## Application Structure

### Directory Layout
```
waqt/
├── src/
│   └── waqtracker/          # Main application package
│       ├── __init__.py      # Flask app factory
│       ├── models.py        # SQLAlchemy models
│       ├── routes.py        # Route handlers
│       ├── wsgi.py          # WSGI entry point
│       ├── scripts/         # Utility scripts (init_db, etc.)
│       ├── utils.py         # Helper functions
│       ├── templates/       # Jinja2 HTML templates
│       │   ├── base.html
│       │   ├── dashboard.html
│       │   ├── time_entry.html
│       │   ├── reports.html
│       │   └── leave.html
│       └── static/          # CSS, JS, images
│           ├── css/
│           └── js/
├── migrations/              # Database migration scripts
├── tests/                   # Unit and integration tests
├── pyproject.toml           # Project dependencies
```

## Technology Stack

### Core Technologies
- **Python 3.8+**: Primary programming language
- **Flask**: Lightweight web framework
- **SQLite3**: Embedded database
- **SQLAlchemy**: ORM for database operations
- **Jinja2**: Template engine (included with Flask)
- **HTML/CSS/JavaScript**: Frontend interface

### Key Libraries
- `Flask`: Web framework
- `Flask-SQLAlchemy`: Database ORM
- `python-dateutil`: Date/time handling
- `pytest`: Testing framework (development)

## Database Schema

### Tables

#### time_entries
- `id`: Primary key
- `date`: Date of work
- `start_time`: Work start time
- `end_time`: Work end time
- `duration_hours`: Calculated duration
- `accumulated_pause_seconds`: Total pause duration in seconds
- `last_pause_start_time`: Timestamp when current pause started
- `is_active`: Boolean flag for active timer status
- `description`: Activity description
- `created_at`: Timestamp

#### leave_days
- `id`: Primary key
- `date`: Date of leave
- `leave_type`: 'vacation' or 'sick'
- `description`: Optional notes
- `created_at`: Timestamp

#### settings
- `id`: Primary key
- `key`: Setting name
- `value`: Setting value
- Example: `standard_hours_per_day`: 8, `standard_hours_per_week`: 40

## Key Features and Business Logic

### Work Hours Tracking
- Standard work day: 8 hours
- Standard work week: 40 hours (Monday-Friday)
- Overtime: Any hours over 8 in a day or 40 in a week
- Track multiple time entries per day
- **Pause/Resume**: Pause active timers and resume them later, excluding break time from duration

### Overtime Calculation
- Daily overtime: Hours beyond 8 per day
- Weekly overtime: Hours beyond 40 per week
- Display in weekly and monthly reports

### Leave Management
- Vacation days: Track with dates and descriptions
- Sick leaves: Separate tracking from vacation
- Calendar view of all leave days

### Reporting
- Weekly summary: Total hours, overtime, leave days
- Monthly summary: Aggregated statistics
- Activity log: Detailed list of all entries

## Code Style Guidelines

### Python Conventions
- Follow PEP 8 style guide
- Use type hints where appropriate
- Docstrings for all functions and classes
- Maximum line length: 88 characters (Black formatter)

### Flask Best Practices
- Use blueprints for route organization
- Environment-based configuration
- Proper error handling with try-except
- Use Flask's context managers

### Database Operations
- Use SQLAlchemy ORM, avoid raw SQL
- Proper session management
- Commit transactions explicitly
- Handle database errors gracefully

### Frontend
- Semantic HTML5
- Responsive CSS (mobile-friendly)
- Progressive enhancement (works without JS)
- Clean, minimal design

## Development Workflow

### Setting Up Development Environment
1. Create virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -e .`
4. Initialize database: `python -m waqtracker.scripts.init_db`
5. Run app: `python -m waqtracker.wsgi`

### Running Tests
```bash
pytest tests/
pytest tests/ -v  # Verbose output
pytest tests/ --cov=app  # With coverage
```

### Code Quality
- Use `black` for code formatting
- Use `flake8` for linting
- Use `mypy` for type checking (optional)

## When Contributing to This Repository

### Adding New Features
1. **Database Changes**: Update models.py and create migration if needed
2. **Route Handlers**: Add routes in routes.py with proper error handling
3. **Templates**: Create/update HTML templates with consistent styling
4. **Business Logic**: Add helper functions in utils.py
5. **Tests**: Add tests for new functionality

### Code Review Checklist
- [ ] Code follows PEP 8 style guide
- [ ] Functions have docstrings
- [ ] Error handling is implemented
- [ ] Database operations are properly managed
- [ ] Templates are mobile-responsive
- [ ] Tests cover new functionality
- [ ] No hardcoded values (use configuration)

### Security Considerations
- Input validation on all forms
- SQL injection prevention (use ORM)
- XSS prevention (Jinja2 auto-escaping)
- CSRF protection for forms
- Secure session configuration

## Common Tasks

### Adding a New Route
```python
@app.route('/new-feature')
def new_feature():
    # Logic here
    return render_template('new_feature.html')
```

### Database Query Example
```python
from src.waqtracker.models import TimeEntry
from datetime import datetime

# Get all entries for a date
entries = TimeEntry.query.filter_by(
    date=datetime.now().date()
).all()
```

### Calculating Overtime
```python
def calculate_overtime(total_hours, standard_hours=8):
    """Calculate overtime hours."""
    return max(0, total_hours - standard_hours)
```

## Testing Strategy

### Unit Tests
- Test models and business logic
- Test utility functions
- Mock database operations

### Integration Tests
- Test routes and views
- Test database operations
- Test form submissions

### Coverage Goals
- Aim for 80%+ code coverage
- Focus on critical business logic
- Test edge cases and error conditions

## Helpful Patterns

### When working on time tracking features:
- Always validate date/time inputs
- Handle timezone considerations
- Calculate durations accurately
- Consider edge cases (midnight crossing, etc.)

### When working on reports:
- Aggregate data efficiently
- Cache expensive calculations
- Paginate large result sets
- Format numbers consistently

### When working on the UI:
- Keep it simple and intuitive
- Provide clear feedback on actions
- Show validation errors clearly
- Make forms easy to use

This repository is focused on providing a simple, portable, and effective time tracking solution. Contributors should maintain code quality, ensure thorough testing, and keep the user experience smooth and intuitive.