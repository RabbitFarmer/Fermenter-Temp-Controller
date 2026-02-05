#!/usr/bin/env python3
"""
Test to reproduce the Temperature Control Chart failure issue.

The user reports:
- Clicked [Chart] button on Temperature Control Card
- Chart page shows blank with "Failed to load data" message  
- Export shows 445 records available

This test creates sample data and verifies the chart endpoint works.
"""

import json
import os
import sys
from datetime import datetime, timedelta

# Create test data directory
os.makedirs('temp_control', exist_ok=True)

# Create sample temperature control log data
# Simulating what the user might have - 445 records
log_path = 'temp_control/temp_control_log.jsonl'

print(f"Creating test data in {log_path}...")

# Create realistic test data spanning a few days
base_time = datetime(2026, 1, 25, 10, 0, 0)
events = []

for i in range(445):
    # Simulate readings every 15 minutes
    timestamp = base_time + timedelta(minutes=15*i)
    iso_ts = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H:%M:%S")
    
    # Vary temperature between 64-68°F
    temp_f = 66.0 + (i % 20) * 0.1
    
    # Mix of event types
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
        "tilt_color": "Black",  # Active tilt
        "brewid": "BREW001",
        "low_limit": 64.0,
        "current_temp": temp_f,
        "temp_f": temp_f,
        "gravity": 1.050 - (i * 0.00002),  # Slowly decreasing gravity
        "high_limit": 68.0,
        "event": event
    }
    events.append(entry)

# Write to JSONL file
with open(log_path, 'w') as f:
    for entry in events:
        f.write(json.dumps(entry) + '\n')

print(f"Created {len(events)} test records")

# Now test the chart_data endpoint
print("\nTesting chart_data endpoint...")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and test the app
import app

with app.app.test_client() as client:
    # Test the chart_data endpoint for Fermenter
    response = client.get('/chart_data/Fermenter?limit=1000')
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.get_json()
        print(f"Points returned: {len(data.get('points', []))}")
        print(f"Matched: {data.get('matched', 0)}")
        print(f"Truncated: {data.get('truncated', False)}")
        
        if len(data.get('points', [])) > 0:
            print(f"\nFirst point: {json.dumps(data['points'][0], indent=2)}")
            print(f"Last point: {json.dumps(data['points'][-1], indent=2)}")
            print("\n✅ Chart endpoint works!")
        else:
            print("\n❌ No points returned despite having data!")
            print(f"Full response: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.get_data(as_text=True)}")

print("\nTest complete.")