#!/bin/bash

# Get the directory where this script is located and navigate to it
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create and activate virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "No virtual environment found. Creating one..."
    if ! python3 -m venv .venv; then
        echo "Failed to create a virtual environment. Exiting."
        exit 1
    fi
fi

source .venv/bin/activate
echo "Virtual environment activated."

# Install dependencies if 'requirements.txt' exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    if ! pip install -r requirements.txt; then
        echo "Failed to install dependencies. Exiting."
        exit 1
    fi
else
    echo "Warning: requirements.txt not found. Skipping dependency installation."
fi

# Start the application in the background and log output
echo "Starting the application..."
if ! (python3 app.py > app.log 2>&1 &); then
    echo "Failed to start the application. See app.log for details."
    exit 1
fi

# Wait for the application to start with retries
RETRIES=10
for i in $(seq 1 $RETRIES); do
    echo "Checking if the application is running... Attempt $i/$RETRIES"
    if curl -s http://127.0.0.1:5000 > /dev/null; then
        echo "The application is running!"
        break
    fi
    sleep 2
done

if ! curl -s http://127.0.0.1:5000 > /dev/null; then
    echo "Error: The application never responded after $((RETRIES * 2)) seconds."
    exit 1
fi

# Open the application in the default web browser
echo "Opening the application in your default browser..."
if command -v xdg-open > /dev/null; then
    xdg-open http://127.0.0.1:5000   # Linux
elif command -v open > /dev/null; then
    open http://127.0.0.1:5000       # macOS
else
    echo "Please open http://127.0.0.1:5000 in your browser manually."
fi

echo "The application is now running."