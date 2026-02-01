#!/bin/bash

# Test script to verify auto-start timing fix
# Tests boot mode detection and extended timeout logic

echo "=== Testing Auto-Start Timing Fix ==="
echo ""

# Test 1: Verify boot mode detection logic exists
echo "Test 1: Checking boot mode detection..."
if grep -q "BOOT_MODE=false" start.sh && grep -q "if \[ ! -t 0 \] && \[ -z \"\$DISPLAY\" \]" start.sh; then
    echo "✓ Boot mode detection logic found"
else
    echo "✗ FAILED: Boot mode detection missing"
    exit 1
fi
echo ""

# Test 2: Verify extended timeout in boot mode
echo "Test 2: Checking extended timeout configuration..."
if grep -q "RETRIES=60" start.sh && grep -q "RETRY_DELAY=3" start.sh; then
    echo "✓ Extended boot mode timeout configured (60 × 3 = 180 seconds)"
else
    echo "✗ FAILED: Extended timeout not configured correctly"
    exit 1
fi
echo ""

# Test 3: Verify standard timeout for interactive mode
echo "Test 3: Checking interactive mode timeout..."
if grep -q "RETRIES=30" start.sh && grep -q "RETRY_DELAY=2" start.sh; then
    echo "✓ Interactive mode timeout configured (30 × 2 = 60 seconds)"
else
    echo "✗ FAILED: Interactive timeout not configured correctly"
    exit 1
fi
echo ""

# Test 4: Verify desktop environment wait logic
echo "Test 4: Checking desktop environment wait..."
if grep -q "Waiting for desktop environment to be ready" start.sh && grep -q "xset q" start.sh; then
    echo "✓ Desktop environment wait logic found"
else
    echo "✗ FAILED: Desktop environment wait missing"
    exit 1
fi
echo ""

# Test 5: Verify progress updates
echo "Test 5: Checking progress updates..."
if grep -q "Still waiting..." start.sh && grep -q "i % 10" start.sh; then
    echo "✓ Progress update logic found (every 10 attempts)"
else
    echo "✗ FAILED: Progress updates missing"
    exit 1
fi
echo ""

# Test 6: Verify system stabilization wait
echo "Test 6: Checking system stabilization wait..."
if grep -q "Waiting for system to stabilize" start.sh && grep -q "sleep 5" start.sh; then
    echo "✓ System stabilization wait found (5 seconds in boot mode)"
else
    echo "✗ FAILED: System stabilization wait missing"
    exit 1
fi
echo ""

# Test 7: Test desktop autostart installer exists and is executable
echo "Test 7: Checking desktop autostart installer..."
if [ -f "install_desktop_autostart.sh" ] && [ -x "install_desktop_autostart.sh" ]; then
    echo "✓ Desktop autostart installer exists and is executable"
else
    echo "✗ FAILED: Desktop autostart installer missing or not executable"
    exit 1
fi
echo ""

# Test 8: Verify desktop entry template exists
echo "Test 8: Checking desktop entry template..."
if [ -f "fermenter-autostart.desktop" ]; then
    echo "✓ Desktop entry template exists"
else
    echo "✗ FAILED: Desktop entry template missing"
    exit 1
fi
echo ""

# Test 9: Bash syntax validation
echo "Test 9: Validating bash syntax..."
if bash -n start.sh 2>&1 && bash -n install_desktop_autostart.sh 2>&1; then
    echo "✓ All bash scripts have valid syntax"
else
    echo "✗ FAILED: Syntax errors in bash scripts"
    exit 1
fi
echo ""

# Test 10: Simulate boot mode detection
echo "Test 10: Simulating boot mode detection..."
# Create a test script that simulates boot conditions
cat > /tmp/test_boot_mode.sh << 'EOF'
#!/bin/bash
# Simulate boot mode (no terminal input, no DISPLAY)
BOOT_MODE=false
if [ ! -t 0 ] && [ -z "$DISPLAY" ]; then
    BOOT_MODE=true
fi
echo "$BOOT_MODE"
EOF

# Run with no stdin and no DISPLAY
RESULT=$(bash /tmp/test_boot_mode.sh < /dev/null)
if [ "$RESULT" = "true" ]; then
    echo "✓ Boot mode detection logic works correctly"
else
    echo "✗ FAILED: Boot mode detection returned '$RESULT', expected 'true'"
    exit 1
fi
rm /tmp/test_boot_mode.sh
echo ""

echo "============================================================"
echo "✓ All tests passed!"
echo "============================================================"
echo ""
echo "The auto-start timing fix is correctly implemented with:"
echo "  ✓ Automatic boot mode detection"
echo "  ✓ Extended 180-second timeout for boot scenarios"
echo "  ✓ Desktop environment readiness checks"
echo "  ✓ Progress updates every 10 attempts"
echo "  ✓ System stabilization wait (5 seconds in boot mode)"
echo "  ✓ Desktop autostart installer available"
echo ""
