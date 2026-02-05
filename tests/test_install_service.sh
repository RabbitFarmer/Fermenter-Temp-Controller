#!/bin/bash
# Test script for install_service.sh logic

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Testing install_service.sh logic..."
echo ""

# Check for virtual environment
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "❌ Error: No virtual environment found for testing"
    exit 1
fi

# Determine which venv directory exists
if [ -d ".venv" ]; then
    VENV_DIR=".venv"
    echo "✓ Found virtual environment: .venv"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
    echo "✓ Found virtual environment: venv"
fi

# Get Python path in virtual environment
PYTHON_PATH="$SCRIPT_DIR/$VENV_DIR/bin/python3"
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Error: Python not found in virtual environment!"
    echo "   Expected: $PYTHON_PATH"
    exit 1
fi
echo "✓ Python path: $PYTHON_PATH"

# Generate test service file
TEMP_SERVICE_FILE="/tmp/fermenter_test_service.tmp"

cat > "$TEMP_SERVICE_FILE" << EOF
[Unit]
Description=Fermenter Temperature Controller
After=network.target bluetooth.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment="DISPLAY=:0"
Environment="SKIP_BROWSER_OPEN=1"
ExecStart=$PYTHON_PATH $SCRIPT_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "Generated test service file:"
echo "============================================================"
cat "$TEMP_SERVICE_FILE"
echo "============================================================"
echo ""

# Verify key fields
if grep -q "User=$USER" "$TEMP_SERVICE_FILE"; then
    echo "✓ User field correct: $USER"
else
    echo "❌ User field incorrect"
    exit 1
fi

if grep -q "WorkingDirectory=$SCRIPT_DIR" "$TEMP_SERVICE_FILE"; then
    echo "✓ WorkingDirectory correct: $SCRIPT_DIR"
else
    echo "❌ WorkingDirectory incorrect"
    exit 1
fi

if grep -q "ExecStart=$PYTHON_PATH $SCRIPT_DIR/app.py" "$TEMP_SERVICE_FILE"; then
    echo "✓ ExecStart correct"
else
    echo "❌ ExecStart incorrect"
    exit 1
fi

if grep -q 'Environment="SKIP_BROWSER_OPEN=1"' "$TEMP_SERVICE_FILE"; then
    echo "✓ SKIP_BROWSER_OPEN environment variable present"
else
    echo "❌ SKIP_BROWSER_OPEN environment variable missing"
    exit 1
fi

# Clean up
rm "$TEMP_SERVICE_FILE"

echo ""
echo "✓ All tests passed!"
