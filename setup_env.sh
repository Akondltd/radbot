#!/bin/bash

# Setup script for Akond Rad Bot environment (Linux)

echo "Starting environment setup for Akond Rad Bot..."

# Check Python version (Python 3.8+ recommended)
if ! command -v python3 &>/dev/null; then
    echo "Python3 is not installed. Please install Python 3.8 or newer."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(sys.version_info[:])")
echo "Detected Python version: $PYTHON_VERSION"

# Create virtual environment directory
VENV_DIR="akond_rad_bot_venv"

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
echo "To activate the environment later, run: source $VENV_DIR/bin/activate"
