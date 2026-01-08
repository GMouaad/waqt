# Building Portable Executables

This document explains how to build standalone executables for the Waqt application using PyInstaller and the provided GitHub Actions workflows.

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

This workflow publishes a draft release as an official release:
- **Trigger**: Manual dispatch via GitHub Actions UI
- **Prerequisites**: A draft release must exist (created by the Dev Build workflow)
- **Process**:
  1. Finds the latest draft release
  2. Verifies the Dev Build workflow passed for that commit
  3. Verifies all expected artifacts are attached to the draft release:
     - `waqtracker-linux-amd64.zip`
     - `waqtracker-macos-arm64.zip`
     - `waqtracker-windows-amd64.zip`
  4. Builds the final release notes (keeps AI-generated notes or uses custom notes)
  5. Publishes the draft release as the latest release

### 3. Development Builds (`dev-build.yaml`)

This workflow runs on every push to `main` or `develop` branches:
- **Trigger**: Push to `main` or `develop`, or pull requests
- **Process**:
  1. Runs tests across multiple Python versions (3.11, 3.12)
  2. Builds executables for all platforms (Linux, macOS, Windows)
  3. Creates/updates a draft release with artifacts (main branch only)
  
**Draft Release Creation** (main branch only):
- Tag format: `v0.1.${run_number}-dev` (e.g., `v0.1.123-dev`)
- Downloads all build artifacts from the workflow
- Creates or updates a draft release on GitHub
- Uploads the following artifacts to the draft release:
  - `waqtracker-linux-amd64.zip`
  - `waqtracker-macos-arm64.zip`
  - `waqtracker-windows-amd64.zip`
- These artifacts are then available for the Release workflow to verify and publish

## Version Injection

The build process automatically injects version information into `src/waqtracker/_version.py` so the executable knows its version and commit SHA.

When building locally without the workflow scripts, the version will default to what is in `_version.py` (usually "0.0.0-dev").
