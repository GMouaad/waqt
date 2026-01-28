# Copilot Instructions for Waqt App

## Project Overview
This repository contains a portable Python time tracking application with **three interfaces**: Flask web UI, CLI, and MCP (Model Context Protocol) server. The app helps users track work hours, overtime, vacation days, sick leaves, and work activities without requiring any external services.

## Repository Purpose and Context

### Primary Goals
- **Time Tracking**: Enable users to log daily work hours and activities
- **Overtime Management**: Automatically calculate and track overtime hours
- **Leave Management**: Track vacation days and sick leaves with multi-day support
- **Category Management**: Organize time entries by customizable categories
- **Reporting**: Provide weekly and monthly summaries with export capabilities
- **Portability**: Single-file SQLite database, no external dependencies

### Architecture Philosophy
- **Multi-Interface**: CLI, Web UI, and MCP server share the same core logic
- **Simple and Portable**: Self-contained application with local SQLite storage
- **Decoupled Database Layer**: Standalone SQLAlchemy works with Flask and CLI contexts
- **Self-Updating**: Frozen executables can auto-update from GitHub releases
- **Standards-Based**: 8 hours/day, 40 hours/week configurable work schedule


## Application Structure

### Directory Layout
```
waqt/
├── src/
│   └── waqt/                # Main application package
│       ├── __init__.py      # Flask app factory
│       ├── __main__.py      # Module entry point
│       ├── _version.py      # Version and repo info
│       ├── cli.py           # Click-based CLI interface
│       ├── config.py        # Configuration management
│       ├── database.py      # Standalone SQLAlchemy setup
│       ├── logging.py       # App and CLI logging utilities
│       ├── mcp_server.py    # MCP server implementation
│       ├── models.py        # SQLAlchemy models
│       ├── routes.py        # Flask route handlers
│       ├── services.py      # Business logic layer
│       ├── updater.py       # Self-update functionality
│       ├── utils.py         # Helper functions
│       ├── wsgi.py          # WSGI entry point
│       ├── scripts/         # Utility scripts (init_db, etc.)
│       ├── templates/       # Jinja2 HTML templates
│       │   ├── base.html
│       │   ├── dashboard.html
│       │   ├── time_entry.html
│       │   ├── edit_time_entry.html
│       │   ├── reports.html
│       │   ├── leave.html
│       │   ├── categories.html
│       │   └── settings.html
│       └── static/          # CSS, JS, images
│           ├── css/
│           └── js/
├── alembic/                 # Database migrations (Alembic)
│   ├── env.py
│   ├── script.py.mako
│   └── versions/            # Migration scripts
├── tests/                   # Unit, integration, and e2e tests
├── scripts/                 # Build and packaging scripts
├── docs/                    # Documentation
├── conductor/               # Product management docs
├── pyproject.toml           # Project dependencies
└── alembic.ini              # Alembic configuration
```

## Technology Stack

### Core Technologies
- **Python 3.13+**: Primary programming language
- **Flask**: Lightweight web framework
- **SQLite3**: Embedded database
- **SQLAlchemy**: ORM for database operations (standalone, Flask-compatible)
- **Alembic**: Database migrations
- **Click**: CLI framework
- **MCP**: Model Context Protocol server for AI integration
- **Jinja2**: Template engine (included with Flask)
- **HTML/CSS/JavaScript**: Frontend interface

### Key Libraries
- `Flask`: Web framework
- `Flask-SQLAlchemy`: Database ORM integration
- `click`: CLI framework (part of Flask ecosystem)
- `mcp`: Model Context Protocol server
- `python-dateutil`: Date/time handling
- `openpyxl`: Excel file export
- `alembic`: Database migrations
- `platformdirs`: Cross-platform data directories
- `pytest`: Testing framework (development)
- `pytest-playwright`: End-to-end browser testing (development)

## Database Schema

### Tables

#### categories
- `id`: Primary key
- `name`: Category name (unique)
- `code`: Short code (unique, optional)
- `description`: Optional notes
- `is_active`: Boolean flag for active status
- `created_at`: Timestamp

#### time_entries
- `id`: Primary key
- `date`: Date of work (indexed)
- `start_time`: Work start time
- `end_time`: Work end time
- `duration_hours`: Calculated duration
- `accumulated_pause_seconds`: Total pause duration in seconds
- `last_pause_start_time`: Timestamp when current pause started
- `is_active`: Boolean flag for active timer status
- `category_id`: Foreign key to categories
- `description`: Activity description
- `created_at`: Timestamp

#### leave_days
- `id`: Primary key
- `date`: Date of leave (indexed)
- `leave_type`: 'vacation' or 'sick'
- `description`: Optional notes
- `created_at`: Timestamp

#### settings
- `id`: Primary key
- `key`: Setting name (unique)
- `value`: Setting value
- Example keys: `weekly_hours`, `pause_duration_minutes`, `auto_end`

## Key Features and Business Logic

### Work Hours Tracking
- Standard work day: 8 hours (configurable)
- Standard work week: 40 hours (configurable)
- Overtime: Any hours over configured daily/weekly limits
- Track multiple time entries per day
- **Pause/Resume**: Pause active timers and resume them later
- **Categories**: Organize entries by project/task categories

