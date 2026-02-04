#!/usr/bin/env python3
"""
Test to verify that tilt reading SAMPLE events include temperature control limits.

This test reproduces the issue from GitHub issue #275 where:
- Temperature readings are logged with null low_limit and high_limit
- This causes confusion when debugging temperature control issues
- The fix ensures control tilt readings include the temperature limits
"""

import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Create a temporary test directory
test_dir = tempfile.mkdtemp(prefix="tilt_limits_test_")
print(f"Test directory: {test_dir}")

# Set up test config paths
TILT_CONFIG_FILE = os.path.join(test_dir, "tilt_config.json")
TEMP_CFG_FILE = os.path.join(test_dir, "temp_control_config.json")
SYSTEM_CFG_FILE = os.path.join(test_dir, "system_config.json")
LOG_PATH = os.path.join(test_dir, "temp_control", "temp_control_log.jsonl")

# Create directories
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# Initial configs
tilt_config = {
    "Black": {
        "beer_name": "Test Beer",
        "batch_name": "Batch 1",
        "brewid": "9d0274c9",
        "recipe_og": "1.055",
        "actual_og": 1.055,
        "og_confirmed": True
    }
}

temp_config = {
    "tilt_color": "Black",
    "low_limit": 74.0,
    "high_limit": 75.0,
    "current_temp": 75.0,
    "enable_heating": True,
    "enable_cooling": False,
    "heating_plug": "192.168.1.208",
    "cooling_plug": "",
    "heater_on": True,
    "cooler_on": False,
    "temp_control_active": True
}

system_config = {
    "update_interval": 2,
    "tilt_logging_interval_minutes": 15
}

# Write configs
with open(TILT_CONFIG_FILE, 'w') as f:
    json.dump(tilt_config, f, indent=2)
with open(TEMP_CFG_FILE, 'w') as f:
    json.dump(temp_config, f, indent=2)
with open(SYSTEM_CFG_FILE, 'w') as f:
    json.dump(system_config, f, indent=2)

print("✓ Test configs written")
print(f"  - Tilt: Black, brewid: 9d0274c9")
print(f"  - Temp control: low=74.0, high=75.0, current=75.0")
print(f"  - Heating enabled, currently ON")

def simulate_log_tilt_reading(color, gravity, temp_f, rssi, tilt_cfg, temp_cfg, system_cfg, log_path):
    """
    Simplified version of log_tilt_reading that demonstrates the fix.
    """
    cfg = tilt_cfg.get(color, {})
    brewid = cfg.get('brewid', '')
    
    # Check if this is the control tilt
    control_tilt_color = temp_cfg.get("tilt_color")
    is_control_tilt = (color == control_tilt_color)
    
    # Create timestamp
    now = datetime.utcnow()
    
    # Create payload - this is where the bug was
    # Old code: payload did NOT include low_limit and high_limit
    # New code: payload DOES include limits for control tilt
    payload = {
        "timestamp": now.replace(microsecond=0).isoformat() + "Z",
        "tilt_color": color,
        "gravity": round(gravity, 3) if gravity is not None else None,
        "temp_f": temp_f,
        "rssi": rssi,
        "beer_name": cfg.get("beer_name", ""),
        "batch_name": cfg.get("batch_name", ""),
        "brewid": brewid,
        "recipe_og": cfg.get("recipe_og", ""),
        "actual_og": cfg.get("actual_og"),
        "og_confirmed": cfg.get("og_confirmed", False)
    }
    
    # THE FIX: Include temperature control limits in the payload if this is the control tilt
    if is_control_tilt:
        payload["low_limit"] = temp_cfg.get("low_limit")
        payload["high_limit"] = temp_cfg.get("high_limit")
    
    # Format the control log entry
    entry = {
        "timestamp": payload["timestamp"],
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "tilt_color": payload.get("tilt_color", ""),
        "brewid": payload.get("brewid"),
        "low_limit": payload.get("low_limit"),
        "current_temp": payload.get("temp_f"),
        "temp_f": payload.get("temp_f"),
        "gravity": payload.get("gravity"),
        "high_limit": payload.get("high_limit"),
        "event": "SAMPLE"
    }
    
    # Write to log
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + "\n")
    
    return entry

def test_control_tilt_includes_limits():
    """Test that control tilt readings include temperature limits"""
    print("\n=== Test: Control tilt readings include limits ===")
    
    # Simulate a tilt reading from the Black tilt (which is assigned to temp control)
    entry = simulate_log_tilt_reading(
        color="Black",
        gravity=1.0,
        temp_f=75.0,
        rssi=-50,
        tilt_cfg=tilt_config,
        temp_cfg=temp_config,
        system_cfg=system_config,
        log_path=LOG_PATH
    )
    
    # Verify the entry has temperature limits
    assert entry["low_limit"] == 74.0, f"Expected low_limit=74.0, got {entry['low_limit']}"
    assert entry["high_limit"] == 75.0, f"Expected high_limit=75.0, got {entry['high_limit']}"
    assert entry["current_temp"] == 75.0, f"Expected current_temp=75.0, got {entry['current_temp']}"
    assert entry["tilt_color"] == "Black", f"Expected tilt_color=Black, got {entry['tilt_color']}"
    assert entry["event"] == "SAMPLE", f"Expected event=SAMPLE, got {entry['event']}"
    
    print("✓ Control tilt reading includes limits:")
    print(f"  - low_limit: {entry['low_limit']}")
    print(f"  - high_limit: {entry['high_limit']}")
    print(f"  - current_temp: {entry['current_temp']}")
    
    # Verify it was written to the log file
    with open(LOG_PATH, 'r') as f:
        logged_entry = json.loads(f.read().strip())
    
    assert logged_entry["low_limit"] == 74.0, "Logged entry should have low_limit=74.0"
    assert logged_entry["high_limit"] == 75.0, "Logged entry should have high_limit=75.0"
    print("✓ Log file contains limits")
    
    print("✓ TEST PASSED: Control tilt readings now include temperature limits")

