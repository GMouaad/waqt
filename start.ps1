# Startup script for Waqt application (PowerShell)
# Supports both uv (recommended) and pip (legacy)

Write-Host "🚀 Starting Waqt..."
Write-Host ""

# Detect if uv is available
$UV_AVAILABLE = $false
if (Get-Command uv -ErrorAction SilentlyContinue) {
    $UV_AVAILABLE = $true
    Write-Host "✨ Using uv package manager (fast mode)"
} else {
    Write-Host "📦 Using pip package manager (legacy mode)"
    Write-Host "💡 Tip: Install uv for 10-100x faster package management: https://github.com/astral-sh/uv"
}
Write-Host ""

# Determine which venv directory exists or create new one
$VENV_DIR = ""
if (Test-Path ".venv") {
    $VENV_DIR = ".venv"
}
if (Test-Path "venv") {
    if ([string]::IsNullOrEmpty($VENV_DIR)) {
        $VENV_DIR = "venv"
    }
}

# Warn if both virtual environments are present
if ((Test-Path ".venv") -and (Test-Path "venv")) {
    Write-Host "⚠️  WARNING: Both '.venv' and 'venv' directories were found."
    Write-Host "          Using '$VENV_DIR' for this session."
    Write-Host "          Consider removing the unused environment to avoid confusion."
    Write-Host ""
}

# Create virtual environment if it doesn't exist
if ([string]::IsNullOrEmpty($VENV_DIR)) {
    Write-Host "❌ Virtual environment not found!"
    Write-Host "Creating virtual environment..."
    if ($UV_AVAILABLE) {
        uv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to create virtual environment with uv."
            exit 1
        }
        $VENV_DIR = ".venv"
    } else {
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to create virtual environment with python -m venv."
            exit 1
        }
        $VENV_DIR = "venv"
    }
    Write-Host "✅ Virtual environment created"
    Write-Host ""
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
$ActivationScript = Join-Path $VENV_DIR "Scripts" "Activate.ps1"
if (Test-Path $ActivationScript) {
    . $ActivationScript
} else {
    # Fallback for non-standard or unix-like venv on Windows (sometimes happens with cross-platform tools)
    $ActivationScriptUnix = Join-Path $VENV_DIR "bin" "Activate.ps1"
    if (Test-Path $ActivationScriptUnix) {
        . $ActivationScriptUnix
    } else {
        # Manual activation if script missing
        $env:VIRTUAL_ENV = Join-Path (Get-Location) $VENV_DIR
        $env:PATH = "$env:VIRTUAL_ENV\Scripts;$env:VIRTUAL_ENV\bin;$env:PATH"
    }
}

# Check if dependencies are installed
python -c "import flask" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "📦 Installing dependencies..."
    if ($UV_AVAILABLE) {
        uv pip install -e .
    } else {
        pip install -e .
    }
    Write-Host "✅ Dependencies installed"
    Write-Host ""
}

# Start the application
Write-Host "🌐 Starting Flask server..."
if ([string]::IsNullOrEmpty($env:PORT)) {
    $env:PORT = "5555"
}
Write-Host "📍 Application will be available at: http://localhost:$env:PORT"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""

python -m waqt.wsgi
