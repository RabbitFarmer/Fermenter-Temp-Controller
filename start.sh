#!/bin/bash

# Startup log file
STARTUP_LOG="startup.log"

# Redirect all output to both terminal and log file
exec > >(tee -a "$STARTUP_LOG") 2>&1

echo "======================================================================="
echo "Startup trace log - $(date)"
echo "======================================================================="

# Enable debug tracing if DEBUG environment variable is set
# Usage: DEBUG=1 ./start.sh
# To enable Flask debug mode (with Werkzeug reloader): FLASK_DEBUG=1 ./start.sh
if [ "${DEBUG:-0}" = "1" ]; then
    set -x  # Print each command before executing
    echo "[DEBUG] Debug mode enabled - all commands will be traced"
fi

# Function to print timestamped debug messages
debug_log() {
    if [ "${DEBUG:-0}" = "1" ]; then
        echo "[DEBUG $(date '+%Y-%m-%d %H:%M:%S')] $*"
    fi
}

# Function to print timestamped progress messages
log_step() {
    echo "[$(date '+%H:%M:%S')] $*"
}

# Track startup time
STARTUP_BEGIN=$(date +%s)

log_step "=== Fermenter Temp Controller Startup ==="
log_step "Startup log will be saved to: $STARTUP_LOG"
debug_log "Script: $0"
debug_log "Working directory: $(pwd)"

# Get the directory where this script is located and navigate to it
log_step "Navigating to script directory..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
debug_log "Script directory: $SCRIPT_DIR"
cd "$SCRIPT_DIR"
debug_log "Current directory: $(pwd)"

# Create and activate virtual environment if missing
log_step "Checking for virtual environment..."
if [ ! -d ".venv" ]; then
    log_step "No virtual environment found. Creating one..."
    debug_log "Running: python3 -m venv .venv"
    if ! python3 -m venv .venv; then
        echo "[ERROR] Failed to create a virtual environment. Exiting."
        exit 1
    fi
    log_step "Virtual environment created successfully."
else
    debug_log "Virtual environment already exists at .venv"
fi

log_step "Activating virtual environment..."
debug_log "Sourcing .venv/bin/activate"
source .venv/bin/activate
log_step "Virtual environment activated."
debug_log "Python path: $(which python3)"
debug_log "Python version: $(python3 --version)"

# Install dependencies if 'requirements.txt' exists
if [ -f "requirements.txt" ]; then
    log_step "Installing dependencies from requirements.txt..."
    debug_log "Pip version: $(pip --version)"
    if ! pip install -r requirements.txt; then
        echo "[ERROR] Failed to install dependencies. Exiting."
        exit 1
    fi
    log_step "Dependencies installed successfully."
else
    log_step "Warning: requirements.txt not found. Skipping dependency installation."
fi

# Start the application in the background and log output
log_step "Starting the application..."
# Set environment variable to prevent app.py from opening browser (start.sh will do it)
# Use nohup to ensure the app continues running even if this script exits
# Get the full path to python3 in the venv to ensure it works after script exits
PYTHON_PATH="$(which python3)"
debug_log "Python path for app: $PYTHON_PATH"
debug_log "Setting SKIP_BROWSER_OPEN=1"
export SKIP_BROWSER_OPEN=1

log_step "Launching app.py with nohup..."
debug_log "Command: nohup $PYTHON_PATH app.py > app.log 2>&1 &"
nohup "$PYTHON_PATH" app.py > app.log 2>&1 &
APP_PID=$!

# Also disown the process to fully detach from the shell
# Use -h flag to mark job as non-SIGHUP without removing from job table (more robust)
disown -h $APP_PID 2>/dev/null || true

log_step "Application started with PID $APP_PID"
debug_log "Process status:"
if [ "${DEBUG:-0}" = "1" ]; then
    ps -p $APP_PID -o pid,ppid,stat,cmd 2>/dev/null || echo "  Process not found (may have exited immediately)"
fi

# Give the app a moment to initialize
sleep 1

