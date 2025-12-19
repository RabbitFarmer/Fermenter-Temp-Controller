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

def parse_timestamp(timestamp):
    """
    Parse ISO format timestamp and return datetime object.
    Handles multiple formats: UTC with 'Z', with timezone offset, or naive timestamps.
    Supports timestamps with or without microseconds.
    """
    try:
        # Handle both UTC timestamps with 'Z' and timestamps without timezone
        timestamp_str = timestamp.replace('Z', '+00:00') if 'Z' in timestamp else timestamp
        # Try parsing with timezone info, fall back to naive parsing
        try:
            return datetime.fromisoformat(timestamp_str)
        except ValueError:
            # Fallback for timestamps without timezone (remove microseconds if present)
            base_timestamp = timestamp_str.split('.')[0] if '.' in timestamp_str else timestamp_str
            return datetime.strptime(base_timestamp, "%Y-%m-%dT%H:%M:%S")
    except (ValueError, AttributeError):
        return None

def calculate_fermentation_metrics(history, ferm_start_date):
    """
    Calculate fermentation days and stall days from history data.
    
    Args:
        history: List of batch history entries
        ferm_start_date: Fermentation start date in 'YYYY-MM-DD' format from tilt_config.json
    
    Returns:
        Tuple of (ferm_days, stall_days)
    
    Note:
        The stall days calculation assumes READINGS_PER_DAY (96) readings occur per day,
        which may not be accurate due to network issues or device restarts. For a more
        accurate calculation, consider tracking actual time intervals between readings.
    """
    ferm_days = 0
    stall_days = 0
    
    if ferm_start_date:
        try:
            start_date = datetime.strptime(ferm_start_date, "%Y-%m-%d")
            ferm_days = (datetime.now() - start_date).days
        except (ValueError, TypeError):
            pass
    
    # Calculate stall days - count consecutive days where gravity hasn't changed
    if len(history) > 1:
        last_gravity = None
        max_stall_count = 0
        current_stall_count = 0
        # Process recent history entries
        recent_history = history[-STALL_CHECK_ENTRIES:] if len(history) > STALL_CHECK_ENTRIES else history
        for entry in reversed(recent_history):
            gravity = entry.get("gravity")
            if gravity is not None:
                if last_gravity is not None and abs(gravity - last_gravity) < GRAVITY_STALL_THRESHOLD:
                    current_stall_count += 1
                    max_stall_count = max(max_stall_count, current_stall_count)
                else:
                    current_stall_count = 0
                last_gravity = gravity
        # Convert consecutive stalled readings to days
        stall_days = max_stall_count // READINGS_PER_DAY if max_stall_count > 0 else 0
    
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
            dt = parse_timestamp(timestamp)
            if dt:
                formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                timestamps.append(formatted_time)
                gravities.append(float(gravity))
                temps.append(float(temp))
    
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
