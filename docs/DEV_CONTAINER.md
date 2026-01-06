# Development Container Setup

This document explains how to use the development container (dev container) for the Waqtracker time tracking application.

## What is a Dev Container?

A development container is a Docker container specifically configured for development. It provides a consistent development environment across different machines and operating systems.

## Prerequisites

### Option 1: VS Code (Recommended)
- [Visual Studio Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

### Option 2: GitHub Codespaces
- A GitHub account
- No local installation required

## Getting Started with VS Code

### First-Time Setup

1. **Install Prerequisites:**
   - Install VS Code, Docker Desktop, and the Dev Containers extension

2. **Open the Project:**
   ```bash
   git clone https://github.com/GMouaad/time-tracker.git
   cd time-tracker
   code .
   ```

3. **Start the Dev Container:**
   - VS Code will prompt you to "Reopen in Container"
   - Click the prompt or use F1 → "Dev Containers: Reopen in Container"
   - Wait for the container to build (first time takes 2-5 minutes)

4. **Automatic Setup:**
   The dev container will automatically:
   - Install Python 3.11
   - Install all dependencies
   - Initialize the database
   - Configure VS Code

### Running the Application

Once the dev container is ready:

```bash
python run.py
```

Access the application at `http://localhost:5000`

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src.waqtracker
```

## Features Included

### VS Code Extensions
- Python
- Pylance  
- Black Formatter
- Flake8
- Python Debugger
- Markdown Lint

### Environment Configuration
- Python 3.11
- SQLite3
- Git
- Port 5000 forwarded for Flask app

## Troubleshooting

### Container Won't Build

1. Check Docker is running: `docker ps`
2. Rebuild: F1 → "Dev Containers: Rebuild Container"
3. Check logs: F1 → "Dev Containers: Show Container Log"

### Dependencies Not Installing

Rebuild without cache: F1 → "Dev Containers: Rebuild Container Without Cache"

### Database Issues

```bash
rm -f time_tracker.db
python init_db.py
```

## Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
