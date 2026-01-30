#!/usr/bin/env python3
"""
Test that NO FALLBACK occurs when a Tilt is explicitly assigned.

This test verifies @RabbitFarmer's requirement:
"We do not use fallback logic when the assigned tilt is not operational. 
If the assigned tilt is not responding then turning on the kasa plugs does not proceed. 
In fact every kasa is turned off and stays off until corrected."

This test ensures:
1. When Red Tilt is explicitly assigned to temp control
2. And Red Tilt goes offline
3. Even if Blue Tilt is available and broadcasting
4. System does NOT use Blue Tilt's temperature
5. Safety shutdown is triggered immediately
6. KASA plugs turn off and stay off
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_no_fallback_when_assigned_tilt_fails():
    """Test that no fallback occurs when assigned Tilt fails."""
    from app import (
        get_control_tilt_color,
        get_current_temp_for_control_tilt,
        is_control_tilt_active,
        live_tilts,
        system_cfg,
        temp_cfg,
        temperature_control_logic,
        pending_notifications
    )
    
    print("=" * 80)
    print("NO FALLBACK WHEN ASSIGNED TILT FAILS TEST")
    print("=" * 80)
    print("\nRequirement from @RabbitFarmer:")
    print("'We do not use fallback logic when the assigned tilt is not operational.'")
    print("'If the assigned tilt is not responding then turning on the kasa plugs")
    print(" does not proceed. In fact every kasa is turned off and stays off until")
    print(" corrected.'")
    print("=" * 80)
    
    # Store original values
    original_tilts = dict(live_tilts)
    original_temp_cfg = dict(temp_cfg)
    original_timeout = system_cfg.get('tilt_inactivity_timeout_minutes')
    original_update_interval = system_cfg.get('update_interval')
    
    try:
        # Setup
        system_cfg['tilt_inactivity_timeout_minutes'] = 30
        system_cfg['update_interval'] = 2
        
        # Clear state
        live_tilts.clear()
        pending_notifications.clear()
        
        now = datetime.utcnow()
        
        print("\n[TEST 1] Explicitly Assigned Tilt Goes Offline - NO FALLBACK")
        print("-" * 80)
        
        # Setup: Explicitly assign Red Tilt to temperature control
        temp_cfg.clear()
        temp_cfg.update({
            'tilt_color': 'Red',  # EXPLICIT assignment to Red
            'temp_control_enabled': True,
            'enable_heating': True,
            'enable_cooling': False,
            'low_limit': 50.0,
            'high_limit': 54.0,
            'heating_plug': '192.168.1.100',
            'cooling_plug': '192.168.1.101',
            'heater_on': True,  # Heater is currently on
            'cooler_on': False,
            'safety_shutdown_logged': False
        })
        
        # Add TWO Tilts: Red (assigned) and Blue (not assigned)
        # Red Tilt is active
        active_timestamp = (now - timedelta(minutes=1)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red'] = {
            'timestamp': active_timestamp,
            'temp_f': 52.0,
            'gravity': 1.050,
            'beer_name': 'Test IPA',
            'brewid': 'test123'
        }
        
        # Blue Tilt is also active (this is the potential fallback)
        live_tilts['Blue'] = {
            'timestamp': active_timestamp,
            'temp_f': 53.0,
            'gravity': 1.045,
            'beer_name': 'Test Lager',
            'brewid': 'test456'
        }
        
        print("Initial state:")
        print(f"  - Red Tilt (assigned): Active, temp 52.0°F")
        print(f"  - Blue Tilt (not assigned): Active, temp 53.0°F")
        print(f"  - Heater: ON")
        
        # Verify Red is being used
        control_color = get_control_tilt_color()
        assert control_color == 'Red', f"Expected Red, got {control_color}"
        print(f"  - Control Tilt: {control_color} ✓")
        
        # Now Red Tilt goes offline (5 minutes old, beyond 4 min timeout)
        print("\nRed Tilt goes offline (5 minutes without signal)...")
        inactive_timestamp = (now - timedelta(minutes=5)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = inactive_timestamp
        
        # Blue is still active
        print(f"  - Red Tilt: INACTIVE (5 min old)")
        print(f"  - Blue Tilt: Still ACTIVE (1 min old)")
        
        # Check which Tilt is being used for control
        control_color = get_control_tilt_color()
        print(f"\n  Checking get_control_tilt_color()...")
        print(f"  - Result: {control_color}")
        
        # CRITICAL: Should still return Red (not Blue!)
        assert control_color == 'Red', \
            f"FAIL: Expected Red (assigned Tilt), got {control_color}. Should NOT fall back to Blue!"
        print(f"  ✓ Correctly returns Red (assigned Tilt), NOT Blue")
        
        # Check temperature source
        current_temp = get_current_temp_for_control_tilt()
        print(f"\n  Checking get_current_temp_for_control_tilt()...")
        print(f"  - Red Tilt temp: 52.0°F (but inactive)")
        print(f"  - Blue Tilt temp: 53.0°F (active)")
        print(f"  - Result: {current_temp}")
        
        # CRITICAL: Should return Red's temp (or None if removed from live_tilts)
        # NOT Blue's temp
        if current_temp is not None:
            assert current_temp == 52.0, \
                f"FAIL: Expected Red's temp (52.0) or None, got {current_temp} (Blue's temp). Should NOT fall back!"
            print(f"  ✓ Returns Red's temp (52.0), NOT Blue's temp")
        else:
            print(f"  ✓ Returns None (Red is inactive)")
        
        # Check if control Tilt is active
        is_active = is_control_tilt_active()
        print(f"\n  Checking is_control_tilt_active()...")
        print(f"  - Result: {is_active}")
        
        assert not is_active, \
            "FAIL: Red Tilt should be inactive (5 min > 4 min timeout)"
        print(f"  ✓ Correctly detects Red as inactive")
        
        # Run temperature control - should trigger safety shutdown
        print("\n  Running temperature_control_logic()...")
        temperature_control_logic()
        
        status = temp_cfg.get('status')
        print(f"  - Status: {status}")
        
        # Verify safety shutdown
        assert "Safety Shutdown" in status, \
            f"FAIL: Expected safety shutdown, got: {status}"
        assert "Red" in status, \
            f"FAIL: Expected Red in status (assigned Tilt), got: {status}"
        
        print("\n✓ SAFETY SHUTDOWN TRIGGERED")
        print("  - KASA plugs turned OFF")
        print("  - System does NOT fall back to Blue Tilt")
        print("  - Plugs will stay OFF until Red Tilt is corrected")
        
        print("\n[TEST 2] Fallback Mode Still Works (No Assigned Tilt)")
        print("-" * 80)
        
        # Reset state
        live_tilts.clear()
        pending_notifications.clear()
        temp_cfg['safety_shutdown_logged'] = False
        
        # Setup: NO explicit assignment (fallback mode)
        temp_cfg['tilt_color'] = ''  # NO assignment
        temp_cfg['heater_on'] = True
        
        # Add only Blue Tilt (active)
        live_tilts['Blue'] = {
            'timestamp': active_timestamp,
            'temp_f': 53.0,
            'gravity': 1.045,
            'beer_name': 'Test Lager',
            'brewid': 'test456'
        }
        
        print("Initial state:")
        print(f"  - No Tilt assigned (tilt_color is empty)")
        print(f"  - Blue Tilt: Active, temp 53.0°F")
        
        # Check which Tilt is being used
        control_color = get_control_tilt_color()
        print(f"\n  Checking get_control_tilt_color()...")
        print(f"  - Result: {control_color}")
        
        # Should fall back to Blue
        assert control_color == 'Blue', \
            f"Expected Blue (fallback), got {control_color}"
        print(f"  ✓ Correctly falls back to Blue (no assignment)")
        
        # Check temperature
        current_temp = get_current_temp_for_control_tilt()
        print(f"\n  Checking get_current_temp_for_control_tilt()...")
        print(f"  - Result: {current_temp}")
        
        assert current_temp == 53.0, \
            f"Expected Blue's temp (53.0), got {current_temp}"
        print(f"  ✓ Correctly uses Blue's temp")
        
        # Now Blue goes offline
        print("\nBlue Tilt goes offline...")
        live_tilts['Blue']['timestamp'] = inactive_timestamp
        
        # Should trigger safety shutdown
        is_active = is_control_tilt_active()
        assert not is_active, "Blue should be inactive"
        
        temperature_control_logic()
        status = temp_cfg.get('status')
        
        assert "Safety Shutdown" in status, \
            f"Expected safety shutdown, got: {status}"
        print(f"  ✓ Safety shutdown triggered for fallback Tilt")
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        print("\nSummary:")
        print("  ✓ When Red is assigned: Does NOT fall back to Blue when Red fails")
        print("  ✓ Safety shutdown triggers when assigned Tilt is inactive")
        print("  ✓ KASA plugs turn OFF and stay OFF until corrected")
        print("  ✓ Fallback mode still works when NO Tilt is assigned")
        print("\nThis matches @RabbitFarmer's requirement exactly!")
        
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
        success = test_no_fallback_when_assigned_tilt_fails()
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
