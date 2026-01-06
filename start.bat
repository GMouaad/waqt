@echo off
REM Startup script for Time Tracker application (Windows)
REM Supports both uv (recommended) and pip (legacy)

echo Starting Time Tracker...
echo.

REM Detect if uv is available
where uv >nul 2>nul
if %errorlevel% equ 0 (
    set UV_AVAILABLE=true
    echo Using uv package manager (fast mode)
) else (
    set UV_AVAILABLE=false
    echo Using pip package manager (legacy mode)
    echo Tip: Install uv for 10-100x faster package management: https://github.com/astral-sh/uv
)
echo.

REM Check if virtual environment exists
if not exist "venv" if not exist ".venv" (
    echo Virtual environment not found!
    echo Creating virtual environment...
    if "%UV_AVAILABLE%"=="true" (
        uv venv
        set VENV_DIR=.venv
    ) else (
        python -m venv venv
        set VENV_DIR=venv
    )
    echo Virtual environment created
    echo.
) else (
    REM Determine which venv directory exists
    if exist ".venv" (
        set VENV_DIR=.venv
    ) else (
        set VENV_DIR=venv
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call %VENV_DIR%\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    if "%UV_AVAILABLE%"=="true" (
        uv pip install -e .
    ) else (
        pip install -r requirements.txt
    )
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
