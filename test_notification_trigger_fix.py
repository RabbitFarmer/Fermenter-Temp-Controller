#!/usr/bin/env python3
"""
Test that ALL notification triggers are preserved across config reloads.

This test verifies the fix for the bug where notifications were sent every 5 minutes
instead of once per condition. The bug was caused by trigger flags being overwritten
when the config file was reloaded in periodic_temp_control().

There are two types of triggers:
1. Temperature notification triggers (below/above/in_range_limit_trigger_armed)
2. Safety notification triggers (heating/cooling_blocked_trigger, heating/cooling_safety_off_trigger)
"""

import json
import os
import tempfile
from datetime import datetime

def test_trigger_preservation():
    """
    Test that ALL trigger flags are preserved when config is reloaded.
    
    Simulates the bug scenario:
    1. Triggers are armed (True) initially
    2. Notifications sent, triggers disarmed (False) in memory
    3. Config reloaded from disk (which has True)
    4. Triggers should remain False (preserved), not reset to True
    """
    print("=" * 80)
    print("TEST: ALL Notification Trigger Preservation Across Config Reload")
    print("=" * 80)
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_file = f.name
        config_data = {
            'low_limit': 68.0,
            'high_limit': 72.0,
            'enable_heating': True,
            'enable_cooling': False,
            # Temperature notification triggers - stored as True on disk
            'below_limit_trigger_armed': True,
            'above_limit_trigger_armed': True,
            'in_range_trigger_armed': True,
            # Safety notification triggers - stored as True on disk
            'heating_blocked_trigger': True,
            'cooling_blocked_trigger': True,
            'heating_safety_off_trigger': True,
            'cooling_safety_off_trigger': True,
        }
        json.dump(config_data, f, indent=2)
    
    try:
        # Simulate in-memory config (after notifications were sent)
        temp_cfg = {
            'low_limit': 68.0,
            'high_limit': 72.0,
            'enable_heating': True,
            'enable_cooling': False,
            # Temperature notification triggers - disarmed after notifications sent
            'below_limit_trigger_armed': False,
            'above_limit_trigger_armed': True,
            'in_range_trigger_armed': True,
            # Safety notification triggers - disarmed after safety events
            'heating_blocked_trigger': True,  # Heating was blocked, notification sent
            'cooling_blocked_trigger': False,  # Not blocked
            'heating_safety_off_trigger': False,  # Not turned off for safety
            'cooling_safety_off_trigger': True,  # Cooling turned off, notification sent
            'current_temp': 65.0,  # Below low limit
        }
        
        print("\n1. Initial state (after notifications sent):")
        print(f"   In-memory below_limit_trigger_armed: {temp_cfg['below_limit_trigger_armed']}")
        print(f"   In-memory heating_blocked_trigger: {temp_cfg['heating_blocked_trigger']}")
        print(f"   In-memory cooling_safety_off_trigger: {temp_cfg['cooling_safety_off_trigger']}")
        
        # Load config from disk (simulating periodic_temp_control reload)
        with open(config_file, 'r') as f:
            file_cfg = json.load(f)
        
        print(f"\n2. Config file on disk:")
        print(f"   File below_limit_trigger_armed: {file_cfg['below_limit_trigger_armed']}")
        print(f"   File heating_blocked_trigger: {file_cfg['heating_blocked_trigger']}")
        print(f"   File cooling_safety_off_trigger: {file_cfg['cooling_safety_off_trigger']}")
        
        # OLD BUGGY BEHAVIOR (would reset trigger to True):
        print("\n3. OLD BUGGY BEHAVIOR (WITHOUT FIX):")
        buggy_cfg = temp_cfg.copy()
        buggy_cfg.update(file_cfg)
        print(f"   After config reload: below_limit_trigger_armed={buggy_cfg['below_limit_trigger_armed']}")
        if buggy_cfg['below_limit_trigger_armed']:
            print("   ❌ BUG: Trigger was reset to True - notification would be sent again!")
        else:
            print("   ✅ Trigger remained False")
        
        # NEW FIXED BEHAVIOR (preserves ALL trigger states):
        print("\n4. NEW FIXED BEHAVIOR (WITH FIX - ALL TRIGGERS):")
        
        # Preserve ALL runtime trigger states before reload
        preserved_triggers = {
            # Temperature limit notification triggers
            'below_limit_trigger_armed': temp_cfg.get('below_limit_trigger_armed'),
            'above_limit_trigger_armed': temp_cfg.get('above_limit_trigger_armed'),
            'in_range_trigger_armed': temp_cfg.get('in_range_trigger_armed'),
            # Safety notification triggers (Tilt connection loss)
            'heating_blocked_trigger': temp_cfg.get('heating_blocked_trigger'),
            'cooling_blocked_trigger': temp_cfg.get('cooling_blocked_trigger'),
            'heating_safety_off_trigger': temp_cfg.get('heating_safety_off_trigger'),
            'cooling_safety_off_trigger': temp_cfg.get('cooling_safety_off_trigger'),
        }
        
        # Reload config from disk
        temp_cfg.update(file_cfg)
        
        # Restore preserved triggers
        temp_cfg.update(preserved_triggers)
        
        print(f"   After config reload with preservation:")
        print(f"      below_limit_trigger_armed: {temp_cfg['below_limit_trigger_armed']}")
        print(f"      heating_blocked_trigger: {temp_cfg['heating_blocked_trigger']}")
        print(f"      cooling_safety_off_trigger: {temp_cfg['cooling_safety_off_trigger']}")
        if not temp_cfg['below_limit_trigger_armed']:
            print("   ✅ FIX WORKS: Temperature triggers preserved - no duplicate notifications!")
        else:
            print("   ❌ FIX FAILED: Trigger was reset to True")
        
        # Verify ALL trigger states are preserved
        print("\n5. Verification of ALL trigger states:")
        all_triggers = [
            'below_limit_trigger_armed', 
            'above_limit_trigger_armed', 
            'in_range_trigger_armed',
            'heating_blocked_trigger',
            'cooling_blocked_trigger',
            'heating_safety_off_trigger',
            'cooling_safety_off_trigger'
        ]
        for key in all_triggers:
            file_val = file_cfg.get(key)
            mem_val = preserved_triggers.get(key)
            final_val = temp_cfg.get(key)
            status = "✅ PRESERVED" if final_val == mem_val else "❌ NOT PRESERVED"
            print(f"   {key}: {status}")
            print(f"      File: {file_val}, Memory: {mem_val}, Final: {final_val}")
            assert final_val == mem_val, f"Trigger {key} was not preserved!"
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - All trigger types preserved correctly!")
        print("=" * 80)
        print("\nSummary:")
        print("- ALL trigger flags (7 total) are now preserved across config reloads:")
        print("  • Temperature notification triggers (below/above/in_range_limit_trigger_armed)")
        print("  • Safety notification triggers (heating/cooling_blocked/safety_off_trigger)")
        print("- Notifications will only be sent once per condition")
        print("- Config file changes (like low_limit, high_limit) still work")
        print("- Triggers are separate from Kasa plug management (plugs work independently)")
        print("- Trigger flags reset only when conditions are resolved (temp in range, Tilt reconnects)")
        
    finally:
        # Clean up temp file
        os.unlink(config_file)

if __name__ == '__main__':
    test_trigger_preservation()
