#!/bin/bash
# Demo script to show tracing output

echo "=========================================================================="
echo "DEMO: Startup Tracing Feature"
echo "=========================================================================="
echo ""
echo "This demonstrates the new startup tracing capabilities added to start.sh"
echo ""

# Create a mock startup scenario
cat > mock_startup.sh << 'MOCKEOF'
#!/bin/bash

STARTUP_LOG="demo_startup.log"
exec > >(tee -a "$STARTUP_LOG") 2>&1

echo "======================================================================="
echo "Startup trace log - $(date)"
echo "======================================================================="

log_step() {
    echo "[$(date '+%H:%M:%S')] $*"
}

STARTUP_BEGIN=$(date +%s)

log_step "=== Fermenter Temp Controller Startup ==="
log_step "Startup log will be saved to: $STARTUP_LOG"
log_step "Navigating to script directory..."
sleep 0.5
log_step "Checking for virtual environment..."
sleep 0.3
log_step "Virtual environment activated."
sleep 0.5
log_step "Installing dependencies from requirements.txt..."
sleep 1
log_step "Dependencies installed successfully."
sleep 0.5
log_step "Starting the application..."
log_step "Launching app.py with nohup..."
log_step "Application started with PID 12345"
sleep 0.5
log_step "Waiting for application to respond on http://127.0.0.1:5000..."
sleep 0.5
log_step "Health check attempt 1/30..."
sleep 0.5
log_step "Health check attempt 2/30..."
sleep 0.5
log_step "Health check attempt 3/30..."
sleep 0.5

ELAPSED=$(($(date +%s) - STARTUP_BEGIN))
log_step "✓ Application is responding! (after ${ELAPSED}s)"
log_step "Opening the application in your default browser..."
log_step "Browser launched with xdg-open"

TOTAL_TIME=$(($(date +%s) - STARTUP_BEGIN))

echo "======================================================================="
log_step "✓ Startup completed successfully!"
echo "======================================================================="
echo "  Application PID: 12345"
echo "  Total startup time: ${TOTAL_TIME} seconds"
echo "  Access dashboard: http://127.0.0.1:5000"
echo "  Startup log saved: $STARTUP_LOG"
echo "  Application log: app.log"
echo "======================================================================="
echo ""
echo "To view logs:"
echo "  Startup trace: cat $STARTUP_LOG"
echo "  App log: tail -f app.log"
echo "  Debug mode: DEBUG=1 ./start.sh"
echo "======================================================================="
MOCKEOF

chmod +x mock_startup.sh

echo "1. Running mock startup (normal mode)..."
echo "----------------------------------------------------------------------"
./mock_startup.sh
echo ""

echo "2. Showing startup.log contents..."
echo "----------------------------------------------------------------------"
cat demo_startup.log
echo ""

echo "3. Key Features Demonstrated:"
echo "----------------------------------------------------------------------"
echo "  ✓ Timestamped progress messages"
echo "  ✓ All output saved to startup.log"
echo "  ✓ Process verification"
echo "  ✓ Health check monitoring"
echo "  ✓ Startup timing tracked"
echo "  ✓ Clear troubleshooting instructions"
echo ""

echo "4. Additional Features (not shown in demo):"
echo "----------------------------------------------------------------------"
echo "  ✓ DEBUG=1 mode for detailed command tracing"
echo "  ✓ Process death detection during startup"
echo "  ✓ Last lines of app.log shown on errors"
echo "  ✓ Real-time output + log file (via tee)"
echo ""

# Cleanup
rm -f mock_startup.sh demo_startup.log

echo "=========================================================================="
echo "To use the tracing feature:"
echo "=========================================================================="
echo ""
echo "  Normal startup (with logging):"
echo "    ./start.sh"
echo ""
echo "  Debug mode (detailed tracing):"
echo "    DEBUG=1 ./start.sh"
echo ""
echo "  View the log:"
echo "    cat startup.log"
echo ""
echo "  Follow startup in real-time:"
echo "    tail -f startup.log"
echo ""
echo "=========================================================================="
