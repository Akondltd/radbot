@echo off
cd /d "%~dp0"
echo Activating virtual environment and launching Radbot...

call radbot_venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment. Please run windows_setup.bat first.
    pause
    exit /b 1
)

python main.py

pause