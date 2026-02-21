#!/bin/bash

VENV_DIR="akond_rad_bot_venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "Virtual environment not found. Run ./setup.sh first."
  exit 1
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "Launching Akond Rad Bot..."

python3 main.py