# Check if process is still running
if ! ps -p $APP_PID > /dev/null 2>&1; then
    echo "[ERROR] Application process $APP_PID died immediately after launch!"
    echo "[ERROR] Last 20 lines of app.log:"
    tail -20 app.log 2>/dev/null || echo "  (no log file yet)"
    exit 1
fi
debug_log "Process $APP_PID is running"

# Wait for the application to start with retries
log_step "Waiting for application to respond on http://127.0.0.1:5000..."
RETRIES=30
RETRY_DELAY=2
for i in $(seq 1 $RETRIES); do
    log_step "Health check attempt $i/$RETRIES..."
    debug_log "Running: curl -s http://127.0.0.1:5000"
    
    if curl -s http://127.0.0.1:5000 > /dev/null 2>&1; then
        ELAPSED=$(($(date +%s) - STARTUP_BEGIN))
        log_step "✓ Application is responding! (after ${ELAPSED}s)"
        break
    fi
    
    # Note: We don't check if the original PID is alive because Flask debug mode
    # uses Werkzeug reloader which forks a child process, causing the original PID
    # to exit. The HTTP health check above is sufficient to verify the app is running.
    
    debug_log "App not ready yet, waiting for HTTP response. Waiting ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
done

if ! curl -s http://127.0.0.1:5000 > /dev/null 2>&1; then
    ELAPSED=$(($(date +%s) - STARTUP_BEGIN))
    echo "======================================================================="
    echo "[WARNING] Application did not respond after $((RETRIES * RETRY_DELAY)) seconds (${ELAPSED}s elapsed)"
    echo "======================================================================="
    echo "The application is still starting in the background (PID $APP_PID)."
    echo ""
    echo "Process status:"
    ps -p $APP_PID -o pid,ppid,stat,etime,cmd 2>/dev/null || echo "  Process not found!"
    echo ""
    echo "Last 20 lines of app.log:"
    tail -20 app.log 2>/dev/null || echo "  (no log file yet)"
    echo ""
    echo "======================================================================="
    echo "TROUBLESHOOTING:"
    echo "  - Check app.log for errors: tail -f app.log"
    echo "  - Check startup log: cat $STARTUP_LOG"
    echo "  - Test if app responds: curl http://127.0.0.1:5000"
    echo "  - Check process: ps -p $APP_PID"
    echo "  - Try with shell tracing: DEBUG=1 ./start.sh"
    echo "  - Try with Flask debug: FLASK_DEBUG=1 ./start.sh"
    echo "  - Manually open browser: http://127.0.0.1:5000"
    echo "======================================================================="
    exit 0
fi

# Open the application in the default web browser
log_step "Opening the application in your default browser..."
debug_log "Checking for browser commands..."
if command -v xdg-open > /dev/null; then
    debug_log "Using xdg-open (Linux)"
    # Use nohup and run in subshell to completely detach from script
    (nohup xdg-open http://127.0.0.1:5000 </dev/null >/dev/null 2>&1 &)
    log_step "Browser launched with xdg-open"
elif command -v open > /dev/null; then
    debug_log "Using open (macOS)"
    # Use nohup and run in subshell to completely detach from script (macOS)
    (nohup open http://127.0.0.1:5000 </dev/null >/dev/null 2>&1 &)
    log_step "Browser launched with open"
else
    log_step "No browser command found (xdg-open/open)"
    echo "Please open http://127.0.0.1:5000 in your browser manually."
fi

STARTUP_END=$(date +%s)
TOTAL_TIME=$((STARTUP_END - STARTUP_BEGIN))

echo "======================================================================="
log_step "✓ Startup completed successfully!"
echo "======================================================================="
echo "  Application PID: $APP_PID"
echo "  Total startup time: ${TOTAL_TIME} seconds"
echo "  Access dashboard: http://127.0.0.1:5000"
echo "  Startup log saved: $STARTUP_LOG"
echo "  Application log: app.log"
echo "======================================================================="
echo ""
echo "To view logs:"
echo "  Startup trace: cat $STARTUP_LOG"
echo "  App log: tail -f app.log"
echo ""
echo "Debug options:"
echo "  Shell tracing: DEBUG=1 ./start.sh"
echo "  Flask debug mode: FLASK_DEBUG=1 ./start.sh"
echo "======================================================================="