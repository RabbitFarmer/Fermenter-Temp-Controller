#!/usr/bin/env python3
"""
Test script to generate sample temperature control data and verify chart behavior
"""
import json
from datetime import datetime, timedelta

# Generate sample temperature control log data
def generate_test_data():
    """Generate test data with one active tilt and cooling/heating events"""
    data = []
    start_time = datetime(2026, 1, 30, 10, 0, 0)
    
    # Simulate temperature fluctuations between 65-70°F with heating and cooling events
    temps = [65, 66, 67, 68, 69, 70, 69, 68, 67, 66, 65, 66, 67, 68, 69, 70, 71, 70, 69, 68]
    
    for i, temp in enumerate(temps):
        timestamp = (start_time + timedelta(minutes=i*5)).isoformat() + 'Z'
        
        # Regular sample
        entry = {
            "timestamp": timestamp,
            "event": "SAMPLE",
            "tilt_color": "Blue",
            "current_temp": temp,
            "temp_f": temp,
            "gravity": 1.050 - (i * 0.001)  # Gradually decreasing gravity
        }
        data.append(entry)
        
        # Add heating events when temp drops
        if temp < 66 and i > 0 and temps[i-1] >= temp:
            heating_on = {
                "timestamp": timestamp,
                "event": "HEATING-PLUG TURNED ON",
                "tilt_color": "Blue",
                "current_temp": temp,
                "temp_f": temp,
            }
            data.append(heating_on)
        elif temp >= 67 and i > 0 and temps[i-1] < temp and any(d.get('event') == 'HEATING-PLUG TURNED ON' for d in data[-3:]):
            heating_off = {
                "timestamp": timestamp,
                "event": "HEATING-PLUG TURNED OFF",
                "tilt_color": "Blue",
                "current_temp": temp,
                "temp_f": temp,
            }
            data.append(heating_off)
        
        # Add cooling events when temp rises above 70
        if temp > 70 and i > 0 and temps[i-1] <= 70:
            cooling_on = {
                "timestamp": timestamp,
                "event": "COOLING-PLUG TURNED ON",
                "tilt_color": "Blue",
                "current_temp": temp,
                "temp_f": temp,
            }
            data.append(cooling_on)
        elif temp <= 69 and i > 0 and temps[i-1] > 70:
            cooling_off = {
                "timestamp": timestamp,
                "event": "COOLING-PLUG TURNED OFF",
                "tilt_color": "Blue",
                "current_temp": temp,
                "temp_f": temp,
            }
            data.append(cooling_off)
    
    return data

def main():
    print("Generating test temperature control data...")
    data = generate_test_data()
    
    # Write to temp_control_log.jsonl
    with open('temp_control_log.jsonl', 'w') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')
    
    print(f"✓ Generated {len(data)} log entries")
    
    # Summary
    samples = [d for d in data if d['event'] == 'SAMPLE']
    heating_on = [d for d in data if d['event'] == 'HEATING-PLUG TURNED ON']
    heating_off = [d for d in data if d['event'] == 'HEATING-PLUG TURNED OFF']
    cooling_on = [d for d in data if d['event'] == 'COOLING-PLUG TURNED ON']
    cooling_off = [d for d in data if d['event'] == 'COOLING-PLUG TURNED OFF']
    
    print(f"  - {len(samples)} SAMPLE events")
    print(f"  - {len(heating_on)} HEATING-PLUG TURNED ON events")
    print(f"  - {len(heating_off)} HEATING-PLUG TURNED OFF events")
    print(f"  - {len(cooling_on)} COOLING-PLUG TURNED ON events")
    print(f"  - {len(cooling_off)} COOLING-PLUG TURNED OFF events")
    
    # Temperature range
    temps = [d['temp_f'] for d in samples]
    print(f"\nTemperature range: {min(temps)}°F - {max(temps)}°F")
    print(f"Tilt color: Blue (active)")
    
    print("\nTest data written to temp_control_log.jsonl")
    print("You can now view the chart at /chart_plotly/Fermenter")

if __name__ == '__main__':
    main()
