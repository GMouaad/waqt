# Waqt

<div align="center">
  <h1>⏰ Waqt - Time Tracking Application</h1>
  <p><strong>A portable Python time tracking application for managing work hours, overtime, vacation days, sick leaves, and work activities.</strong></p>
</div>

---

## Welcome to Waqt

Waqt is a self-contained Flask-based time tracking application with no external services required. All data is stored locally in SQLite, making it completely portable and easy to run anywhere.

## Features

✨ **Key Features:**

- **One-Click Timer**: Interactive dashboard timer with Start, Stop, Pause, and Resume controls for real-time tracking
- **Work Hours Tracking**: Track daily work hours (8 hours/day, 40 hours/week standard)
- **Overtime Calculation**: Automatically calculate overtime hours
- **Vacation Days**: Track and manage vacation days
- **Sick Leaves**: Record sick leave days
- **Work Activities**: Log detailed work activities and tasks
- **Reports**: View weekly and monthly overtime summaries
- **CLI Tool**: Command-line interface (`waqt`) for quick time tracking from the terminal
- **MCP Server**: Model Context Protocol server for AI assistant integration

## Technology Stack

- **Backend**: Flask (Python 3.11+)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript
- **Portable**: No external services required

## Quick Start

### One-Line Installer

=== "Linux/macOS"

    ```bash
    curl -fsSL https://raw.githubusercontent.com/GMouaad/waqt/main/install.sh | bash
    ```

=== "Windows (PowerShell)"

    ```powershell
    irm https://raw.githubusercontent.com/GMouaad/waqt/main/install.ps1 | iex
    ```

These installers will:

- Download the latest stable release for your platform
- Install to `~/.waqt/bin` (Unix) or `%LOCALAPPDATA%\waqt` (Windows)
- Add to your PATH automatically
- Verify the installation

After installation, use `waqt` or `waqtracker` commands:

```bash
waqt --version      # Check version
waqtracker          # Start the web server (http://localhost:5555)
waqt start          # Start time tracking from CLI
waqt summary        # View summary
```

## Documentation

📚 **Explore the Documentation:**

- [**Installation Guide**](installation.md) - Detailed installation instructions for all platforms
- [**Usage Guide**](usage.md) - Complete guide on how to use the application
- [**Building Executables**](build.md) - Instructions for building standalone executables
- [**Development Container**](dev-container.md) - Setting up the dev container for development
- [**E2E Testing**](e2e-testing.md) - End-to-end testing documentation
- [**MCP Integration**](mcp-guide.md) - Model Context Protocol server documentation
- [**UV Migration Guide**](uv-migration.md) - Migrating from pip to uv package manager
- [**Contributing**](contributing.md) - How to contribute to the project

## CLI Usage

The `waqt` command-line tool provides a quick way to track time from your terminal:

### Available Commands

```bash
# Start tracking time
waqt start --time 09:00 --description "Working on feature X"

# End tracking time
waqt end --time 17:30

# View summary
waqt summary

# Export time entries
waqt export --period week

# Configuration management
waqt config list
waqt config set weekly_hours 40
```

For complete CLI documentation, see the [Usage Guide](usage.md).

## MCP Server

The `waqt-mcp` server provides Model Context Protocol (MCP) support for AI assistant integration:

```bash
# Run the MCP server
waqt-mcp
```

Available tools for AI assistants:

- `start` - Start time tracking
- `end` - End time tracking  
- `summary` - Get time summaries (week/month)
- `list_entries` - List time entries
- `export_entries` - Export data to CSV

For complete MCP documentation, see the [MCP Guide](mcp-guide.md).

## Web Interface

Navigate to `http://localhost:5555` after running `waqtracker` to access the web interface.

### Features

- **Dashboard Timer**: One-click start/stop/pause/resume timer
- **Time Entry Management**: Add, view, and delete time entries
- **Reports**: Weekly and monthly summaries with overtime calculations
- **Leave Management**: Track vacation days and sick leaves
- **Activity Log**: Browse all recorded activities

For detailed web interface usage, see the [Usage Guide](usage.md).

## Project Structure

```
waqt/
├── src/
│   └── waqtracker/          # Main application package
│       ├── __init__.py      # Flask app initialization
│       ├── models.py        # Database models
│       ├── routes.py        # Application routes
│       ├── wsgi.py          # WSGI entry point
│       ├── scripts/         # Utility scripts (init_db, etc.)
│       ├── templates/       # HTML templates
│       └── static/          # CSS, JS, images
├── docs/                    # Documentation
├── tests/                   # Unit tests
├── pyproject.toml           # Project dependencies
└── README.md               # This file
```

## Getting Help

If you need assistance:

1. Check the documentation (links above)
2. Review the [Installation Guide](installation.md) for setup issues
3. See the [Usage Guide](usage.md) for operational questions
4. Open an issue on [GitHub](https://github.com/GMouaad/waqt/issues)

## License

This project is licensed under the MIT License - see the [License](license.md) page for details.

---

<div align="center">
  <p>Made with ❤️ by the Waqt Contributors</p>
  <p><a href="https://github.com/GMouaad/waqt">⭐ Star us on GitHub</a></p>
</div>
