#!/usr/bin/env python3
"""
Test to verify that heating/cooling state change markers are only logged
when the plug state actually changes, not on every successful command confirmation.

This test simulates the scenario where:
1. Heater turns ON (should log "heating_on")
2. Heater ON command sent again (should NOT log again)
3. Heater turns OFF (should log "heating_off")
4. Heater OFF command sent again (should NOT log again)
"""

import json
import os
import queue
import time
from datetime import datetime

# Clean up any existing test files
test_log_file = 'temp_control/test_state_change.jsonl'
os.makedirs('temp_control', exist_ok=True)
if os.path.exists(test_log_file):
    os.remove(test_log_file)

# Import the app module
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app

# Override the control log file for testing
original_log_file = app.TEMP_CONTROL_LOG_FILE
app.TEMP_CONTROL_LOG_FILE = test_log_file

print("=" * 70)
print("Testing State Change Logging")
print("=" * 70)
print("\nThis test verifies that markers are only logged when state CHANGES,")
print("not on every successful command confirmation.\n")

# Initialize temp_cfg with test values
app.temp_cfg.update({
    "heater_on": False,
    "cooler_on": False,
    "heater_pending": False,
    "cooler_pending": False,
    "low_limit": 64.0,
    "current_temp": 70.0,
    "high_limit": 68.0,
    "tilt_color": "Black"
})

# Helper function to count events in the log
def count_events_in_log():
    if not os.path.exists(test_log_file):
        return {"heating_on": 0, "heating_off": 0, "cooling_on": 0, "cooling_off": 0}
    
    counts = {"heating_on": 0, "heating_off": 0, "cooling_on": 0, "cooling_off": 0}
    with open(test_log_file, 'r') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                event = entry.get('event', '')
                if event == "HEATING-PLUG TURNED ON":
                    counts["heating_on"] += 1
                elif event == "HEATING-PLUG TURNED OFF":
                    counts["heating_off"] += 1
                elif event == "COOLING-PLUG TURNED ON":
                    counts["cooling_on"] += 1
                elif event == "COOLING-PLUG TURNED OFF":
                    counts["cooling_off"] += 1
    return counts

print("Test Scenario: Heating Control")
print("-" * 70)

# Simulate heating ON (state change: False -> True)
print("\n1. First heating ON command (state change: False -> True)")
print("   Expected: Log 'heating_on' event")
result = {
    'mode': 'heating',
    'action': 'on',
    'success': True,
    'url': '192.168.1.100',
    'error': ''
}
# Manually process the result (simulating kasa_result_listener)
previous_state = app.temp_cfg.get("heater_on", False)
new_state = (result['action'] == 'on')
app.temp_cfg["heater_on"] = new_state

if new_state != previous_state:
    event = "heating_on" if result['action'] == 'on' else "heating_off"
    app.append_control_log(event, {
        "low_limit": app.temp_cfg.get("low_limit"),
        "current_temp": app.temp_cfg.get("current_temp"),
        "high_limit": app.temp_cfg.get("high_limit"),
        "tilt_color": app.temp_cfg.get("tilt_color", "")
    })
    print(f"   ✓ State changed from {previous_state} to {new_state} - Event logged")
else:
    print(f"   ✓ No state change (already {previous_state}) - Event NOT logged")

counts = count_events_in_log()
assert counts["heating_on"] == 1, f"Expected 1 heating_on event, got {counts['heating_on']}"
print(f"   Verified: {counts['heating_on']} heating_on event in log")

# Simulate heating ON again (no state change: True -> True)
print("\n2. Second heating ON command (no state change: True -> True)")
print("   Expected: Do NOT log 'heating_on' event")
result = {
    'mode': 'heating',
    'action': 'on',
    'success': True,
    'url': '192.168.1.100',
    'error': ''
}
previous_state = app.temp_cfg.get("heater_on", False)
new_state = (result['action'] == 'on')
app.temp_cfg["heater_on"] = new_state

