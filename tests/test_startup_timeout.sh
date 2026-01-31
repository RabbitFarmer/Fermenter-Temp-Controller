#!/bin/bash
# Test script to verify that start.sh has adequate timeout for slow startups

echo "Testing startup timeout configuration..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Extract RETRIES value from start.sh (one level up from tests/)
RETRIES=$(grep "^RETRIES=" "$SCRIPT_DIR/../start.sh" | cut -d'=' -f2)

if [ -z "$RETRIES" ]; then
    echo "FAIL: Could not find RETRIES variable in start.sh"
    exit 1
fi

echo "Found RETRIES=$RETRIES in start.sh"

# Calculate total timeout (RETRIES * 2 seconds per retry)
TIMEOUT=$((RETRIES * 2))

echo "Total timeout: $TIMEOUT seconds"

# Verify timeout is at least 40 seconds (20 retries * 2 seconds)
# This accommodates slower Raspberry Pi startup times
if [ "$TIMEOUT" -ge 40 ]; then
    echo "PASS: Timeout of $TIMEOUT seconds is adequate for Raspberry Pi startup"
    exit 0
else
    echo "FAIL: Timeout of $TIMEOUT seconds may be too short for Raspberry Pi startup"
    echo "      Recommended: at least 40 seconds (20 retries)"
    exit 1
fi