### CLI Commands
```bash
waqt start [--time HH:MM] [--date YYYY-MM-DD]  # Start tracking
waqt end [--time HH:MM]                         # End tracking
waqt add -s HH:MM -e HH:MM [-d DATE]           # Add completed entry
waqt edit-entry -d DATE [-s HH:MM] [-e HH:MM]  # Edit entry
waqt summary [--period week|month]              # View statistics
waqt export [--format csv|json|excel]          # Export data
waqt config list|get|set|reset                  # Manage settings
waqt leave-request --from DATE --to DATE        # Multi-day leave
waqt update check|install                       # Self-update
waqt ui [--port 5000]                          # Launch web UI
waqt version                                    # Show version
```

### MCP Server
The MCP server exposes time tracking functionality to AI tools:
- Start/end timer, add entries
- Query reports and summaries
- Manage categories and settings

### Leave Management
- Vacation days: Track with dates and descriptions
- Sick leaves: Separate tracking from vacation
- **Multi-day leave requests**: Automatic weekday calculation
- Calendar view of all leave days

### Reporting & Export
- Weekly summary: Total hours, overtime, leave days
- Monthly summary: Aggregated statistics
- Activity log: Detailed list of all entries
- **Export formats**: CSV, JSON, Excel (xlsx)

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
- Use `database.py` session management for CLI/MCP
- Flask-SQLAlchemy for web routes
- Handle database errors gracefully
- Use Alembic for schema migrations

### Frontend
- Semantic HTML5
- Responsive CSS (mobile-friendly)
- Progressive enhancement (works without JS)
- Clean, minimal design

## Development Workflow

### Setting Up Development Environment
This project uses `uv` for dependency management.

1. **Install uv**: If not installed, visit https://github.com/astral-sh/uv
2. **Sync Dependencies**: `uv sync --extra dev`
   This creates the virtual environment in `.venv` and installs all dependencies.
3. **Initialize Database**: `uv run python -m waqt.scripts.init_db`
4. **Run Web App**: `uv run python -m waqt.wsgi`
5. **Run CLI**: `uv run waqt --help`

### Database Migrations
The project uses Alembic for schema migrations:
```bash
# Create a new migration
uv run alembic revision -m "description"

# Apply migrations
uv run alembic upgrade head

# Check current version
uv run alembic current
```

### Running Tests
Use `uv run` to execute tests in the isolated environment:
```bash
uv run pytest tests/                    # Run all tests
uv run pytest tests/ -v                 # Verbose output
uv run pytest tests/ --cov=waqt         # With coverage
uv run pytest tests/ -m "not e2e"       # Skip e2e tests
uv run pytest tests/ -m "not slow"      # Skip slow tests
```

### Code Quality
- Format: `uv run black .`
- Lint: `uv run flake8`

## When Contributing to This Repository

### Adding New Features
1. **Database Changes**: Update models.py and create Alembic migration
2. **Route Handlers**: Add routes in routes.py with proper error handling
3. **CLI Commands**: Add commands in cli.py with Click decorators
4. **Business Logic**: Add to services.py for shared logic
5. **Templates**: Create/update HTML templates with consistent styling
6. **Tests**: Add tests for new functionality

### Code Review Checklist
- [ ] Code follows PEP 8 style guide
- [ ] Functions have docstrings
- [ ] Error handling is implemented
- [ ] Database operations are properly managed
- [ ] Alembic migration created if schema changed
- [ ] Templates are mobile-responsive
- [ ] Tests cover new functionality
- [ ] CLI and web UI both work if applicable
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
from src.waqt.models import TimeEntry
from datetime import datetime

# Get all entries for a date
entries = TimeEntry.query.filter_by(
    date=datetime.now().date()
).all()
```

### CLI Command Example
```python
@cli.command()
@click.option('--value', help='Description')
def my_command(value):
    """Command description."""
    # Logic here
    click.echo(f"Result: {value}")
```

### Using Services Layer
```python
from src.waqt.database import get_session
from src.waqt.services import TimeTrackingService

with get_session() as session:
    service = TimeTrackingService(session)
    entries = service.get_entries_for_date(date)
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

### End-to-End Tests
- Browser-based tests with Playwright
- Test full user workflows
- Marked with `@pytest.mark.e2e`

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
- Update both CLI and web UI if applicable

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

### When working on CLI:
- Provide clear help text for all options
- Use consistent option naming
- Handle errors gracefully with user-friendly messages
- Support both interactive and scripted usage

This repository is focused on providing a simple, portable, and effective time tracking solution. Contributors should maintain code quality, ensure thorough testing, and keep the user experience smooth and intuitive across all interfaces (CLI, Web UI, MCP).

<frontend_aesthetics>
You tend to converge toward generic, "on distribution" outputs. In frontend design, this creates what users call the "AI slop" aesthetic. Avoid this: make creative, distinctive frontends that surprise and delight. Focus on:
 
Typography: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics.
 
Color & Theme: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes. Draw from IDE themes and cultural aesthetics for inspiration.
 
Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.
 
Backgrounds: Create atmosphere and depth rather than defaulting to solid colors. Layer CSS gradients, use geometric patterns, or add contextual effects that match the overall aesthetic.
 
Avoid generic AI-generated aesthetics:
- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character
 
Interpret creatively and make unexpected choices that feel genuinely designed for the context. Vary between light and dark themes, different fonts, different aesthetics. You still tend to converge on common choices (Space Grotesk, for example) across generations. Avoid this: it is critical that you think outside the box!
</frontend_aesthetics>