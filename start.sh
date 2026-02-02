#!/bin/bash

echo "=== Fermenter Temp Controller Startup ==="

# Get the directory where this script is located and navigate to it
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to show desktop notification if available
show_notification() {
    local title="$1"
    local message="$2"
    local urgency="${3:-normal}"  # normal, low, or critical
    
    # Try notify-send if desktop environment is available
    if [ -n "$DISPLAY" ] && command -v notify-send > /dev/null 2>&1; then
        notify-send -u "$urgency" "$title" "$message" 2>/dev/null || true
    fi
}

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

# Suppress pip upgrade warnings to avoid clutter and delays
export PIP_DISABLE_PIP_VERSION_CHECK=1

# Install dependencies if 'requirements.txt' exists
if [ -f "requirements.txt" ]; then
    echo "Checking dependencies..."
    
    # Quick check: try importing key packages to see if deps are satisfied
    if "$VENV_DIR/bin/python3" -c "import flask, bleak" 2>/dev/null; then
        echo "Dependencies already satisfied (skipping pip install)"
    else
        echo "Installing/updating dependencies from requirements.txt..."
        if ! pip install --quiet --disable-pip-version-check -r requirements.txt 2>>app.log; then
            echo "WARNING: Failed to install dependencies (network may not be ready)"
            echo "         Will attempt to start anyway if packages are already installed..."
            if ! "$VENV_DIR/bin/python3" -c "import flask" 2>/dev/null; then
                echo "ERROR: Flask not available. Cannot start application."
                echo "       Please run ./start.sh manually after boot completes."
                exit 1
            fi
        else
            echo "Dependencies installed successfully."
        fi
    fi
else
    echo "Warning: requirements.txt not found. Skipping dependency installation."
fi

# Start the application in the background and log output
echo "Starting the application..."
# Get the full path to python3 in the venv to ensure it works after script exits
PYTHON_PATH="$(which python3)"

# Don't set SKIP_BROWSER_OPEN - let the script handle browser opening
nohup "$PYTHON_PATH" app.py > app.log 2>&1 &
APP_PID=$!

# Also disown the process to fully detach from the shell
disown -h $APP_PID 2>/dev/null || true

echo "Application started with PID $APP_PID"

# Give the app a moment to initialize
sleep 2

# Check if process is still running
if ! ps -p $APP_PID > /dev/null 2>&1; then
    echo "=========================================="
    echo "ERROR: Application process $APP_PID died immediately after launch!"
    echo "=========================================="
    echo ""
    echo "This usually means:"
    echo "  1. Python dependencies are missing"
    echo "  2. There's a syntax error in app.py"
    echo "  3. A required service (Bluetooth) is not ready"
    echo ""
    echo "Last 30 lines of app.log:"
    tail -30 app.log 2>/dev/null || echo "  (no log file yet)"
    echo ""
    echo "=========================================="
    echo "To diagnose: cat app.log"
    echo "To test manually: ./start.sh"
    echo "=========================================="
    
    show_notification "Fermenter Failed" "Application failed to start. Check terminal for details." "critical"
    
    exit 1
fi

# Wait for the application to respond
echo "Waiting for application to respond on http://127.0.0.1:5000..."

RETRIES=30
RETRY_DELAY=2

for i in $(seq 1 $RETRIES); do
    if curl -s http://127.0.0.1:5000 > /dev/null 2>&1; then
        echo "✓ Application is responding!"
        show_notification "Fermenter Ready" "Application is ready!" "normal"
        break
    fi
    if [ $((i % 10)) -eq 0 ]; then
        echo "  Still waiting... ($i/$RETRIES attempts)"
    fi
    sleep $RETRY_DELAY
done

if ! curl -s http://127.0.0.1:5000 > /dev/null 2>&1; then
    echo "WARNING: Application did not respond after $((RETRIES * RETRY_DELAY)) seconds"
    echo "The application is still starting in the background (PID $APP_PID)."
    echo "Check app.log for errors: tail -f app.log"
    # Continue anyway - the app might still start
fi

# Try to open browser if display is available
# This section only runs if we have a desktop environment
BROWSER_OPENED=false

if [ -n "$DISPLAY" ]; then
    echo "Display detected ($DISPLAY), attempting to open browser..."
    
    # Wait for X server to be ready (up to 60 seconds)
    echo "Waiting for X server to be ready..."
    for i in $(seq 1 60); do
        if xset q &>/dev/null 2>&1; then
            echo "✓ X server is ready"
            break
        fi
        if [ $((i % 10)) -eq 0 ]; then
            echo "  Still waiting for X server... ($i/60 seconds)"
        fi
        sleep 1
    done
    
    # Additional delay for window manager
    echo "Waiting for window manager..."
    sleep 3
    
    # Try to open browser
    if command -v xdg-open > /dev/null 2>&1; then
        echo "Opening browser with xdg-open..."
        if xdg-open http://127.0.0.1:5000 &>/dev/null &; then
            echo "✓ Browser command executed"
            BROWSER_OPENED=true
            show_notification "Fermenter Ready" "Browser opened successfully!" "normal"
            
            # Try to set fullscreen if xdotool is available
            if command -v xdotool > /dev/null 2>&1; then
                sleep 3  # Give browser time to open
                xdotool search --class --sync "chromium|firefox|chrome" windowactivate --sync key F11 &>/dev/null || true
            fi
        fi
    elif command -v open > /dev/null 2>&1; then
        echo "Opening browser with open (macOS)..."
        if open http://127.0.0.1:5000 2>/dev/null; then
            echo "✓ Browser command executed"
            BROWSER_OPENED=true
            show_notification "Fermenter Ready" "Browser opened successfully!" "normal"
        fi
    fi
    
    if [ "$BROWSER_OPENED" = false ]; then
        echo "⚠️  Could not open browser automatically"
    fi
else
    echo "No display detected - running in headless mode"
fi

echo "======================================================================="
echo "✓ Startup completed successfully!"
echo "======================================================================="
echo "  Application PID: $APP_PID"
echo "  Access dashboard: http://127.0.0.1:5000"
echo "  Application log: app.log"
if [ "$BROWSER_OPENED" = false ]; then
    echo ""
    echo "  Browser did not open automatically."
    echo "  Please open http://127.0.0.1:5000 manually in your browser."
fi
echo "======================================================================="