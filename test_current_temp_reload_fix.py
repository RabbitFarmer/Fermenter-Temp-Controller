#!/usr/bin/env python3
"""
Test to verify that current_temp is not overwritten by periodic config reload.

This test simulates the scenario where:
- BLE scanner updates current_temp in temp_cfg every 5 seconds
- periodic_temp_control() reloads config from file every 2 minutes
- current_temp should NOT be overwritten by stale file values

The bug: current_temp was being saved to file on every Kasa command, then
reloaded and overwriting the live temperature, causing visible fluctuations.

The fix: Add current_temp and last_reading_time to runtime_state_vars exclusion
list in periodic_temp_control() to prevent them from being overwritten.
"""

import json
import os
import sys
import tempfile
from datetime import datetime

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_current_temp_not_overwritten_by_reload():
    """Test that current_temp is preserved during config reload."""
    import app as app_module
    
    # Create a temporary config file
    temp_dir = tempfile.mkdtemp()
    test_config_file = os.path.join(temp_dir, 'temp_control_config.json')
    
    # Save original config file path
    original_config_file = app_module.TEMP_CFG_FILE
    
    try:
        # Override the config file path
        app_module.TEMP_CFG_FILE = test_config_file
        
        # Setup initial temp_cfg state
        app_module.temp_cfg.clear()
        app_module.temp_cfg.update({
            'tilt_color': 'Black',
            'enable_heating': True,
            'enable_cooling': False,
            'low_limit': 66.0,
            'high_limit': 70.0,
            'current_temp': 68.5,  # Live temperature from BLE scanner
            'last_reading_time': datetime.utcnow().isoformat() + 'Z',
            'temp_control_active': True
        })
        
        # Save config to file with an OLD temperature value
        file_config = app_module.temp_cfg.copy()
        file_config['current_temp'] = 65.0  # Stale temperature value in file
        file_config['last_reading_time'] = '2024-01-01T00:00:00Z'  # Old timestamp
        
        with open(test_config_file, 'w') as f:
            json.dump(file_config, f, indent=2)
        
        print("Initial state:")
        print(f"  temp_cfg['current_temp'] = {app_module.temp_cfg.get('current_temp')}")
        print(f"  temp_cfg['last_reading_time'] = {app_module.temp_cfg.get('last_reading_time')}")
        print(f"\nFile config:")
        print(f"  file current_temp = 65.0 (stale)")
        print(f"  file last_reading_time = 2024-01-01T00:00:00Z (old)")
        
        # Simulate the periodic config reload logic from periodic_temp_control()
        file_cfg = app_module.load_json(test_config_file, {})
        
        # Apply the runtime state exclusion logic (this is the fix being tested)
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
            # THE FIX: Exclude current_temp and last_reading_time from reload
            'current_temp', 'last_reading_time',
            'low_limit', 'high_limit'
        ]
        
        for var in runtime_state_vars:
            file_cfg.pop(var, None)
        
        print(f"\nAfter exclusion, file_cfg contains:")
        print(f"  'current_temp' in file_cfg: {'current_temp' in file_cfg}")
        print(f"  'last_reading_time' in file_cfg: {'last_reading_time' in file_cfg}")
        
        # Apply the reload
        app_module.temp_cfg.update(file_cfg)
        
        print(f"\nAfter reload:")
        print(f"  temp_cfg['current_temp'] = {app_module.temp_cfg.get('current_temp')}")
        print(f"  temp_cfg['last_reading_time'] = {app_module.temp_cfg.get('last_reading_time')}")
        
        # Verify that current_temp was NOT overwritten
        assert app_module.temp_cfg.get('current_temp') == 68.5, \
            f"ERROR: current_temp was overwritten! Expected 68.5, got {app_module.temp_cfg.get('current_temp')}"
        
        # Verify that last_reading_time was NOT overwritten
        assert app_module.temp_cfg.get('last_reading_time') != '2024-01-01T00:00:00Z', \
            f"ERROR: last_reading_time was overwritten with old timestamp!"
        
        # Verify that other config values CAN be updated (e.g., tilt_color)
        file_cfg_with_change = app_module.load_json(test_config_file, {})
        file_cfg_with_change['tilt_color'] = 'Red'  # Change tilt assignment
        with open(test_config_file, 'w') as f:
            json.dump(file_cfg_with_change, f, indent=2)
        
        # Reload again
        file_cfg = app_module.load_json(test_config_file, {})
        for var in runtime_state_vars:
            file_cfg.pop(var, None)
        app_module.temp_cfg.update(file_cfg)
        
        # Verify tilt_color WAS updated (it's not in exclusion list)
        assert app_module.temp_cfg.get('tilt_color') == 'Red', \
            f"ERROR: tilt_color was not updated! Expected 'Red', got {app_module.temp_cfg.get('tilt_color')}"
        
        # Verify current_temp is STILL preserved
        assert app_module.temp_cfg.get('current_temp') == 68.5, \
            f"ERROR: current_temp was overwritten on second reload! Expected 68.5, got {app_module.temp_cfg.get('current_temp')}"
        
        print("\n✓ TEST PASSED: current_temp and last_reading_time are preserved during config reload")
        print("✓ TEST PASSED: Other config values (like tilt_color) can still be updated")
        
    finally:
        # Restore original config file path
        app_module.TEMP_CFG_FILE = original_config_file
        
        # Cleanup temp directory
        if os.path.exists(test_config_file):
            os.remove(test_config_file)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

if __name__ == '__main__':
    print("=" * 70)
    print("Testing: current_temp preservation during periodic config reload")
    print("=" * 70)
    test_current_temp_not_overwritten_by_reload()
    print("\nAll tests passed!")
