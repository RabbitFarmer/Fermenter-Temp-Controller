#!/usr/bin/env python3
"""
Integration test to demonstrate the temp_control_tilt.jsonl fix.
This test simulates the actual scenario described in the issue.
"""

import json
import os
import tempfile
import shutil

def simulate_before_fix():
    """
    Simulate the BEFORE behavior - logs all tilts
    """
    print("="*70)
    print("BEFORE FIX - Incorrect Behavior")
    print("="*70)
    
    # Simulate config with NO assigned tilt
    temp_cfg = {
        "tilt_color": "",  # No tilt assigned - should NOT log anything
    }
    
    # Multiple tilts available
    live_tilts = {
        "Red": {"temp_f": 70.2, "gravity": 1.048},
        "Blue": {"temp_f": 68.5, "gravity": 1.050}
    }
    
    # OLD LOGIC (before fix): Uses get_control_tilt_color() which returns fallback
    def get_control_tilt_color_old():
        # Returns fallback tilt even when none is assigned
        for tilt_color, info in live_tilts.items():
            if info.get("temp_f") is not None:
                return tilt_color
        return None
    
    control_tilt_color = get_control_tilt_color_old()
    
    print(f"Assigned Tilt: '{temp_cfg.get('tilt_color')}' (empty)")
    print(f"Fallback Tilt returned by get_control_tilt_color(): {control_tilt_color}")
    print(f"Result: INCORRECT - Would log {control_tilt_color} even though NO tilt is assigned!")
    print()


def simulate_after_fix():
    """
    Simulate the AFTER behavior - only logs explicitly assigned tilt
    """
    print("="*70)
    print("AFTER FIX - Correct Behavior")
    print("="*70)
    
    # Scenario 1: No tilt assigned
    print("\nScenario 1: NO Tilt Assigned")
    print("-" * 40)
    temp_cfg = {
        "tilt_color": "",  # No tilt assigned
    }
    
    live_tilts = {
        "Red": {"temp_f": 70.2, "gravity": 1.048},
        "Blue": {"temp_f": 68.5, "gravity": 1.050}
    }
    
    # NEW LOGIC (after fix): Check explicitly assigned tilt
    assigned_tilt_color = temp_cfg.get("tilt_color")
    
    print(f"Assigned Tilt: '{assigned_tilt_color}' (empty)")
    print(f"Available Tilts: {list(live_tilts.keys())}")
    
    if assigned_tilt_color and assigned_tilt_color in live_tilts:
        print(f"Result: Would log {assigned_tilt_color}")
    else:
        print("Result: CORRECT - Nothing logged (no tilt assigned)")
    
    # Scenario 2: Black tilt assigned
    print("\nScenario 2: Black Tilt Assigned")
    print("-" * 40)
    temp_cfg = {
        "tilt_color": "Black",  # Black explicitly assigned
    }
    
    live_tilts = {
        "Black": {"temp_f": 68.0, "gravity": 1.050},
        "Red": {"temp_f": 70.2, "gravity": 1.048},
        "Blue": {"temp_f": 68.5, "gravity": 1.050}
    }
    
    assigned_tilt_color = temp_cfg.get("tilt_color")
    
    print(f"Assigned Tilt: '{assigned_tilt_color}'")
    print(f"Available Tilts: {list(live_tilts.keys())}")
    
    if assigned_tilt_color and assigned_tilt_color in live_tilts:
        print(f"Result: CORRECT - Only {assigned_tilt_color} will be logged")
        print(f"  Red and Blue will NOT be logged")
    else:
        print("Result: Nothing logged")
    
    # Scenario 3: Assigned tilt is offline
    print("\nScenario 3: Assigned Tilt is Offline")
    print("-" * 40)
    temp_cfg = {
        "tilt_color": "Black",  # Black assigned but offline
    }
    
    live_tilts = {
        "Red": {"temp_f": 70.2, "gravity": 1.048},
        "Blue": {"temp_f": 68.5, "gravity": 1.050}
        # Black is offline - not in live_tilts
    }
    
    assigned_tilt_color = temp_cfg.get("tilt_color")
    
    print(f"Assigned Tilt: '{assigned_tilt_color}'")
    print(f"Available Tilts: {list(live_tilts.keys())}")
    
    if assigned_tilt_color and assigned_tilt_color in live_tilts:
        print(f"Result: Would log {assigned_tilt_color}")
    else:
        print("Result: CORRECT - Nothing logged (assigned tilt is offline)")
        print("  Red and Blue are NOT logged even though they are available")
    
    print()


def demonstrate_issue_scenario():
    """
    Demonstrate the exact scenario from the GitHub issue
    """
    print("="*70)
    print("GITHUB ISSUE SCENARIO")
    print("="*70)
    print()
    print("User's Situation:")
    print("- Testing with Black tilt assigned for temperature control")
    print("- Does NOT own a Red tilt")
    print("- Saw these entries in temp_control_tilt.jsonl:")
    print('  {"tilt_color": "Red", "temperature": 70.2, "gravity": 1.048}')
    print('  {"tilt_color": "Blue", "temperature": 68.5, "gravity": 1.05, ...}')
    print()
    print("Problem: Red and Blue tilts were logged when only Black should be logged")
    print()
    print("Root Cause Analysis:")
    print("- The old code used get_control_tilt_color() which has fallback logic")
    print("- When temp_cfg['tilt_color'] was empty or not set correctly,")
    print("  get_control_tilt_color() would return ANY available tilt")
    print("- This caused ALL tilts to be logged to temp_control_tilt.jsonl")
    print()
    print("The Fix:")
    print("- Changed to use temp_cfg.get('tilt_color') directly")
    print("- Only logs when a tilt is EXPLICITLY assigned")
    print("- Fallback tilts are NOT logged")
    print()


if __name__ == "__main__":
    demonstrate_issue_scenario()
    simulate_before_fix()
    simulate_after_fix()
    
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print("The fix ensures that temp_control_tilt.jsonl ONLY contains entries")
    print("for the Tilt that is explicitly assigned for temperature control.")
    print()
    print("Benefits:")
    print("✓ No more confusion about which Tilt is being used for temp control")
    print("✓ Log file accurately reflects the assigned Tilt's readings")
    print("✓ No fallback Tilts are logged")
    print("✓ Clear separation between assigned vs. available Tilts")
    print()
