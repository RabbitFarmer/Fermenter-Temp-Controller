#!/usr/bin/env python3
"""
Test temperature control without a Tilt configured.

This test verifies that temperature control works when:
1. No tilt_color is configured (empty string)
2. current_temp is set manually
3. Heating/cooling plugs are configured

This addresses the bug where is_control_tilt_active() returned False
when no tilt was configured, causing an incorrect safety shutdown.
"""

import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_temperature_control_without_tilt():
    """Test that temperature control works without a Tilt configured."""
    from app import (
        is_control_tilt_active,
        temp_cfg,
        temperature_control_logic,
        kasa_queue
    )
    
    print("=" * 80)
    print("TEST: Temperature Control Without Tilt")
    print("=" * 80)
    
    # Store original values
    original_temp_cfg = dict(temp_cfg)
    
    try:
        # Clear the kasa queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        # Setup: Configure temperature control WITHOUT a Tilt
        temp_cfg['tilt_color'] = ''  # No tilt configured
        temp_cfg['temp_control_enabled'] = True
        temp_cfg['enable_heating'] = True
        temp_cfg['enable_cooling'] = False
        temp_cfg['low_limit'] = 65.0
        temp_cfg['high_limit'] = 70.0
        temp_cfg['current_temp'] = 60.0  # Below low limit - should trigger heating
        temp_cfg['heating_plug'] = '192.168.1.100'
        temp_cfg['cooling_plug'] = '192.168.1.101'
        temp_cfg['heater_on'] = False
        temp_cfg['cooler_on'] = False
        
        print("\n[TEST 1] is_control_tilt_active() with no Tilt configured")
        print("-" * 80)
        
        # Verify that is_control_tilt_active returns True when no tilt is configured
        assert is_control_tilt_active(), \
            "is_control_tilt_active() should return True when no tilt is configured"
        print(f"✓ is_control_tilt_active() = True (no tilt configured)")
        
        print("\n[TEST 2] Temperature control should work without Tilt")
        print("-" * 80)
        
        # Run temperature control
        temperature_control_logic()
        
        # Verify it did NOT trigger safety shutdown
        status = temp_cfg.get('status')
        assert status != "Control Tilt Inactive - Safety Shutdown", \
            f"Should not trigger safety shutdown when no Tilt configured, got status: {status}"
        print(f"✓ No safety shutdown triggered")
        print(f"  Status: {status}")
        
        # Verify heating command was sent (check queue)
        # The command may have been consumed by the worker, check heater_pending flag
        print(f"✓ Temperature control activated heating")
        print(f"  heater_pending: {temp_cfg.get('heater_pending')}")
        
        # The heater_pending flag should be True after control_heating("on")
        assert temp_cfg.get('heater_pending'), \
            "heater_pending should be True after sending heating command"
        
        print("\n[TEST 3] Temperature control with high temp (should turn off)")
        print("-" * 80)
        
        # Clear queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        # Set temp above midpoint to turn off heating
        temp_cfg['current_temp'] = 68.0  # Above midpoint (67.5)
        temp_cfg['heater_on'] = True  # Simulate heater was on
        
        # Run temperature control
        temperature_control_logic()
        
        # Verify heating OFF command behavior
        # The heater_pending flag should be True after control_heating("off")
        assert temp_cfg.get('heater_pending'), \
            "heater_pending should be True after sending heating OFF command"
        print(f"✓ Heating OFF command sent")
        print(f"  heater_pending: {temp_cfg.get('heater_pending')}")
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        print("\nSummary:")
        print("  - Temperature control works without a Tilt configured")
        print("  - is_control_tilt_active() returns True when no tilt is configured")
        print("  - No incorrect safety shutdown when tilt_color is empty")
        print("  - Heating commands are sent based on current_temp")
        
        return True
        
    finally:
        # Clear queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        # Restore original values
        temp_cfg.clear()
        temp_cfg.update(original_temp_cfg)

if __name__ == '__main__':
    try:
        success = test_temperature_control_without_tilt()
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
