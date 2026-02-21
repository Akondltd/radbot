# setup_env.ps1 - Updated environment setup script for Akond Rad Bot on Windows
Set-Location -Path (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)

Write-Host "Starting environment setup for Akond Rad Bot..."

# Attempt to detect python or python3 command
$python = Get-Command python -ErrorAction SilentlyContinue
$python3 = Get-Command python3 -ErrorAction SilentlyContinue

if ($python) {
    $pythonCmd = 'python'
} elseif ($python3) {
    $pythonCmd = 'python3'
} else {
    Write-Host "Python is not installed or not found in PATH. Please install Python 3.8 or newer." -ForegroundColor Red
    exit 1
}

# Create virtual environment directory
$venvDir = "akond_rad_bot_venv"

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

Write-Host "Environment setup complete."
Write-Host "To activate the environment later, double click the windows_launch.bat file."

if ($Host.Name -eq 'ConsoleHost') {
    Read-Host -Prompt "Press Enter to exit setup"
}