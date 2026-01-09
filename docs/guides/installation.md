# Installation Guide

This guide will help you install and set up the Waqt application on your system.

## Quick Install (Recommended)

The fastest way to get started is using our automated installer scripts:

### Linux/macOS
```bash
curl -fsSL https://raw.githubusercontent.com/GMouaad/waqt/main/install.sh | bash
```

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/GMouaad/waqt/main/install.ps1 | iex
```

These installers will:
- Automatically detect your OS and architecture
- Download the latest stable release
- Install to `~/.waqt/bin` (Unix) or `%LOCALAPPDATA%\waqt` (Windows)
- Add the installation directory to your PATH
- Verify the installation with `waqt --version`

**Install development build (prerelease):**
```bash
# Linux/macOS
curl -fsSL https://raw.githubusercontent.com/GMouaad/waqt/main/install.sh | bash -s -- --prerelease

# Windows PowerShell
iex "& { $(irm https://raw.githubusercontent.com/GMouaad/waqt/main/install.ps1) } -Prerelease"
```

After installation, use these commands:
```bash
waqt --version      # Check version
waqt          # Start the web server (http://localhost:5555)
waqt start          # Start time tracking from CLI
waqt summary        # View summary
```

**Security Note:** Review the installer scripts before running:
- [install.sh](../install.sh) for Linux/macOS
- [install.ps1](../install.ps1) for Windows

---

## Prerequisites

For manual or source installation, ensure you have the following:

- **Python 3.10 or higher**: The application requires Python 3.10+
  - Check your Python version: `python --version` or `python3 --version`
  - Download from: https://www.python.org/downloads/

- **uv** (Recommended): Modern, fast Python package manager
  - Installation instructions below
  - Or **pip**: Traditional Python package installer (legacy method)

- **Git** (optional): For cloning the repository
  - Download from: https://git-scm.com/downloads

### Operating System Support

The Waqt application works on:
- Linux (Ubuntu, Debian, Fedora, etc.)
- macOS
- Windows 10/11

## Installation Methods

Choose one of the following installation methods:

### Method 1: Using uv (Recommended - Fast & Modern)

This is the **recommended** approach using the modern `uv` package manager, which is 10-100x faster than pip.

### Method 2: Using pip (Legacy)

Traditional installation method using pip. **Note**: This method is deprecated in favor of `uv`.

---

## Method 1: Installation with uv (Recommended)

### Step 1: Install uv

First, install the `uv` package manager:

#### Recommended: Using pip

```bash
pip install uv
```

#### Alternative: Using install script

**⚠️ Security Note**: The install scripts download and execute code. Review the script source before running:
- Linux/macOS: https://astral.sh/uv/install.sh
- Windows: https://astral.sh/uv/install.ps1

##### On Linux/macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

##### On Windows:

Using PowerShell:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Verify Installation

After installing with any method:
```bash
uv --version
```

Verify installation:
```bash
uv --version
```

### Step 2: Get the Source Code

#### Option A: Clone with Git (Recommended)

```bash
git clone https://github.com/GMouaad/waqt.git
cd waqt
```

#### Option B: Download ZIP

1. Visit https://github.com/GMouaad/waqt
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Navigate to the extracted folder

### Step 3: Create a Virtual Environment with uv

`uv` automatically manages virtual environments. Create one with:

```bash
uv venv
```

Activate the virtual environment:

#### On Linux/macOS:
```bash
source .venv/bin/activate
```

#### On Windows:
```bash
.venv\Scripts\activate
```

You should see `(.venv)` in your terminal prompt.

### Step 4: Install Dependencies with uv

Install all dependencies using `uv`:

```bash
uv pip install -e .
```

This installs:
- Flask 3.0.0 (web framework)
- Flask-SQLAlchemy 3.1.1 (database ORM)
- python-dateutil 2.8.2 (date/time utilities)
- Werkzeug 3.0.1 (WSGI utilities)

**Benefits of uv:**
- ⚡ 10-100x faster than pip
- 🔒 Automatic dependency resolution
- 📦 Built-in virtual environment management
- 🚀 Significantly faster installation times

### Step 5: Initialize the Database (Optional)

The Waqt application is designed to be **self-initializing**. When you run the application for the first time, it will automatically:
- Create the SQLite database file (`time_tracker.db`)
- Create all necessary tables
- Apply any pending schema migrations
- Seed default configuration settings

If you prefer to initialize the database manually before running the app, you can use:

```bash
python -m waqt.scripts.init_db
```

This creates a `time_tracker.db` file in your project directory with all default settings.

### Step 6: Run the Application

Start the Flask development server:

**Using uv (Recommended):**
```bash
uv run waqt ui
```

**Using activated environment:**
```bash
waqt ui
```

You should see output like:
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in production.
 * Running on http://0.0.0.0:5555
```

### Step 7: Access the Application

Open your web browser and navigate to:

```
http://localhost:5555
```

You should see the Waqt dashboard!

---

## Method 2: Installation with pip (Legacy - Deprecated)

> **⚠️ DEPRECATED**: This method is maintained for backward compatibility but is deprecated. Please use `uv` (Method 1) for better performance and modern tooling.

### 1. Get the Source Code

