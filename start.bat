@echo off
REM Startup script for Time Tracker application (Windows)

echo Starting Time Tracker...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo Dependencies installed
    echo.
)

REM Check if database exists
if not exist "time_tracker.db" (
    echo Initializing database...
    python init_db.py
    echo.
)

REM Start the application
echo Starting Flask server...
echo Application will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python run.py
