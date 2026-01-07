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
   - Install all Python dependencies from `requirements.txt` and `requirements-dev.txt`
   - Initialize the SQLite database with `init_db.py`
   - Configure VS Code with recommended extensions and settings

### Running the Application

Once the dev container is ready:

1. **Start the Flask server:**
   ```bash
   python run.py
   ```
   Or use the provided startup script:
   ```bash
   ./start.sh
   ```

2. **Access the application:**
   - VS Code will automatically forward port 5555
   - Click the notification or go to `http://localhost:5555` in your browser

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_models.py
```

### Code Formatting and Linting

The dev container is pre-configured with:
- **Black**: Auto-formats code on save
- **Flake8**: Lints code for style issues

Manual commands:
```bash
# Format code with Black
black .

# Check linting with Flake8
flake8 app/ tests/
```

## Getting Started with GitHub Codespaces

1. **Create a Codespace:**
   - Go to the repository on GitHub
   - Click the "Code" button → "Codespaces" tab
   - Click "Create codespace on main"

2. **Wait for Setup:**
   - The codespace will automatically build and configure the environment
   - All dependencies will be installed automatically

3. **Start Development:**
   - Run `python run.py` to start the application
   - Access the app through the forwarded port (VS Code will notify you)

## Features Included

### VS Code Extensions

The dev container automatically installs:
- **Python**: Core Python support
- **Pylance**: Advanced Python language server
- **Black Formatter**: Code formatting
- **Flake8**: Code linting
- **Python Debugger**: Debugging support
- **Markdown Lint**: Documentation linting

### Environment Configuration

- **Python 3.11**: Latest stable Python version
- **SQLite3**: Pre-installed for database operations
- **Git**: Version control tools
- **Port Forwarding**: Port 5555 for Flask app

### Automatic Setup

On container creation:
1. All Python dependencies are installed
2. Development dependencies are installed
3. Database is initialized with schema
4. VS Code settings are configured

## Customization

### Adding Extensions

Edit `.devcontainer/devcontainer.json` and add extensions to the `extensions` array:

```json
"extensions": [
    "ms-python.python",
    "your-extension-id"
]
```

### Modifying Python Version

Edit `.devcontainer/Dockerfile` and change the base image:

```dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.12
```

### Adding System Packages

Edit `.devcontainer/Dockerfile` and add packages to the `apt-get install` command:

```dockerfile
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    your-package \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*
```

## Troubleshooting

### Container Won't Build

1. **Check Docker is running:**
   ```bash
   docker ps
   ```

2. **Rebuild the container:**
   - Command Palette (F1) → "Dev Containers: Rebuild Container"

3. **Check logs:**
   - Command Palette (F1) → "Dev Containers: Show Container Log"

### Dependencies Not Installing

1. **Rebuild without cache:**
   - Command Palette (F1) → "Dev Containers: Rebuild Container Without Cache"

2. **Manually install dependencies:**
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

### Database Issues

1. **Reinitialize the database:**
   ```bash
   rm -f time_tracker.db
   python init_db.py
   ```

### Port Already in Use

1. **Stop other services using port 5555:**
   ```bash
   # On Linux/Mac
   lsof -ti:5555 | xargs kill -9
   
   # On Windows (PowerShell)
   Get-Process -Id (Get-NetTCPConnection -LocalPort 5555).OwningProcess | Stop-Process
   ```

2. **Use a different port:**
   Set the `PORT` environment variable: `PORT=5556 python run.py`

## Best Practices

1. **Keep the container updated:**
   - Rebuild periodically to get updates: "Dev Containers: Rebuild Container"

2. **Don't modify files outside the container:**
   - Always edit files while connected to the dev container

3. **Commit your changes:**
   - The dev container has Git pre-configured
   - Use the integrated terminal for Git operations

4. **Use version control:**
   - Don't modify `.devcontainer/` files without committing them
   - Changes should work for all team members

## Additional Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container Specification](https://containers.dev/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)

## Support

If you encounter issues with the dev container:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review container logs
3. Open an issue on GitHub with:
   - Your operating system
   - Docker version (`docker --version`)
   - VS Code version
   - Error messages or logs
