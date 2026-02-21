@echo off
setlocal

REM --- Check for Python 3.11 installation ---
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.11 is not installed or not registered with py launcher.
    echo Please install Python 3.11 from https://www.python.org/downloads/windows/
    pause
    exit /b 1
)

REM --- Create venv if it does not exist ---
if not exist venv311 (
    echo Creating Python 3.11 virtual environment...
    py -3.11 -m venv venv311
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment 'venv311' already exists.
)

REM --- Activate virtual environment ---
call venv311\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM --- Check Python version inside venv ---
python --version

REM --- Upgrade pip ---
python -m pip install --upgrade pip

REM --- Install all requirements ---
REM Prefer hash-locked requirements for security (verifies package integrity)
if exist requirements-hashed.txt (
    echo Installing dependencies from requirements-hashed.txt with hash verification...
    pip install --require-hashes -r requirements-hashed.txt
    if errorlevel 1 (
        echo Hash-verified install failed. Falling back to regular requirements...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo Failed to install some dependencies.
            pause
            exit /b 1
        )
    )
) else if exist requirements.txt (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install some dependencies.
        pause
        exit /b 1
    )
) else (
    echo No requirements file found, skipping dependency installation.
)

REM Ensure logs directory exists
if not exist logs mkdir logs

REM Run your main app and capture output and errors
echo Running main.py ...
set QT_DEBUG_PLUGINS=1
set QT_OPENGL=software
python main.py > logs\app_output.log 2>&1

echo Application exited. See logs\ directory for details.
pause