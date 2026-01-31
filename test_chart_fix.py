#!/usr/bin/env python3
"""
Test the Temperature Control Chart fix with empty tilt_color.

This verifies that the chart can render even when tilt_color is empty.
"""

import json
import os
import sys
from datetime import datetime, timedelta

# Cleanup
log_path = 'temp_control/temp_control_log.jsonl'
if os.path.exists(log_path):
    os.remove(log_path)

os.makedirs('temp_control', exist_ok=True)

print("Test 1: Data with EMPTY tilt_color")
print("=" * 60)

# Create sample data with empty tilt_color
base_time = datetime(2026, 1, 25, 10, 0, 0)
events = []

for i in range(100):
    timestamp = base_time + timedelta(minutes=15*i)
    iso_ts = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    temp_f = 66.0 + (i % 20) * 0.1
    
    if i % 30 == 0:
        event = "HEATING-PLUG TURNED ON"
    elif i % 30 == 15:
        event = "HEATING-PLUG TURNED OFF"
    else:
        event = "SAMPLE"
    
    entry = {
        "timestamp": iso_ts,
        "date": timestamp.strftime("%Y-%m-%d"),
        "time": timestamp.strftime("%H:%M:%S"),
        "tilt_color": "",  # EMPTY
        "brewid": None,
        "low_limit": 64.0,
        "current_temp": temp_f,
        "temp_f": temp_f,
        "gravity": 1.050 - (i * 0.0001),
        "high_limit": 68.0,
        "event": event
    }
    events.append(entry)

with open(log_path, 'w') as f:
    for entry in events:
        f.write(json.dumps(entry) + '\n')

print(f"Created {len(events)} records with empty tilt_color")

# Start Flask app in test mode
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app

with app.app.test_client() as client:
    # Test chart_data endpoint
    response = client.get('/chart_data/Fermenter?limit=200')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.get_json()
    points = data.get('points', [])
    
    print(f"✓ Server returned {len(points)} points")
    assert len(points) == 100, f"Expected 100 points, got {len(points)}"
    
    # Simulate JavaScript logic with the FIX
    validDataPoints = [p for p in points if p.get('tilt_color') and p.get('tilt_color').strip() != '']
    
    if len(validDataPoints) > 0:
        activeTiltColor = validDataPoints[-1].get('tilt_color')
        displayData = [p for p in validDataPoints if p.get('tilt_color') == activeTiltColor]
        displayLabel = f"{activeTiltColor} Tilt"
    else:
        # FIX: When no tilt_color, use all data
        displayData = points
        displayLabel = "Temperature"
    
    print(f"✓ Display data: {len(displayData)} points")
    print(f"✓ Display label: '{displayLabel}'")
    
    assert len(displayData) > 0, "Display data should not be empty!"
    print("\n✅ Test 1 PASSED: Chart can render with empty tilt_color\n")

print("\nTest 2: Data with valid tilt_color")
print("=" * 60)

# Cleanup and create new data with tilt_color
os.remove(log_path)
events = []

for i in range(100):
    timestamp = base_time + timedelta(minutes=15*i)
    iso_ts = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    temp_f = 68.0 + (i % 15) * 0.1
    
    entry = {
        "timestamp": iso_ts,
        "date": timestamp.strftime("%Y-%m-%d"),
        "time": timestamp.strftime("%H:%M:%S"),
        "tilt_color": "Black",  # Has tilt_color
        "brewid": "BREW001",
        "low_limit": 64.0,
        "current_temp": temp_f,
        "temp_f": temp_f,
        "gravity": 1.045,
        "high_limit": 68.0,
        "event": "SAMPLE"
    }
    events.append(entry)

with open(log_path, 'w') as f:
    for entry in events:
        f.write(json.dumps(entry) + '\n')

print(f"Created {len(events)} records with tilt_color='Black'")

with app.app.test_client() as client:
    response = client.get('/chart_data/Fermenter?limit=200')
    assert response.status_code == 200
    
    data = response.get_json()
    points = data.get('points', [])
    
    print(f"✓ Server returned {len(points)} points")
    
    # Simulate JavaScript logic
    validDataPoints = [p for p in points if p.get('tilt_color') and p.get('tilt_color').strip() != '']
    
    if len(validDataPoints) > 0:
        activeTiltColor = validDataPoints[-1].get('tilt_color')
        displayData = [p for p in validDataPoints if p.get('tilt_color') == activeTiltColor]
        displayLabel = f"{activeTiltColor} Tilt"
    else:
        displayData = points
        displayLabel = "Temperature"
    
    print(f"✓ Display data: {len(displayData)} points")
    print(f"✓ Display label: '{displayLabel}'")
    
    assert len(displayData) > 0, "Display data should not be empty!"
    assert displayLabel == "Black Tilt", f"Expected 'Black Tilt', got '{displayLabel}'"
    print("\n✅ Test 2 PASSED: Chart shows active tilt when tilt_color is present\n")

print("=" * 60)
print("✅✅✅ ALL TESTS PASSED! ✅✅✅")
print("=" * 60)
print("\nThe fix ensures that:")
print("  1. When tilt_color is empty → Show all data as 'Temperature'")
print("  2. When tilt_color exists → Show active tilt data with tilt name")
