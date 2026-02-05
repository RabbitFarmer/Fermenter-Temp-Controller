#!/usr/bin/env python3
"""
End-to-end demonstration of the inactive Tilt filtering feature.

This script simulates the exact issue described:
- A Tilt was last active 2 hours ago
- Program should NOT list it as active
- Program should NOT display it on main display
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simulate_issue():
    """Simulate the exact issue reported in the GitHub issue."""
    from app import get_active_tilts, live_tilts, system_cfg, update_live_tilt
    
    print("=" * 80)
    print("SIMULATION: Tilt Inactive Detection Fix")
    print("=" * 80)
    print("\nISSUE DESCRIPTION:")
    print("  'Tilt was last active 2 hours ago but program continues to list it as")
    print("   active and continues to display it on main display.'")
    print("\n" + "=" * 80)
    
    # Clear any existing tilts
    live_tilts.clear()
    
    # Set timeout to 60 minutes (default)
    system_cfg['tilt_inactivity_timeout_minutes'] = 60
    
    now = datetime.utcnow()
    
    print("\n[1] SIMULATING INITIAL STATE")
    print("-" * 80)
    print("Tilt 'Red' sends data...")
    
    # Simulate a tilt sending data (this would normally come from BLE)
    update_live_tilt('Red', gravity=1.050, temp_f=68.5, rssi=-75)
    
    print(f"✓ Red Tilt updated at: {live_tilts['Red']['timestamp']}")
    print(f"  Temperature: {live_tilts['Red']['temp_f']}°F")
    print(f"  Gravity: {live_tilts['Red']['gravity']}")
    
    # Check if it shows as active
    active_tilts = get_active_tilts()
    print(f"\nActive Tilts on display: {list(active_tilts.keys())}")
    print(f"Total Tilts in memory: {list(live_tilts.keys())}")
    
    assert 'Red' in active_tilts, "Red should be active"
    print("✓ Red Tilt correctly shows as ACTIVE")
    
    print("\n[2] SIMULATING TIME PASSAGE - 2 HOURS LATER")
    print("-" * 80)
    print("Manually setting Tilt's timestamp to 2 hours ago...")
    
    # Simulate the timestamp being 2 hours old (no new BLE data received)
    old_timestamp = (now - timedelta(hours=2)).replace(microsecond=0).isoformat() + "Z"
    live_tilts['Red']['timestamp'] = old_timestamp
    
    print(f"✓ Red Tilt timestamp set to: {old_timestamp}")
    print(f"  Elapsed time: 2 hours (120 minutes)")
    print(f"  Timeout threshold: {system_cfg.get('tilt_inactivity_timeout_minutes')} minutes")
    
    print("\n[3] CHECKING ACTIVE STATUS")
    print("-" * 80)
    
    # Check active tilts again
    active_tilts_now = get_active_tilts()
    
    print(f"Active Tilts on display: {list(active_tilts_now.keys())}")
    print(f"Total Tilts in memory: {list(live_tilts.keys())}")
    
    # BEFORE THE FIX: The tilt would still show in active_tilts
    # AFTER THE FIX: The tilt should NOT show in active_tilts
    
    if 'Red' in active_tilts_now:
        print("\n✗ FAILED: Red Tilt still shows as ACTIVE (BUG NOT FIXED)")
        print("  The tilt should be hidden after 2 hours of inactivity")
        return False
    else:
        print("\n✓ SUCCESS: Red Tilt correctly shows as INACTIVE")
        print("  The tilt is hidden from the main display")
        print("\n[4] RESULT")
        print("-" * 80)
        print("✓ Issue is FIXED!")
        print("  - Tilts that haven't sent data for 2+ hours are filtered out")
        print("  - They will NOT appear on the main display")
        print("  - They will NOT appear in the /live_snapshot API")
        print("  - The timeout is configurable (default: 60 minutes)")
        return True
    
def demonstrate_configuration():
    """Demonstrate how to configure the timeout."""
    from app import system_cfg
    
    print("\n" + "=" * 80)
    print("CONFIGURATION")
    print("=" * 80)
    print("\nThe inactivity timeout can be configured in system_config.json:")
    print("\n  {")
    print('    "tilt_inactivity_timeout_minutes": 60')
    print("  }")
    print("\nThis setting controls how long a Tilt can be inactive before it's")
    print("hidden from the display.")
    print("\nDefault: 60 minutes")
    print(f"Current: {system_cfg.get('tilt_inactivity_timeout_minutes', 60)} minutes")
    
    print("\n" + "=" * 80)
    print("EXAMPLE SCENARIOS")
    print("=" * 80)
    
    scenarios = [
        (15, "Quick detection - hide inactive tilts after 15 minutes"),
        (30, "Normal detection - hide inactive tilts after 30 minutes"),
        (60, "Default - hide inactive tilts after 1 hour"),
        (120, "Extended - hide inactive tilts after 2 hours"),
    ]
    
    for timeout, description in scenarios:
        print(f"\n  • {timeout} minutes: {description}")

if __name__ == '__main__':
    try:
        success = simulate_issue()
        if success:
            demonstrate_configuration()
            print("\n" + "=" * 80)
            print("END-TO-END TEST PASSED ✓")
            print("=" * 80)
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
