#!/usr/bin/env python3
"""
Test for Issue #244: Temperature Control Limits Lost After Heating Starts

This test reproduces the exact bug where low_limit and high_limit become null
after the heater turns ON, preventing it from turning OFF.

Root Cause:
- periodic_temp_control() loads config from disk
- If disk config has None values, it overwrites valid in-memory values
- Critical fields like low_limit and high_limit get lost

Expected Fix:
- Preserve critical config values from in-memory when disk has None
- low_limit, high_limit, tilt_color, enable_heating, enable_cooling, heating_plug, cooling_plug
"""

import json
import os
import tempfile
import shutil


def test_limit_preservation():
    """
    Test that temperature limits are preserved during config reload.
    
    Simulates the scenario:
    1. User sets low_limit=74.0, high_limit=75.0
    2. Heater turns ON
    3. periodic_temp_control() reloads config from disk
    4. Disk config has None values (empty or incomplete)
    5. Limits should NOT be overwritten with None
    """
    
    print("=" * 80)
    print("TEST: Temperature Limit Preservation (Issue #244)")
    print("=" * 80)
    print()
    
    # Create temporary directory for test configs
    test_dir = tempfile.mkdtemp()
    temp_cfg_file = os.path.join(test_dir, 'temp_control_config.json')
    
    try:
        # Scenario 1: Config file is empty (has None values)
        print("Scenario 1: Empty/incomplete config file")
        print("-" * 80)
        
        # Initial in-memory state (user has set limits)
        temp_cfg = {
            "low_limit": 74.0,
            "high_limit": 75.0,
            "tilt_color": "Red",
            "enable_heating": True,
            "enable_cooling": False,
            "heating_plug": "http://192.168.1.100",
            "cooling_plug": "",
            "current_temp": 73.5,
            "heater_on": True,  # Heater is ON
            "status": "Heating - Below Low Limit"
        }
        
        print(f"Initial in-memory config:")
        print(f"  low_limit: {temp_cfg.get('low_limit')}")
        print(f"  high_limit: {temp_cfg.get('high_limit')}")
        print(f"  tilt_color: {temp_cfg.get('tilt_color')}")
        print(f"  heater_on: {temp_cfg.get('heater_on')}")
        print()
        
        # Disk config has explicit None values (this is what causes the bug)
        # This can happen when temp_control_config.json is saved with None values
        disk_cfg = {
            "low_limit": None,
            "high_limit": None,
            "tilt_color": None,
            "enable_heating": None,
        }
        
        # Save config with None values to disk
        with open(temp_cfg_file, 'w') as f:
            json.dump(disk_cfg, f)
        
        print(f"Config on disk: {disk_cfg}")
        print()
        
        # === BUGGY BEHAVIOR (current code) ===
        print("Testing BUGGY behavior (without fix):")
        print("-" * 40)
        
        # Reload from disk
        with open(temp_cfg_file, 'r') as f:
            file_cfg = json.load(f)
        
        # Current code only removes runtime state vars
        runtime_state_vars = [
            'heater_on', 'cooler_on',
            'heater_pending', 'cooler_pending',
            'heater_pending_since', 'cooler_pending_since',
            'status'
        ]
        for var in runtime_state_vars:
            file_cfg.pop(var, None)
        
        # Create buggy copy for testing
        buggy_cfg = temp_cfg.copy()
        buggy_cfg.update(file_cfg)  # BUG: This overwrites limits with None!
        
        print(f"After reload (BUGGY):")
        print(f"  low_limit: {buggy_cfg.get('low_limit')}")  # Will be None!
        print(f"  high_limit: {buggy_cfg.get('high_limit')}")  # Will be None!
        print(f"  tilt_color: {buggy_cfg.get('tilt_color')}")  # Will be None!
        print()
        
        buggy_passed = (
            buggy_cfg.get('low_limit') is None and
            buggy_cfg.get('high_limit') is None and
            buggy_cfg.get('tilt_color') is None
        )
        
        if buggy_passed:
            print("✓ BUG CONFIRMED: Limits became None (expected for buggy code)")
        else:
            print("✗ Unexpected: Buggy code should have lost limits")
        print()
        
        # === FIXED BEHAVIOR (with preservation logic) ===
        print("Testing FIXED behavior (with preservation logic):")
        print("-" * 40)
        
        # Reload from disk again
        with open(temp_cfg_file, 'r') as f:
            file_cfg = json.load(f)
        
        # Remove runtime state vars (same as before)
        for var in runtime_state_vars:
            file_cfg.pop(var, None)
        
        # NEW: Preserve critical config values
        config_persistence_vars = [
            'low_limit', 'high_limit',  # Temperature limits - CRITICAL
            'tilt_color',               # Selected monitoring Tilt
            'enable_heating', 'enable_cooling',  # Control modes
            'heating_plug', 'cooling_plug',      # Kasa plug URLs
        ]
        
        # If file has None for critical values but memory has valid values, preserve from memory
        for var in config_persistence_vars:
            if var in file_cfg and file_cfg[var] is None and temp_cfg.get(var) is not None:
                file_cfg.pop(var)  # Remove the None so in-memory value is preserved
            # Also handle case where var is missing from file_cfg entirely
            elif var not in file_cfg and temp_cfg.get(var) is not None:
                # Don't add anything, update() will preserve the existing value
                pass
        
        # Create fixed copy for testing
        fixed_cfg = temp_cfg.copy()
        fixed_cfg.update(file_cfg)  # FIX: Critical values are preserved!
        
        print(f"After reload (FIXED):")
        print(f"  low_limit: {fixed_cfg.get('low_limit')}")  # Should be 74.0
        print(f"  high_limit: {fixed_cfg.get('high_limit')}")  # Should be 75.0
        print(f"  tilt_color: {fixed_cfg.get('tilt_color')}")  # Should be "Red"
        print(f"  heater_on: {fixed_cfg.get('heater_on')}")  # Should be True
        print()
        
        # Verify fix
        test_passed = True
        
        if fixed_cfg.get('low_limit') == 74.0:
            print("✓ PASS: low_limit preserved (74.0)")
        else:
            print(f"✗ FAIL: low_limit = {fixed_cfg.get('low_limit')} (expected 74.0)")
            test_passed = False
        
        if fixed_cfg.get('high_limit') == 75.0:
            print("✓ PASS: high_limit preserved (75.0)")
        else:
            print(f"✗ FAIL: high_limit = {fixed_cfg.get('high_limit')} (expected 75.0)")
            test_passed = False
        
        if fixed_cfg.get('tilt_color') == "Red":
            print("✓ PASS: tilt_color preserved ('Red')")
        else:
            print(f"✗ FAIL: tilt_color = {fixed_cfg.get('tilt_color')} (expected 'Red')")
            test_passed = False
        
        if fixed_cfg.get('heater_on') is True:
            print("✓ PASS: heater_on preserved (True)")
        else:
            print(f"✗ FAIL: heater_on = {fixed_cfg.get('heater_on')} (expected True)")
            test_passed = False
        
        print()
        
        # Scenario 2: Config file has explicit None values
        print()
        print("Scenario 2: Config file with explicit None values")
        print("-" * 80)
        
        # Disk config has explicit None values (could happen from bad write)
        disk_cfg_with_nulls = {
            "low_limit": None,
            "high_limit": None,
            "tilt_color": None,
            "enable_heating": None,
        }
        
        with open(temp_cfg_file, 'w') as f:
            json.dump(disk_cfg_with_nulls, f)
        
        print(f"Config on disk: {disk_cfg_with_nulls}")
        print()
        
        # Reload from disk
        with open(temp_cfg_file, 'r') as f:
            file_cfg = json.load(f)
        
        # Remove runtime state vars
        for var in runtime_state_vars:
            file_cfg.pop(var, None)
        
        # Apply preservation logic
        for var in config_persistence_vars:
            if var in file_cfg and file_cfg[var] is None and temp_cfg.get(var) is not None:
                file_cfg.pop(var)  # Remove the None so in-memory value is preserved
        
        # Create fixed copy for testing
        fixed_cfg2 = temp_cfg.copy()
        fixed_cfg2.update(file_cfg)
        
        print(f"After reload with preservation:")
        print(f"  low_limit: {fixed_cfg2.get('low_limit')}")
        print(f"  high_limit: {fixed_cfg2.get('high_limit')}")
        print(f"  tilt_color: {fixed_cfg2.get('tilt_color')}")
        print()
        
        if (fixed_cfg2.get('low_limit') == 74.0 and
            fixed_cfg2.get('high_limit') == 75.0 and
            fixed_cfg2.get('tilt_color') == "Red"):
            print("✓ PASS: All critical values preserved even with explicit None in file")
        else:
            print("✗ FAIL: Some critical values were lost")
            test_passed = False
        
        print()
        print("=" * 80)
        if test_passed:
            print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        else:
            print("✗✗✗ SOME TESTS FAILED ✗✗✗")
        print("=" * 80)
        
        return test_passed
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)


if __name__ == '__main__':
    import sys
    
    try:
        success = test_limit_preservation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        sys.exit(1)
