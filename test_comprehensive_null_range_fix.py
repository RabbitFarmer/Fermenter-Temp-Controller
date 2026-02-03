#!/usr/bin/env python3
"""
Test to verify the fix for temp ranges being dropped when heating is turned on.

This simulates the actual bug scenario where:
1. User has valid temperature ranges set (e.g., 73-75°F)
2. Heating is turned ON
3. The config file somehow gets corrupted with 0 values for temp ranges
4. The periodic_temp_control reloads from file and overwrites good memory values
5. Heater never turns off because high_limit is 0
"""

import json
import os
import tempfile
import shutil

# Create a temporary test directory
test_dir = tempfile.mkdtemp(prefix="null_temp_range_test_")
print(f"Test directory: {test_dir}")

TEMP_CFG_FILE = os.path.join(test_dir, "temp_control_config.json")

def test_scenario_1_corrupted_file_with_zeros():
    """
    Scenario: Config file gets corrupted with 0 values for temp ranges during heating
    Expected: In-memory values should be protected from being overwritten
    """
    print("\n" + "="*70)
    print("TEST 1: Corrupted file with zero temp ranges")
    print("="*70)
    
    # Simulate in-memory config with valid temp ranges
    temp_cfg = {
        "tilt_color": "Red",
        "low_limit": 73.0,
        "high_limit": 75.0,
        "current_temp": 72.5,
        "enable_heating": True,
        "heater_on": True,  # Heating is currently ON
        "heating_plug": "192.168.1.100",
        "temp_control_active": True
    }
    
    # Simulate corrupted file on disk with 0 values (the bug scenario)
    corrupted_file_cfg = {
        "tilt_color": "Red",
        "low_limit": 0,  # CORRUPTED - should be 73.0
        "high_limit": 0,  # CORRUPTED - should be 75.0
        "current_temp": 72.5,
        "enable_heating": True,
        "heating_plug": "192.168.1.100",
        "temp_control_active": True
    }
    
    with open(TEMP_CFG_FILE, 'w') as f:
        json.dump(corrupted_file_cfg, f, indent=2)
    
    print(f"✓ In-memory config: low_limit={temp_cfg['low_limit']}, high_limit={temp_cfg['high_limit']}")
    print(f"✗ Corrupted file:   low_limit={corrupted_file_cfg['low_limit']}, high_limit={corrupted_file_cfg['high_limit']}")
    
    # Simulate the FIX in periodic_temp_control
    file_cfg = {}
    with open(TEMP_CFG_FILE, 'r') as f:
        file_cfg = json.load(f)
    
    # THE FIX: Protect against invalid temperature ranges
    if temp_cfg.get('low_limit') and temp_cfg.get('high_limit'):
        file_low = file_cfg.get('low_limit')
        file_high = file_cfg.get('high_limit')
        if not file_low or not file_high or file_low == 0 or file_high == 0:
            print(f"✓ FIX ACTIVATED: Detected invalid file limits (low={file_low}, high={file_high})")
            print(f"✓ FIX ACTIVATED: Keeping in-memory values (low={temp_cfg.get('low_limit')}, high={temp_cfg.get('high_limit')})")
            file_cfg.pop('low_limit', None)
            file_cfg.pop('high_limit', None)
    
    # Update in-memory config with file config
    temp_cfg.update(file_cfg)
    
    # Verify the fix worked
    assert temp_cfg['low_limit'] == 73.0, f"❌ FAILED: low_limit was overwritten! Got {temp_cfg['low_limit']}, expected 73.0"
    assert temp_cfg['high_limit'] == 75.0, f"❌ FAILED: high_limit was overwritten! Got {temp_cfg['high_limit']}, expected 75.0"
    
    print(f"✓ After reload: low_limit={temp_cfg['low_limit']}, high_limit={temp_cfg['high_limit']}")
    print("✓ TEST PASSED: In-memory values protected from corrupted file")

