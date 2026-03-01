#!/bin/bash
# macos_launch.sh - Launch script for Radbot on macOS/Linux
cd "$(dirname "$0")"

echo "Activating virtual environment and launching Radbot..."

VENV_DIR="radbot_venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Please run ./macos_setup.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment. Please run ./macos_setup.sh first."
    exit 1
fi

python main.py
