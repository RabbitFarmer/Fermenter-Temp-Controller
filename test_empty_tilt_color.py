#!/usr/bin/env python3
"""
Test Temperature Control Chart with EMPTY tilt_color fields.

This simulates older log data or data where tilt_color wasn't tracked.
"""

import json
import os
import sys
from datetime import datetime, timedelta

# Remove old test data
log_path = 'temp_control/temp_control_log.jsonl'
if os.path.exists(log_path):
    os.remove(log_path)

os.makedirs('temp_control', exist_ok=True)

print(f"Creating test data with EMPTY tilt_color in {log_path}...")

# Create sample data with empty tilt_color
base_time = datetime(2026, 1, 25, 10, 0, 0)
events = []

for i in range(445):
    timestamp = base_time + timedelta(minutes=15*i)
    iso_ts = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H:%M:%S")
    
    temp_f = 66.0 + (i % 20) * 0.1
    
    if i % 30 == 0:
        event = "HEATING-PLUG TURNED ON"
    elif i % 30 == 15:
        event = "HEATING-PLUG TURNED OFF"
    else:
        event = "SAMPLE"
    
    entry = {
        "timestamp": iso_ts,
        "date": date_str,
        "time": time_str,
        "tilt_color": "",  # EMPTY - this is the key difference!
        "brewid": None,
        "low_limit": 64.0,
        "current_temp": temp_f,
        "temp_f": temp_f,
        "gravity": 1.050 - (i * 0.00002),
        "high_limit": 68.0,
        "event": event
    }
    events.append(entry)

with open(log_path, 'w') as f:
    for entry in events:
        f.write(json.dumps(entry) + '\n')

print(f"Created {len(events)} test records (all with empty tilt_color)")

# Test the chart_data endpoint
print("\nTesting chart_data endpoint...")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app

with app.app.test_client() as client:
    response = client.get('/chart_data/Fermenter?limit=1000')
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.get_json()
        print(f"Points returned: {len(data.get('points', []))}")
        print(f"Matched: {data.get('matched', 0)}")
        print(f"Truncated: {data.get('truncated', False)}")
        
        if len(data.get('points', [])) > 0:
            print(f"\nFirst point: {json.dumps(data['points'][0], indent=2)}")
            print("\n✅ Chart endpoint returns data")
        else:
            print("\n❌ No points returned despite having data!")
            
        # Now simulate what the JavaScript does
        print("\n--- Simulating JavaScript Processing ---")
        dataPoints = data.get('points', [])
        print(f"Total dataPoints from server: {len(dataPoints)}")
        
        # Line 99 in chart_plotly.html
        validDataPoints = [p for p in dataPoints if p.get('tilt_color') and p.get('tilt_color').strip() != '']
        print(f"validDataPoints (after filtering empty tilt_color): {len(validDataPoints)}")
        
        if len(validDataPoints) == 0:
            print("\n❌ BUG FOUND! All data filtered out because tilt_color is empty!")
            print("This will cause:")
            print("  - activeTiltColor = null")
            print("  - activeTiltData = []")
            print("  - No temperature trace created")
            print("  - Empty chart or error when rendering")
        else:
            print("✅ Data would be displayed")
            
    else:
        print(f"❌ Error: {response.status_code}")

print("\nTest complete.")
