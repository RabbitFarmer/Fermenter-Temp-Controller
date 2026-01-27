#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start the Flask application in the background
python3 app.py &

# Wait for the app to be ready by polling the startup endpoint
echo "Waiting for Flask server to start..."
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    # Try using curl first, fallback to wget, then python
    if command -v curl > /dev/null; then
        if curl -s -f http://127.0.0.1:5000/startup >/dev/null 2>&1; then
            echo "Flask server is ready!"
            break
        fi
    elif command -v wget > /dev/null; then
        if wget -q --spider --timeout=1 http://127.0.0.1:5000/startup 2>/dev/null; then
            echo "Flask server is ready!"
            break
        fi
    else
        # Fallback to python urllib
        if python3 -c "try:
    import urllib.request
    urllib.request.urlopen('http://127.0.0.1:5000/startup', timeout=1)
except:
    exit(1)" 2>/dev/null; then
            echo "Flask server is ready!"
            break
        fi
    fi
    ATTEMPT=$((ATTEMPT + 1))
    sleep 1
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "Warning: Flask server did not respond within 30 seconds"
fi

# Open the startup splash page in the default browser
if command -v xdg-open > /dev/null; then
    xdg-open http://127.0.0.1:5000/startup   # For Linux
elif command -v open > /dev/null; then
    open http://127.0.0.1:5000/startup       # For macOS
else
    echo "Please open http://127.0.0.1:5000/startup in your browser"
fi