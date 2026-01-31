#!/bin/bash
# Test script to verify the browser autostart fix works correctly
# This verifies the fix for Flask debug mode PID fork issue

set -e

echo "Testing browser autostart fix (Flask debug mode PID issue)..."
echo

# Test 1: Verify the PID check has been removed from start.sh
echo "Test 1: Verifying PID death check has been removed..."

# Check if the problematic PID check has been removed
if grep -q "Application process.*died during startup" start.sh; then
    echo "✗ Test 1 FAILED: Old PID check code still present in start.sh"
    echo "  This will cause the script to exit when Flask debug mode forks"
    exit 1
else
    echo "✓ Test 1 PASSED: PID death check removed from health check loop"
fi
echo

# Test 2: Verify explanatory comment is present
echo "Test 2: Verifying explanatory comment about Flask debug mode..."
if grep -q "Werkzeug reloader" start.sh; then
    echo "✓ Test 2 PASSED: Explanatory comment found"
else
    echo "⚠ Test 2 WARNING: Explanatory comment not found (not critical)"
fi
echo

# Test 3: Verify start.sh syntax is valid
echo "Test 3: Verifying start.sh syntax..."
if bash -n start.sh; then
    echo "✓ Test 3 PASSED: start.sh syntax is valid"
else
    echo "✗ Test 3 FAILED: start.sh has syntax errors"
    exit 1
fi
echo

# Test 4: Verify HTTP health check is still present
echo "Test 4: Verifying HTTP health check is present..."
if grep -q "curl -s http://127.0.0.1:5000" start.sh; then
    echo "✓ Test 4 PASSED: HTTP health check is present"
else
    echo "✗ Test 4 FAILED: HTTP health check missing!"
    exit 1
fi
echo

# Test 5: Verify browser opening logic is still present
echo "Test 5: Verifying browser opening logic..."
if grep -q "xdg-open" start.sh; then
    echo "✓ Test 5 PASSED: Browser opening logic is present"
else
    echo "✗ Test 5 FAILED: Browser opening logic missing!"
    exit 1
fi
echo

# Test 6: Verify SKIP_BROWSER_OPEN is set in start.sh
echo "Test 6: Verifying SKIP_BROWSER_OPEN is set in start.sh..."
if grep -q "SKIP_BROWSER_OPEN=1" start.sh; then
    echo "✓ Test 6 PASSED: start.sh correctly sets SKIP_BROWSER_OPEN=1"
else
    echo "✗ Test 6 FAILED: SKIP_BROWSER_OPEN not found in start.sh"
    exit 1
fi
echo

echo "=========================================="
echo "✓ ALL TESTS PASSED!"
echo "=========================================="
echo ""
echo "The fix ensures that:"
echo "  - HTTP health check verifies app is running"
echo "  - Script doesn't exit when original PID dies (Flask debug mode)"
echo "  - Browser opens after app responds to HTTP requests"
echo ""
