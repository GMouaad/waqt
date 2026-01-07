# Building Portable Executables

This document explains how to build standalone executables for the Time Tracker application using PyInstaller and the provided GitHub Actions workflows.

## Overview

The application is configured to be built as a single-file executable for Linux, macOS, and Windows. This allows users to run the application without installing Python or dependencies.

## Build Requirements

- Python 3.11+
- `uv` package manager (recommended) or `pip`
- PyInstaller (installed via `build` optional dependency)

## Building Locally

To build the executable on your local machine:

1. **Install Build Dependencies**:
   ```bash
   uv pip install -e ".[build]"
   ```

2. **Run PyInstaller**:
   ```bash
   pyinstaller --name waqtracker --onefile --add-data "src/waqtracker/templates:waqtracker/templates" --add-data "src/waqtracker/static:waqtracker/static" --hidden-import flask --hidden-import werkzeug --hidden-import click src/waqtracker/__main__.py
   ```
   
   *Note: On Windows, use `;` instead of `:` for `--add-data` separator.*

3. **Locate Executable**:
   The built executable will be in the `dist/` directory.

## GitHub Actions Workflows

The repository includes automated workflows for building and releasing executables.

### 1. Cross-Platform Build (`build.yaml`)

This workflow builds executables for all supported platforms:
- **Platforms**: Linux (amd64), macOS (Intel and Apple Silicon), Windows (amd64)
- **Trigger**: Called by other workflows
- **Artifacts**: Uploads built executables as artifacts

### 2. Release Publishing (`release.yaml`)

This workflow publishes a new release with attached artifacts:
- **Trigger**: Manual dispatch or tag push
- **Process**:
  1. Builds executables for all platforms
  2. Generates release notes
  3. Publishes release with assets

### 3. Development Builds (`dev-build.yaml`)

This workflow runs on every push to `main` or `develop` branches:
- **Trigger**: Push to `main` or `develop`
- **Process**:
  1. Runs tests
  2. Builds executables
  3. Creates a "dev" release (or uploads artifacts)

## Version Injection

The build process automatically injects version information into `src/waqtracker/_version.py` so the executable knows its version and commit SHA.

When building locally without the workflow scripts, the version will default to what is in `_version.py` (usually "0.0.0-dev").
