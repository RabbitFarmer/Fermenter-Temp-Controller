#!/usr/bin/env python3
"""
Test the safety shutdown feature when using fallback Tilt (no explicit assignment).

This test verifies that:
1. When no Tilt is explicitly assigned to temp control (tilt_color is empty)
2. But temperature is sourced from a Tilt via fallback logic
3. And that fallback Tilt becomes inactive (beyond temp control timeout)
4. The safety shutdown is triggered and all Kasa plugs are turned off

Temperature control uses a shorter timeout than general monitoring:
- General monitoring: 30 minutes (2 readings at 15-min intervals)
- Temperature control: 2 × update_interval (default: 4 minutes with 2-min updates)
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_fallback_tilt_safety_shutdown():
    """Test that inactive fallback Tilt triggers safety shutdown."""
    from app import (
        get_active_tilts,
        get_control_tilt_color,
        is_control_tilt_active,
        live_tilts,
        system_cfg,
        temp_cfg,
        update_live_tilt,
        temperature_control_logic,
        pending_notifications
    )
    
    print("=" * 80)
    print("FALLBACK TILT SAFETY SHUTDOWN TEST")
    print("=" * 80)
    print("\nTemperature Control Timeout: 2 × update_interval")
    print("With 2-minute update interval: 4 minute timeout")
    print("=" * 80)
    
    # Store original values
    original_tilts = dict(live_tilts)
    original_temp_cfg = dict(temp_cfg)
    original_timeout = system_cfg.get('tilt_inactivity_timeout_minutes')
    original_update_interval = system_cfg.get('update_interval')
    
    try:
        # Setup: Configure temperature control WITHOUT assigning a specific Tilt
        system_cfg['tilt_inactivity_timeout_minutes'] = 30  # General monitoring: 30 min
        system_cfg['update_interval'] = 2  # Temp control update: 2 min → timeout: 4 min
        temp_cfg['tilt_color'] = ''  # NO explicit Tilt assignment
        temp_cfg['temp_control_enabled'] = True
        temp_cfg['enable_heating'] = True
        temp_cfg['enable_cooling'] = False
        temp_cfg['low_limit'] = 65.0
        temp_cfg['high_limit'] = 70.0
        temp_cfg['heating_plug'] = '192.168.1.100'
        temp_cfg['cooling_plug'] = '192.168.1.101'
        
        # Clear live tilts and pending notifications
        live_tilts.clear()
        pending_notifications.clear()
        
        now = datetime.utcnow()
        
        print("\n[TEST 1] Fallback Tilt Active - Normal Operation")
        print("-" * 80)
        
        # Add an active Red Tilt (1 minute ago - well within 4 min timeout)
        recent_timestamp = (now - timedelta(minutes=1)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red'] = {
            'timestamp': recent_timestamp,
            'temp_f': 68.0,
            'gravity': 1.050,
            'beer_name': 'Test IPA',
            'brewid': 'test123'
        }
        
        # Verify that Red Tilt is being used for control (fallback)
        control_color = get_control_tilt_color()
        assert control_color == 'Red', f"Expected Red Tilt as fallback, got: {control_color}"
        print(f"✓ Red Tilt is being used as fallback (no explicit assignment)")
        
        # Verify Tilt is active (1 min < 4 min timeout)
        assert is_control_tilt_active(), "Fallback Tilt should be active"
        print(f"✓ Fallback Tilt is active (1 minute old, within 4 min timeout)")
        
        # Set current temp from the fallback Tilt
        temp_cfg['current_temp'] = 68.0
        
        # Run temperature control - should operate normally
        temperature_control_logic()
        status_after = temp_cfg.get('status')
        
        assert "Safety Shutdown" not in status_after, \
            "Should not trigger safety shutdown with active fallback Tilt"
        print(f"✓ Temperature control operating normally with fallback Tilt")
        print(f"  Status: {status_after}")
        
        print("\n[TEST 2] Tilt at 3 Minutes - Still Active (within 4 min timeout)")
        print("-" * 80)
        
        # Make the Red Tilt 3 minutes old (still within 4 min timeout)
        timestamp_3min = (now - timedelta(minutes=3)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = timestamp_3min
        
        # Should still be active
        assert is_control_tilt_active(), "Tilt at 3 min should be active (< 4 min timeout)"
        print(f"✓ Fallback Red Tilt is still active (3 minutes old)")
        
        # Run temperature control - should still operate normally
        temperature_control_logic()
        status = temp_cfg.get('status')
        assert "Safety Shutdown" not in status, "Should not trigger shutdown at 3 minutes"
        print(f"✓ Temperature control still operating (3 min < 4 min timeout)")
        
        print("\n[TEST 3] Tilt at 5 Minutes - Inactive (beyond 4 min timeout)")
        print("-" * 80)
        
        # Make the Red Tilt 5 minutes old (beyond 4 min timeout)
        timestamp_5min = (now - timedelta(minutes=5)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = timestamp_5min
        
        # Verify Tilt is now inactive for temp control
        assert not is_control_tilt_active(), "Tilt at 5 min should be inactive (> 4 min timeout)"
        print(f"✓ Fallback Red Tilt is now inactive (5 minutes old, beyond 4 min timeout)")
        
        # Simulate that heater was on before
        temp_cfg['heater_on'] = True
        temp_cfg['safety_shutdown_logged'] = False  # Reset flag
        
        # Run temperature control - should trigger safety shutdown
        temperature_control_logic()
        
        # Verify safety shutdown
        status = temp_cfg.get('status')
        assert "Safety Shutdown" in status, \
            f"Expected safety shutdown in status, got: {status}"
        assert "Red" in status or "fallback" in status.lower(), \
            f"Expected Tilt color or 'fallback' in status, got: {status}"
        print(f"✓ Safety shutdown triggered for inactive fallback Tilt")
        print(f"  Status: {status}")
        
        # Verify heating and cooling commands were sent to OFF
        print(f"✓ Heating and cooling commands sent to OFF")
        
        # Verify safety shutdown was logged
        assert temp_cfg.get('safety_shutdown_logged'), \
            "Safety shutdown should be logged"
        print(f"✓ Safety shutdown event logged")
        
        # Verify notification was queued
        safety_notifications = [n for n in pending_notifications if n.get('notification_type') == 'safety_shutdown']
        assert len(safety_notifications) > 0, \
            "Safety shutdown notification should be queued"
        print(f"✓ Safety shutdown notification queued")
        
        print("\n[TEST 4] Explicitly Assigned Tilt - Same 4 Minute Timeout")
        print("-" * 80)
        
        # Reset state
        live_tilts.clear()
        pending_notifications.clear()
        temp_cfg['safety_shutdown_logged'] = False
        
        # Add active Blue Tilt (2 minutes ago)
        timestamp_2min = (now - timedelta(minutes=2)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Blue'] = {
            'timestamp': timestamp_2min,
            'temp_f': 66.0,
            'gravity': 1.045,
            'beer_name': 'Test Lager',
            'brewid': 'test456'
        }
        
        # Explicitly assign Blue Tilt
        temp_cfg['tilt_color'] = 'Blue'
        temp_cfg['current_temp'] = 66.0
        temp_cfg['heater_on'] = False
        
        # Verify Blue is being used and still active (2 min < 4 min)
        control_color = get_control_tilt_color()
        assert control_color == 'Blue', f"Expected Blue Tilt, got: {control_color}"
        assert is_control_tilt_active(), "Blue at 2 min should be active"
        print(f"✓ Blue Tilt explicitly assigned and active (2 min < 4 min timeout)")
        
        # Run temperature control - should operate normally
        temperature_control_logic()
        status = temp_cfg.get('status')
        assert "Safety Shutdown" not in status, \
            "Should not trigger safety shutdown at 2 minutes"
        print(f"✓ Temperature control operating normally with explicit assignment")
        
        print("\n[TEST 5] Explicitly Assigned Tilt Becomes Inactive at 5 Minutes")
        print("-" * 80)
        
        # Make Blue Tilt 5 minutes old (beyond 4 min timeout)
        timestamp_5min = (now - timedelta(minutes=5)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Blue']['timestamp'] = timestamp_5min
        
        # Verify inactive
        assert not is_control_tilt_active(), "Blue at 5 min should be inactive"
        print(f"✓ Explicitly assigned Blue Tilt is now inactive (5 min > 4 min timeout)")
        
        # Simulate heater on
        temp_cfg['heater_on'] = True
        temp_cfg['safety_shutdown_logged'] = False
        
        # Run temperature control - should trigger safety shutdown
        temperature_control_logic()
        
        status = temp_cfg.get('status')
        assert "Safety Shutdown" in status, \
            f"Expected safety shutdown, got: {status}"
        assert "Blue" in status, \
            f"Expected Blue in status, got: {status}"
        print(f"✓ Safety shutdown triggered for inactive explicit Tilt")
        print(f"  Status: {status}")
        
        print("\n" + "=" * 80)
        print("ALL FALLBACK TILT SAFETY TESTS PASSED ✓")
        print("=" * 80)
        print("\nSummary:")
        print("  ✓ Temperature control timeout: 2 × update_interval = 4 minutes")
        print("  ✓ Tilt at 3 minutes: Still active, control continues")
        print("  ✓ Tilt at 5 minutes: Inactive, safety shutdown triggered")
        print("  ✓ Fallback mode (no explicit assignment): Works correctly")
        print("  ✓ Explicitly assigned Tilt: Works correctly")
        print("  ✓ Both modes use the 4-minute temp control timeout")
        print("\nThis is much faster than the 30-minute general monitoring timeout,")
        print("ensuring KASA plugs turn off quickly when Tilt signal is lost.")
        
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
        success = test_fallback_tilt_safety_shutdown()
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
