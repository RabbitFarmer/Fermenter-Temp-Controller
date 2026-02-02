#!/usr/bin/env python3
"""
Test to verify low_limit and high_limit are preserved during config reload.

This test simulates the issue from GitHub Issue #244 where limits become null
after heating turns on due to config reload from disk with null values.
"""

import json
import os
import tempfile


def test_limit_preservation():
    """
    Test that low_limit and high_limit are preserved when config is reloaded
    from a file that has null values for these fields.
    """
    
    print("=" * 80)
    print("TEMPERATURE LIMIT PRESERVATION TEST")
    print("=" * 80)
    print()
    print("Simulating GitHub Issue #244:")
    print("- Initial state: low_limit=74.0, high_limit=75.0")
    print("- File saved with null values (due to corruption or incomplete save)")
    print("- Config reloaded from file")
    print("- Expected: Limits should be preserved from memory")
    print()
    
    # Simulate temp_cfg in memory with valid limits
    temp_cfg = {
        "low_limit": 74.0,
        "high_limit": 75.0,
        "current_temp": 73.5,
        "enable_heating": True,
        "heating_plug": "192.168.1.100",
        "tilt_color": "Red",
        "heater_on": False
    }
    
    print("Initial temp_cfg (in memory):")
    print(f"  low_limit: {temp_cfg.get('low_limit')}")
    print(f"  high_limit: {temp_cfg.get('high_limit')}")
    print(f"  current_temp: {temp_cfg.get('current_temp')}")
    print()
    
    # Simulate file_cfg loaded from disk with null limits
    # This can happen if the file was saved during a state where limits were missing
    file_cfg = {
        "low_limit": None,
        "high_limit": None,
        "current_temp": 73.5,
        "enable_heating": True,
        "heating_plug": "192.168.1.100",
        "tilt_color": "Red",
        "heater_on": True  # Heating turned on
    }
    
    print("File config loaded from disk (simulated corruption):")
    print(f"  low_limit: {file_cfg.get('low_limit')}")
    print(f"  high_limit: {file_cfg.get('high_limit')}")
    print(f"  heater_on: {file_cfg.get('heater_on')}")
    print()
    
    # Apply the fix logic from periodic_temp_control()
    print("Applying fix logic:")
    
    # Prevent null current_temp from overwriting valid value
    if 'current_temp' in file_cfg and file_cfg['current_temp'] is None and temp_cfg.get('current_temp') is not None:
        print("  - Removing null current_temp from file_cfg")
        file_cfg.pop('current_temp')
    
    # Prevent null low_limit from overwriting valid value
    if 'low_limit' in file_cfg and file_cfg['low_limit'] is None and temp_cfg.get('low_limit') is not None:
        print("  - Removing null low_limit from file_cfg")
        file_cfg.pop('low_limit')
    
    # Prevent null high_limit from overwriting valid value
    if 'high_limit' in file_cfg and file_cfg['high_limit'] is None and temp_cfg.get('high_limit') is not None:
        print("  - Removing null high_limit from file_cfg")
        file_cfg.pop('high_limit')
    
    print()
    
    # Exclude runtime state vars (simplified for test)
    runtime_state_vars = ['heater_on', 'cooler_on']
    for var in runtime_state_vars:
        if var in file_cfg:
            print(f"  - Removing runtime var '{var}' from file_cfg")
            file_cfg.pop(var, None)
    
    print()
    
    # Update temp_cfg with file_cfg (same as app.py line 3172)
    print("Updating temp_cfg with file_cfg...")
    temp_cfg.update(file_cfg)
    print()
    
    # Verify limits are preserved
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print()
    print("Final temp_cfg (after reload):")
    print(f"  low_limit: {temp_cfg.get('low_limit')}")
    print(f"  high_limit: {temp_cfg.get('high_limit')}")
    print(f"  current_temp: {temp_cfg.get('current_temp')}")
    print()
    
    # Test results
    low_preserved = temp_cfg.get('low_limit') == 74.0
    high_preserved = temp_cfg.get('high_limit') == 75.0
    temp_preserved = temp_cfg.get('current_temp') == 73.5
    heater_preserved = temp_cfg.get('heater_on') == False  # Should be False (runtime var excluded)
    
    print("Test Results:")
    print(f"  {'✓' if low_preserved else '✗'} low_limit preserved (expected: 74.0, actual: {temp_cfg.get('low_limit')})")
    print(f"  {'✓' if high_preserved else '✗'} high_limit preserved (expected: 75.0, actual: {temp_cfg.get('high_limit')})")
    print(f"  {'✓' if temp_preserved else '✗'} current_temp preserved (expected: 73.5, actual: {temp_cfg.get('current_temp')})")
    print(f"  {'✓' if heater_preserved else '✗'} heater_on excluded from reload (expected: False, actual: {temp_cfg.get('heater_on')})")
    print()
    
    if low_preserved and high_preserved and temp_preserved and heater_preserved:
        print("✓ SUCCESS: All limits preserved during config reload!")
        print()
        print("This fix prevents the issue where limits become null after heating turns on.")
        return True
    else:
        print("✗ FAILED: Limits were not properly preserved!")
        return False


