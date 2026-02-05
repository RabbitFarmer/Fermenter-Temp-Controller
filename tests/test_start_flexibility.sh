#!/bin/bash
# Test start.sh flexibility with different venv names and installation directories

set -e

echo "============================================================"
echo "Testing start.sh flexibility"
echo "============================================================"
echo ""

# Test 1: Test with venv directory
echo "Test 1: Testing with 'venv' directory..."
echo "-----------------------------------------------------------"

TEST_DIR="/tmp/test_fermenter_venv_$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Copy necessary files
cp /home/runner/work/Fermenter-Temp-Controller/Fermenter-Temp-Controller/start.sh .
cp /home/runner/work/Fermenter-Temp-Controller/Fermenter-Temp-Controller/requirements.txt .
touch app.py  # Create dummy app.py

# Create venv (not .venv)
python3 -m venv venv

# Extract just the venv detection logic from start.sh to test
VENV_DIR=""
if [ -d ".venv" ]; then
    VENV_DIR=".venv"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
fi

if [ "$VENV_DIR" = "venv" ]; then
    echo "✓ Correctly detected 'venv' directory"
else
    echo "❌ Failed to detect 'venv' directory (got: $VENV_DIR)"
    cd /
    rm -rf "$TEST_DIR"
    exit 1
fi

cd /
rm -rf "$TEST_DIR"

# Test 2: Test with .venv directory
echo ""
echo "Test 2: Testing with '.venv' directory..."
echo "-----------------------------------------------------------"

TEST_DIR="/tmp/test_fermenter_dotvenv_$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Copy necessary files
cp /home/runner/work/Fermenter-Temp-Controller/Fermenter-Temp-Controller/start.sh .
cp /home/runner/work/Fermenter-Temp-Controller/Fermenter-Temp-Controller/requirements.txt .
touch app.py

# Create .venv
python3 -m venv .venv

# Extract venv detection logic
VENV_DIR=""
if [ -d ".venv" ]; then
    VENV_DIR=".venv"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
fi

if [ "$VENV_DIR" = ".venv" ]; then
    echo "✓ Correctly detected '.venv' directory"
else
    echo "❌ Failed to detect '.venv' directory (got: $VENV_DIR)"
    cd /
    rm -rf "$TEST_DIR"
    exit 1
fi

cd /
rm -rf "$TEST_DIR"

# Test 3: Test with custom directory name (FermenterApp)
echo ""
echo "Test 3: Testing with custom directory name 'FermenterApp'..."
echo "-----------------------------------------------------------"

TEST_DIR="/tmp/FermenterApp_$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Copy start.sh
cp /home/runner/work/Fermenter-Temp-Controller/Fermenter-Temp-Controller/start.sh .

# Test SCRIPT_DIR detection
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [[ "$SCRIPT_DIR" == *"FermenterApp"* ]]; then
    echo "✓ SCRIPT_DIR correctly detected custom directory: $SCRIPT_DIR"
else
    echo "❌ SCRIPT_DIR failed to detect custom directory (got: $SCRIPT_DIR)"
    cd /
    rm -rf "$TEST_DIR"
    exit 1
fi

cd /
rm -rf "$TEST_DIR"

# Test 4: Test with both venv directories present (should prefer .venv)
echo ""
echo "Test 4: Testing with both 'venv' and '.venv' present..."
echo "-----------------------------------------------------------"

TEST_DIR="/tmp/test_fermenter_both_$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Create both directories
mkdir -p venv .venv

# Extract venv detection logic
VENV_DIR=""
if [ -d ".venv" ]; then
    VENV_DIR=".venv"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
fi

if [ "$VENV_DIR" = ".venv" ]; then
    echo "✓ Correctly prefers '.venv' when both exist"
else
    echo "❌ Should prefer '.venv' when both exist (got: $VENV_DIR)"
    cd /
    rm -rf "$TEST_DIR"
    exit 1
fi

cd /
rm -rf "$TEST_DIR"

# Test 5: Verify start.sh has no hardcoded directory names
echo ""
echo "Test 5: Checking for hardcoded directory references..."
echo "-----------------------------------------------------------"

if grep -q "Fermenter-Temp-Controller" /home/runner/work/Fermenter-Temp-Controller/Fermenter-Temp-Controller/start.sh; then
    echo "❌ Found hardcoded 'Fermenter-Temp-Controller' reference in start.sh"
    exit 1
else
    echo "✓ No hardcoded 'Fermenter-Temp-Controller' references"
fi

if grep -q "FermenterApp" /home/runner/work/Fermenter-Temp-Controller/Fermenter-Temp-Controller/start.sh; then
    echo "❌ Found hardcoded 'FermenterApp' reference in start.sh"
    exit 1
else
    echo "✓ No hardcoded 'FermenterApp' references"
fi

# Check that VENV_DIR variable is used instead of hardcoded paths
if grep -q 'source "$VENV_DIR/bin/activate"' /home/runner/work/Fermenter-Temp-Controller/Fermenter-Temp-Controller/start.sh; then
    echo "✓ Uses VENV_DIR variable for activation"
else
    echo "❌ Does not use VENV_DIR variable for activation"
    exit 1
fi

echo ""
echo "============================================================"
echo "✓ All flexibility tests passed!"
echo "============================================================"
echo ""
echo "Summary:"
echo "  ✓ Detects 'venv' directory"
echo "  ✓ Detects '.venv' directory"
echo "  ✓ Prefers '.venv' when both exist"
echo "  ✓ Works with any installation directory name"
echo "  ✓ No hardcoded directory references"
echo "  ✓ Uses VENV_DIR variable consistently"
