#!/usr/bin/env python3
"""
Test that KASA commands are retried after failures.

This test validates the fix for the issue where heating/cooling plugs
would not turn off after a failed command because failed commands were
being rate-limited.

The fix ensures that:
1. Successful commands are recorded in the rate limiter
2. Failed commands are NOT recorded, allowing immediate retry
3. Critical OFF commands can be retried even after failure
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_heating_retry_after_failure():
    """Test that heating OFF commands are retried after failure."""
    from app import (
        temp_cfg,
        temperature_control_logic,
        live_tilts,
        update_live_tilt,
        kasa_result_queue,
        _last_kasa_command
    )
    
    print("=" * 80)
    print("TEST: KASA Command Retry After Failure")
    print("=" * 80)
    
    # Clear state
    live_tilts.clear()
    _last_kasa_command.clear()
    
    # Configure temperature control
    temp_cfg.clear()
    temp_cfg['temp_control_enabled'] = True
    temp_cfg['temp_control_active'] = True
    temp_cfg['tilt_color'] = 'Red'
    temp_cfg['low_limit'] = 73.0
    temp_cfg['high_limit'] = 75.0
    temp_cfg['heating_plug'] = '192.168.1.100'
    temp_cfg['enable_heating'] = True
    temp_cfg['enable_cooling'] = False
    temp_cfg['control_initialized'] = True
    temp_cfg['heater_on'] = False
    temp_cfg['heater_pending'] = False
    
    print("\n[TEST 1] Failed OFF Command Should Allow Retry")
    print("-" * 80)
    
    # Step 1: Heater is ON, temperature is above high limit
    update_live_tilt('Red', gravity=1.050, temp_f=80.0, rssi=-75)
    temp_cfg['current_temp'] = 80.0
    temp_cfg['heater_on'] = True  # Simulate heater is ON
    temp_cfg['heater_pending'] = False
    
    print(f"Initial State: heater_on = True, temp = 80°F (> 75°F high limit)")
    print(f"Rate Limiter State: {_last_kasa_command}")
    
    # Step 2: Run temperature control - should send OFF command
    temperature_control_logic()
    
    first_pending = temp_cfg.get('heater_pending', False)
    print(f"After first call: heater_pending = {first_pending}")
    print(f"Rate Limiter State: {_last_kasa_command}")
    
    if not first_pending:
        print("✗ FAILED: OFF command was not sent")
        return False
    
    # Step 3: Simulate command failure by putting failure result on queue
    # (In real scenario, kasa_worker would put this)
    kasa_result_queue.put({
        'mode': 'heating',
        'action': 'off',
        'success': False,
        'url': '192.168.1.100',
        'error': 'Network timeout'
    })
    
    # Give result listener time to process
    time.sleep(0.5)
    
    # heater_on should still be True (unchanged after failure)
    heater_on_after_failure = temp_cfg.get('heater_on', False)
    heater_pending_after_failure = temp_cfg.get('heater_pending', False)
    
    print(f"After failure: heater_on = {heater_on_after_failure}, heater_pending = {heater_pending_after_failure}")
    print(f"Rate Limiter State: {_last_kasa_command}")
    
    if not heater_on_after_failure:
        print("✗ FAILED: heater_on was changed after failure (should remain True)")
        return False
    
    if heater_pending_after_failure:
        print("✗ FAILED: heater_pending still True after failure (should be cleared)")
        return False
    
    # THE CRITICAL TEST: Can we send another OFF command immediately?
    # Step 4: Run temperature control again - should retry OFF command
    temperature_control_logic()
    
    second_pending = temp_cfg.get('heater_pending', False)
    print(f"After retry: heater_pending = {second_pending}")
    print(f"Rate Limiter State: {_last_kasa_command}")
    
    if not second_pending:
        print("✗ FAILED: OFF command was not retried after failure")
        print("   This is the BUG - failed commands should be retried!")
        return False
    
    print("✓ SUCCESS: OFF command was retried after failure")
    
    # Step 5: Now simulate SUCCESS
    kasa_result_queue.put({
        'mode': 'heating',
        'action': 'off',
        'success': True,
        'url': '192.168.1.100',
        'error': ''
    })
    
    # Give result listener time to process
    time.sleep(0.5)
    
    heater_on_after_success = temp_cfg.get('heater_on', False)
    print(f"After success: heater_on = {heater_on_after_success}")
    print(f"Rate Limiter State: {_last_kasa_command}")
    
    if heater_on_after_success:
        print("✗ FAILED: heater_on still True after successful OFF")
        return False
    
    # Check that successful command WAS recorded in rate limiter
    if '192.168.1.100' not in _last_kasa_command:
        print("✗ FAILED: Successful command was not recorded in rate limiter")
        return False
    
    if _last_kasa_command['192.168.1.100']['action'] != 'off':
        print("✗ FAILED: Wrong action recorded in rate limiter")
        return False
    
    print("✓ SUCCESS: Successful command was recorded in rate limiter")
    
    # Step 6: Verify that duplicate OFF command is now blocked (rate limited)
    # Note: Rate limiting check happens immediately since the successful command
    # was just recorded and the rate limit period (default 10s) has not elapsed
    temperature_control_logic()
    
    third_pending = temp_cfg.get('heater_pending', False)
    print(f"After duplicate: heater_pending = {third_pending}")
    
    if third_pending:
        print("✗ FAILED: Duplicate OFF command was not rate-limited")
        return False
    
    print("✓ SUCCESS: Duplicate OFF command was correctly rate-limited")
    
    return True

def test_cooling_retry_after_failure():
    """Test that cooling OFF commands are retried after failure."""
    from app import (
        temp_cfg,
        temperature_control_logic,
        live_tilts,
        update_live_tilt,
        kasa_result_queue,
        _last_kasa_command
    )
    
    print("\n" + "=" * 80)
    print("TEST: Cooling Retry After Failure")
    print("=" * 80)
    
    # Clear state
    live_tilts.clear()
    _last_kasa_command.clear()
    
    # Configure temperature control for COOLING
    temp_cfg.clear()
    temp_cfg['temp_control_enabled'] = True
    temp_cfg['temp_control_active'] = True
    temp_cfg['tilt_color'] = 'Red'
    temp_cfg['low_limit'] = 73.0
    temp_cfg['high_limit'] = 75.0
    temp_cfg['cooling_plug'] = '192.168.1.101'
    temp_cfg['enable_heating'] = False
    temp_cfg['enable_cooling'] = True
    temp_cfg['control_initialized'] = True
    temp_cfg['cooler_on'] = False
    temp_cfg['cooler_pending'] = False
    
    # Cooler is ON, temperature is below low limit
    update_live_tilt('Red', gravity=1.050, temp_f=70.0, rssi=-75)
    temp_cfg['current_temp'] = 70.0
    temp_cfg['cooler_on'] = True  # Simulate cooler is ON
    temp_cfg['cooler_pending'] = False
    
    print(f"Initial State: cooler_on = True, temp = 70°F (< 73°F low limit)")
    
    # Run temperature control - should send OFF command
    temperature_control_logic()
    
    if not temp_cfg.get('cooler_pending', False):
        print("✗ FAILED: Cooling OFF command was not sent")
        return False
    
    # Simulate failure
    kasa_result_queue.put({
        'mode': 'cooling',
        'action': 'off',
        'success': False,
        'url': '192.168.1.101',
        'error': 'Network timeout'
    })
    
    time.sleep(0.5)
    
    # Retry
    temperature_control_logic()
    
    if not temp_cfg.get('cooler_pending', False):
        print("✗ FAILED: Cooling OFF command was not retried after failure")
        return False
    
    print("✓ SUCCESS: Cooling OFF command was retried after failure")
    
    # Simulate success
    kasa_result_queue.put({
        'mode': 'cooling',
        'action': 'off',
        'success': True,
        'url': '192.168.1.101',
        'error': ''
    })
    
    time.sleep(0.5)
    
    if temp_cfg.get('cooler_on', True):
        print("✗ FAILED: cooler_on still True after successful OFF")
        return False
    
    print("✓ SUCCESS: Cooling state updated correctly after success")
    
    return True

if __name__ == '__main__':
    try:
        print("\nStarting KASA retry tests...")
        print("These tests validate that failed commands can be retried immediately,")
        print("while successful commands are rate-limited to prevent duplicate sends.\n")
        
        test1_passed = test_heating_retry_after_failure()
        test2_passed = test_cooling_retry_after_failure()
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Test 1 (Heating Retry): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
        print(f"Test 2 (Cooling Retry): {'✓ PASSED' if test2_passed else '✗ FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n✓ ALL TESTS PASSED")
            print("\nThe fix correctly ensures that:")
            print("  1. Failed commands are NOT rate-limited")
            print("  2. Failed commands can be retried immediately")
            print("  3. Successful commands ARE rate-limited")
            print("  4. This prevents plugs from staying ON indefinitely")
            sys.exit(0)
        else:
            print("\n✗ SOME TESTS FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
