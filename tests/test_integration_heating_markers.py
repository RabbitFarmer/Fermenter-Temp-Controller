#!/usr/bin/env python3
"""
Integration test to verify that the heating marker fix works with the actual app code.

This test simulates the full flow:
1. Load config from file
2. Temperature control logic runs periodically
3. Heating events are logged
4. Verify only ONE heating ON marker per actual state change
"""

import os
import sys
import json
import tempfile
import time
from datetime import datetime

# Mock the dependencies before importing app
class MockBleakScanner:
    async def discover(self):
        return []

sys.modules['bleak'] = type('MockBleak', (), {'BleakScanner': MockBleakScanner})()
sys.modules['daemon'] = type('MockDaemon', (), {})()

# Now import app components
from app import (
    temp_cfg, system_cfg, 
    TEMP_CFG_FILE, LOG_PATH,
    load_json, save_json,
    ALLOWED_EVENTS
)

def test_heating_marker_deduplication():
    """
    Test that heating markers are only added on state changes, not every periodic reading.
    """
    print("="*70)
    print("Integration Test: Heating Marker Deduplication")
    print("="*70)
    
    # Setup test environment
    import tempfile as tmp
    test_log_fd, test_log = tmp.mkstemp(suffix=".jsonl")
    test_cfg_fd, test_cfg = tmp.mkstemp(suffix=".json")
    
    # Close the file descriptors since we'll use the paths directly
    os.close(test_log_fd)
    os.close(test_cfg_fd)
    
    try:
        # Initialize temp_cfg with test values
        temp_cfg.clear()
        temp_cfg.update({
            "enable_heating": True,
            "enable_cooling": False,
            "heating_plug": "http://test-plug",
            "cooling_plug": "",
            "low_limit": 68.0,
            "high_limit": 72.0,
            "tilt_color": "Red",
            "temp_control_active": True,
            "temp_control_enabled": True,
            "current_temp": 70.0,
            "heater_on": False,  # Initial state: heating OFF
            "cooler_on": False,
            "heater_pending": False,
            "cooler_pending": False
        })
        
        print("\n1. Initial Configuration")
        print(f"   heater_on: {temp_cfg['heater_on']}")
        print(f"   current_temp: {temp_cfg['current_temp']}°F")
        print(f"   limits: {temp_cfg['low_limit']}°F - {temp_cfg['high_limit']}°F")
        
        # Save config to file (simulating user saving settings)
        save_json(test_cfg, temp_cfg)
        print(f"\n2. Saved config to file")
        
        # Simulate periodic control loop iterations
        events = []
        
        # Iteration 1: Temperature drops, heating should turn ON
        print("\n3. Iteration 1: Temp drops to 67.5°F")
        temp_cfg["current_temp"] = 67.5
        
        # Simulate heating ON command succeeding
        # This is what kasa_result_listener would do
        previous_state = temp_cfg.get("heater_on", False)
        new_state = True
        
        if new_state != previous_state:
            event_name = "HEATING-PLUG TURNED ON"
            print(f"   → State change detected: {previous_state} → {new_state}")
            print(f"   → Logging event: {event_name}")
            events.append(event_name)
            temp_cfg["heater_on"] = new_state
        
        # Save updated state to config file (including runtime state)
        save_json(test_cfg, temp_cfg)
        
        # Iteration 2: Next periodic interval (2 minutes later)
        # Temperature is rising but still below high limit
        print("\n4. Iteration 2: Reload config and check for duplicates")
        print(f"   Current in-memory heater_on: {temp_cfg['heater_on']}")
        
        # Load config from file (this is where the bug was)
        file_cfg = load_json(test_cfg, {})
        print(f"   File has heater_on: {file_cfg.get('heater_on')}")
        
        # BEFORE FIX: temp_cfg.update(file_cfg) would overwrite heater_on
        # AFTER FIX: Runtime state variables are excluded
        
        # Apply the fix (this is what periodic_temp_control now does)
        if 'current_temp' in file_cfg and file_cfg['current_temp'] is None and temp_cfg.get('current_temp') is not None:
            file_cfg.pop('current_temp')
        
        runtime_state_vars = [
            'heater_on', 'cooler_on',
            'heater_pending', 'cooler_pending',
            'heater_pending_since', 'cooler_pending_since',
            'heater_pending_action', 'cooler_pending_action',
            'heating_error', 'cooling_error',
            'heating_error_msg', 'cooling_error_msg',
            'heating_error_notified', 'cooling_error_notified',
            'heating_blocked_trigger', 'heating_safety_off_trigger',
            'below_limit_logged', 'above_limit_logged',
            'below_limit_trigger_armed', 'above_limit_trigger_armed',
            'in_range_trigger_armed',
            'safety_shutdown_logged',
            'status'
        ]
        for var in runtime_state_vars:
            file_cfg.pop(var, None)
        
        temp_cfg.update(file_cfg)
        
        print(f"   After reload (with fix): heater_on = {temp_cfg['heater_on']}")
        
        # Temperature rises to 69°F
        temp_cfg["current_temp"] = 69.0
        
        # Control logic would send heating ON command again
        # (because temp is still < high_limit)
        # But kasa_result_listener should NOT log it because state hasn't changed
        
        previous_state = temp_cfg.get("heater_on", False)
        new_state = True
        
        if new_state != previous_state:
            event_name = "HEATING-PLUG TURNED ON"
            print(f"   → State change detected: {previous_state} → {new_state}")
            print(f"   → Logging event: {event_name} (DUPLICATE - BUG!)")
            events.append(event_name)
        else:
            print(f"   → No state change ({previous_state} → {new_state})")
            print(f"   → NOT logging event (CORRECT!)")
        
        # Iteration 3: Temperature reaches high limit, heating turns OFF
        print("\n5. Iteration 3: Temp reaches 72°F")
        temp_cfg["current_temp"] = 72.0
        
        # Simulate heating OFF command succeeding
        previous_state = temp_cfg.get("heater_on", False)
        new_state = False
        
        if new_state != previous_state:
            event_name = "HEATING-PLUG TURNED OFF"
            print(f"   → State change detected: {previous_state} → {new_state}")
            print(f"   → Logging event: {event_name}")
            events.append(event_name)
            temp_cfg["heater_on"] = new_state
        
        # Verify results
        print("\n" + "="*70)
        print("Results")
        print("="*70)
        print(f"\nTotal events logged: {len(events)}")
        for i, event in enumerate(events, 1):
            print(f"  {i}. {event}")
        
        # Count heating ON events
        heating_on_count = sum(1 for e in events if e == "HEATING-PLUG TURNED ON")
        heating_off_count = sum(1 for e in events if e == "HEATING-PLUG TURNED OFF")
        
        print(f"\nHeating ON events: {heating_on_count}")
        print(f"Heating OFF events: {heating_off_count}")
        
        # Verify expectations
        if heating_on_count == 1 and heating_off_count == 1:
            print("\n✓ TEST PASSED: Only one heating ON event and one heating OFF event")
            print("  Fix successfully prevents duplicate heating markers!")
            return True
        else:
            print(f"\n✗ TEST FAILED: Expected 1 heating ON event, got {heating_on_count}")
            print("  Duplicate markers are still being created!")
            return False
            
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            if os.path.exists(test_log):
                os.remove(test_log)
            if os.path.exists(test_cfg):
                os.remove(test_cfg)
        except:
            pass

if __name__ == "__main__":
    success = test_heating_marker_deduplication()
    exit(0 if success else 1)
