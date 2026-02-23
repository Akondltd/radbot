#!/bin/bash

# Setup script for Radbot environment (Linux / macOS)

echo "Starting environment setup for Radbot..."

# Check Python is installed
if ! command -v python3 &>/dev/null; then
    echo "Python3 is not installed. Please install Python 3.11 or newer."
    exit 1
fi

# Verify Python version >= 3.11
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
    echo "Python $PYTHON_VERSION detected but Radbot requires Python 3.11 or newer."
    exit 1
fi
echo "Detected Python $PYTHON_VERSION"

# Create virtual environment directory
VENV_DIR="radbot_venv"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment directory '$VENV_DIR' already exists. Skipping creation."
else
    echo "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing required Python packages..."
pip install -r requirements.txt

echo "Environment setup complete."
echo "To launch Radbot, run: ./linux_launch.sh"
