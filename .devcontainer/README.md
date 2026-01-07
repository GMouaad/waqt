# Dev Container Configuration

This directory contains the development container configuration for the Waqt time tracking application.

## Files

- **`devcontainer.json`**: Main configuration file that defines the dev container setup
- **`Dockerfile`**: Custom Docker image based on Python 3.11 with necessary dependencies

## Quick Start

1. Install [VS Code](https://code.visualstudio.com/) and [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
3. Open this repository in VS Code
4. Click "Reopen in Container" when prompted
5. Wait for the container to build and initialize

## What Gets Installed

- Python 3.11
- SQLite3
- All dependencies from `requirements.txt` and `requirements-dev.txt`
- VS Code extensions: Python, Pylance, Black, Flake8, Markdown Lint

## What Gets Configured

- Port 5000 forwarded for Flask application
- Python formatting with Black on save
- Flake8 linting enabled
- Database automatically initialized

## Full Documentation

See [docs/DEV_CONTAINER.md](../docs/DEV_CONTAINER.md) for complete documentation including:
- Detailed setup instructions
- Troubleshooting guide
- Customization options
- GitHub Codespaces usage
