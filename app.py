# Updated app.py file to include a corrected dynamic route for chart rendering for tilt_color
from flask import Flask, jsonify, render_template, abort
from datetime import datetime
import json
import os

app = Flask(__name__)

# Valid tilt colors based on tilt_config.json
VALID_TILT_COLORS = ["Red", "Green", "Black", "Purple", "Orange", "Blue", "Yellow", "Pink"]

# Constants for fermentation calculations
STALL_CHECK_ENTRIES = 100  # Number of recent entries to check for stall detection
GRAVITY_STALL_THRESHOLD = 0.001  # Gravity change threshold for stall detection
READINGS_PER_DAY = 96  # Approximate number of readings per day (15 min intervals)

def load_json_config(filename):
    """Load JSON configuration file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_batch_history(color):
    """Load batch history data from jsonl file for a specific tilt color"""
    filename = f'batch_history_{color}.jsonl'
    history = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.strip():
                    history.append(json.loads(line))
    except FileNotFoundError:
        pass
    return history

def calculate_fermentation_metrics(history, ferm_start_date):
    """Calculate fermentation days and stall days from history data"""
    ferm_days = 0
    stall_days = 0
    
    if ferm_start_date:
        try:
            start_date = datetime.strptime(ferm_start_date, "%Y-%m-%d")
            ferm_days = (datetime.now() - start_date).days
        except (ValueError, TypeError):
            pass
    
    # Calculate stall days - count days where gravity hasn't changed
    if len(history) > 1:
        last_gravity = None
        stall_count = 0
        for entry in reversed(history[-STALL_CHECK_ENTRIES:]):
            gravity = entry.get("gravity")
            if gravity is not None:
                if last_gravity is not None and abs(gravity - last_gravity) < GRAVITY_STALL_THRESHOLD:
                    stall_count += 1
                else:
                    stall_count = 0
                last_gravity = gravity
        stall_days = stall_count // READINGS_PER_DAY if stall_count > 0 else 0
    
    return ferm_days, stall_days

@app.route('/')
def home():
    return "Welcome to the Fermenter Temperature Controller!"

@app.route('/chart/<tilt_color>')
def show_chart(tilt_color):
    # Normalize color input (capitalize first letter)
    color = tilt_color.capitalize()
    
    # Validate tilt color
    if color not in VALID_TILT_COLORS:
        return jsonify({"error": "Invalid tilt color"}), 404
    
    # Load configuration files
    tilt_config = load_json_config('tilt_config.json')
    system_config = load_json_config('system_config.json')
    
    # Check if tilt color has data configured
    if color not in tilt_config:
        return jsonify({"error": "Tilt color not configured"}), 404
    
    tilt_info = tilt_config[color]
    
    # Load batch history data
    history = load_batch_history(color)
    
    if not history:
        return jsonify({"error": "No data available for this tilt color"}), 404
    
    # Extract data for chart
    timestamps = []
    gravities = []
    temps = []
    
    for entry in history:
        timestamp = entry.get("timestamp", "")
        gravity = entry.get("gravity")
        temp = entry.get("temp_f")
        
        if timestamp and gravity is not None and temp is not None:
            # Format timestamp for display
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                timestamps.append(formatted_time)
                gravities.append(float(gravity))
                temps.append(float(temp))
            except (ValueError, AttributeError):
                pass
    
    # Get fermentation start date
    ferm_start_date = tilt_info.get("ferm_start_date", "")
    
    # Calculate metrics
    ferm_days, stall_days = calculate_fermentation_metrics(history, ferm_start_date)
    
    # Render template with all required data
    return render_template(
        'chart.html',
        color=color,
        system_settings=system_config,
        ferm_start_date=ferm_start_date,
        ferm_days=ferm_days,
        stall_days=stall_days,
        timestamps=timestamps,
        gravities=gravities,
        temps=temps
    )

if __name__ == '__main__':
    app.run(debug=True)
