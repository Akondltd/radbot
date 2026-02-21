@echo off
cd /d "%~dp0"
echo Activating virtual environment and launching Akond Rad Bot...

call akond_rad_bot_venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment. Please run windows_setup.bat first.
    pause
    exit /b 1
)

python main.py

pause