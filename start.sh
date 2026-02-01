#!/bin/bash

echo "=== Fermenter Temp Controller Startup ==="

# Get the directory where this script is located and navigate to it
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Detect if we're running at boot time (non-interactive terminal)
# This helps us adjust wait times and retry logic appropriately
BOOT_MODE=false
if [ ! -t 0 ] && [ -z "$DISPLAY" ]; then
    BOOT_MODE=true
    echo "Detected boot-time startup (non-interactive mode)"
    echo "Will use extended timeouts for system initialization..."
fi

# Function to show desktop notification if available
show_notification() {
    local title="$1"
    local message="$2"
    local urgency="${3:-normal}"  # normal, low, or critical
    
    # Try notify-send first (most common on Linux desktop)
    if command -v notify-send > /dev/null 2>&1; then
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
    # Only run pip install if dependencies might be missing or outdated
    # This makes the script faster and more reliable at boot
    # Use --quiet to reduce output, and check if it's needed first
    echo "Checking dependencies..."
    
    # Quick check: try importing key packages to see if deps are satisfied
    if "$VENV_DIR/bin/python3" -c "import flask, bleak" 2>/dev/null; then
        echo "Dependencies already satisfied (skipping pip install)"
    else
        echo "Installing/updating dependencies from requirements.txt..."
        # Use pip with --quiet and --disable-pip-version-check to avoid warnings
        # At boot, network might not be ready yet, so we'll retry if needed
        if ! pip install --quiet --disable-pip-version-check -r requirements.txt 2>>app.log; then
            echo "WARNING: Failed to install dependencies (network may not be ready)"
            echo "         Will attempt to start anyway if packages are already installed..."
            # Check again if we can at least import the basics
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
# Use longer delay during boot to allow system services to stabilize
if [ "$BOOT_MODE" = true ]; then
    echo "Waiting for system to stabilize (boot mode)..."
    sleep 5
else
    sleep 1
fi

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
    
    # If in boot mode, show a notification
    if [ "$BOOT_MODE" = true ]; then
        show_notification "Fermenter Failed" "Application failed to start. Check terminal for details." "critical"
    fi
    
    exit 1
fi

# Wait for the application to start with retries
# Use extended timeouts during boot when system services are initializing
echo "Waiting for application to respond on http://127.0.0.1:5000..."

# Show visual notification if running at boot with display available
if [ "$BOOT_MODE" = true ]; then
    # Boot mode: longer timeout to handle system initialization delays
    # Network stack, Bluetooth, and desktop environment may still be starting
    RETRIES=60
    RETRY_DELAY=3
    echo "Using extended boot-time timeout: $((RETRIES * RETRY_DELAY)) seconds"
    
    # Show desktop notification to inform user
    show_notification "Fermenter Starting" "Please wait while the application starts (up to 3 minutes)..." "normal"
else
    # Interactive mode: standard timeout
    RETRIES=30
    RETRY_DELAY=2
fi

for i in $(seq 1 $RETRIES); do
    if curl -s http://127.0.0.1:5000 > /dev/null 2>&1; then
        echo "✓ Application is responding!"
        # Show success notification
        show_notification "Fermenter Ready" "Application is ready! Opening browser..." "normal"
        break
    fi
    if [ $((i % 10)) -eq 0 ]; then
        echo "  Still waiting... ($i/$RETRIES attempts)"
        # Show progress notification every 30 seconds in boot mode
        if [ "$BOOT_MODE" = true ]; then
            show_notification "Fermenter Starting" "Still starting... ($i/$RETRIES attempts completed)" "low"
        fi
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
# Wait for desktop environment to be ready before opening browser
# This is critical for autostart scenarios where DISPLAY may be set but
# the window manager and desktop components aren't fully initialized yet
echo "Ensuring desktop environment is ready for browser launch..."
show_notification "Fermenter Starting" "Waiting for desktop to be ready..." "low"

# Wait for DISPLAY to be set and X server to be responsive (up to 30 seconds)
# Check both DISPLAY variable and xset command to ensure X server is ready
for i in $(seq 1 30); do
    if [ -n "$DISPLAY" ] && xset q &>/dev/null; then
        echo "✓ Desktop environment is ready (DISPLAY=$DISPLAY, X server responding)"
        break
    fi
    if [ $((i % 5)) -eq 0 ]; then
        echo "  Still waiting for desktop... ($i/30 seconds)"
    fi
    sleep 1
done

# Additional delay to ensure window manager and browser are ready
# This is especially important for autostart where services start in parallel
if [ "$BOOT_MODE" = true ]; then
    # Longer delay during boot when many services are starting
    echo "Allowing extra time for window manager initialization (boot mode)..."
    sleep 5
else
    # Shorter delay for manual runs, but still give WM time to stabilize
    echo "Allowing window manager to stabilize..."
    sleep 2
fi

echo "Opening the application in your default browser..."
BROWSER_OPENED=false
# Create secure temporary file for error logging
BROWSER_ERROR_LOG=$(mktemp /tmp/fermenter_browser_error.XXXXXX)

if command -v xdg-open > /dev/null; then
    echo "  Using xdg-open to launch browser..."
    # Try to open browser and capture any errors
    if xdg-open http://127.0.0.1:5000 2>"$BROWSER_ERROR_LOG" &
    then
        echo "✓ Browser command executed successfully"
        BROWSER_OPENED=true
        # Attempt to send F11 for fullscreen mode if xdotool is available
        if command -v xdotool > /dev/null; then
            echo "  Attempting to set fullscreen mode..."
            # Give browser time to open and become the active window
            sleep 3
            # Try to find and activate the browser window, then send F11
            # This is best-effort; if it fails, the browser opens normally
            if xdotool search --class --sync "chromium|firefox|chrome" windowactivate --sync key F11 2>/dev/null; then
                echo "✓ Fullscreen mode activated"
            else
                # Fallback: just send F11 to active window
                xdotool key F11 2>/dev/null || true
                echo "  (Fullscreen mode attempted - may not have worked)"
            fi
        fi
    else
        echo "⚠️  Warning: xdg-open command failed"
        if [ -f "$BROWSER_ERROR_LOG" ] && [ -s "$BROWSER_ERROR_LOG" ]; then
            echo "  Error details:"
            cat "$BROWSER_ERROR_LOG"
        fi
    fi
elif command -v open > /dev/null; then
    echo "  Using open to launch browser (macOS)..."
    # Try to open browser and capture any errors (macOS)
    if open http://127.0.0.1:5000 2>"$BROWSER_ERROR_LOG"
    then
        echo "✓ Browser command executed successfully"
        BROWSER_OPENED=true
    else
        echo "⚠️  Warning: open command failed"
        if [ -f "$BROWSER_ERROR_LOG" ] && [ -s "$BROWSER_ERROR_LOG" ]; then
            echo "  Error details:"
            cat "$BROWSER_ERROR_LOG"
        fi
    fi
else
    echo "⚠️  No browser command found (xdg-open/open not available)"
fi

# Clean up temporary error log
rm -f "$BROWSER_ERROR_LOG"

# Show final status
if [ "$BROWSER_OPENED" = true ]; then
    show_notification "Fermenter Ready" "Browser opened successfully!" "normal"
else
    echo ""
    echo "=========================================="
    echo "⚠️  BROWSER DID NOT OPEN AUTOMATICALLY"
    echo "=========================================="
    echo "Please open http://127.0.0.1:5000 manually in your browser."
    echo ""
    show_notification "Fermenter Ready" "Please open browser manually to 127.0.0.1:5000" "normal"
fi

echo "======================================================================="
echo "✓ Startup completed successfully!"
echo "======================================================================="
echo "  Application PID: $APP_PID"
echo "  Access dashboard: http://127.0.0.1:5000"
echo "  Application log: app.log"
echo "======================================================================="

# If browser didn't open automatically, keep terminal open for user to see instructions
if [ "$BROWSER_OPENED" != true ]; then
    echo ""
    echo "Terminal will remain open. Close this window after you've opened the browser."
    echo "Press Ctrl+C or close this window when done."
    # Keep the script running so terminal stays open
    # No timeout - let user close when ready
    read -p "Press Enter to close this terminal..." || true
else
    # Browser opened successfully - brief pause to let user see success message
    echo ""
    echo "This terminal will close in 5 seconds..."
    sleep 5
fi