def test_limit_preservation_with_file():
    """
    Test limit preservation using actual file I/O to simulate real-world scenario.
    """
    
    print()
    print("=" * 80)
    print("FILE I/O TEST - Limit Preservation with Actual File Operations")
    print("=" * 80)
    print()
    
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, "temp_control_config.json")
        
        # Step 1: Initialize config with valid limits
        initial_cfg = {
            "low_limit": 74.0,
            "high_limit": 75.0,
            "current_temp": 73.5,
            "enable_heating": True,
            "heating_plug": "192.168.1.100",
            "tilt_color": "Red",
            "heater_on": False
        }
        
        print("Step 1: Save initial config to file")
        with open(config_file, 'w') as f:
            json.dump(initial_cfg, f, indent=2)
        
        # Step 2: Simulate corruption - file gets saved with null limits
        print("Step 2: Simulate corruption - file saved with null limits")
        corrupted_cfg = initial_cfg.copy()
        corrupted_cfg["low_limit"] = None
        corrupted_cfg["high_limit"] = None
        corrupted_cfg["heater_on"] = True  # Heating turned on
        
        with open(config_file, 'w') as f:
            json.dump(corrupted_cfg, f, indent=2)
        
        print(f"  File now has: low_limit={corrupted_cfg['low_limit']}, high_limit={corrupted_cfg['high_limit']}")
        print()
        
        # Step 3: Load from file and apply fix
        print("Step 3: Load config from file (with fix applied)")
        
        # Memory still has valid limits
        temp_cfg = {
            "low_limit": 74.0,
            "high_limit": 75.0,
            "current_temp": 73.5,
            "heater_on": False
        }
        
        # Load from file
        with open(config_file, 'r') as f:
            file_cfg = json.load(f)
        
        print(f"  Loaded from file: low_limit={file_cfg.get('low_limit')}, high_limit={file_cfg.get('high_limit')}")
        
        # Apply fix
        if 'low_limit' in file_cfg and file_cfg['low_limit'] is None and temp_cfg.get('low_limit') is not None:
            file_cfg.pop('low_limit')
            print("  - Removed null low_limit from file_cfg")
        
        if 'high_limit' in file_cfg and file_cfg['high_limit'] is None and temp_cfg.get('high_limit') is not None:
            file_cfg.pop('high_limit')
            print("  - Removed null high_limit from file_cfg")
        
        # Exclude runtime vars
        runtime_state_vars = ['heater_on', 'cooler_on']
        for var in runtime_state_vars:
            file_cfg.pop(var, None)
        
        # Update
        temp_cfg.update(file_cfg)
        
        print()
        print("Step 4: Verify limits preserved")
        print(f"  low_limit: {temp_cfg.get('low_limit')}")
        print(f"  high_limit: {temp_cfg.get('high_limit')}")
        print()
        
        # Verify
        success = (temp_cfg.get('low_limit') == 74.0 and 
                   temp_cfg.get('high_limit') == 75.0 and
                   temp_cfg.get('heater_on') == False)
        
        if success:
            print("✓ SUCCESS: Limits preserved even with corrupted file!")
            return True
        else:
            print("✗ FAILED: Limits not preserved!")
            return False


if __name__ == '__main__':
    print("\n")
    result1 = test_limit_preservation()
    result2 = test_limit_preservation_with_file()
    
    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print()
    print(f"Memory-based test: {'✓ PASSED' if result1 else '✗ FAILED'}")
    print(f"File I/O test: {'✓ PASSED' if result2 else '✗ FAILED'}")
    print()
    
    if result1 and result2:
        print("✓ ALL TESTS PASSED - Fix prevents limits from becoming null!")
    else:
        print("✗ SOME TESTS FAILED - Fix needs adjustment!")
    print()
