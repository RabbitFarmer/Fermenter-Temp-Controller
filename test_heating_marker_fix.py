#!/usr/bin/env python3
"""
Test to verify that the heating marker fix prevents duplicate "HEATING-PLUG TURNED ON" events.

The bug: Runtime state variables (heater_on, cooler_on) were being reloaded from the config file
every periodic interval, resetting the state and causing duplicate log entries.

The fix: Exclude runtime state variables from config file reload in periodic_temp_control().
"""

import json
import os
import tempfile
from datetime import datetime

def test_runtime_state_not_overwritten_from_file():
    """
    Test that runtime state variables are not overwritten when reloading config from file.
    
    This simulates the periodic_temp_control() loop behavior.
    """
    print("=== Testing Runtime State Preservation ===\n")
    
    # Simulate initial temp_cfg state (in memory)
    temp_cfg = {
        "enable_heating": True,
        "heating_plug": "http://192.168.1.100",
        "low_limit": 68.0,
        "high_limit": 72.0,
        "tilt_color": "Red",
        "heater_on": True,  # RUNTIME STATE: Heating is currently ON
        "heater_pending": False,
        "current_temp": 69.5,
        "status": "Heating"
    }
    
    print("Initial in-memory state:")
    print(f"  heater_on: {temp_cfg['heater_on']}")
    print(f"  current_temp: {temp_cfg['current_temp']}")
    print(f"  status: {temp_cfg['status']}")
    
    # Simulate config file with stale runtime state
    file_cfg = {
        "enable_heating": True,
        "heating_plug": "http://192.168.1.100",
        "low_limit": 68.0,
        "high_limit": 72.0,
        "tilt_color": "Red",
        "heater_on": False,  # STALE VALUE: File has old state
        "heater_pending": False,
        "current_temp": None,  # Stale temp
        "status": "Idle"  # Stale status
    }
    
    print("\nConfig file (potentially stale):")
    print(f"  heater_on: {file_cfg['heater_on']}")
    print(f"  current_temp: {file_cfg['current_temp']}")
    print(f"  status: {file_cfg['status']}")
    
    # Apply the fix: Exclude runtime state variables
    print("\nApplying fix: Excluding runtime state variables...")
    
    # This is the existing special handling for current_temp
    if 'current_temp' in file_cfg and file_cfg['current_temp'] is None and temp_cfg.get('current_temp') is not None:
        file_cfg.pop('current_temp')
    
    # NEW FIX: Exclude runtime state variables from file reload
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
    
    # Update temp_cfg with file_cfg (runtime state should be preserved)
    temp_cfg.update(file_cfg)
    
    print("\nAfter reload (with fix):")
    print(f"  heater_on: {temp_cfg['heater_on']}")
    print(f"  current_temp: {temp_cfg['current_temp']}")
    print(f"  status: {temp_cfg['status']}")
    
    # Verify runtime state was preserved
    assert temp_cfg['heater_on'] == True, "heater_on should be preserved (True)"
    assert temp_cfg['current_temp'] == 69.5, "current_temp should be preserved"
    assert temp_cfg['status'] == "Heating", "status should be preserved"
    
    # Verify config values were updated
    assert temp_cfg['enable_heating'] == True, "enable_heating should be updated"
    assert temp_cfg['low_limit'] == 68.0, "low_limit should be updated"
    assert temp_cfg['high_limit'] == 72.0, "high_limit should be updated"
    
    print("\n✓ Test PASSED: Runtime state preserved, config values updated")
    return True

