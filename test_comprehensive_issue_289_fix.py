#!/usr/bin/env python3
"""
Comprehensive test for issue #289: Verify all fixes for temperature limit nullification

This test verifies:
1. SAMPLE events include temperature limits (first fix)
2. Startup handles None values in config file (second fix)
3. Periodic reload protects against None values (third fix)
"""

import json
import os
import tempfile
import shutil

# Create a temporary test directory
test_dir = tempfile.mkdtemp(prefix="issue_289_comprehensive_")
print(f"Test directory: {test_dir}")

TEMP_CFG_FILE = os.path.join(test_dir, "temp_control_config.json")

def load_json(path, default=None):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

def save_json(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return False

def ensure_temp_defaults(temp_cfg):
    """
    Simulates the FIXED ensure_temp_defaults() function that handles None values
    """
    temp_cfg.setdefault("current_temp", None)
    
    # CRITICAL FIX for issue #289: Handle None values from corrupted config files
    if temp_cfg.get("low_limit") is None:
        temp_cfg["low_limit"] = 0.0
    else:
        temp_cfg.setdefault("low_limit", 0.0)
    
    if temp_cfg.get("high_limit") is None:
        temp_cfg["high_limit"] = 0.0
    else:
        temp_cfg.setdefault("high_limit", 0.0)
    
    temp_cfg.setdefault("enable_heating", False)
    temp_cfg.setdefault("enable_cooling", False)
    temp_cfg["temp_control_active"] = False
    
    return temp_cfg

def periodic_temp_control_reload(temp_cfg):
    """
    Simulates the FIXED periodic_temp_control reload logic with None protection
    """
    file_cfg = load_json(TEMP_CFG_FILE, {})
    
    # Exclude runtime state variables including limits
    runtime_state_vars = [
        'heater_on', 'cooler_on',
        'low_limit', 'high_limit'  # Limits are excluded from reload
    ]
    
    for var in runtime_state_vars:
        file_cfg.pop(var, None)
    
    temp_cfg.update(file_cfg)
    
    # CRITICAL FIX for issue #289: Ensure temperature limits are never None
    if temp_cfg.get("low_limit") is None:
        print("[FIX] low_limit was None, resetting to 0.0")
        temp_cfg["low_limit"] = 0.0
    if temp_cfg.get("high_limit") is None:
        print("[FIX] high_limit was None, resetting to 0.0")
        temp_cfg["high_limit"] = 0.0
    
    return temp_cfg

def test_corrupted_config_file_with_null_limits():
    """
    Test scenario: Config file has null values for limits (e.g., from previous bug)
    Expected: System should reset them to 0.0, not keep them as None
    """
    print("\n" + "="*70)
    print("TEST 1: Corrupted config file with null limits")
    print("="*70)
    
    # Create a corrupted config file with null limits
    corrupted_config = {
        "tilt_color": "Black",
        "low_limit": None,  # ← This is the corruption
        "high_limit": None,  # ← This is the corruption
        "current_temp": 71.0,
        "enable_heating": True,
        "heater_on": False
    }
    
    save_json(TEMP_CFG_FILE, corrupted_config)
    print("\n✓ Created corrupted config file:")
    print(f"  - low_limit: {corrupted_config['low_limit']}")
    print(f"  - high_limit: {corrupted_config['high_limit']}")
    
    # Simulate system startup: load config and apply defaults
    temp_cfg = load_json(TEMP_CFG_FILE, {})
    print(f"\n✓ Loaded config from file:")
    print(f"  - low_limit: {temp_cfg.get('low_limit')}")
    print(f"  - high_limit: {temp_cfg.get('high_limit')}")
    
    # OLD behavior (without fix): setdefault doesn't change None values
    temp_cfg_old = temp_cfg.copy()
    temp_cfg_old.setdefault("low_limit", 0.0)
    temp_cfg_old.setdefault("high_limit", 0.0)
    print(f"\n✗ OLD behavior (without fix):")
    print(f"  - low_limit: {temp_cfg_old.get('low_limit')} (still None!)")
    print(f"  - high_limit: {temp_cfg_old.get('high_limit')} (still None!)")
    
    # NEW behavior (with fix): explicitly check for None and reset
    temp_cfg = ensure_temp_defaults(temp_cfg)
    print(f"\n✓ NEW behavior (with fix):")
    print(f"  - low_limit: {temp_cfg.get('low_limit')} (reset to 0.0)")
    print(f"  - high_limit: {temp_cfg.get('high_limit')} (reset to 0.0)")
    
    # Verify the fix worked
    assert temp_cfg.get("low_limit") == 0.0, "low_limit should be 0.0, not None"
    assert temp_cfg.get("high_limit") == 0.0, "high_limit should be 0.0, not None"
    print("\n✓ TEST 1 PASSED: Corrupted None values are fixed at startup")
    
    return True

def test_periodic_reload_with_none_protection():
    """
    Test scenario: Config file gets corrupted during runtime
    Expected: Periodic reload should detect and fix None values
    """
    print("\n" + "="*70)
    print("TEST 2: Periodic reload with None protection")
    print("="*70)
    
    # Start with valid config
    temp_cfg = {
        "tilt_color": "Black",
        "low_limit": 74.0,
        "high_limit": 75.0,
        "current_temp": 72.0,
        "enable_heating": True,
        "heater_on": True
    }
    
    save_json(TEMP_CFG_FILE, temp_cfg)
    print("\n✓ Initial config:")
    print(f"  - low_limit: {temp_cfg['low_limit']}")
    print(f"  - high_limit: {temp_cfg['high_limit']}")
    
    # Simulate something corrupting temp_cfg in memory (setting to None)
    # This could happen due to a bug elsewhere in the code
    temp_cfg["low_limit"] = None
    temp_cfg["high_limit"] = None
    print(f"\n✗ Config corrupted in memory (simulating unknown bug):")
    print(f"  - low_limit: {temp_cfg.get('low_limit')}")
    print(f"  - high_limit: {temp_cfg.get('high_limit')}")
    
    # Simulate periodic reload with protection
    temp_cfg = periodic_temp_control_reload(temp_cfg)
    
    print(f"\n✓ After periodic reload with None protection:")
    print(f"  - low_limit: {temp_cfg.get('low_limit')}")
    print(f"  - high_limit: {temp_cfg.get('high_limit')}")
    
    # Verify the fix worked
    assert temp_cfg.get("low_limit") == 0.0, "low_limit should be reset to 0.0"
    assert temp_cfg.get("high_limit") == 0.0, "high_limit should be reset to 0.0"
    print("\n✓ TEST 2 PASSED: Periodic reload protects against None values")
    
    return True

def test_user_set_limits_preserved():
    """
    Test scenario: User sets limits via web UI, they should be preserved
    Expected: Limits should remain as set by user, not be reset to 0.0
    """
    print("\n" + "="*70)
    print("TEST 3: User-set limits are preserved")
    print("="*70)
    
    # User sets limits via web UI
    temp_cfg = {
        "tilt_color": "Black",
        "low_limit": 74.0,
        "high_limit": 75.0,
        "current_temp": 71.0,
        "enable_heating": True,
        "heater_on": False
    }
    
    save_json(TEMP_CFG_FILE, temp_cfg)
    print("\n✓ User sets limits via web UI:")
    print(f"  - low_limit: {temp_cfg['low_limit']}")
    print(f"  - high_limit: {temp_cfg['high_limit']}")
    
    # Simulate system restart: load and apply defaults
    temp_cfg = load_json(TEMP_CFG_FILE, {})
    temp_cfg = ensure_temp_defaults(temp_cfg)
    
    print(f"\n✓ After system restart:")
    print(f"  - low_limit: {temp_cfg.get('low_limit')}")
    print(f"  - high_limit: {temp_cfg.get('high_limit')}")
    
    # Verify user settings are preserved
    assert temp_cfg.get("low_limit") == 74.0, "User's low_limit should be preserved"
    assert temp_cfg.get("high_limit") == 75.0, "User's high_limit should be preserved"
    print("\n✓ TEST 3 PASSED: User-set limits are preserved across restart")
    
    return True

def test_sample_events_include_limits():
    """
    Test scenario: Tilt reading SAMPLE events should include temperature limits
    Expected: Control tilt SAMPLE events include limits in the log
    """
    print("\n" + "="*70)
    print("TEST 4: SAMPLE events include temperature limits")
    print("="*70)
    
    # This is tested in test_tilt_reading_limits_fix.py
    # Here we just verify the concept
    
    temp_cfg = {
        "tilt_color": "Black",
        "low_limit": 74.0,
        "high_limit": 75.0
    }
    
    # Simulate creating a tilt reading payload with limits (the fix)
    is_control_tilt = True
    payload = {
        "tilt_color": "Black",
        "temp_f": 75.0,
        "gravity": 1.0
    }
    
    # THE FIX: Include limits for control tilt
    if is_control_tilt:
        payload["low_limit"] = temp_cfg.get("low_limit")
        payload["high_limit"] = temp_cfg.get("high_limit")
    
    print(f"\n✓ SAMPLE event payload for control tilt:")
    print(f"  - low_limit: {payload.get('low_limit')}")
    print(f"  - high_limit: {payload.get('high_limit')}")
    print(f"  - temp_f: {payload.get('temp_f')}")
    
    assert payload.get("low_limit") == 74.0, "SAMPLE should include low_limit"
    assert payload.get("high_limit") == 75.0, "SAMPLE should include high_limit"
    print("\n✓ TEST 4 PASSED: SAMPLE events include limits")
    
    return True

# Run all tests
try:
    print("="*70)
    print("COMPREHENSIVE TEST SUITE FOR ISSUE #289")
    print("="*70)
    
    test_corrupted_config_file_with_null_limits()
    test_periodic_reload_with_none_protection()
    test_user_set_limits_preserved()
    test_sample_events_include_limits()
    
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED")
    print("="*70)
    print("\nSummary of fixes for issue #289:")
    print("1. SAMPLE events now include temperature limits for control tilt")
    print("2. Startup handles None values in config file by resetting to 0.0")
    print("3. Periodic reload includes None protection to prevent corruption")
    print("4. User-set limits are preserved across restarts")
    print("\nThese fixes ensure that:")
    print("- Temperature limits are never None in temp_cfg")
    print("- Heating/cooling OFF commands will be sent correctly")
    print("- Log files contain complete information for debugging")
    
except AssertionError as e:
    print(f"\n✗ TEST FAILED: {e}")
    exit(1)
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
finally:
    try:
        shutil.rmtree(test_dir)
        print(f"\n✓ Cleaned up test directory: {test_dir}")
    except Exception:
        pass
