#!/usr/bin/env python3
"""
Test to reproduce issue #289: High and low limits nullified as heater is turned on

This test simulates the exact scenario from the user's logs:
1. Temp control is started with limits 74.0/75.0
2. Heating is turned ON
3. After heating ON, limits become null in subsequent SAMPLE events

This test will help identify the root cause of why limits are being nullified.
"""

import json
import os
import tempfile
import shutil
import time
from datetime import datetime

# Create a temporary test directory
test_dir = tempfile.mkdtemp(prefix="issue_289_test_")
print(f"Test directory: {test_dir}")

# Set up test config paths
TEMP_CFG_FILE = os.path.join(test_dir, "temp_control_config.json")

# Create initial config with limits set
initial_config = {
    "tilt_color": "Black",
    "low_limit": 74.0,
    "high_limit": 75.0,
    "current_temp": 71.0,
    "enable_heating": True,
    "enable_cooling": False,
    "heating_plug": "192.168.1.208",
    "cooling_plug": "",
    "heater_on": False,
    "cooler_on": False,
    "heater_pending": False,
    "cooler_pending": False,
    "temp_control_active": True,
    "temp_control_enabled": True
}

# Write initial config
with open(TEMP_CFG_FILE, 'w') as f:
    json.dump(initial_config, f, indent=2)

print("✓ Initial config written:")
print(f"  - low_limit: {initial_config['low_limit']}")
print(f"  - high_limit: {initial_config['high_limit']}")
print(f"  - heater_on: {initial_config['heater_on']}")

def load_json(path, default=None):
    """Load JSON from file"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

def save_json(path, data):
    """Save JSON to file"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return False

def simulate_kasa_result_listener(temp_cfg, action="on"):
    """
    Simulate kasa_result_listener behavior when heating command succeeds.
    This is the code from lines 3138-3186 in app.py
    """
    print(f"\n[KASA_RESULT] Simulating heating {action} result...")
    
    # This simulates the kasa result processing
    mode = 'heating'
    success = True
    
    temp_cfg["heater_pending"] = False
    temp_cfg["heater_pending_since"] = None
    temp_cfg["heater_pending_action"] = None
    
    if success:
        previous_state = temp_cfg.get("heater_on", False)
        new_state = (action == 'on')
        temp_cfg["heater_on"] = new_state
        temp_cfg["heating_error"] = False
        temp_cfg["heating_error_msg"] = ""
        temp_cfg["heating_error_notified"] = False
        
        print(f"  - Previous state: {previous_state}")
        print(f"  - New state: {new_state}")
        print(f"  - low_limit BEFORE save: {temp_cfg.get('low_limit')}")
        print(f"  - high_limit BEFORE save: {temp_cfg.get('high_limit')}")
        
        # This is line 3186 - the save that happens after heating turns on
        save_json(TEMP_CFG_FILE, temp_cfg)
        
        print(f"  - Config saved to disk")
    
    return temp_cfg

