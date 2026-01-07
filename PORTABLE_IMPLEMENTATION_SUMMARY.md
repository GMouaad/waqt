# Portable Executable Implementation Summary

## Overview

This document summarizes the changes made to make waqtracker a portable, cross-platform application that can be built and distributed as standalone executables for Windows, Linux, and macOS.

## Changes Made

### 1. Version Tracking (`src/waqtracker/_version.py`)

Created a centralized version tracking file that stores:
- `VERSION`: Application version (e.g., "0.1.0")
- `GIT_SHA`: Git commit SHA for traceability
- `REPO_URL`: Repository URL

This file is dynamically updated during the build process to inject version information into the executables.

### 2. Main Entry Point (`src/waqtracker/__main__.py`)

Created a new entry point that:
- Handles both package execution (`python -m waqtracker`) and frozen PyInstaller execution
- Intelligently routes to either web app or CLI based on command-line arguments:
  - No arguments → Starts the web application
  - With arguments → Runs CLI commands via the `waqt` tool
- Uses conditional imports to handle both frozen and package execution modes

### 3. Python Version Requirements

Updated the minimum Python version requirement from 3.10 to 3.11:
- `pyproject.toml`: Updated `requires-python` to `>=3.11`
- `pyproject.toml`: Updated classifiers to list Python 3.11 and 3.12
- `pyproject.toml`: Updated Black target versions to `py311` and `py312`
- `.github/workflows/python-ci.yml`: Updated test matrix to use Python 3.11 and 3.12

### 4. Build Dependencies

Added PyInstaller to optional dependencies:
```toml
[project.optional-dependencies]
build = [
    "pyinstaller>=6.0.0",
]
```

### 5. GitHub Actions Workflows

#### a. `build.yaml` - Cross-Platform Build Workflow

A reusable workflow that builds executables for all supported platforms:
- **Platforms**: Linux (amd64), macOS (Intel and Apple Silicon), Windows (amd64)
- **Uses uv** for fast dependency management
- **Injects version info** dynamically into `_version.py`
- **PyInstaller configuration**:
  - Single-file executable (`--onefile`)
  - Includes templates and static files
  - Hidden imports for Flask, Werkzeug, and Click
- **Creates zip archives** for each platform
- **Uploads artifacts** for later use in releases

#### b. `release.yaml` - Release Publishing Workflow

A workflow to publish releases with attached build artifacts:
- Finds the latest draft release
- Verifies that builds passed on the main branch
- Generates release notes with installation instructions
- Publishes the release with all platform artifacts attached
- Can use existing AI-generated notes or custom notes

#### c. `dev-build.yaml` - Automated Development Builds

A workflow that automatically triggers on push to main/develop:
- Runs tests on Python 3.11 and 3.12
- Calls the `build.yaml` workflow to build executables
- Creates development versions with auto-incrementing build numbers

### 6. CI/CD Updates

#### `python-ci.yml` Updates
- Removed the `test-legacy-pip` job (no longer needed)
- Removed the `build` job (replaced by separate build workflow)
- Updated Python version matrix to 3.11 and 3.12
- Simplified to focus on testing only

### 7. Documentation Updates

Updated `README.md` with new installation options:
1. **Option 1**: Download standalone executable (added as the easiest method)
2. **Option 2**: Using uv (kept as recommended for development)
3. **Option 3**: Using Dev Container
4. **Option 4**: Manual pip installation (marked as deprecated)

### 8. `.gitignore` Updates

Added entries to exclude:
- PyInstaller artifacts (`*.spec`, `*.manifest`)
- Test virtual environment (`test-venv/`)

## How It Works

### Building Executables

The build process works as follows:

1. **Checkout code**: Gets the repository at a specific ref/SHA
2. **Setup Python**: Uses uv to install Python 3.11
3. **Install dependencies**: Syncs dependencies including PyInstaller
4. **Inject version**: Updates `_version.py` with build version and SHA
5. **Run PyInstaller**: Builds a single-file executable with all dependencies
6. **Package**: Creates a zip file for distribution
7. **Upload**: Uploads the artifact to GitHub Actions

### Cross-Platform Considerations

- **Unix (Linux/macOS)**: Uses `:` separator for `--add-data`
- **Windows**: Uses `;` separator for `--add-data`
- **Different runners**: Uses platform-specific GitHub runners (ubuntu-latest, macos-13, macos-latest, windows-latest)

### Running the Executable

Users can use the same `waqtracker` executable in two ways, depending on whether
command-line arguments are provided:

1. **Web Application mode** (no arguments):
   ```bash
   ./waqtracker
   ```
   This starts the Flask web server on `http://localhost:5555`.

2. **CLI mode** (with arguments):
   When invoked with arguments, the executable does **not** start the web server;
   instead, it forwards the arguments to the internal `waqt` CLI tool.

   ```bash
   # Using the bundled executable in CLI mode
   ./waqtracker --version
   ./waqtracker start
   ./waqtracker end
   ./waqtracker summary

   # Equivalent usage when running the CLI directly (Python environment)
   waqt --version
   waqt start
   waqt end
   waqt summary
   ```

## Testing

All changes have been tested:
- ✅ All 29 existing tests pass
- ✅ CLI commands work (`waqt --version`, `waqt --help`)
- ✅ `python -m waqtracker` works as expected
- ✅ PyInstaller build completes successfully
- ✅ Built executable works correctly (tested locally on Linux)

## File Structure

```
time-tracker/
├── .github/workflows/
│   ├── build.yaml          # NEW - Cross-platform build workflow
│   ├── dev-build.yaml      # NEW - Automated dev builds
│   ├── release.yaml        # NEW - Release publishing workflow
│   └── python-ci.yml       # UPDATED - Simplified to Python 3.11+
├── src/waqtracker/
│   ├── __main__.py         # NEW - Main entry point for executables
│   ├── _version.py         # NEW - Version tracking
│   └── cli.py              # UPDATED - Uses version from _version.py
├── pyproject.toml          # UPDATED - Python 3.11+, build dependencies
├── .gitignore              # UPDATED - Exclude build artifacts
└── README.md               # UPDATED - Installation instructions
```

## Benefits

1. **Ease of Use**: Users can download a single executable without installing Python
2. **Cross-Platform**: Supports Windows, Linux, and macOS (both Intel and Apple Silicon)
3. **Automated**: Builds and releases are fully automated via GitHub Actions
4. **Portable**: No external dependencies or services required
5. **Versioned**: Each build is properly versioned and traceable to a Git SHA
6. **Professional**: Follows industry best practices for distributable applications

## Future Enhancements

Potential improvements for the future:
- Add code signing for executables (Windows/macOS)
- Create installer packages (MSI for Windows, DMG for macOS, DEB/RPM for Linux)
- Add auto-update functionality
- Create a GUI wrapper for the application
- Add performance optimizations for startup time

## Maintenance Notes

- The `build.yaml` workflow is reusable and can be called from other workflows
- Version injection happens at build time, so `_version.py` in the repo always has defaults
- The `dev-build.yaml` workflow creates development versions on every push to main/develop
- Release workflow requires a draft release to exist first (can be created manually or via another workflow)