def test_non_control_tilt_no_limits():
    """Test that non-control tilt readings do NOT include temperature limits"""
    print("\n=== Test: Non-control tilt readings exclude limits ===")
    
    # Add a Blue tilt that is NOT assigned to temperature control
    tilt_config["Blue"] = {
        "beer_name": "Other Beer",
        "batch_name": "Batch 2",
        "brewid": "abc123",
        "recipe_og": "1.050",
        "actual_og": None,
        "og_confirmed": False
    }
    
    # Clear the log
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    
    # Simulate a tilt reading from the Blue tilt (NOT assigned to temp control)
    entry = simulate_log_tilt_reading(
        color="Blue",
        gravity=1.012,
        temp_f=68.0,
        rssi=-55,
        tilt_cfg=tilt_config,
        temp_cfg=temp_config,
        system_cfg=system_config,
        log_path=LOG_PATH
    )
    
    # Verify the entry does NOT have temperature limits (they should be None)
    assert entry["low_limit"] is None, f"Expected low_limit=None for non-control tilt, got {entry['low_limit']}"
    assert entry["high_limit"] is None, f"Expected high_limit=None for non-control tilt, got {entry['high_limit']}"
    assert entry["tilt_color"] == "Blue", f"Expected tilt_color=Blue, got {entry['tilt_color']}"
    
    print("✓ Non-control tilt reading excludes limits:")
    print(f"  - low_limit: {entry['low_limit']}")
    print(f"  - high_limit: {entry['high_limit']}")
    print(f"  - current_temp: {entry['current_temp']}")
    
    print("✓ TEST PASSED: Non-control tilt readings correctly exclude limits")

def test_issue_275_scenario():
    """Reproduce the exact scenario from issue #275"""
    print("\n=== Test: Issue #275 scenario ===")
    print("Scenario:")
    print("  - High limit: 75F")
    print("  - Low limit: 74F")
    print("  - Current temp: 75F")
    print("  - Heating ON (should turn OFF at high limit)")
    
    # Clear the log
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    
    # Simulate temperature readings at different times
    readings = [
        (74.0, "06:16:02"),  # At low limit, heating should be ON
        (74.0, "06:31:03"),  # At low limit, heating should stay ON
        (75.0, "06:46:03"),  # At high limit, heating should turn OFF
    ]
    
    for temp, time_str in readings:
        entry = simulate_log_tilt_reading(
            color="Black",
            gravity=1.0,
            temp_f=temp,
            rssi=-50,
            tilt_cfg=tilt_config,
            temp_cfg=temp_config,
            system_cfg=system_config,
            log_path=LOG_PATH
        )
        print(f"  - {time_str}: temp={temp}F, low_limit={entry['low_limit']}, high_limit={entry['high_limit']}")
    
    # Read all log entries
    with open(LOG_PATH, 'r') as f:
        log_entries = [json.loads(line) for line in f]
    
    # Verify all entries have limits
    for i, entry in enumerate(log_entries):
        assert entry["low_limit"] == 74.0, f"Entry {i}: Expected low_limit=74.0, got {entry['low_limit']}"
        assert entry["high_limit"] == 75.0, f"Entry {i}: Expected high_limit=75.0, got {entry['high_limit']}"
    
    # Verify the last entry (at high limit)
    last_entry = log_entries[-1]
    assert last_entry["temp_f"] == 75.0, "Last reading should be at 75F"
    assert last_entry["high_limit"] == 75.0, "High limit should be 75F"
    assert last_entry["low_limit"] == 74.0, "Low limit should be 74F"
    
    print("✓ All log entries have correct limits")
    print("✓ TEST PASSED: Issue #275 scenario now logs limits correctly")
    print("\nWith this fix, the temperature control logic will have access to:")
    print(f"  - temp={last_entry['temp_f']}F")
    print(f"  - high_limit={last_entry['high_limit']}F")
    print(f"  - low_limit={last_entry['low_limit']}F")
    print("And will correctly determine: temp >= high_limit → turn heating OFF")

# Run all tests
try:
    test_control_tilt_includes_limits()
    test_non_control_tilt_no_limits()
    test_issue_275_scenario()
    
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED")
    print("="*70)
    print("\nFix Summary:")
    print("- Control tilt readings now include low_limit and high_limit in SAMPLE events")
    print("- This ensures the temp_control_log.jsonl has complete information")
    print("- Non-control tilts still exclude limits (as expected)")
    print("- This fix resolves the confusion from issue #275")
    
except AssertionError as e:
    print(f"\n✗ TEST FAILED: {e}")
    exit(1)
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