def simulate_periodic_temp_control_reload(temp_cfg):
    """
    Simulate periodic_temp_control loading config from file.
    This is the code from lines 3449-3486 in app.py
    """
    print(f"\n[PERIODIC] Simulating periodic_temp_control reload...")
    
    # Load config from file
    file_cfg = load_json(TEMP_CFG_FILE, {})
    
    print(f"  - Loaded from file:")
    print(f"    - low_limit: {file_cfg.get('low_limit')}")
    print(f"    - high_limit: {file_cfg.get('high_limit')}")
    print(f"    - heater_on: {file_cfg.get('heater_on')}")
    
    # Exclude runtime state variables from file reload
    runtime_state_vars = [
        'heater_on', 'cooler_on',
        'heater_pending', 'cooler_pending',
        'heater_pending_since', 'cooler_pending_since',
        'heater_pending_action', 'cooler_pending_action',
        'heating_error', 'cooling_error',
        'heating_error_msg', 'cooling_error_msg',
        'heating_error_notified', 'cooling_error_notified',
        'heater_baseline_temp', 'heater_baseline_time',
        'cooler_baseline_temp', 'cooler_baseline_time',
        'swapped_plugs_detected', 'swapped_plugs_notified', 'swapped_plug_type',
        'heating_blocked_trigger', 'cooling_blocked_trigger',
        'heating_safety_off_trigger', 'cooling_safety_off_trigger',
        'below_limit_logged', 'above_limit_logged',
        'below_limit_trigger_armed', 'above_limit_trigger_armed',
        'in_range_trigger_armed',
        'safety_shutdown_logged',
        'status',
        'current_temp', 'last_reading_time',
        # CRITICAL: Temperature limits are excluded to prevent corruption
        'low_limit', 'high_limit'
    ]
    
    print(f"  - Popping {len(runtime_state_vars)} runtime state vars...")
    for var in runtime_state_vars:
        file_cfg.pop(var, None)
    
    print(f"  - After popping:")
    print(f"    - low_limit in file_cfg: {'low_limit' in file_cfg}")
    print(f"    - high_limit in file_cfg: {'high_limit' in file_cfg}")
    
    print(f"  - temp_cfg BEFORE update:")
    print(f"    - low_limit: {temp_cfg.get('low_limit')}")
    print(f"    - high_limit: {temp_cfg.get('high_limit')}")
    
    # Update temp_cfg with file_cfg
    temp_cfg.update(file_cfg)
    
    print(f"  - temp_cfg AFTER update:")
    print(f"    - low_limit: {temp_cfg.get('low_limit')}")
    print(f"    - high_limit: {temp_cfg.get('high_limit')}")
    
    return temp_cfg

def test_issue_289_scenario():
    """
    Reproduce the exact scenario from issue #289:
    1. Start with limits set (74.0/75.0)
    2. Turn heating ON
    3. Check if limits are still set after periodic reload
    """
    print("\n" + "="*70)
    print("TEST: Reproducing Issue #289")
    print("="*70)
    
    # Load initial config
    temp_cfg = load_json(TEMP_CFG_FILE)
    
    print(f"\nStep 1: Initial state")
    print(f"  - low_limit: {temp_cfg.get('low_limit')}")
    print(f"  - high_limit: {temp_cfg.get('high_limit')}")
    print(f"  - heater_on: {temp_cfg.get('heater_on')}")
    
    # Simulate heating turned ON (this triggers save_json at line 3186)
    print(f"\nStep 2: Turning heating ON...")
    temp_cfg = simulate_kasa_result_listener(temp_cfg, action="on")
    
    # Simulate periodic_temp_control reload (this happens every 2 minutes)
    print(f"\nStep 3: Periodic reload...")
    temp_cfg = simulate_periodic_temp_control_reload(temp_cfg)
    
    # Check final state
    print(f"\n" + "="*70)
    print("FINAL STATE:")
    print(f"  - low_limit: {temp_cfg.get('low_limit')}")
    print(f"  - high_limit: {temp_cfg.get('high_limit')}")
    print(f"  - heater_on: {temp_cfg.get('heater_on')}")
    print("="*70)
    
    # Verify limits are still set
    if temp_cfg.get('low_limit') == 74.0 and temp_cfg.get('high_limit') == 75.0:
        print("\n✓ TEST PASSED: Limits are preserved after heating ON and periodic reload")
        return True
    else:
        print(f"\n✗ TEST FAILED: Limits were changed!")
        print(f"  Expected: low=74.0, high=75.0")
        print(f"  Got: low={temp_cfg.get('low_limit')}, high={temp_cfg.get('high_limit')}")
        return False

# Run the test
try:
    success = test_issue_289_scenario()
    
    if success:
        print("\nConclusion: The exclusion logic in periodic_temp_control appears to work correctly.")
        print("The bug must be happening somewhere else. Possible causes:")
        print("1. Config file was corrupted with null values before the test")
        print("2. Another code path is setting limits to None")
        print("3. A race condition between threads")
        print("4. The file itself has null values that aren't being properly excluded")
    
    exit(0 if success else 1)
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
finally:
    # Cleanup
    try:
        shutil.rmtree(test_dir)
        print(f"\n✓ Cleaned up test directory: {test_dir}")
    except Exception:
        pass
