# setup_env.ps1 - Environment setup script for Radbot on Windows
Set-Location -Path (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)

Write-Host "Starting environment setup for Radbot..."

# Attempt to detect python or python3 command
$python = Get-Command python -ErrorAction SilentlyContinue
$python3 = Get-Command python3 -ErrorAction SilentlyContinue

if ($python) {
    $pythonCmd = 'python'
} elseif ($python3) {
    $pythonCmd = 'python3'
} else {
    Write-Host "Python is not installed or not found in PATH. Please install Python 3.11 or newer." -ForegroundColor Red
    exit 1
}

# Verify Python version >= 3.11
$pyVer = & $pythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pyVer -lt [version]'3.11') {
    Write-Host "Python $pyVer detected but Radbot requires Python 3.11 or newer." -ForegroundColor Red
    exit 1
}
Write-Host "Detected Python $pyVer" -ForegroundColor Green

# Create virtual environment directory
$venvDir = "radbot_venv"

if (Test-Path $venvDir) {
    Write-Host "Virtual environment directory '$venvDir' already exists. Skipping creation." -ForegroundColor Yellow
} else {
    Write-Host "Creating Python virtual environment..."
    & $pythonCmd -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Activating virtual environment..."
& "$venvDir\Scripts\Activate.ps1"

Write-Host "Upgrading pip..."
& $pythonCmd -m pip install --upgrade pip

Write-Host "Installing required Python packages..."
& $pythonCmd -m pip install -r requirements.txt

Write-Host "Environment setup complete." -ForegroundColor Green
Write-Host "To launch Radbot, double click windows_launch.bat"

if ($Host.Name -eq 'ConsoleHost') {
    Read-Host -Prompt "Press Enter to exit setup"
}