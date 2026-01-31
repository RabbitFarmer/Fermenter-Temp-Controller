#!/bin/bash

# Fermenter Temp Controller - Automated Setup Script
# This script sets up a virtual environment and installs all dependencies

set -e  # Exit on error

echo "=========================================="
echo "Fermenter Temp Controller - Setup Script"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed!"
    echo "   Please install Python 3.7 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Found Python $PYTHON_VERSION"

# Check if python3-venv is installed (required on Debian/Ubuntu)
echo ""
echo "Checking for python3-venv..."
if ! python3 -m venv --help &> /dev/null; then
    echo "❌ Error: python3-venv is not installed!"
    echo ""
    echo "On Raspberry Pi / Debian / Ubuntu, install it with:"
    echo "   sudo apt update"
    echo "   sudo apt install python3-venv python3-full"
    echo ""
    exit 1
fi
echo "✓ python3-venv is available"

# Create virtual environment (using .venv to match start.sh and service expectations)
VENV_DIR=".venv"
echo ""
echo "Creating virtual environment in '$VENV_DIR/'..."
if [ -d "$VENV_DIR" ]; then
    echo "⚠  Virtual environment already exists at '$VENV_DIR/'"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
        python3 -m venv "$VENV_DIR"
        echo "✓ Virtual environment recreated"
    else
        echo "Keeping existing virtual environment"
    fi
else
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p batches logs temp_control export
echo "✓ Directories created"

# Check for config files
echo ""
echo "Checking configuration files..."
if [ ! -f "config/system_config.json" ]; then
    echo "⚠  No system_config.json found - will be created from template on first run"
fi
if [ ! -f "config/tilt_config.json" ]; then
    echo "⚠  No tilt_config.json found - will be created from template on first run"
fi
if [ ! -f "config/temp_control_config.json" ]; then
    echo "⚠  No temp_control_config.json found - will be created from template on first run"
fi

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the application:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Run the application:"
echo "     python3 app.py"
echo ""
echo "  Or use the convenience script:"
echo "     ./start.sh"
echo ""
echo "  The web interface will be available at:"
echo "     http://localhost:5000"
echo ""
echo "  To access from another device on your network:"
echo "     http://<raspberry-pi-ip>:5000"
echo ""
echo "=========================================="
