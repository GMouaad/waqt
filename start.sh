#!/bin/bash
# Startup script for Time Tracker application

echo "🚀 Starting Time Tracker..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
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
echo "📍 Application will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python run.py