Follow the same instructions as Method 1, Step 2.

### 2. Create a Virtual Environment

A virtual environment keeps project dependencies isolated from your system Python.

#### On Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

#### On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

### 3. Install Dependencies

With the virtual environment activated, install the required packages:

```bash
pip install -e .
```

### 4-7. Complete Setup

Follow Steps 5-7 from Method 1 above to initialize the database and run the application.

## Quick Start Scripts

For convenience, the project includes startup scripts that automate the installation and setup process.

### Using uv (Recommended):

The scripts now support both `uv` and `pip`. They will automatically detect and use `uv` if available.

### On Linux/macOS:

```bash
chmod +x start.sh
./start.sh
```

### On Windows:

```bash
.\start.ps1
```

These scripts will:
- Detect and use `uv` if available (falls back to pip)
- Create a virtual environment (if not exists)
- Activate the virtual environment
- Install dependencies (if not installed)
- Start the application (which handles database initialization)

## Verification

To verify your installation is working correctly:

1. **Check the Dashboard**: Visit `http://localhost:5555` and see the dashboard
2. **Add a Test Entry**: Click "Add Time Entry" and create a test work log
3. **View Reports**: Navigate to the Reports page to see weekly/monthly summaries

## Troubleshooting

### Python Version Issues

**Problem**: `python: command not found` or wrong version

**Solution**: 
- Try `python3` instead of `python`
- Install Python 3.8+ from https://www.python.org/downloads/
- On Linux: `sudo apt install python3` (Ubuntu/Debian) or `sudo yum install python3` (Fedora)

### Permission Errors

**Problem**: Permission denied when creating files/folders

**Solution**:
- Ensure you have write permissions in the project directory
- On Linux/macOS, you may need to use `chmod` to set permissions
- Don't use `sudo` with pip; use virtual environments instead

### Database Initialization Fails

**Problem**: Errors when running `init_db.py`

**Solution**:
- Ensure virtual environment is activated
- Check that Flask and SQLAlchemy are installed: `pip list | grep -i flask`
- Delete `time_tracker.db` if it exists and try again
- Check file permissions in the project directory

### Port Already in Use

**Problem**: `Address already in use` error

**Solution**:
- Another application is using port 5555
- Find and stop the other application
- Or set the `PORT` environment variable to use a different port (e.g., 5556):
  - Linux/macOS: `PORT=5556 waqt ui`
  - Windows (CMD): `set PORT=5556 && waqt ui`
  - Windows (PowerShell): `$env:PORT=5556; waqt ui`

### Virtual Environment Not Activating

**Problem**: Virtual environment won't activate on Windows

**Solution**:
- You may need to enable script execution:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- Then try activating again

### Dependencies Won't Install

**Problem**: Package installation fails

**Solution with uv**:
- Update uv: `uv self update`
- Check your internet connection
- Clear cache: `uv cache clean`
- Try installing with pip as fallback: `pip install -e .`

**Solution with pip (legacy)**:
- Update pip: `pip install --upgrade pip`
- Check your internet connection
- Try installing packages individually:
  ```bash
  pip install Flask==3.0.0
  pip install Flask-SQLAlchemy==3.1.1
  pip install python-dateutil==2.8.2
  ```

### uv Command Not Found

**Problem**: `uv: command not found`

**Solution**:
- Ensure uv is installed: Follow Step 1 of Method 1
- On Linux/macOS, restart your terminal or run: `source ~/.bashrc` or `source ~/.zshrc`
- On Windows, restart PowerShell
- Alternatively, use pip method (Method 2) as fallback

## Development Installation

If you plan to contribute to the project, install development dependencies:

### With uv (Recommended):

```bash
uv pip install -e ".[dev]"
```

### With pip (Legacy):

```bash
pip install -e ".[dev]"
```

This includes testing and code quality tools:
- pytest 9.0.2 (testing framework)
- pytest-cov 7.0.0 (coverage reporting)
- flake8 7.0.0 (linting)
- black 24.1.1 (code formatting)

## Uninstallation

To remove the Waqt application:

1. Deactivate virtual environment: `deactivate`
2. Delete the project folder

### Data Backup

Your time tracking data is stored in a platform-specific data directory. If you want to back it up or delete it:

- **Linux**: `~/.local/share/waqt/time_tracker.db`
- **macOS**: `~/Library/Application Support/waqt/time_tracker.db`
- **Windows**: `%LOCALAPPDATA%\GMouaad\waqt\time_tracker.db`

You can override this location by setting the `WAQT_DATA_DIR` environment variable.

*Note: Older versions stored data in `time_tracker.db` within the installation directory. The application automatically migrates this data to the new location on first run.*

## Next Steps

Once installed, proceed to the [Usage Guide](usage.md) to learn how to use the Waqt application effectively.

## Migrating from pip to uv

If you're an existing user with a pip-based setup and want to switch to uv, see the **[UV Migration Guide](UV_MIGRATION_GUIDE.md)** for step-by-step instructions.

## Getting Help

If you encounter issues not covered here:

1. Check the [Usage Guide](usage.md) for operational questions
2. Review the project's [README.md](../README.md)
3. Open an issue on GitHub: https://github.com/GMouaad/waqt/issues
