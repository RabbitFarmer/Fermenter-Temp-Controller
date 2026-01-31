#!/bin/bash

echo "=== Fermenter Temp Controller Startup ==="

# Get the directory where this script is located and navigate to it
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Detect or create virtual environment (supports both .venv and venv)
echo "Checking for virtual environment..."
VENV_DIR=""

if [ -d ".venv" ]; then
    VENV_DIR=".venv"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
else
    # No venv found, create .venv as default
    VENV_DIR=".venv"
    echo "No virtual environment found. Creating .venv..."
    if ! python3 -m venv "$VENV_DIR"; then
        echo "ERROR: Failed to create a virtual environment. Exiting."
        exit 1
    fi
    echo "Virtual environment created successfully at $VENV_DIR"
fi

echo "Activating virtual environment ($VENV_DIR)..."
source "$VENV_DIR/bin/activate"
echo "Virtual environment activated."

# Install dependencies if 'requirements.txt' exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    if ! pip install -r requirements.txt; then
        echo "ERROR: Failed to install dependencies. Exiting."
        exit 1
    fi
    echo "Dependencies installed successfully."
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

# Give the app a moment to initialize
sleep 1

# Check if process is still running
if ! ps -p $APP_PID > /dev/null 2>&1; then
    echo "ERROR: Application process $APP_PID died immediately after launch!"
    echo "Last 20 lines of app.log:"
    tail -20 app.log 2>/dev/null || echo "  (no log file yet)"
    exit 1
fi

# Wait for the application to start with retries
echo "Waiting for application to respond on http://127.0.0.1:5000..."
RETRIES=30
RETRY_DELAY=2
for i in $(seq 1 $RETRIES); do
    if curl -s http://127.0.0.1:5000 > /dev/null 2>&1; then
        echo "✓ Application is responding!"
        break
    fi
    sleep $RETRY_DELAY
done

if ! curl -s http://127.0.0.1:5000 > /dev/null 2>&1; then
    echo "WARNING: Application did not respond after $((RETRIES * RETRY_DELAY)) seconds"
    echo "The application is still starting in the background (PID $APP_PID)."
    echo "Check app.log for errors: tail -f app.log"
    exit 0
fi

# Open the application in the default web browser in fullscreen
echo "Opening the application in your default browser..."
if command -v xdg-open > /dev/null; then
    # Use nohup and run in subshell to completely detach from script
    (nohup xdg-open http://127.0.0.1:5000 </dev/null >/dev/null 2>&1 &)
    # Attempt to send F11 for fullscreen mode if xdotool is available
    if command -v xdotool > /dev/null; then
        # Give browser time to open and become the active window
        sleep 3
        # Try to find and activate the browser window, then send F11
        # This is best-effort; if it fails, the browser opens normally
        xdotool search --class --sync "chromium|firefox|chrome" windowactivate --sync key F11 2>/dev/null || \
        xdotool key F11 2>/dev/null || true
    fi
    echo "Browser launched"
elif command -v open > /dev/null; then
    # Use nohup and run in subshell to completely detach from script (macOS)
    (nohup open http://127.0.0.1:5000 </dev/null >/dev/null 2>&1 &)
    echo "Browser launched"
else
    echo "No browser command found (xdg-open/open)"
    echo "Please open http://127.0.0.1:5000 in your browser manually."
fi

echo "======================================================================="
echo "✓ Startup completed successfully!"
echo "======================================================================="
echo "  Application PID: $APP_PID"
echo "  Access dashboard: http://127.0.0.1:5000"
echo "  Application log: app.log"
echo "======================================================================="