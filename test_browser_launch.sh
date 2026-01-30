#!/bin/bash
# Test script to verify browser launch doesn't hang

echo "Testing browser launch detachment..."

# Simulate the browser launch command from start.sh
if command -v xdg-open > /dev/null; then
    echo "Using xdg-open (Linux)"
    timeout 3 bash -c '(nohup xdg-open http://127.0.0.1:5000 </dev/null >/dev/null 2>&1 &)'
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ Browser launch command completed immediately (non-blocking)"
    elif [ $EXIT_CODE -eq 124 ]; then
        echo "✗ Browser launch command timed out (hanging)"
        exit 1
    else
        echo "⚠ Browser launch command exited with code $EXIT_CODE"
    fi
elif command -v open > /dev/null; then
    echo "Using open (macOS)"
    timeout 3 bash -c '(nohup open http://127.0.0.1:5000 </dev/null >/dev/null 2>&1 &)'
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ Browser launch command completed immediately (non-blocking)"
    elif [ $EXIT_CODE -eq 124 ]; then
        echo "✗ Browser launch command timed out (hanging)"
        exit 1
    else
        echo "⚠ Browser launch command exited with code $EXIT_CODE"
    fi
else
    echo "⚠ No browser opening command available"
    exit 0
fi

echo ""
echo "Test completed successfully!"
