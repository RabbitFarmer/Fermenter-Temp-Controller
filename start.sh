#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start the Flask application in the background
python3 app.py &

# Wait for the app to start
sleep 3

# Open the HTTP URL in the default browser
if command -v xdg-open > /dev/null; then
    xdg-open http://127.0.0.1:5000   # For Linux
elif command -v open > /dev/null; then
    open http://127.0.0.1:5000       # For macOS
else
    echo "Please open http://127.0.0.1:5000 in your browser"
fi