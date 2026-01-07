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

REM Determine which venv directory exists or create new one
set VENV_DIR=
if exist ".venv" set VENV_DIR=.venv
if exist "venv" (
    if not defined VENV_DIR set VENV_DIR=venv
)

REM Warn if both virtual environments are present
if exist ".venv" if exist "venv" (
    echo WARNING: Both ".venv" and "venv" directories were found.
    echo          Using "%VENV_DIR%" for this session.
    echo          Consider removing the unused environment to avoid confusion.
    echo.
)

REM Create virtual environment if it doesn't exist
if not defined VENV_DIR (
    echo Virtual environment not found!
    echo Creating virtual environment...
    if "%UV_AVAILABLE%"=="true" (
        uv venv
        if errorlevel 1 (
            echo Failed to create virtual environment with uv.
            exit /b 1
        )
        set VENV_DIR=.venv
    ) else (
        python -m venv venv
        if errorlevel 1 (
            echo Failed to create virtual environment with python -m venv.
            exit /b 1
        )
        set VENV_DIR=venv
    )
    echo Virtual environment created
    echo.
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
        pip install -e .
    )
    echo Dependencies installed
    echo.
)

REM Check if database exists
if not exist "time_tracker.db" (
    echo Initializing database...
    python -m waqtracker.scripts.init_db
    echo.
)

REM Start the application
echo Starting Flask server...
if "%PORT%"=="" set PORT=5555
echo Application will be available at: http://localhost:%PORT%
echo.
echo Press Ctrl+C to stop the server
echo.

python -m waqtracker.wsgi
