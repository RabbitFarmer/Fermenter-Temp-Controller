#!/bin/bash

# Get the directory where this script is located and navigate to it
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create and activate virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "No virtual environment found. Creating one..."
    if ! python3 -m venv .venv; then
        echo "Failed to create a virtual environment. Exiting."
        exit 1
    fi
fi

source .venv/bin/activate
echo "Virtual environment activated."

# Install dependencies if 'requirements.txt' exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    if ! pip install -r requirements.txt; then
        echo "Failed to install dependencies. Exiting."
        exit 1
    fi
else
    echo "Warning: requirements.txt not found. Skipping dependency installation."
fi

# Start the application in the background and log output
echo "Starting the application..."
# Set environment variable to prevent app.py from opening browser (start.sh will do it)
# Use nohup to ensure the app continues running even if this script exits
# Get the full path to python3 in the venv to ensure it works after script exits
PYTHON_PATH="$(which python3)"
export SKIP_BROWSER_OPEN=1
nohup "$PYTHON_PATH" app.py > app.log 2>&1 &
APP_PID=$!
# Also disown the process to fully detach from the shell
# Use -h flag to mark job as non-SIGHUP without removing from job table (more robust)
disown -h $APP_PID 2>/dev/null || true
echo "Application started with PID $APP_PID"

# Wait for the application to start with retries
RETRIES=30
for i in $(seq 1 $RETRIES); do
    echo "Checking if the application is running... Attempt $i/$RETRIES"
    if curl -s http://127.0.0.1:5000 > /dev/null; then
        echo "The application is running!"
        break
    fi
    sleep 2
done

if ! curl -s http://127.0.0.1:5000 > /dev/null; then
    echo "Warning: The application did not respond after $((RETRIES * 2)) seconds."
    echo "The application is still starting in the background (PID $APP_PID)."
    echo "You can check app.log for startup progress."
    echo "Please manually open http://127.0.0.1:5000 in your browser once it's ready."
    echo ""
    echo "To check if the app is running: curl http://127.0.0.1:5000"
    echo "To view logs: tail -f app.log"
    exit 0
fi

# Open the application in the default web browser
echo "Opening the application in your default browser..."
if command -v xdg-open > /dev/null; then
    # Use nohup and run in subshell to completely detach from script
    (nohup xdg-open http://127.0.0.1:5000 </dev/null >/dev/null 2>&1 &)
elif command -v open > /dev/null; then
    # Use nohup and run in subshell to completely detach from script (macOS)
    (nohup open http://127.0.0.1:5000 </dev/null >/dev/null 2>&1 &)
else
    echo "Please open http://127.0.0.1:5000 in your browser manually."
fi

echo "The application is now running."
echo "Access the dashboard at: http://127.0.0.1:5000"