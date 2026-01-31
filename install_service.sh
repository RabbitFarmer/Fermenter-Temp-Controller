#!/bin/bash

# Fermenter Temp Controller - Systemd Service Installation Script
# This script generates and installs a systemd service file with correct paths
# for your specific installation

set -e  # Exit on error

echo "============================================================"
echo "Fermenter Temp Controller - Systemd Service Installer"
echo "============================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Current installation directory: $SCRIPT_DIR"
echo "Current user: $USER"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "❌ Error: No virtual environment found!"
    echo ""
    echo "Please run setup first:"
    echo "  ./setup.sh"
    echo ""
    echo "Or create a virtual environment:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
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
echo ""

# Generate the service file
SERVICE_FILE="fermenter.service"
TEMP_SERVICE_FILE="/tmp/fermenter_service_$$.tmp"

echo "Generating systemd service file..."
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

echo "✓ Service file generated"
echo ""

# Show the generated service file
echo "Generated service file content:"
echo "============================================================"
cat "$TEMP_SERVICE_FILE"
echo "============================================================"
echo ""

# Ask for confirmation
read -p "Install this service file to /etc/systemd/system/fermenter.service? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    rm "$TEMP_SERVICE_FILE"
    exit 0
fi

# Install the service file
echo ""
echo "Installing service file..."
if ! sudo cp "$TEMP_SERVICE_FILE" /etc/systemd/system/fermenter.service; then
    echo "❌ Error: Failed to copy service file!"
    echo "   You may need to run this script with appropriate permissions."
    rm "$TEMP_SERVICE_FILE"
    exit 1
fi

# Clean up temp file
rm "$TEMP_SERVICE_FILE"

echo "✓ Service file installed to /etc/systemd/system/fermenter.service"
echo ""

# Reload systemd
echo "Reloading systemd daemon..."
if ! sudo systemctl daemon-reload; then
    echo "❌ Error: Failed to reload systemd daemon!"
    exit 1
fi
echo "✓ Systemd daemon reloaded"
echo ""

# Ask if user wants to enable and start the service
read -p "Enable service to start on boot? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Enabling service..."
    sudo systemctl enable fermenter
    echo "✓ Service enabled (will start on boot)"
    echo ""
    
    read -p "Start service now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting service..."
        sudo systemctl start fermenter
        echo "✓ Service started"
        echo ""
        
        # Check status
        echo "Service status:"
        sudo systemctl status fermenter --no-pager || true
        echo ""
    fi
fi

echo "============================================================"
echo "✓ Installation Complete!"
echo "============================================================"
echo ""
echo "Service management commands:"
echo "  View status:   sudo systemctl status fermenter"
echo "  Start service: sudo systemctl start fermenter"
echo "  Stop service:  sudo systemctl stop fermenter"
echo "  Restart:       sudo systemctl restart fermenter"
echo "  Enable boot:   sudo systemctl enable fermenter"
echo "  Disable boot:  sudo systemctl disable fermenter"
echo "  View logs:     sudo journalctl -u fermenter -f"
echo ""
echo "Access the web interface at:"
echo "  Local:   http://localhost:5000"
echo "  Network: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Note: The service is configured with SKIP_BROWSER_OPEN=1"
echo "      to prevent browser opening when running as a service."
echo "      Access the dashboard by manually opening the URL above."
echo "============================================================"
