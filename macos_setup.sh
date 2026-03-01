#!/bin/bash
# macos_setup.sh - Environment setup script for Radbot on macOS/Linux
cd "$(dirname "$0")"

echo "Starting environment setup for Radbot..."

# Attempt to detect python3 or python command
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Python is not installed or not found in PATH. Please install Python 3.11 or newer."
    exit 1
fi

# Verify Python version >= 3.11
PY_VER=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    echo "Python $PY_VER detected but Radbot requires Python 3.11 or newer."
    exit 1
fi
echo "Detected Python $PY_VER"

# Create virtual environment directory
VENV_DIR="radbot_venv"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment directory '$VENV_DIR' already exists. Skipping creation."
else
    echo "Creating Python virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip

echo "Installing required Python packages..."
$PYTHON_CMD -m pip install -r requirements.txt

echo ""
echo "Environment setup complete."
echo "To launch Radbot, run: ./macos_launch.sh"
