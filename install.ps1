# Waqt installer script for Windows
# Usage: irm https://raw.githubusercontent.com/GMouaad/waqt/main/install.ps1 | iex
# Usage: iex "& { $(irm https://raw.githubusercontent.com/GMouaad/waqt/main/install.ps1) } -Prerelease"

param(
    [switch]$Prerelease
)

$ErrorActionPreference = "Stop"

$Repo = "GMouaad/waqt"
$InstallDir = "$env:LOCALAPPDATA\waqt"

function Write-Info { param($msg) Write-Host "==> " -ForegroundColor Green -NoNewline; Write-Host $msg }
function Write-Warn { param($msg) Write-Host "warning: " -ForegroundColor Yellow -NoNewline; Write-Host $msg }
function Write-Err { param($msg) Write-Host "error: " -ForegroundColor Red -NoNewline; Write-Host $msg; exit 1 }

if ($Prerelease) {
    Write-Info "Installing waqt (development build)..."
} else {
    Write-Info "Installing waqt..."
}

# Detect architecture
$Arch = "amd64"
if ([System.Environment]::Is64BitOperatingSystem) {
    # Check processor architecture
    $ProcessorArch = (Get-CimInstance Win32_Processor).Architecture
    # 9 = x64 (AMD64/EM64T), 12 = ARM64
    if ($ProcessorArch -eq 12) {
        $Arch = "arm64"
    }
}
Write-Info "Detected architecture: $Arch"

# Get release version
try {
    if ($Prerelease) {
        # Dev prerelease always uses 'dev' tag - no API call needed
        $Version = "dev"
        Write-Info "Development build: $Version"
    } else {
        $Release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest"
        $Version = $Release.tag_name
        Write-Info "Latest version: $Version"
    }
} catch {
    Write-Err "Could not determine latest version. Check https://github.com/$Repo/releases"
}

# Download
$Filename = "waqtracker-windows-$Arch.zip"
$Url = "https://github.com/$Repo/releases/download/$Version/$Filename"
# Resolve $env:TEMP to long path (fixes 8.3 short path issues like C:\Users\TERRY~1.ANE)
$TempBase = (Get-Item $env:TEMP).FullName
$TempDir = Join-Path $TempBase "waqt-install-$PID"
$ZipPath = Join-Path $TempDir $Filename

Write-Info "Downloading $Url..."

try {
    New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
    Invoke-WebRequest -Uri $Url -OutFile $ZipPath
} catch {
    Write-Err "Failed to download $Url. $_"
}

# Extract
Write-Info "Extracting..."
Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force

# Install
Write-Info "Installing to $InstallDir..."
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Move-Item -Path (Join-Path $TempDir "waqtracker.exe") -Destination (Join-Path $InstallDir "waqtracker.exe") -Force

# Create a batch wrapper for 'waqt' command
$WaqtBatch = @"
@echo off
"%~dp0waqtracker.exe" %*
"@
$WaqtBatch | Out-File -FilePath (Join-Path $InstallDir "waqt.cmd") -Encoding ASCII

# Cleanup
Remove-Item -Recurse -Force $TempDir

# Add to PATH
if ($env:GITHUB_ACTIONS) {
    # GitHub Actions: add to GITHUB_PATH
    Write-Info "Adding to GITHUB_PATH for this workflow..."
    $InstallDir | Out-File -FilePath $env:GITHUB_PATH -Append -Encoding utf8
    $env:Path = "$InstallDir;$env:Path"
} else {
    # Regular install: add to user PATH if not already there
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    # Split PATH and check for exact match
    $PathEntries = $UserPath -split ';' | ForEach-Object { $_.TrimEnd('\') }
    $InstallDirNormalized = $InstallDir.TrimEnd('\')
    
    if ($PathEntries -notcontains $InstallDirNormalized) {
        Write-Info "Adding $InstallDir to PATH..."
        if ($UserPath) {
            [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", "User")
        } else {
            [Environment]::SetEnvironmentVariable("Path", "$InstallDir", "User")
        }
        $env:Path = "$env:Path;$InstallDir"
    } else {
        Write-Info "Install directory is already in PATH"
    }
}

# Verify
Write-Info "Successfully installed waqt!"
& "$InstallDir\waqtracker.exe" --version

Write-Host ""
Write-Info "Installation complete! You can now use 'waqt' or 'waqtracker' commands."
Write-Host ""
Write-Host "  Quick start:"
Write-Host "    waqt --version      # Check version"
Write-Host "    waqtracker          # Start the web server (http://localhost:5555)"
Write-Host "    waqt start          # Start time tracking from CLI"
Write-Host "    waqt summary        # View summary"
Write-Host ""
Write-Host "Restart your terminal or run:" -ForegroundColor Yellow
Write-Host "  `$env:Path = [Environment]::GetEnvironmentVariable('Path', 'User')"
