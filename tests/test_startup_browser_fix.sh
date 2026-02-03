#!/bin/bash
# Test script to verify the simplified browser autostart logic
# This verifies that complex X server checks have been removed

set -e

echo "Testing simplified browser autostart logic..."
echo

# Test 1: Verify old complex X server wait loop has been removed
echo "Test 1: Verifying complex X server wait loop has been removed..."

# Check if the old xset q loop has been removed
if grep -q "Waiting for X server to be ready" start.sh; then
    echo "✗ Test 1 FAILED: Old X server wait loop still present in start.sh"
    echo "  This complex check should be removed for simpler timing approach"
    exit 1
else
    echo "✓ Test 1 PASSED: Complex X server wait loop removed"
fi
echo

# Test 2: Verify xdotool fullscreen logic has been removed
echo "Test 2: Verifying xdotool fullscreen logic has been removed..."
if grep -q "xdotool" start.sh; then
    echo "✗ Test 2 FAILED: xdotool fullscreen code still present"
    echo "  This should be removed for reliability"
    exit 1
else
    echo "✓ Test 2 PASSED: xdotool fullscreen logic removed"
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

# Test 5: Verify simplified browser opening logic is present
echo "Test 5: Verifying simplified browser opening logic..."
if grep -q "xdg-open http://127.0.0.1:5000" start.sh; then
    echo "✓ Test 5 PASSED: Browser opening logic is present"
else
    echo "✗ Test 5 FAILED: Browser opening logic missing!"
    exit 1
fi
echo

# Test 6: Verify nohup is used for browser opening
echo "Test 6: Verifying nohup is used for browser opening..."
if grep -q "nohup xdg-open" start.sh || grep -q "nohup open" start.sh; then
    echo "✓ Test 6 PASSED: nohup is used for browser opening"
else
    echo "✗ Test 6 FAILED: nohup not found for browser opening"
    exit 1
fi
echo

# Test 7: Verify simplified sleep delay is used
echo "Test 7: Verifying simplified 10 second delay..."
if grep -q "sleep 10" start.sh; then
    echo "✓ Test 7 PASSED: Simple 10 second delay found"
else
    echo "⚠ Test 7 WARNING: 10 second delay not found (not critical)"
fi
echo

echo "=========================================="
echo "✓ ALL TESTS PASSED!"
echo "=========================================="
echo ""
echo "The simplified fix ensures that:"
echo "  - No complex X server checks that can timeout"
echo "  - Simple 10 second delay for desktop initialization"
echo "  - Browser opens with nohup in background"
echo "  - Gracefully handles display being unavailable"
echo ""