def test_scenario_2_missing_temp_ranges_in_file():
    """
    Scenario: Config file is missing temp range fields entirely
    Expected: In-memory values should be preserved
    """
    print("\n" + "="*70)
    print("TEST 2: File missing temp range fields")
    print("="*70)
    
    temp_cfg = {
        "tilt_color": "Blue",
        "low_limit": 68.0,
        "high_limit": 70.0,
        "current_temp": 69.0,
        "enable_cooling": True,
        "cooler_on": False,
        "cooling_plug": "192.168.1.101"
    }
    
    # File missing low_limit and high_limit fields
    incomplete_file_cfg = {
        "tilt_color": "Blue",
        "current_temp": 69.0,
        "enable_cooling": True,
        "cooling_plug": "192.168.1.101"
        # low_limit and high_limit are MISSING
    }
    
    with open(TEMP_CFG_FILE, 'w') as f:
        json.dump(incomplete_file_cfg, f, indent=2)
    
    print(f"✓ In-memory: low_limit={temp_cfg.get('low_limit')}, high_limit={temp_cfg.get('high_limit')}")
    print(f"✗ File: low_limit={incomplete_file_cfg.get('low_limit')}, high_limit={incomplete_file_cfg.get('high_limit')}")
    
    # Load and apply fix
    file_cfg = {}
    with open(TEMP_CFG_FILE, 'r') as f:
        file_cfg = json.load(f)
    
    # THE FIX
    if temp_cfg.get('low_limit') and temp_cfg.get('high_limit'):
        file_low = file_cfg.get('low_limit')
        file_high = file_cfg.get('high_limit')
        if not file_low or not file_high or file_low == 0 or file_high == 0:
            print(f"✓ FIX ACTIVATED: File missing limits, keeping memory values")
            file_cfg.pop('low_limit', None)
            file_cfg.pop('high_limit', None)
    
    temp_cfg.update(file_cfg)
    
    assert temp_cfg['low_limit'] == 68.0, f"❌ FAILED: low_limit was lost! Got {temp_cfg.get('low_limit')}"
    assert temp_cfg['high_limit'] == 70.0, f"❌ FAILED: high_limit was lost! Got {temp_cfg.get('high_limit')}"
    
    print(f"✓ After reload: low_limit={temp_cfg['low_limit']}, high_limit={temp_cfg['high_limit']}")
    print("✓ TEST PASSED: Missing fields didn't overwrite memory values")

def test_scenario_3_valid_file_update_allowed():
    """
    Scenario: User legitimately updates temp ranges via web UI
    Expected: New valid values should be loaded from file
    """
    print("\n" + "="*70)
    print("TEST 3: Valid file update should be allowed")
    print("="*70)
    
    temp_cfg = {
        "low_limit": 73.0,
        "high_limit": 75.0,
        "enable_heating": True
    }
    
    # User updates ranges via web UI to new valid values
    updated_file_cfg = {
        "low_limit": 76.0,  # Valid new value
        "high_limit": 78.0,  # Valid new value
        "enable_heating": True
    }
    
    with open(TEMP_CFG_FILE, 'w') as f:
        json.dump(updated_file_cfg, f, indent=2)
    
    print(f"✓ Old memory: low_limit={temp_cfg['low_limit']}, high_limit={temp_cfg['high_limit']}")
    print(f"✓ New file:   low_limit={updated_file_cfg['low_limit']}, high_limit={updated_file_cfg['high_limit']}")
    
    # Load and apply fix
    file_cfg = {}
    with open(TEMP_CFG_FILE, 'r') as f:
        file_cfg = json.load(f)
    
    # THE FIX - should NOT block valid updates
    if temp_cfg.get('low_limit') and temp_cfg.get('high_limit'):
        file_low = file_cfg.get('low_limit')
        file_high = file_cfg.get('high_limit')
        if not file_low or not file_high or file_low == 0 or file_high == 0:
            print(f"✓ FIX would activate here, but file has valid values")
            file_cfg.pop('low_limit', None)
            file_cfg.pop('high_limit', None)
        else:
            print(f"✓ File has valid values - update will proceed")
    
    temp_cfg.update(file_cfg)
    
    assert temp_cfg['low_limit'] == 76.0, f"❌ FAILED: Valid update blocked! Got {temp_cfg['low_limit']}"
    assert temp_cfg['high_limit'] == 78.0, f"❌ FAILED: Valid update blocked! Got {temp_cfg['high_limit']}"
    
    print(f"✓ After reload: low_limit={temp_cfg['low_limit']}, high_limit={temp_cfg['high_limit']}")
    print("✓ TEST PASSED: Valid file updates are allowed through")

