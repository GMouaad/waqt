# Waqt

A portable Python time tracking application for managing work hours, overtime, vacation days, sick leaves, and work activities.

## Project Overview

This is a self-contained Flask-based time tracking application with no external services required. All data is stored locally in SQLite, making it completely portable and easy to run anywhere.

## Documentation

📚 **[View Documentation Website](https://gmouaad.github.io/waqt/)** - Complete documentation with guides and examples

Additional reference guides:
- **[Installation Guide](docs/guides/installation.html)** - Detailed installation instructions, prerequisites, and troubleshooting
- **[Usage Guide](docs/guides/usage.html)** - Complete guide on how to use the application, workflows, and best practices
- **[MCP Guide](docs/guides/MCP_GUIDE.html)** - Model Context Protocol server documentation for AI assistant integration

## Features

- **One-Click Timer**: Interactive dashboard timer with Start, Stop, Pause, and Resume controls for real-time tracking
- **Session Alerts**: Configurable alerts when work sessions exceed 8 hours (helps comply with labor laws)
- **Work Hours Tracking**: Track daily work hours (8 hours/day, 40 hours/week standard)
- **Edit Time Entries**: Correct mistakes in your time logs via UI or CLI using simple date-based editing
- **Overtime Calculation**: Automatically calculate overtime hours
- **Vacation Days**: Track and manage vacation days
- **Sick Leaves**: Record sick leave days
- **Work Activities**: Log detailed work activities and tasks
- **Reports**: View weekly and monthly overtime summaries
- **Data Persistence**: Automatic data migration and secure storage in user data directories, preventing data loss during updates
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

*Note: If you encounter an execution policy error, you may need to run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first.*

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

**Note:** You can also switch between stable and prerelease channels using the update command:
```bash
waqt update install --prerelease  # Switch to prerelease
waqt update install               # Switch back to stable
```

After installation, use `waqt` commands:
```bash
waqt --version      # Check version
waqt ui             # Start the web UI (http://localhost:5555)
waqt start          # Start time tracking from CLI
waqt summary        # View summary
waqt update check   # Check for updates
waqt update         # Self-update to latest version
```

---

### Option 1: Download Standalone Executable (Manual Install)

Alternatively, you can manually download a pre-built executable for your platform:

1. **Download the latest release:**
   - Go to the [Releases page](https://github.com/GMouaad/waqt/releases)
   - Download the zip file for your platform:
     - **Linux (x64)**: `waqt-linux-amd64.zip`
     - **macOS (Intel)**: `waqt-macos-amd64.zip`
     - **macOS (Apple Silicon)**: `waqt-macos-arm64.zip`
     - **Windows (x64)**: `waqt-windows-amd64.zip`

2. **Extract and run:**
   ```bash
   # Linux/macOS
   unzip waqt-*.zip
   chmod +x waqt  # macOS/Linux only
   ./waqt
   
   # Windows PowerShell
   Expand-Archive waqt-windows-amd64.zip
   .\waqt.exe
   ```

3. **Access:** Open `http://localhost:5555` in your browser

**CLI Usage:** When running the standalone executable, pass CLI commands directly as arguments:
```bash
./waqt --version      # Check version
./waqt start          # Start time tracking
./waqt end            # End time tracking
./waqt summary        # View summary
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
   waqt ui   # Database initialized automatically on first run
   ```

3. **Access:** Open `http://localhost:5555`

📚 **For detailed uv installation guide, see [docs/guides/installation.html](docs/guides/installation.html)**

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
   waqt ui
   ```
   Access at `http://localhost:5555`

### Option 4: Manual Installation with pip (Legacy - Deprecated)

> **⚠️ DEPRECATED**: This method is maintained for backward compatibility. Please use the standalone executable (Option 1) or `uv` (Option 2) for better experience.

**Requirements:** Python 3.11 or higher

For detailed installation instructions including troubleshooting, see the **[Installation Guide](docs/guides/installation.html)**.

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
waqt ui
```

*Note: The database is automatically initialized and migrated on first run.*

6. Open your browser and navigate to `http://localhost:5555`

**Alternative:** Use the quick start scripts:
- Linux/macOS: `./start.sh`
- Windows: `.\start.ps1`

## CLI Usage (`waqt`)

The `waqt` command-line tool provides a quick and convenient way to track time from your terminal.

**Using uv (Recommended):**
You can run commands directly without activating a virtual environment:
```bash
uv run waqt start
uv run waqt summary
```

**Using activated environment:**
```bash
waqt start
waqt summary
```

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
- `time_format`: Time display format (12 or 24) (default: 24)

**Configuration Features:**
- All settings persist in the database
- Configuration changes immediately affect calculations
- Values are validated before being saved
- Non-default values are marked with an asterisk (*) in list output
- **Custom Data Directory**: Set `WAQT_DATA_DIR` environment variable to override storage location

#### Check for Updates
Check if a newer version of waqt is available:
```bash
# Check for stable release updates
waqt update check

# Check for prerelease (dev) updates
waqt update check --prerelease
```

#### Self-Update
Update waqt to the latest version (frozen executables only):
```bash
# Update to latest stable release
waqt update

# Update with confirmation prompt
waqt update install

# Update without confirmation
waqt update install --yes

# Update to latest prerelease (dev channel)
waqt update install --prerelease
```

**Note:** Self-update only works for frozen executables (installed via `install.sh` or `install.ps1`). If running from source, update using:
```bash
cd <waqt-repo-directory>
git pull
uv pip install -e .  # or: pip install -e .
```

#### Display Version Information
Show the current version and git commit:
```bash
waqt version
```

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

## Development

### Running Tests

This project uses `pytest` for unit tests and `playwright` for end-to-end (E2E) tests.

**Prerequisites:**
1. Install dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```
2. Install Playwright browsers (required for E2E tests):
   ```bash
   playwright install chromium --with-deps
   ```

**Running Tests:**
```bash
# Run all tests (unit + E2E)
pytest tests/ -v

# Run only E2E tests
pytest tests/ -v -m e2e

# Run excluding E2E tests
pytest tests/ -v -m "not e2e"
```

*Note: E2E tests verify major user flows like navigation, time entries, leave management, and reports. If Playwright browsers are not installed, these tests will automatically skip.*

### Building Standalone Executables

You can build single-file executables for Linux, macOS, and Windows using PyInstaller.

**Requirements:**
- Python 3.11+
- `uv` package manager (recommended) or `pip`

**Build Steps:**
1. Install build dependencies:
   ```bash
   uv pip install -e ".[build]"
   ```
2. Run PyInstaller:
   ```bash
   pyinstaller --name waqt --onefile --add-data "src/waqt/templates:waqt/templates" --add-data "src/waqt/static:waqt/static" --hidden-import flask --hidden-import werkzeug --hidden-import click src/waqt/__main__.py
   ```
   *Note: On Windows, use `;` instead of `:` for the `--add-data` separator.*

3. The executable will be created in the `dist/` directory.

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
    "waqt": {
      "command": "waqt-mcp",
      "env": {}
    }
  }
}
```

📚 **For detailed MCP documentation, see [docs/guides/MCP_GUIDE.html](docs/guides/MCP_GUIDE.html)**

## Web Interface Usage

For detailed usage instructions, workflows, and examples, see the **[Usage Guide](docs/guides/usage.html)**.

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
│   └── waqt/          # Main application package
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
│       ├── installation.html  # Installation guide
│       └── usage.html        # Usage guide
├── tests/                   # Unit tests
├── pyproject.toml           # Project dependencies
└── README.md               # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.