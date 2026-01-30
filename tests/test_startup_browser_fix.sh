#!/bin/bash
# Test script to verify the browser opening fix works correctly
# This simulates running start.sh without actually starting the full Flask app

set -e

echo "Testing browser opening fix for Issue #169..."
echo

# Test 1: Verify SKIP_BROWSER_OPEN environment variable prevents browser opening in app.py
echo "Test 1: Verifying SKIP_BROWSER_OPEN prevents double browser opening..."

# Create a minimal test Python script that simulates the app.py browser opening logic
cat > /tmp/test_app_browser.py << 'EOF'
import os
import sys
import threading
import time

opened_browser = False

def open_browser():
    global opened_browser
    time.sleep(0.1)
    opened_browser = True
    print("Browser would be opened")

# Simulate the app.py conditional logic
if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and not os.environ.get('SKIP_BROWSER_OPEN'):
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    time.sleep(0.2)

if opened_browser:
    print("RESULT: Browser was opened")
    sys.exit(1)  # Should NOT open when SKIP_BROWSER_OPEN is set
else:
    print("RESULT: Browser was NOT opened (correct)")
    sys.exit(0)
EOF

# Run with SKIP_BROWSER_OPEN set (should NOT open browser)
if SKIP_BROWSER_OPEN=1 python3 /tmp/test_app_browser.py; then
    echo "✓ Test 1 PASSED: Browser correctly skipped when SKIP_BROWSER_OPEN=1"
else
    echo "✗ Test 1 FAILED: Browser was opened when it should have been skipped"
    exit 1
fi
echo

# Test 2: Verify browser opens normally without SKIP_BROWSER_OPEN
echo "Test 2: Verifying browser opens without SKIP_BROWSER_OPEN..."

cat > /tmp/test_app_browser2.py << 'EOF'
import os
import sys
import threading
import time

opened_browser = False

def open_browser():
    global opened_browser
    time.sleep(0.1)
    opened_browser = True
    print("Browser would be opened")

# Simulate the app.py conditional logic
if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and not os.environ.get('SKIP_BROWSER_OPEN'):
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    time.sleep(0.2)

if opened_browser:
    print("RESULT: Browser was opened (correct)")
    sys.exit(0)  # Should open when SKIP_BROWSER_OPEN is not set
else:
    print("RESULT: Browser was NOT opened")
    sys.exit(1)
EOF

# Run without SKIP_BROWSER_OPEN (should open browser)
if python3 /tmp/test_app_browser2.py; then
    echo "✓ Test 2 PASSED: Browser correctly opens when SKIP_BROWSER_OPEN is not set"
else
    echo "✗ Test 2 FAILED: Browser was not opened when it should have been"
    exit 1
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

# Test 4: Verify the SKIP_BROWSER_OPEN is set in start.sh
echo "Test 4: Verifying SKIP_BROWSER_OPEN is set in start.sh..."
if grep -q "SKIP_BROWSER_OPEN=1 python3 app.py" start.sh; then
    echo "✓ Test 4 PASSED: start.sh correctly sets SKIP_BROWSER_OPEN=1"
else
    echo "✗ Test 4 FAILED: SKIP_BROWSER_OPEN not found in start.sh"
    exit 1
fi
echo

# Test 5: Verify app.py checks for SKIP_BROWSER_OPEN
echo "Test 5: Verifying app.py checks for SKIP_BROWSER_OPEN..."
if grep -q "not os.environ.get('SKIP_BROWSER_OPEN')" app.py; then
    echo "✓ Test 5 PASSED: app.py correctly checks for SKIP_BROWSER_OPEN"
else
    echo "✗ Test 5 FAILED: SKIP_BROWSER_OPEN check not found in app.py"
    exit 1
fi
echo

# Clean up
rm -f /tmp/test_app_browser.py /tmp/test_app_browser2.py

echo "=========================================="
echo "✓ ALL TESTS PASSED!"
echo "=========================================="
echo "The fix correctly prevents duplicate browser opening."
echo "When running via start.sh, only start.sh opens the browser."
echo "When running app.py directly, app.py opens the browser."