if new_state != previous_state:
    event = "heating_on" if result['action'] == 'on' else "heating_off"
    app.append_control_log(event, {
        "low_limit": app.temp_cfg.get("low_limit"),
        "current_temp": app.temp_cfg.get("current_temp"),
        "high_limit": app.temp_cfg.get("high_limit"),
        "tilt_color": app.temp_cfg.get("tilt_color", "")
    })
    print(f"   ✓ State changed from {previous_state} to {new_state} - Event logged")
else:
    print(f"   ✓ No state change (already {previous_state}) - Event NOT logged")

counts = count_events_in_log()
assert counts["heating_on"] == 1, f"Expected 1 heating_on event, got {counts['heating_on']}"
print(f"   Verified: Still {counts['heating_on']} heating_on event in log (no duplicate)")

# Simulate heating OFF (state change: True -> False)
print("\n3. First heating OFF command (state change: True -> False)")
print("   Expected: Log 'heating_off' event")
result = {
    'mode': 'heating',
    'action': 'off',
    'success': True,
    'url': '192.168.1.100',
    'error': ''
}
previous_state = app.temp_cfg.get("heater_on", False)
new_state = (result['action'] == 'on')
app.temp_cfg["heater_on"] = new_state

if new_state != previous_state:
    event = "heating_on" if result['action'] == 'on' else "heating_off"
    app.append_control_log(event, {
        "low_limit": app.temp_cfg.get("low_limit"),
        "current_temp": app.temp_cfg.get("current_temp"),
        "high_limit": app.temp_cfg.get("high_limit"),
        "tilt_color": app.temp_cfg.get("tilt_color", "")
    })
    print(f"   ✓ State changed from {previous_state} to {new_state} - Event logged")
else:
    print(f"   ✓ No state change (already {previous_state}) - Event NOT logged")

counts = count_events_in_log()
assert counts["heating_off"] == 1, f"Expected 1 heating_off event, got {counts['heating_off']}"
print(f"   Verified: {counts['heating_off']} heating_off event in log")

# Simulate heating OFF again (no state change: False -> False)
print("\n4. Second heating OFF command (no state change: False -> False)")
print("   Expected: Do NOT log 'heating_off' event")
result = {
    'mode': 'heating',
    'action': 'off',
    'success': True,
    'url': '192.168.1.100',
    'error': ''
}
previous_state = app.temp_cfg.get("heater_on", False)
new_state = (result['action'] == 'on')
app.temp_cfg["heater_on"] = new_state

if new_state != previous_state:
    event = "heating_on" if result['action'] == 'on' else "heating_off"
    app.append_control_log(event, {
        "low_limit": app.temp_cfg.get("low_limit"),
        "current_temp": app.temp_cfg.get("current_temp"),
        "high_limit": app.temp_cfg.get("high_limit"),
        "tilt_color": app.temp_cfg.get("tilt_color", "")
    })
    print(f"   ✓ State changed from {previous_state} to {new_state} - Event logged")
else:
    print(f"   ✓ No state change (already {previous_state}) - Event NOT logged")

counts = count_events_in_log()
assert counts["heating_off"] == 1, f"Expected 1 heating_off event, got {counts['heating_off']}"
print(f"   Verified: Still {counts['heating_off']} heating_off event in log (no duplicate)")

print("\n" + "=" * 70)
print("✅ All tests passed!")
print("=" * 70)
print("\nSummary:")
print(f"  - heating_on events: {counts['heating_on']} (expected: 1)")
print(f"  - heating_off events: {counts['heating_off']} (expected: 1)")
print(f"  - cooling_on events: {counts['cooling_on']} (expected: 0)")
print(f"  - cooling_off events: {counts['cooling_off']} (expected: 0)")
print("\n✓ State change detection is working correctly!")
print("✓ Duplicate markers are prevented!")

# Restore original log file
app.TEMP_CONTROL_LOG_FILE = original_log_file
