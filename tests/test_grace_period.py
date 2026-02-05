#!/usr/bin/env python3
"""
Test the grace period for newly assigned Tilts in temperature control.

This test verifies that:
1. When a Tilt is newly assigned to temperature control
2. There's a 15-minute grace period
3. During this grace period, safety shutdown does NOT trigger even if Tilt is inactive
4. This allows time for Tilt to start broadcasting and for user to complete setup
5. After grace period expires, normal 4-minute timeout applies
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_grace_period_for_new_assignment():
    """Test the grace period when assigning a new Tilt to temperature control."""
    from app import (
        is_control_tilt_active,
        live_tilts,
        system_cfg,
        temp_cfg,
        temperature_control_logic,
        pending_notifications
    )
    
    print("=" * 80)
    print("GRACE PERIOD TEST: Newly Assigned Tilt")
    print("=" * 80)
    print("\nScenario: User starts new batch and assigns Tilt to temperature control")
    print("Expected: 15-minute grace period before 4-minute timeout enforcement")
    print("=" * 80)
    
    # Store original values
    original_tilts = dict(live_tilts)
    original_temp_cfg = dict(temp_cfg)
    original_timeout = system_cfg.get('tilt_inactivity_timeout_minutes')
    original_update_interval = system_cfg.get('update_interval')
    
    try:
        # Setup
        system_cfg['tilt_inactivity_timeout_minutes'] = 30
        system_cfg['update_interval'] = 2  # 2 min intervals → 4 min timeout
        
        # Clear state
        live_tilts.clear()
        pending_notifications.clear()
        temp_cfg.clear()
        
        now = datetime.utcnow()
        
        print("\n[TEST 1] Newly Assigned Tilt - NO Broadcasts Yet")
        print("-" * 80)
        print("User assigns Red Tilt to temp control, but Tilt hasn't broadcast yet")
        
        # Setup: Assign Red Tilt to temperature control RIGHT NOW
        temp_cfg.update({
            'tilt_color': 'Red',  # Assign Red
            'tilt_assignment_time': now.isoformat(),  # Just assigned
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
        
        # Red Tilt has NOT broadcast yet - not in live_tilts
        # OR it last broadcast 10 minutes ago (before assignment)
        old_timestamp = (now - timedelta(minutes=10)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red'] = {
            'timestamp': old_timestamp,
            'temp_f': 52.0,
            'gravity': 1.050,
            'beer_name': 'Test IPA',
            'brewid': 'test123'
        }
        
        print(f"  - Red Tilt assigned: Just now (0 minutes ago)")
        print(f"  - Red Tilt last broadcast: 10 minutes ago")
        print(f"  - Grace period: 15 minutes")
        print(f"  - Normal timeout after grace: 4 minutes")
        
        # Check if Tilt is considered active (should be True during grace period)
        is_active = is_control_tilt_active()
        print(f"\n  Checking is_control_tilt_active()...")
        print(f"  - Result: {is_active}")
        
        assert is_active, \
            "FAIL: Should be active during grace period (even though last broadcast was 10 min ago)"
        print(f"  ✓ Correctly returns True during grace period")
        
        # Run temperature control - should NOT trigger safety shutdown
        temperature_control_logic()
        status = temp_cfg.get('status')
        print(f"\n  Running temperature_control_logic()...")
        print(f"  - Status: {status}")
        
        assert "Safety Shutdown" not in status, \
            f"FAIL: Should NOT trigger safety shutdown during grace period, got: {status}"
        print(f"  ✓ No safety shutdown during grace period")
        
        print("\n[TEST 2] Grace Period - 10 Minutes After Assignment")
        print("-" * 80)
        print("10 minutes after assignment, Tilt still hasn't broadcast")
        
        # Simulate 10 minutes passing since assignment
        assignment_10min_ago = (now - timedelta(minutes=10)).isoformat()
        temp_cfg['tilt_assignment_time'] = assignment_10min_ago
        temp_cfg['safety_shutdown_logged'] = False
        
        print(f"  - Time since assignment: 10 minutes")
        print(f"  - Grace period remaining: 5 minutes")
        print(f"  - Red Tilt last broadcast: 20 minutes ago (10 min before assignment + 10 min)")
        
        # Update Red's timestamp to be even older
        very_old_timestamp = (now - timedelta(minutes=20)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = very_old_timestamp
        
        # Should still be active (in grace period)
        is_active = is_control_tilt_active()
        print(f"\n  Checking is_control_tilt_active()...")
        print(f"  - Result: {is_active}")
        
        assert is_active, \
            "FAIL: Should still be active (10 min < 15 min grace period)"
        print(f"  ✓ Still active during grace period (10/15 minutes)")
        
        # Run temperature control - should NOT trigger safety shutdown
        temperature_control_logic()
        status = temp_cfg.get('status')
        
        assert "Safety Shutdown" not in status, \
            f"FAIL: Should NOT trigger shutdown during grace period, got: {status}"
        print(f"  ✓ No safety shutdown (still in grace period)")
        
        print("\n[TEST 3] Grace Period Expires - 16 Minutes After Assignment")
        print("-" * 80)
        print("16 minutes after assignment, grace period has expired")
        
        # Simulate 16 minutes passing since assignment (past 15 min grace period)
        assignment_16min_ago = (now - timedelta(minutes=16)).isoformat()
        temp_cfg['tilt_assignment_time'] = assignment_16min_ago
        temp_cfg['safety_shutdown_logged'] = False
        temp_cfg['heater_on'] = True  # Heater is on
        
        print(f"  - Time since assignment: 16 minutes (grace period expired)")
        print(f"  - Red Tilt last broadcast: 26 minutes ago")
        print(f"  - Normal timeout: 4 minutes (should trigger shutdown)")
        
        # Update Red's timestamp to be very old
        very_old_timestamp = (now - timedelta(minutes=26)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = very_old_timestamp
        
        # Should now be INACTIVE (grace period expired, Tilt is beyond 4 min timeout)
        is_active = is_control_tilt_active()
        print(f"\n  Checking is_control_tilt_active()...")
        print(f"  - Result: {is_active}")
        
        assert not is_active, \
            "FAIL: Should be inactive after grace period expires"
        print(f"  ✓ Correctly detects as inactive (grace period expired)")
        
        # Run temperature control - should NOW trigger safety shutdown
        temperature_control_logic()
        status = temp_cfg.get('status')
        print(f"\n  Running temperature_control_logic()...")
        print(f"  - Status: {status}")
        
        assert "Safety Shutdown" in status, \
            f"FAIL: Should trigger safety shutdown after grace period, got: {status}"
        print(f"  ✓ Safety shutdown triggered after grace period expires")
        
        print("\n[TEST 4] Tilt Starts Broadcasting During Grace Period")
        print("-" * 80)
        print("Tilt starts broadcasting 5 minutes after assignment")
        
        # Reset state
        pending_notifications.clear()
        temp_cfg['safety_shutdown_logged'] = False
        
        # Assignment was 5 minutes ago (still in grace period)
        assignment_5min_ago = (now - timedelta(minutes=5)).isoformat()
        temp_cfg['tilt_assignment_time'] = assignment_5min_ago
        
        # Tilt starts broadcasting NOW (fresh timestamp)
        fresh_timestamp = now.replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = fresh_timestamp
        
        print(f"  - Time since assignment: 5 minutes")
        print(f"  - Red Tilt broadcast: Just now (fresh)")
        print(f"  - Grace period remaining: 10 minutes")
        
        # Should be active (both grace period AND fresh broadcast)
        is_active = is_control_tilt_active()
        print(f"\n  Checking is_control_tilt_active()...")
        print(f"  - Result: {is_active}")
        
        assert is_active, \
            "FAIL: Should be active (fresh broadcast)"
        print(f"  ✓ Active due to fresh broadcast")
        
        # After grace period expires, should still be active if broadcasting
        print("\n  Simulating grace period expiring (20 minutes after assignment)...")
        assignment_20min_ago = (now - timedelta(minutes=20)).isoformat()
        temp_cfg['tilt_assignment_time'] = assignment_20min_ago
        
        # Tilt broadcast 2 minutes ago (within 4 min timeout)
        recent_timestamp = (now - timedelta(minutes=2)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = recent_timestamp
        
        is_active = is_control_tilt_active()
        print(f"  - Time since assignment: 20 minutes (grace expired)")
        print(f"  - Red Tilt broadcast: 2 minutes ago (within 4 min timeout)")
        print(f"  - Result: {is_active}")
        
        assert is_active, \
            "FAIL: Should be active (recent broadcast within timeout)"
        print(f"  ✓ Active due to recent broadcast (normal timeout applies)")
        
        print("\n" + "=" * 80)
        print("ALL GRACE PERIOD TESTS PASSED ✓")
        print("=" * 80)
        print("\nSummary:")
        print("  ✓ 15-minute grace period when Tilt is newly assigned")
        print("  ✓ No safety shutdown during grace period (even if Tilt inactive)")
        print("  ✓ After grace period, normal 4-minute timeout applies")
        print("  ✓ If Tilt starts broadcasting during grace period, it works normally")
        print("\nThis gives users plenty of time to set up a new batch!")
        
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
        success = test_grace_period_for_new_assignment()
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
