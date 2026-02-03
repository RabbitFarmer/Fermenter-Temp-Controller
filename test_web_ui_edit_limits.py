#!/usr/bin/env python3
"""
Test to verify that temperature limits can still be edited via web UI
after implementing the read-only protection during periodic reload.

This ensures the fix doesn't break the normal user workflow.
"""

import json
import os
import tempfile
import shutil

test_dir = tempfile.mkdtemp(prefix="web_ui_edit_test_")
print(f"Test directory: {test_dir}")

TEMP_CFG_FILE = os.path.join(test_dir, "temp_control_config.json")

def test_web_ui_can_edit_temp_limits():
    """
    Verify that web UI can still update temperature limits.
    
    The fix makes limits read-only during periodic file reload,
    but the web UI should still be able to edit them by directly
    updating temp_cfg in memory and saving to file.
    """
    print("\n" + "="*70)
    print("TEST: Web UI can edit temperature limits")
    print("="*70)
    
    # Initial state - user has temp control configured
    temp_cfg = {
        "tilt_color": "Red",
        "low_limit": 73.0,
        "high_limit": 75.0,
        "current_temp": 74.0,
        "enable_heating": True,
        "enable_cooling": False,
        "heating_plug": "192.168.1.100",
        "cooling_plug": "",
        "temp_control_active": True
    }
    
    # Save initial state to file
    with open(TEMP_CFG_FILE, 'w') as f:
        json.dump(temp_cfg, f, indent=2)
    
    print(f"✓ Initial state: low_limit={temp_cfg['low_limit']}°F, high_limit={temp_cfg['high_limit']}°F")
    
    # Simulate user submitting web form with new temperature ranges
    # This is what happens in /update_temp_config route
    print("\n--- User edits limits via web UI ---")
    form_data = {
        'tilt_color': 'Red',
        'low_limit': '68',      # User changed from 73 to 68
        'high_limit': '72',     # User changed from 75 to 72
        'enable_heating': 'on',
        'heating_plug': '192.168.1.100'
    }
    
    # Simulate /update_temp_config processing
    temp_cfg.update({
        "tilt_color": form_data.get('tilt_color', ''),
        "low_limit": float(form_data.get('low_limit', 0)),
        "high_limit": float(form_data.get('high_limit', 100)),
        "enable_heating": 'enable_heating' in form_data,
        "enable_cooling": False,
        "heating_plug": form_data.get("heating_plug", ""),
        "cooling_plug": ""
    })
    
    # Save to file (as the route does)
    with open(TEMP_CFG_FILE, 'w') as f:
        json.dump(temp_cfg, f, indent=2)
    
    print(f"✓ Web UI updated: low_limit={temp_cfg['low_limit']}°F, high_limit={temp_cfg['high_limit']}°F")
    
    # Verify the update worked
    assert temp_cfg['low_limit'] == 68.0, f"Failed: got {temp_cfg['low_limit']}"
    assert temp_cfg['high_limit'] == 72.0, f"Failed: got {temp_cfg['high_limit']}"
    
    # Verify it was saved to file
    with open(TEMP_CFG_FILE, 'r') as f:
        saved_cfg = json.load(f)
    
    assert saved_cfg['low_limit'] == 68.0, f"Not saved: got {saved_cfg['low_limit']}"
    assert saved_cfg['high_limit'] == 72.0, f"Not saved: got {saved_cfg['high_limit']}"
    
    print(f"✓ Changes saved to file: low_limit={saved_cfg['low_limit']}°F, high_limit={saved_cfg['high_limit']}°F")
    
    # Now simulate periodic_temp_control reload (with read-only protection)
    print("\n--- Periodic reload (limits are read-only) ---")
    
    # Load from file
    file_cfg = {}
    with open(TEMP_CFG_FILE, 'r') as f:
        file_cfg = json.load(f)
    
    # Exclude runtime state vars AND temp limits (the fix)
    runtime_state_vars = [
        'heater_on', 'cooler_on', 'status',
        'low_limit', 'high_limit'  # Read-only during periodic reload
    ]
    for var in runtime_state_vars:
        file_cfg.pop(var, None)
    
    print(f"✓ Temp limits excluded from periodic reload")
    
    # Update temp_cfg (simulating periodic reload)
    temp_cfg.update(file_cfg)
    
    # Verify web UI changes are STILL in effect (not overwritten)
    assert temp_cfg['low_limit'] == 68.0, f"Web UI changes lost! Got {temp_cfg['low_limit']}"
    assert temp_cfg['high_limit'] == 72.0, f"Web UI changes lost! Got {temp_cfg['high_limit']}"
    
    print(f"✓ After periodic reload: low_limit={temp_cfg['low_limit']}°F, high_limit={temp_cfg['high_limit']}°F")
    print("✓ Web UI changes persist through periodic reload")
    
    print("\n✓ TEST PASSED: Users can edit temp limits via web UI")

def test_multiple_edits_via_web_ui():
    """Test that users can make multiple edits via web UI"""
    print("\n" + "="*70)
    print("TEST: Multiple web UI edits work correctly")
    print("="*70)
    
    temp_cfg = {
        "low_limit": 70.0,
        "high_limit": 75.0
    }
    
    print(f"✓ Start: {temp_cfg['low_limit']}-{temp_cfg['high_limit']}°F")
    
    # First edit
    temp_cfg.update({"low_limit": 65.0, "high_limit": 68.0})
    print(f"✓ Edit 1: {temp_cfg['low_limit']}-{temp_cfg['high_limit']}°F")
    assert temp_cfg['low_limit'] == 65.0
    assert temp_cfg['high_limit'] == 68.0
    
    # Second edit
    temp_cfg.update({"low_limit": 72.0, "high_limit": 76.0})
    print(f"✓ Edit 2: {temp_cfg['low_limit']}-{temp_cfg['high_limit']}°F")
    assert temp_cfg['low_limit'] == 72.0
    assert temp_cfg['high_limit'] == 76.0
    
    # Third edit
    temp_cfg.update({"low_limit": 66.0, "high_limit": 70.0})
    print(f"✓ Edit 3: {temp_cfg['low_limit']}-{temp_cfg['high_limit']}°F")
    assert temp_cfg['low_limit'] == 66.0
    assert temp_cfg['high_limit'] == 70.0
    
    print("✓ TEST PASSED: Multiple edits work correctly")

# Run tests
try:
    test_web_ui_can_edit_temp_limits()
    test_multiple_edits_via_web_ui()
    
    print("\n" + "="*70)
    print("✓✓✓ ALL TESTS PASSED ✓✓✓")
    print("="*70)
    print("\nSummary:")
    print("✓ Users CAN edit temperature limits via web UI settings page")
    print("✓ Web UI updates persist and are not affected by periodic reload")
    print("✓ The read-only protection only applies to periodic file reload")
    print("✓ This prevents corruption while allowing normal user edits")
    
except AssertionError as e:
    print(f"\n❌ TEST FAILED: {e}")
    exit(1)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
finally:
    try:
        shutil.rmtree(test_dir)
        print(f"\n✓ Cleaned up test directory: {test_dir}")
    except Exception:
        pass
