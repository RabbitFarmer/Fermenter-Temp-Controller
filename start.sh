#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Ensure Python 3.7+ is installed
if ! python3 -c 'import sys; exit(sys.version_info >= (3,7))'; then
    echo "Python 3.7 or newer is required. Please install it and try again."
    exit 1
fi

# Check port 5000 availability
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null; then
    echo "Port 5000 is already in use. Please stop the process using it or configure another port."
    exit 1
fi

# Create and activate virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "No virtual environment found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    if [ -f "requirements.txt" ]; then
        echo "Installing dependencies..."
        pip install -r requirements.txt
    fi
else
    source .venv/bin/activate
fi

# Start the Flask application with logging
python3 app.py > app.log 2>&1 &

# Wait for the app to start
sleep 3

# Open the HTTP URL in the default browser or prompt the user
if [ -n "$DISPLAY" ]; then
    if command -v xdg-open > /dev/null; then
        xdg-open http://127.0.0.1:5000   # For Linux
    elif command -v open > /dev/null; then
        open http://127.0.0.1:5000       # For macOS
    else
        echo "Please open http://127.0.0.1:5000 in your browser."
    fi
else
    echo "GUI not detected. Open http://127.0.0.1:5000 manually in your browser."
fi