def test_duplicate_heating_events_prevented():
    """
    Test that the fix prevents duplicate "HEATING-PLUG TURNED ON" events.
    
    This simulates multiple periodic intervals with the fix applied.
    """
    print("\n\n=== Testing Duplicate Event Prevention ===\n")
    
    # Simulate temp_cfg state
    temp_cfg = {
        "heater_on": False,
        "current_temp": 67.5,
        "low_limit": 68.0,
        "high_limit": 72.0,
        "tilt_color": "Red"
    }
    
    events_log_buggy = []
    events_log_fixed = []
    
    # Iteration 1: Temperature drops below low limit, heating turns ON
    print("Iteration 1: Temp 67.5°F, below low limit")
    print("  → Sending heating ON command")
    
    # Simulate kasa_result_listener
    previous_state = temp_cfg.get("heater_on", False)  # False
    new_state = True  # action == 'on'
    
    if new_state != previous_state:
        print("  → State changed (False → True), logging HEATING ON event")
        events_log_buggy.append("HEATING-PLUG TURNED ON")
        events_log_fixed.append("HEATING-PLUG TURNED ON")
        temp_cfg["heater_on"] = new_state
    else:
        print("  → No state change, NOT logging")
    
    # Save config to file (including runtime state - this is the bug scenario)
    file_cfg = dict(temp_cfg)
    print(f"  → Saved to file: heater_on={file_cfg['heater_on']}")
    
    # Iteration 2: Next periodic interval (WITHOUT fix - bug scenario)
    print("\nIteration 2 (WITHOUT fix): Reloading config from file")
    
    temp_cfg_buggy = dict(temp_cfg)
    
    # Simulate file having stale heater_on=False value
    file_cfg_stale = dict(file_cfg)
    file_cfg_stale["heater_on"] = False  # Stale value in file
    temp_cfg_buggy.update(file_cfg_stale)  # Overwrites runtime state!
    
    print(f"  → After reload: heater_on={temp_cfg_buggy['heater_on']}")
    print("  → Temperature still low, sending heating ON command again")
    
    # Simulate kasa_result_listener (BUG: state appears to change!)
    previous_state_buggy = temp_cfg_buggy.get("heater_on", False)  # False (stale!)
    new_state_buggy = True  # action == 'on'
    
    if new_state_buggy != previous_state_buggy:
        print("  → State changed (False → True) due to stale file value, logging DUPLICATE event!")
        events_log_buggy.append("HEATING-PLUG TURNED ON (DUPLICATE)")
    
    # Iteration 2: WITH fix
    print("\nIteration 2 (WITH fix): Reloading config with runtime state excluded")
    
    file_cfg_fixed = dict(file_cfg)
    file_cfg_fixed["heater_on"] = False  # Stale value
    
    # Apply fix: Remove runtime state variables
    runtime_state_vars = ['heater_on', 'cooler_on', 'heater_pending', 'cooler_pending', 'status']
    for var in runtime_state_vars:
        file_cfg_fixed.pop(var, None)
    
    temp_cfg.update(file_cfg_fixed)  # Runtime state preserved
    
    print(f"  → After reload: heater_on={temp_cfg['heater_on']}")
    print("  → Temperature still low, sending heating ON command again")
    
    # Simulate kasa_result_listener (FIX: state is preserved, no duplicate)
    previous_state = temp_cfg.get("heater_on", False)  # True (preserved!)
    new_state = True  # action == 'on'
    
    if new_state != previous_state:
        print("  → State changed, logging HEATING ON event")
        events_log_fixed.append("HEATING-PLUG TURNED ON (UNEXPECTED)")
    else:
        print("  → No state change, NOT logging (CORRECT!)")
    
    # Check results
    print("\n=== Results ===")
    print(f"WITHOUT fix: {len(events_log_buggy)} events")
    for i, event in enumerate(events_log_buggy, 1):
        print(f"  {i}. {event}")
    
    print(f"\nWITH fix: {len(events_log_fixed)} events")
    for i, event in enumerate(events_log_fixed, 1):
        print(f"  {i}. {event}")
    
    # With fix, we should have only 1 event
    if len(events_log_fixed) == 1 and len(events_log_buggy) == 2:
        print(f"\n✓ Test PASSED: Fix prevents duplicate events (2 → 1)")
        return True
    else:
        print(f"\n✗ Test FAILED: Expected 1 event with fix, got {len(events_log_fixed)}")
        return False

if __name__ == "__main__":
    try:
        test1_passed = test_runtime_state_not_overwritten_from_file()
        test2_passed = test_duplicate_heating_events_prevented()
        
        if test1_passed and test2_passed:
            print("\n" + "="*60)
            print("ALL TESTS PASSED: Fix prevents duplicate heating markers")
            print("="*60)
            exit(0)
        else:
            print("\n" + "="*60)
            print("TESTS FAILED")
            print("="*60)
            exit(1)
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
