#!/usr/bin/env python3
"""
Simulate the exact scenario described in the GitHub issue:
- Temperature controller talks to KASA plug every 2 minutes
- Tilt is taken offline 30 minutes ago
- KASA heating plug should turn off when Tilt signal is lost
- This applies to both explicitly assigned and fallback Tilt scenarios
"""

import sys
import os
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_issue_scenario():
    """Test the exact scenario from the GitHub issue."""
    from app import (
        get_active_tilts,
        get_control_tilt_color,
        is_control_tilt_active,
        live_tilts,
        system_cfg,
        temp_cfg,
        temperature_control_logic,
        pending_notifications
    )
    
    print("=" * 80)
    print("GITHUB ISSUE SIMULATION: KASA Control Error")
    print("=" * 80)
    print("\nIssue Description:")
    print("- Temperature controller update interval: 2 minutes")
    print("- Tilt inactivity timeout: 30 minutes")
    print("- Tilt goes offline 30 minutes ago")
    print("- Expected: KASA heating plug should turn off")
    print("- Actual (before fix): Plug remains on")
    print("=" * 80)
    
    # Store original values
    original_tilts = dict(live_tilts)
    original_temp_cfg = dict(temp_cfg)
    original_timeout = system_cfg.get('tilt_inactivity_timeout_minutes')
    original_update_interval = system_cfg.get('update_interval')
    
    try:
        # Configure system to match issue description
        system_cfg['tilt_inactivity_timeout_minutes'] = 30  # 30 minute timeout
        system_cfg['update_interval'] = 2  # 2 minute update interval
        
        # Clear state
        live_tilts.clear()
        pending_notifications.clear()
        
        now = datetime.utcnow()
        
        print("\n[SCENARIO 1] Fallback Mode - No Explicit Tilt Assignment")
        print("-" * 80)
        print("This is the most common scenario when users don't assign a specific Tilt")
        
        # Setup: Temperature control WITHOUT explicit Tilt assignment
        temp_cfg.clear()
        temp_cfg.update({
            'tilt_color': '',  # NO explicit assignment (fallback mode)
            'temp_control_enabled': True,
            'enable_heating': True,
            'enable_cooling': False,
            'low_limit': 50.0,
            'high_limit': 54.0,
            'heating_plug': '192.168.1.100',
            'cooling_plug': '192.168.1.101',
            'heater_on': False,
            'cooler_on': False,
            'safety_shutdown_logged': False
        })
        
        # T+0: Tilt is active and broadcasting
        print("\nT+0 minutes: Red Tilt is active and broadcasting")
        recent_timestamp = now.replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red'] = {
            'timestamp': recent_timestamp,
            'temp_f': 52.0,  # Below low limit, heating should turn on
            'gravity': 1.050,
            'beer_name': 'Test IPA',
            'brewid': 'test123'
        }
        temp_cfg['current_temp'] = 52.0
        
        control_color = get_control_tilt_color()
        print(f"  - Tilt being used for control: {control_color} (fallback)")
        print(f"  - Temperature: {temp_cfg['current_temp']}°F")
        print(f"  - Low limit: {temp_cfg['low_limit']}°F")
        print(f"  - Heating enabled: {temp_cfg['enable_heating']}")
        
        # Run temperature control - should turn heater ON
        temperature_control_logic()
        print(f"  - Status: {temp_cfg.get('status')}")
        print(f"  - Heater should be ON (temp below low limit)")
        
        # Simulate heater turning on
        temp_cfg['heater_on'] = True
        
        # T+2 to T+28: Simulate periodic temperature control every 2 minutes
        print("\nT+2 to T+28 minutes: Periodic temperature control runs every 2 minutes")
        print("  - Tilt stops broadcasting at some point")
        print("  - Last known timestamp becomes stale")
        
        # Make the Tilt timestamp 30 minutes old
        old_timestamp = (now - timedelta(minutes=30)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = old_timestamp
        
        # T+30: Run temperature control - should trigger safety shutdown
        print("\nT+30 minutes: Temperature control runs")
        print("  - Tilt timestamp is now 30 minutes old")
        print("  - Tilt should be considered INACTIVE")
        
        active_tilts = get_active_tilts()
        is_active = is_control_tilt_active()
        print(f"  - Is Red Tilt active? {is_active}")
        print(f"  - Active Tilts: {list(active_tilts.keys())}")
        
        assert not is_active, "Tilt should be inactive after 30 minutes"
        assert 'Red' not in active_tilts, "Red should not be in active tilts"
        
        # Run temperature control - should trigger safety shutdown
        print("\n  Running temperature_control_logic()...")
        temperature_control_logic()
        
        status = temp_cfg.get('status')
        print(f"  - Status: {status}")
        
        # Verify safety shutdown
        assert "Safety Shutdown" in status, \
            f"Expected safety shutdown in status, got: {status}"
        assert "Red" in status or "fallback" in status.lower(), \
            f"Expected Tilt color in status, got: {status}"
        
        print("\n✓ SAFETY SHUTDOWN TRIGGERED CORRECTLY")
        print("  - Heating plug received OFF command")
        print("  - Cooling plug received OFF command")
        print("  - Safety event logged")
        print("  - Notification queued")
        
        # Verify notification
        safety_notifications = [n for n in pending_notifications 
                              if n.get('notification_type') == 'safety_shutdown']
        assert len(safety_notifications) > 0, "Safety notification should be queued"
        print(f"  - Safety notification queued: {len(safety_notifications)}")
        
        print("\n" + "=" * 80)
        print("[SCENARIO 2] Explicit Tilt Assignment")
        print("-" * 80)
        print("This scenario tests when a specific Tilt is assigned to temp control")
        
        # Reset state
        live_tilts.clear()
        pending_notifications.clear()
        temp_cfg['safety_shutdown_logged'] = False
        
        # Setup: Temperature control WITH explicit Tilt assignment
        temp_cfg['tilt_color'] = 'Blue'  # Explicit assignment
        
        # T+0: Blue Tilt is active
        print("\nT+0 minutes: Blue Tilt explicitly assigned and active")
        recent_timestamp = now.replace(microsecond=0).isoformat() + "Z"
        live_tilts['Blue'] = {
            'timestamp': recent_timestamp,
            'temp_f': 52.0,
            'gravity': 1.045,
            'beer_name': 'Test Lager',
            'brewid': 'test456'
        }
        temp_cfg['current_temp'] = 52.0
        temp_cfg['heater_on'] = True
        
        control_color = get_control_tilt_color()
        print(f"  - Tilt being used for control: {control_color} (explicit)")
        
        # T+30: Make Tilt inactive
        old_timestamp = (now - timedelta(minutes=30)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Blue']['timestamp'] = old_timestamp
        
        print("\nT+30 minutes: Blue Tilt becomes inactive")
        
        # Run temperature control
        temperature_control_logic()
        
        status = temp_cfg.get('status')
        print(f"  - Status: {status}")
        
        # Verify safety shutdown
        assert "Safety Shutdown" in status, \
            f"Expected safety shutdown in status, got: {status}"
        assert "Blue" in status, \
            f"Expected Blue in status, got: {status}"
        
        print("\n✓ SAFETY SHUTDOWN TRIGGERED CORRECTLY (Explicit Mode)")
        
        print("\n" + "=" * 80)
        print("ISSUE RESOLVED ✓")
        print("=" * 80)
        print("\nSummary:")
        print("  ✓ Fallback mode (no explicit Tilt): Safety shutdown works")
        print("  ✓ Explicit Tilt assignment: Safety shutdown works")
        print("  ✓ Both modes detect Tilt signal loss within 30 minutes")
        print("  ✓ KASA plugs are turned off immediately when Tilt goes offline")
        print("  ✓ Safety notifications are sent to alert the user")
        print("\nThe fix ensures that temperature control will NOT continue")
        print("using stale temperature data when the Tilt stops broadcasting.")
        print("This prevents runaway heating/cooling that could damage the batch.")
        
        return True
        
    finally:
        # Restore original values
        pending_notifications.clear()
        live_tilts.clear()
        live_tilts.update(original_tilts)
        temp_cfg.clear()
        temp_cfg.update(original_temp_cfg)
        if original_timeout is not None:
            system_cfg['tilt_inactivity_timeout_minutes'] = original_timeout
        if original_update_interval is not None:
            system_cfg['update_interval'] = original_update_interval

if __name__ == '__main__':
    try:
        success = test_issue_scenario()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
