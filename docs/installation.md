# Installation Guide

This guide will help you install and set up the Time Tracker application on your system.

## Prerequisites

Before installing the Time Tracker application, ensure you have the following:

- **Python 3.8 or higher**: The application requires Python 3.8+
  - Check your Python version: `python --version` or `python3 --version`
  - Download from: https://www.python.org/downloads/

- **pip**: Python package installer (usually comes with Python)
  - Check if installed: `pip --version`

- **Git** (optional): For cloning the repository
  - Download from: https://git-scm.com/downloads

## Installation Steps

### Using Quick Start Scripts

For convenience, the project includes startup scripts:

#### On Linux/macOS:
```bash
chmod +x start.sh
./start.sh
```

#### On Windows:
```bash
start.bat
```

### Manual Installation

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

## Troubleshooting

### Python Version Issues
If you encounter Python version errors, ensure you have Python 3.8 or higher installed.

### Port Already in Use
If port 5000 is already in use, you can modify the port in `run.py`.

### Database Initialization Fails
Ensure your virtual environment is activated and all dependencies are installed.

For more detailed troubleshooting and advanced installation options, see the project documentation.
