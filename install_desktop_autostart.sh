#!/bin/bash

# Fermenter Temp Controller - Desktop Autostart Installer
# This script installs a desktop autostart entry that runs start.sh on boot
# and opens the browser automatically.
#
# Use this method if:
# - You have a Raspberry Pi with a monitor/keyboard/mouse
# - You want the browser to open automatically at boot
# - You prefer not to use systemd
#
# For headless/server setups, use install_service.sh instead.

set -e  # Exit on error

echo "============================================================"
echo "Fermenter Temp Controller - Desktop Autostart Installer"
echo "============================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Installation directory: $SCRIPT_DIR"
echo "Current user: $USER"
echo ""

# Check if start.sh exists
if [ ! -f "start.sh" ]; then
    echo "❌ Error: start.sh not found!"
    echo "   Expected: $SCRIPT_DIR/start.sh"
    exit 1
fi
echo "✓ Found start.sh"

# Create autostart directory if it doesn't exist
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
echo "✓ Autostart directory: $AUTOSTART_DIR"
echo ""

# Generate the desktop entry
DESKTOP_FILE="$AUTOSTART_DIR/fermenter.desktop"
TEMP_FILE="/tmp/fermenter_desktop_$$.tmp"

echo "Generating desktop autostart entry..."
cat > "$TEMP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Fermenter Temperature Controller
Comment=Start fermenter monitoring and temperature control
Exec=$SCRIPT_DIR/start.sh
Terminal=true
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

echo "✓ Desktop entry generated"
echo ""

# Show the generated file
echo "Desktop entry content:"
echo "============================================================"
cat "$TEMP_FILE"
echo "============================================================"
echo ""

# Check if file already exists
if [ -f "$DESKTOP_FILE" ]; then
    echo "⚠️  Warning: Desktop autostart entry already exists!"
    echo "   Location: $DESKTOP_FILE"
    echo ""
    read -p "Overwrite existing entry? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        rm "$TEMP_FILE"
        exit 0
    fi
fi

# Install the desktop entry
echo "Installing desktop autostart entry..."
cp "$TEMP_FILE" "$DESKTOP_FILE"
chmod +x "$DESKTOP_FILE"
rm "$TEMP_FILE"

echo "✓ Desktop autostart entry installed"
echo ""

echo "============================================================"
echo "✓ Installation Complete!"
echo "============================================================"
echo ""
echo "The Fermenter Temperature Controller will now:"
echo "  ✓ Start automatically when you log in"
echo "  ✓ Open the browser to the dashboard automatically"
echo "  ✓ Run in the background"
echo ""
echo "Testing instructions:"
echo "  1. Log out and log back in (or reboot)"
echo "  2. The application should start automatically"
echo "  3. The browser should open to http://127.0.0.1:5000"
echo ""
echo "To disable autostart:"
echo "  rm $DESKTOP_FILE"
echo ""
echo "To re-enable:"
echo "  bash $SCRIPT_DIR/install_desktop_autostart.sh"
echo ""
echo "For headless/server setup instead:"
echo "  bash $SCRIPT_DIR/install_service.sh"
echo "============================================================"
