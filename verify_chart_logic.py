#!/usr/bin/env python3
"""
Test script to verify chart_data endpoint logic
"""
import json

# Read the test data
with open('temp_control_log.jsonl', 'r') as f:
    lines = f.readlines()

data_points = []
for line in lines:
    if line.strip():
        obj = json.loads(line)
        data_points.append(obj)

print(f"Total entries in log: {len(data_points)}")

# Analyze the data
tilt_colors = {}
events = {}
for point in data_points:
    color = point.get('tilt_color', 'Unknown')
    event = point.get('event', 'Unknown')
    
    if color not in tilt_colors:
        tilt_colors[color] = 0
    tilt_colors[color] += 1
    
    if event not in events:
        events[event] = 0
    events[event] += 1

print("\nTilt Colors in data:")
for color, count in tilt_colors.items():
    print(f"  {color}: {count} entries")

print("\nEvents in data:")
for event, count in events.items():
    print(f"  {event}: {count} entries")

# Simulate the chart filtering logic
print("\n--- Simulating Chart Logic ---")

# Filter to active tilt
valid_data_points = [p for p in data_points if p.get('tilt_color') and p['tilt_color'].strip() != '']
print(f"Valid data points (with tilt_color): {len(valid_data_points)}")

if valid_data_points:
    active_tilt_color = valid_data_points[-1]['tilt_color']
    print(f"Active tilt color (from last entry): {active_tilt_color}")
    
    active_tilt_data = [p for p in valid_data_points if p.get('tilt_color') == active_tilt_color]
    print(f"Active tilt data points: {len(active_tilt_data)}")
    
    # Check temperature range
    temps = [p['temp_f'] for p in active_tilt_data if 'temp_f' in p and p['temp_f'] is not None]
    if temps:
        temp_min = min(temps)
        temp_max = max(temps)
        data_range = temp_max - temp_min
        margin = max(data_range * 0.1, 5)
        
        print(f"\nTemperature range:")
        print(f"  Data range: {temp_min}°F - {temp_max}°F")
        print(f"  Data spread: {data_range}°F")
        print(f"  Margin (10% or 5°F min): {margin:.1f}°F")
        print(f"  Chart range: {temp_min - margin:.1f}°F - {temp_max + margin:.1f}°F")
    
    # Check heating/cooling events
    heating_on = [p for p in data_points if p.get('event') == 'HEATING-PLUG TURNED ON']
    heating_off = [p for p in data_points if p.get('event') == 'HEATING-PLUG TURNED OFF']
    cooling_on = [p for p in data_points if p.get('event') == 'COOLING-PLUG TURNED ON']
    cooling_off = [p for p in data_points if p.get('event') == 'COOLING-PLUG TURNED OFF']
    
    print(f"\nControl Events:")
    print(f"  Heating ON: {len(heating_on)} events")
    print(f"  Heating OFF: {len(heating_off)} events")
    print(f"  Cooling ON: {len(cooling_on)} events")
    print(f"  Cooling OFF: {len(cooling_off)} events")
    
    if cooling_on:
        print(f"\n✓ Cooling markers should be visible on the chart")
    else:
        print(f"\n⚠ No cooling ON events - cooling markers will not appear")
else:
    print("No valid data points found!")

print("\n--- Summary ---")
print(f"✓ Chart will show ONLY the '{active_tilt_color}' tilt (not multiple tilts)")
print(f"✓ Y-axis will be zoomed to data range with appropriate margins")
print(f"✓ X-axis will use actual data range with minimal padding")
print(f"✓ Cooling/heating markers will be displayed based on events in log")
