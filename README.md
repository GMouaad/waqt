# Waqt

A portable Python time tracking application for managing work hours, overtime, vacation days, sick leaves, and work activities.

## Project Overview

This is a self-contained Flask-based time tracking application with no external services required. All data is stored locally in SQLite, making it completely portable and easy to run anywhere.

## Documentation

📚 **[View Documentation Website](https://gmouaad.github.io/waqt/)** - Complete documentation with guides and examples

Additional reference guides:
- **[Installation Guide](docs/guides/installation.md)** - Detailed installation instructions, prerequisites, and troubleshooting
- **[UV Migration Guide](docs/guides/UV_MIGRATION_GUIDE.md)** - Guide for migrating from pip to uv package manager
- **[Usage Guide](docs/guides/usage.md)** - Complete guide on how to use the application, workflows, and best practices
- **[MCP Guide](docs/guides/MCP_GUIDE.md)** - Model Context Protocol server documentation for AI assistant integration
- **[E2E Testing Guide](docs/guides/E2E_TESTING.md)** - Playwright end-to-end testing documentation and best practices

## Features

- **One-Click Timer**: Interactive dashboard timer with Start, Stop, Pause, and Resume controls for real-time tracking
- **Session Alerts**: Configurable alerts when work sessions exceed 8 hours (helps comply with labor laws)
- **Work Hours Tracking**: Track daily work hours (8 hours/day, 40 hours/week standard)
- **Overtime Calculation**: Automatically calculate overtime hours
- **Vacation Days**: Track and manage vacation days
- **Sick Leaves**: Record sick leave days
- **Work Activities**: Log detailed work activities and tasks
- **Reports**: View weekly and monthly overtime summaries
- **Configuration**: Customizable settings via CLI for work hours, alerts, and more
- **CLI Tool**: Command-line interface (`waqt`) for quick time tracking from the terminal
- **MCP Server**: Model Context Protocol server for AI assistant integration


## Technology Stack

- **Backend**: Flask (Python 3.11+)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript
- **Portable**: No external services required

## Installation

### Quick Install (Recommended)

**One-line installer for Linux/macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/GMouaad/waqt/main/install.sh | bash
```

**One-line installer for Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/GMouaad/waqt/main/install.ps1 | iex
```

These installers will:
- Download the latest stable release for your platform
- Install to `~/.waqt/bin` (Unix) or `%LOCALAPPDATA%\waqt` (Windows)
- Add to your PATH automatically
- Verify the installation

**Install development build (prerelease):**
```bash
# Linux/macOS
curl -fsSL https://raw.githubusercontent.com/GMouaad/waqt/main/install.sh | bash -s -- --prerelease

# Windows PowerShell
iex "& { $(irm https://raw.githubusercontent.com/GMouaad/waqt/main/install.ps1) } -Prerelease"
```

After installation, use `waqt` or `waqtracker` commands:
```bash
waqt --version      # Check version
waqtracker          # Start the web server (http://localhost:5555)
waqt start          # Start time tracking from CLI
waqt summary        # View summary
```

---

### Option 1: Download Standalone Executable (Manual Install)

Alternatively, you can manually download a pre-built executable for your platform:

1. **Download the latest release:**
   - Go to the [Releases page](https://github.com/GMouaad/waqt/releases)
   - Download the zip file for your platform:
     - **Linux (x64)**: `waqtracker-linux-amd64.zip`
     - **macOS (Intel)**: `waqtracker-macos-amd64.zip`
     - **macOS (Apple Silicon)**: `waqtracker-macos-arm64.zip`
     - **Windows (x64)**: `waqtracker-windows-amd64.zip`

2. **Extract and run:**
   ```bash
   # Linux/macOS
   unzip waqtracker-*.zip
   chmod +x waqtracker  # macOS/Linux only
   ./waqtracker
   
   # Windows PowerShell
   Expand-Archive waqtracker-windows-amd64.zip
   .\waqtracker.exe
   ```

3. **Access:** Open `http://localhost:5555` in your browser

**CLI Usage:** When running the standalone executable, pass CLI commands directly as arguments:
```bash
./waqtracker --version      # Check version
./waqtracker start          # Start time tracking
./waqtracker end            # End time tracking
./waqtracker summary        # View summary
```

### Option 2: Using uv (Recommended for Source Installation)

The fastest way to get started from source is using `uv`, a modern Python package manager that's 10-100x faster than pip:

**Requirements:** Python 3.11 or higher

1. **Install uv:**
   ```bash
   # Recommended: Install via pip
   pip install uv
   
   # Alternative: Install via script (Linux/macOS)
   # For security, review https://astral.sh/uv/install.sh before running
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Alternative: Install via script (Windows PowerShell)
   # For security, review https://astral.sh/uv/install.ps1 before running
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone and setup:**
   ```bash
   git clone https://github.com/GMouaad/waqt.git
   cd waqt
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   python -m waqtracker.wsgi   # Database initialized automatically on first run
   ```

3. **Access:** Open `http://localhost:5555`

📚 **For detailed uv installation guide, see [docs/guides/installation.md](docs/guides/installation.md)**

### Option 3: Using Dev Container (Recommended for Development)

The easiest way to get started is using the pre-configured development container:

1. **Prerequisites:**
   - Install [VS Code](https://code.visualstudio.com/)
   - Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Clone and open:**
   ```bash
   git clone https://github.com/GMouaad/waqt.git
   cd waqt
   code .
   ```

3. **Start the dev container:**
   - When prompted, click "Reopen in Container"
   - Or use Command Palette (F1) → "Dev Containers: Reopen in Container"
   - Everything (dependencies, database) will be set up automatically!

4. **Run the application:**
   ```bash
   python -m waqtracker.wsgi
   ```
   Access at `http://localhost:5555`

📚 **For detailed dev container documentation, see [docs/guides/DEV_CONTAINER.md](docs/guides/DEV_CONTAINER.md)**

### Option 4: Manual Installation with pip (Legacy - Deprecated)

> **⚠️ DEPRECATED**: This method is maintained for backward compatibility. Please use the standalone executable (Option 1) or `uv` (Option 2) for better experience.

**Requirements:** Python 3.11 or higher

For detailed installation instructions including troubleshooting, see the **[Installation Guide](docs/guides/installation.md)**.

### Quick Start (Legacy pip method)

> **Note**: Consider using the standalone executable or `uv` for easier installation.

1. Clone the repository:
```bash
git clone https://github.com/GMouaad/waqt.git
cd waqt
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Run the application:
```bash
python -m waqtracker.wsgi
```

*Note: The database is automatically initialized and migrated on first run.*

6. Open your browser and navigate to `http://localhost:5555`

**Alternative:** Use the quick start scripts:
- Linux/macOS: `./start.sh`
- Windows: `start.bat`

## CLI Usage (`waqt`)

The `waqt` command-line tool provides a quick and convenient way to track time from your terminal.

### Available Commands

#### Start Tracking Time
Start a new time tracking session for today:
```bash
# Start tracking now with default description
waqt start

# Start tracking at a specific time
waqt start --time 09:00

# Start with custom description
waqt start --time 09:00 --description "Working on feature X"

# Start for a specific date
waqt start --date 2024-01-15 --time 09:00
```

#### End Tracking Time
End the current tracking session:
```bash
# End tracking now
waqt end

# End at a specific time
waqt end --time 17:30

# End for a specific date
waqt end --date 2024-01-15 --time 18:00
```

#### View Summary
Get a summary of your tracked time:
```bash
# Weekly summary (default)
waqt summary

# Monthly summary
waqt summary --period month

# Summary for a specific date
waqt summary --date 2024-01-15

# Short alias
waqt sum -p week
```

#### Export Time Entries
Export your time tracking data to CSV:
```bash
# Export all entries
waqt export

# Export current week
waqt export --period week

# Export specific month
waqt export --period month --date 2024-01-15

# Export with custom filename
waqt export --output my_report.csv

# Export week to specific file
waqt export -p week -o weekly_report.csv
```

#### Configuration Management
Manage application configuration settings:
```bash
# List all configuration options
waqt config list

# Get a specific configuration value
waqt config get weekly_hours

# Set a configuration value
waqt config set weekly_hours 35
waqt config set pause_duration_minutes 60
waqt config set auto_end true

# Reset a configuration to default
waqt config reset weekly_hours
```

**Available Configuration Options:**
- `weekly_hours`: Expected weekly working hours (default: 40)
- `standard_hours_per_day`: Standard working hours per day (default: 8)
- `pause_duration_minutes`: Default pause/break duration in minutes (default: 45)
- `auto_end`: Feature flag for auto-ending work sessions (default: false)

**Configuration Features:**
- All settings persist in the database
- Configuration changes immediately affect calculations
- Values are validated before being saved
- Non-default values are marked with an asterisk (*) in list output

#### Reference (Placeholder)
Display reference information:
```bash
waqt reference
```

### Example Workflow
```bash
# Morning: Start tracking
waqt start --time 09:00 --description "Daily work"

# Evening: End tracking
waqt end --time 17:30

# View weekly summary
waqt summary
```

## MCP Server Usage

The `waqt-mcp` server provides Model Context Protocol (MCP) support for AI assistant integration. This allows AI tools like Claude to interact with your time tracking data.

### Quick Start

```bash
# Run the MCP server
waqt-mcp
```

### Available Tools

The MCP server exposes these tools to AI assistants:
- `start` - Start time tracking
- `end` - End time tracking  
- `summary` - Get time summaries (week/month)
- `list_entries` - List time entries
- `export_entries` - Export data to CSV

### Example Configuration for Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "waqtracker": {
      "command": "waqt-mcp",
      "env": {}
    }
  }
}
```

📚 **For detailed MCP documentation, see [docs/guides/MCP_GUIDE.md](docs/guides/MCP_GUIDE.md)**

## Web Interface Usage

For detailed usage instructions, workflows, and examples, see the **[Usage Guide](docs/guides/usage.md)**.

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
├── examples/                # Example scripts
├── docs/                    # Documentation (HTML & Markdown guides)
│   ├── index.html          # Documentation website
│   ├── installation.html    # Installation page
│   ├── usage.html          # Usage page
│   └── guides/             # Markdown documentation
│       ├── installation.md  # Installation guide
│       ├── usage.md        # Usage guide
│       └── DEV_CONTAINER.md # Dev container guide
├── tests/                   # Unit tests
├── pyproject.toml           # Project dependencies
└── README.md               # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.