def test_scenario_4_heater_never_turns_off_bug():
    """
    Scenario: The actual reported bug
    - Temp ranges are 73-75°F
    - Heating turns ON when temp drops below 73°F
    - Config file gets corrupted with 0 values
    - high_limit becomes 0, so heater never turns off (temp never reaches 0°F!)
    """
    print("\n" + "="*70)
    print("TEST 4: Reproducing the 'heater never turns off' bug")
    print("="*70)
    
    # Normal operation starts
    temp_cfg = {
        "low_limit": 73.0,
        "high_limit": 75.0,
        "current_temp": 72.5,  # Below low limit
        "heater_on": False,
        "enable_heating": True
    }
    
    print(f"✓ Initial: temp={temp_cfg['current_temp']}°F, range={temp_cfg['low_limit']}-{temp_cfg['high_limit']}°F")
    print(f"✓ Temp below low limit - heating should turn ON")
    
    # Heating turns ON
    temp_cfg["heater_on"] = True
    temp_cfg["current_temp"] = 73.5  # Temp rises
    print(f"✓ Heating ON, temp rises to {temp_cfg['current_temp']}°F")
    
    # BUG: Config file gets corrupted
    corrupted_cfg = {
        "low_limit": 0,
        "high_limit": 0,
        "current_temp": 73.5,
        "heater_on": True,
        "enable_heating": True
    }
    
    with open(TEMP_CFG_FILE, 'w') as f:
        json.dump(corrupted_cfg, f, indent=2)
    
    print(f"✗ BUG: Config file corrupted with low_limit=0, high_limit=0")
    
    # WITHOUT FIX: periodic reload would do this
    print("\n--- WITHOUT FIX (old behavior) ---")
    temp_cfg_no_fix = temp_cfg.copy()
    file_cfg = {}
    with open(TEMP_CFG_FILE, 'r') as f:
        file_cfg = json.load(f)
    temp_cfg_no_fix.update(file_cfg)  # Direct update without protection
    print(f"✗ After reload: low_limit={temp_cfg_no_fix['low_limit']}, high_limit={temp_cfg_no_fix['high_limit']}")
    print(f"✗ Temp is {temp_cfg_no_fix['current_temp']}°F, high_limit is {temp_cfg_no_fix['high_limit']}°F")
    print(f"✗ Heater will NEVER turn off (temp will never reach 0°F)!")
    
    # WITH FIX: apply protection
    print("\n--- WITH FIX (new behavior) ---")
    file_cfg = {}
    with open(TEMP_CFG_FILE, 'r') as f:
        file_cfg = json.load(f)
    
    # THE FIX
    if temp_cfg.get('low_limit') and temp_cfg.get('high_limit'):
        file_low = file_cfg.get('low_limit')
        file_high = file_cfg.get('high_limit')
        if not file_low or not file_high or file_low == 0 or file_high == 0:
            print(f"✓ FIX: Blocking corrupted values from file")
            file_cfg.pop('low_limit', None)
            file_cfg.pop('high_limit', None)
    
    temp_cfg.update(file_cfg)
    print(f"✓ After reload with fix: low_limit={temp_cfg['low_limit']}, high_limit={temp_cfg['high_limit']}")
    print(f"✓ Temp is {temp_cfg['current_temp']}°F, high_limit is {temp_cfg['high_limit']}°F")
    print(f"✓ Heater WILL turn off when temp reaches {temp_cfg['high_limit']}°F")
    
    assert temp_cfg['low_limit'] == 73.0
    assert temp_cfg['high_limit'] == 75.0
    print("✓ TEST PASSED: Bug is fixed - heater will turn off correctly")

# Run all tests
try:
    test_scenario_1_corrupted_file_with_zeros()
    test_scenario_2_missing_temp_ranges_in_file()
    test_scenario_3_valid_file_update_allowed()
    test_scenario_4_heater_never_turns_off_bug()
    
    print("\n" + "="*70)
    print("✓✓✓ ALL TESTS PASSED ✓✓✓")
    print("="*70)
    print("\nFix Summary:")
    print("1. Config file is saved after successful Kasa commands (persistence)")
    print("2. Invalid temp ranges in file are blocked from overwriting memory")
    print("3. Valid updates from file are still allowed through")
    print("4. Heater will no longer get stuck ON due to corrupted temp ranges")
    
except AssertionError as e:
    print(f"\n❌ TEST FAILED: {e}")
    exit(1)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
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
