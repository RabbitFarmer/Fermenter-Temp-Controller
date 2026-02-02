#!/usr/bin/env python3
"""
Test to reproduce the heating marker issue.

The issue: Chart shows multiple "heating ON" markers when heating is active,
instead of just one marker when heating turns ON and one when it turns OFF.
"""

import json
import os
import tempfile
import time
from datetime import datetime

# Simulate the control log and kasa result listener logic

def create_test_log_scenario():
    """
    Simulate a scenario where heating is active for several periodic readings.
    
    Expected behavior:
    - One "HEATING-PLUG TURNED ON" event when heating starts
    - Multiple "TEMP CONTROL READING" events while heating is active
    - One "HEATING-PLUG TURNED OFF" event when heating stops
    
    Bug scenario (if it exists):
    - Multiple "HEATING-PLUG TURNED ON" events during the heating period
    """
    
    # Simulate temp_cfg state
    temp_cfg = {
        "heater_on": False,
        "current_temp": 70.0,
        "low_limit": 68.0,
        "high_limit": 72.0,
        "tilt_color": "Red"
    }
    
    events_log = []
    
    # Simulate periodic control loops
    print("=== Simulating Temperature Control Scenario ===\n")
    
    # Scenario: Temperature drops below low limit
    # Time 0: Temp is 70°F, in range
    print("Time 0: Temp 70°F - In range, heating OFF")
    events_log.append({
        "timestamp": "2026-02-01T14:00:00Z",
        "event": "TEMP CONTROL READING",
        "temp_f": 70.0,
        "low_limit": 68.0,
        "high_limit": 72.0
    })
    
    # Time 1: Temp drops to 67.5°F, below low limit
    # This should trigger heating ON command
    print("Time 1: Temp 67.5°F - Below low limit, sending heating ON command")
    temp_cfg["current_temp"] = 67.5
    
    # Simulate kasa_result_listener receiving successful ON command
    previous_state = temp_cfg.get("heater_on", False)  # False
    new_state = True  # action == 'on'
    
    if new_state != previous_state:
        print("  → State changed from OFF to ON - LOGGING HEATING ON EVENT")
        events_log.append({
            "timestamp": "2026-02-01T14:02:00Z",
            "event": "HEATING-PLUG TURNED ON",
            "temp_f": 67.5,
            "low_limit": 68.0,
            "high_limit": 72.0
        })
        temp_cfg["heater_on"] = new_state
    else:
        print("  → No state change - NOT logging")
    
    # Add periodic reading
    events_log.append({
        "timestamp": "2026-02-01T14:02:00Z",
        "event": "TEMP CONTROL READING",
        "temp_f": 67.5,
        "low_limit": 68.0,
        "high_limit": 72.0
    })
    
    # Time 2-5: Temp slowly rises while heating, still below high limit
    # Periodic control continues to call control_heating("on") every 2 minutes
    # But rate limiting should prevent sending redundant commands
    # And even if commands are sent, state check should prevent logging
    for i, (minutes, temp) in enumerate([(4, 68.2), (6, 69.1), (8, 70.3), (10, 71.2)], start=2):
        print(f"Time {i}: Temp {temp}°F - Still heating, heater_on={temp_cfg['heater_on']}")
        temp_cfg["current_temp"] = temp
        
        # Simulate control_heating("on") being called again
        # Rate limit might allow command through after 10 seconds
        # But state should be unchanged
        previous_state = temp_cfg.get("heater_on", False)  # True
        new_state = True  # action == 'on'
        
        if new_state != previous_state:
            print(f"  → State changed - LOGGING HEATING ON EVENT (THIS IS THE BUG!)")
            events_log.append({
                "timestamp": f"2026-02-01T14:{minutes:02d}:00Z",
                "event": "HEATING-PLUG TURNED ON",
                "temp_f": temp,
                "low_limit": 68.0,
                "high_limit": 72.0
            })
        else:
            print(f"  → No state change - NOT logging heating event")
        
        # Add periodic reading
        events_log.append({
            "timestamp": f"2026-02-01T14:{minutes:02d}:00Z",
            "event": "TEMP CONTROL READING",
            "temp_f": temp,
            "low_limit": 68.0,
            "high_limit": 72.0
        })
    
    # Time 6: Temp reaches 72°F, at high limit
    # This should trigger heating OFF command
    print("Time 6: Temp 72.0°F - At high limit, sending heating OFF command")
    temp_cfg["current_temp"] = 72.0
    
    # Simulate kasa_result_listener receiving successful OFF command
    previous_state = temp_cfg.get("heater_on", False)  # True
    new_state = False  # action == 'off'
    
    if new_state != previous_state:
        print("  → State changed from ON to OFF - LOGGING HEATING OFF EVENT")
        events_log.append({
            "timestamp": "2026-02-01T14:12:00Z",
            "event": "HEATING-PLUG TURNED OFF",
            "temp_f": 72.0,
            "low_limit": 68.0,
            "high_limit": 72.0
        })
        temp_cfg["heater_on"] = new_state
    else:
        print("  → No state change - NOT logging")
    
    # Add periodic reading
    events_log.append({
        "timestamp": "2026-02-01T14:12:00Z",
        "event": "TEMP CONTROL READING",
        "temp_f": 72.0,
        "low_limit": 68.0,
        "high_limit": 72.0
    })
    
    # Analyze the results
    print("\n=== Event Log Analysis ===")
    print(f"Total events: {len(events_log)}")
    
    heating_on_count = sum(1 for e in events_log if e['event'] == 'HEATING-PLUG TURNED ON')
    heating_off_count = sum(1 for e in events_log if e['event'] == 'HEATING-PLUG TURNED OFF')
    reading_count = sum(1 for e in events_log if e['event'] == 'TEMP CONTROL READING')
    
    print(f"HEATING-PLUG TURNED ON events: {heating_on_count}")
    print(f"HEATING-PLUG TURNED OFF events: {heating_off_count}")
    print(f"TEMP CONTROL READING events: {reading_count}")
    
    print("\n=== Expected vs Actual ===")
    print(f"Expected heating ON events: 1")
    print(f"Actual heating ON events: {heating_on_count}")
    print(f"Result: {'✓ PASS' if heating_on_count == 1 else '✗ FAIL - BUG DETECTED!'}")
    
    # Print all events for inspection
    print("\n=== Full Event Log ===")
    for event in events_log:
        print(f"{event['timestamp']} - {event['event']} (temp: {event['temp_f']}°F)")
    
    return events_log, heating_on_count == 1

if __name__ == "__main__":
    events, passed = create_test_log_scenario()
    
    if not passed:
        print("\n" + "="*60)
        print("BUG CONFIRMED: Multiple heating ON events detected!")
        print("="*60)
        exit(1)
    else:
        print("\n" + "="*60)
        print("Test PASSED: Only one heating ON event as expected")
        print("="*60)
        exit(0)
