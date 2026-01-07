# Time Tracker

A portable Python time tracking application for managing work hours, overtime, vacation days, sick leaves, and work activities.

## Project Overview

This is a self-contained Flask-based time tracking application with no external services required. All data is stored locally in SQLite, making it completely portable and easy to run anywhere.

## Documentation

- **[Installation Guide](docs/installation.md)** - Detailed installation instructions, prerequisites, and troubleshooting
- **[UV Migration Guide](docs/UV_MIGRATION_GUIDE.md)** - Guide for migrating from pip to uv package manager
- **[Usage Guide](docs/usage.md)** - Complete guide on how to use the application, workflows, and best practices
- **[MCP Guide](docs/MCP_GUIDE.md)** - Model Context Protocol server documentation for AI assistant integration

## Features

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

## Installation

### Option 1: Download Standalone Executable (Easiest)

The easiest way to get started is to download a pre-built executable for your platform:

1. **Download the latest release:**
   - Go to the [Releases page](https://github.com/GMouaad/time-tracker/releases)
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

3. **Access:** Open `http://localhost:5000` in your browser

**CLI Usage:** When running the standalone executable, pass CLI commands directly as arguments:
```bash
./waqtracker --version      # Check version
./waqtracker start          # Start time tracking
./waqtracker end            # End time tracking
./waqtracker summary        # View summary
```

### Option 2: Using uv (Recommended - Fast & Modern)

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
   git clone https://github.com/GMouaad/time-tracker.git
   cd time-tracker
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   python init_db.py
   python run.py
   ```

3. **Access:** Open `http://localhost:5000`

📚 **For detailed uv installation guide, see [docs/installation.md](docs/installation.md)**

### Option 3: Using Dev Container (Recommended for Development)

The easiest way to get started is using the pre-configured development container:

1. **Prerequisites:**
   - Install [VS Code](https://code.visualstudio.com/)
   - Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Clone and open:**
   ```bash
   git clone https://github.com/GMouaad/time-tracker.git
   cd time-tracker
   code .
   ```

3. **Start the dev container:**
   - When prompted, click "Reopen in Container"
   - Or use Command Palette (F1) → "Dev Containers: Reopen in Container"
   - Everything (dependencies, database) will be set up automatically!

4. **Run the application:**
   ```bash
   python run.py
   ```
   Access at `http://localhost:5000`

📚 **For detailed dev container documentation, see [docs/DEV_CONTAINER.md](docs/DEV_CONTAINER.md)**

### Option 4: Manual Installation with pip (Legacy - Deprecated)

> **⚠️ DEPRECATED**: This method is maintained for backward compatibility. Please use the standalone executable (Option 1) or `uv` (Option 2) for better experience.

**Requirements:** Python 3.11 or higher

For detailed installation instructions including troubleshooting, see the **[Installation Guide](docs/installation.md)**.

### Quick Start (Legacy pip method)

> **Note**: Consider using the standalone executable or `uv` for easier installation.

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

📚 **For detailed MCP documentation, see [docs/MCP_GUIDE.md](docs/MCP_GUIDE.md)**

## Web Interface Usage

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
├── src/
│   └── waqtracker/          # Main application package
│       ├── __init__.py      # Flask app initialization
│       ├── models.py        # Database models
│       ├── routes.py        # Application routes
│       ├── templates/       # HTML templates
│       └── static/          # CSS, JS, images
├── docs/                    # Documentation
│   ├── installation.md      # Installation guide
│   ├── usage.md            # Usage guide
│   └── DEV_CONTAINER.md    # Dev container guide
├── tests/                   # Unit tests
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
├── init_db.py               # Database initialization
└── README.md               # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.