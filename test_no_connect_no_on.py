#!/usr/bin/env python3
"""
Test the simple safety rule: No connection = no plugs turn ON.

This test verifies the user's requested behavior:
"if the kasa plug/s are on, they are shut off. If the kasa plugs are off, 
the ON command is circumvented until signal/connection is restored."

Simple rule:
1. If Tilt connection is lost AND trying to turn plug ON → Block the command
2. If Tilt connection is lost AND plug is ON → Allow turning it OFF
3. If Tilt connection is active → Allow all commands normally
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_no_connect_no_turn_on():
    """Test that plugs cannot turn ON without Tilt connection."""
    from app import (
        is_control_tilt_active,
        live_tilts,
        system_cfg,
        temp_cfg,
        control_heating,
        control_cooling,
        kasa_queue
    )
    
    print("=" * 80)
    print("NO CONNECTION = NO PLUGS TURN ON TEST")
    print("=" * 80)
    print("\nSimple Safety Rule:")
    print("1. No Tilt connection + trying to turn ON → BLOCK")
    print("2. No Tilt connection + plug is ON → Allow turning OFF")
    print("3. Tilt connection active → Allow all commands")
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
        temp_cfg.clear()
        
        # Clear kasa queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        now = datetime.utcnow()
        
        print("\n[TEST 1] Tilt Connection Active - All Commands Allowed")
        print("-" * 80)
        
        # Setup: Red Tilt is active and assigned
        temp_cfg.update({
            'tilt_color': 'Red',
            'tilt_assignment_time': (now - timedelta(minutes=20)).isoformat(),  # Past grace period
            'temp_control_enabled': True,
            'enable_heating': True,
            'enable_cooling': True,
            'low_limit': 50.0,
            'high_limit': 54.0,
            'heating_plug': '192.168.1.100',
            'cooling_plug': '192.168.1.101',
            'heater_on': False,
            'cooler_on': False
        })
        
        # Red Tilt is active (1 minute ago)
        active_timestamp = (now - timedelta(minutes=1)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red'] = {
            'timestamp': active_timestamp,
            'temp_f': 52.0,
            'gravity': 1.050,
            'beer_name': 'Test IPA',
            'brewid': 'test123'
        }
        
        print(f"  - Red Tilt: Active (1 min old)")
        print(f"  - is_control_tilt_active(): {is_control_tilt_active()}")
        
        assert is_control_tilt_active(), "Tilt should be active"
        print(f"  ✓ Tilt connection is active")
        
        # Try to turn heating ON - should succeed
        print(f"\n  Trying to turn heating ON...")
        control_heating("on")
        
        # Check if command was sent
        queue_size_before = kasa_queue.qsize()
        assert queue_size_before > 0, "Heating ON command should be sent when Tilt is active"
        print(f"  ✓ Heating ON command sent (Tilt active)")
        
        # Clear queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        # Try to turn cooling ON - should succeed
        print(f"\n  Trying to turn cooling ON...")
        control_cooling("on")
        
        queue_size = kasa_queue.qsize()
        assert queue_size > 0, "Cooling ON command should be sent when Tilt is active"
        print(f"  ✓ Cooling ON command sent (Tilt active)")
        
        # Clear queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        # Give a moment for any async processing to complete
        import time
        time.sleep(0.5)
        
        print("\n[TEST 2] NO Tilt Connection - BLOCK ON Commands")
        print("-" * 80)
        
        # Make Red Tilt inactive (10 minutes old, beyond 4 min timeout, past grace period)
        inactive_timestamp = (now - timedelta(minutes=10)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = inactive_timestamp
        
        print(f"  - Red Tilt: INACTIVE (10 min old, > 4 min timeout)")
        print(f"  - is_control_tilt_active(): {is_control_tilt_active()}")
        
        assert not is_control_tilt_active(), "Tilt should be inactive"
        print(f"  ✓ Tilt connection is LOST")
        
        # Clear queue before test
        while not kasa_queue.empty():
            kasa_queue.get()
        
        # Try to turn heating ON - should be BLOCKED
        print(f"\n  Trying to turn heating ON (should be BLOCKED)...")
        control_heating("on")
        
        queue_size = kasa_queue.qsize()
        print(f"  Queue size after control_heating('on'): {queue_size}")
        assert queue_size == 0, "Heating ON command should be BLOCKED when Tilt is inactive"
        print(f"  ✓ Heating ON command BLOCKED (no Tilt connection)")
        
        # Try to turn cooling ON - should be BLOCKED
        print(f"\n  Trying to turn cooling ON (should be BLOCKED)...")
        control_cooling("on")
        
        queue_size = kasa_queue.qsize()
        print(f"  Queue size after control_cooling('on'): {queue_size}")
        assert queue_size == 0, "Cooling ON command should be BLOCKED when Tilt is inactive"
        print(f"  ✓ Cooling ON command BLOCKED (no Tilt connection)")
        
        print("\n[TEST 3] NO Tilt Connection + Plugs Are ON - Allow OFF Commands")
        print("-" * 80)
        
        # Simulate that plugs are currently ON (from before Tilt went offline)
        temp_cfg['heater_on'] = True
        temp_cfg['cooler_on'] = True
        
        print(f"  - Heater: ON (was on before Tilt went offline)")
        print(f"  - Cooler: ON (was on before Tilt went offline)")
        print(f"  - Tilt: INACTIVE (no connection)")
        
        # Try to turn heating OFF - should be ALLOWED
        print(f"\n  Trying to turn heating OFF (should be ALLOWED)...")
        control_heating("off")
        
        queue_size = kasa_queue.qsize()
        assert queue_size > 0, "Heating OFF command should be ALLOWED (safety shutdown)"
        print(f"  ✓ Heating OFF command ALLOWED (turning off for safety)")
        
        # Clear queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        # Try to turn cooling OFF - should be ALLOWED
        print(f"\n  Trying to turn cooling OFF (should be ALLOWED)...")
        control_cooling("off")
        
        queue_size = kasa_queue.qsize()
        assert queue_size > 0, "Cooling OFF command should be ALLOWED (safety shutdown)"
        print(f"  ✓ Cooling OFF command ALLOWED (turning off for safety)")
        
        # Clear queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        print("\n[TEST 4] Connection Restored - All Commands Allowed Again")
        print("-" * 80)
        
        # Tilt starts broadcasting again (fresh timestamp)
        fresh_timestamp = now.replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = fresh_timestamp
        
        print(f"  - Red Tilt: Connection restored (fresh broadcast)")
        print(f"  - is_control_tilt_active(): {is_control_tilt_active()}")
        
        assert is_control_tilt_active(), "Tilt should be active again"
        print(f"  ✓ Tilt connection restored")
        
        # Now try to turn heating ON - should succeed again
        print(f"\n  Trying to turn heating ON...")
        control_heating("on")
        
        queue_size = kasa_queue.qsize()
        assert queue_size > 0, "Heating ON command should work again (connection restored)"
        print(f"  ✓ Heating ON command sent (connection restored)")
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        print("\nSummary of Simple Safety Rule:")
        print("  ✓ Tilt active: All commands allowed (normal operation)")
        print("  ✓ Tilt inactive + trying to turn ON: BLOCKED (safety)")
        print("  ✓ Tilt inactive + turning OFF: ALLOWED (safety shutdown)")
        print("  ✓ Connection restored: Normal operation resumes")
        print("\nThis ensures: No connection = No plugs can turn ON")
        
        return True
        
    finally:
        # Restore original values
        live_tilts.clear()
        live_tilts.update(original_tilts)
        temp_cfg.clear()
        temp_cfg.update(original_temp_cfg)
        if original_timeout is not None:
            system_cfg['tilt_inactivity_timeout_minutes'] = original_timeout
        if original_update_interval is not None:
            system_cfg['update_interval'] = original_update_interval
        
        # Clear queue
        while not kasa_queue.empty():
            kasa_queue.get()

if __name__ == '__main__':
    try:
        success = test_no_connect_no_turn_on()
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
