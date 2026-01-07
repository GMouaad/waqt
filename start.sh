#!/bin/bash
# Startup script for Time Tracker application
# Supports both uv (recommended) and pip (legacy)

echo "🚀 Starting Time Tracker..."
echo ""

# Detect if uv is available
UV_AVAILABLE=false
if command -v uv &> /dev/null; then
    UV_AVAILABLE=true
    echo "✨ Using uv package manager (fast mode)"
else
    echo "📦 Using pip package manager (legacy mode)"
    echo "💡 Tip: Install uv for 10-100x faster package management: https://github.com/astral-sh/uv"
fi
echo ""

# Function to determine venv directory
get_venv_dir() {
    if [ -d ".venv" ]; then
        echo ".venv"
    elif [ -d "venv" ]; then
        echo "venv"
    else
        echo ""
    fi
}

# Check if virtual environment exists
VENV_DIR=$(get_venv_dir)
if [ -z "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    if [ "$UV_AVAILABLE" = true ]; then
        if ! uv venv; then
            echo "❌ Failed to create virtual environment using uv"
            exit 1
        fi
        VENV_DIR=".venv"
    else
        if ! python -m venv venv; then
            echo "❌ Failed to create virtual environment using python -m venv"
            exit 1
        fi
        VENV_DIR="venv"
    fi
    echo "✅ Virtual environment created"
    echo ""
else
    # Warn if both venv directories exist
    if [ -d ".venv" ] && [ -d "venv" ]; then
        echo "⚠️  WARNING: Both .venv and venv directories found."
        echo "    Using $VENV_DIR for this session."
        echo "    Consider removing the unused environment to avoid confusion."
        echo ""
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Check if dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    if [ "$UV_AVAILABLE" = true ]; then
        uv pip install -e .
    else
        pip install -r requirements.txt
    fi
    echo "✅ Dependencies installed"
    echo ""
fi

# Check if database exists
if [ ! -f "time_tracker.db" ]; then
    echo "🗄️  Initializing database..."
    python init_db.py
    echo ""
fi

# Start the application
echo "🌐 Starting Flask server..."
port=${PORT:-5555}
echo "📍 Application will be available at: http://localhost:$port"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python run.py
