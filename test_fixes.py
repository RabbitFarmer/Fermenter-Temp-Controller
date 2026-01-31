#!/usr/bin/env python3
"""
Test to verify the fixes for:
1. heater_pending timeout (prevents stuck pending flag)
2. Proper trigger rearming (only rearm at opposite limit, not in range)
"""

import time

def test_heater_pending_timeout():
    """Test that heater_pending clears after timeout."""
    print("=" * 80)
    print("TEST 1: HEATER_PENDING TIMEOUT")
    print("=" * 80)
    
    low = 73.0
    high = 75.0
    enable_heat = True
    
    # Mock state
    heater_on = False
    heater_pending = False
    heater_pending_since = None
    PENDING_TIMEOUT = 30  # seconds
    
    def _should_send_kasa_command(url, action):
        nonlocal heater_on, heater_pending, heater_pending_since
        
        # Check for timed-out pending flags and clear them
        if heater_pending:
            if heater_pending_since and (time.time() - heater_pending_since) > PENDING_TIMEOUT:
                print(f"      ✓ Clearing stuck heater_pending (pending for {time.time() - heater_pending_since:.1f}s)")
                heater_pending = False
                heater_pending_since = None
            else:
                print(f"      BLOCKED: heater_pending is True (pending for {time.time() - heater_pending_since:.1f}s)")
                return False
        
        if heater_on and action == "on":
            print(f"      BLOCKED: heater already ON")
            return False
        
        return True
    
    def control_heating(action):
        nonlocal heater_on, heater_pending, heater_pending_since
        
        url = "192.168.1.10"
        
        if not _should_send_kasa_command(url, action):
            return
        
        print(f"      ✓ COMMAND SENT: Turn heating {action.upper()}")
        heater_pending = True
        heater_pending_since = time.time()
    
    print("\n[Step 1] Temp drops to 73°F - send heating ON command")
    control_heating("on")
    print(f"    heater_pending={heater_pending}, heater_on={heater_on}")
    
    print("\n[Step 2] Simulate kasa_worker hanging - no response for 10 seconds")
    time.sleep(0.1)  # Small delay to show time passing
    print(f"    heater_pending={heater_pending}, heater_on={heater_on}")
    
    print("\n[Step 3] Temp vacillates to 72°F - try to send command again")
    control_heating("on")
    print(f"    heater_pending={heater_pending}, heater_on={heater_on}")
    
    print("\n[Step 4] Simulate 31 seconds passing (exceeds 30s timeout)")
    # Fast-forward time by adjusting heater_pending_since
    heater_pending_since = time.time() - 31
    
    print("\n[Step 5] Temp at 72°F - try to send command again")
    control_heating("on")
    print(f"    heater_pending={heater_pending}, heater_on={heater_on}")
    
    if not heater_pending:
        print("\n✓ TEST PASSED: heater_pending timeout works correctly")
        return True
    else:
        print("\n✗ TEST FAILED: heater_pending still stuck")
        return False


def test_trigger_rearming():
    """Test that triggers are only rearmed at opposite limit, not in range."""
    print("\n" + "=" * 80)
    print("TEST 2: PROPER TRIGGER REARMING")
    print("=" * 80)
    
    low = 73.0
    high = 75.0
    
    # Mock state
    below_limit_trigger_armed = True
    above_limit_trigger_armed = True
    in_range_trigger_armed = True
    
    temps = [80.0, 73.0, 73.5, 72.9, 73.0, 74.0, 75.0, 74.5, 73.5, 73.0, 72.0]
    
    logs = []
    
    for temp in temps:
        print(f"\nTemp: {temp:5.1f}°F")
        
        # Heating control logic (simplified, just tracking triggers)
        if temp <= low:
            print(f"    Logic: temp <= low_limit")
            if below_limit_trigger_armed:
                logs.append(f"LOG: temp_below_low_limit at {temp}°F")
                print(f"    ✓ LOG EVENT: temp_below_low_limit")
                below_limit_trigger_armed = False
                # Arm the above_limit trigger for when temp rises to high limit
                above_limit_trigger_armed = True
                print(f"    Triggers: below=False, above=True (armed for high limit)")
            else:
                print(f"    No log (trigger disarmed)")
                print(f"    Triggers: below={below_limit_trigger_armed}, above={above_limit_trigger_armed}")
        elif temp >= high:
            print(f"    Logic: temp >= high_limit")
            if above_limit_trigger_armed:
                logs.append(f"LOG: temp_above_high_limit at {temp}°F")
                print(f"    ✓ LOG EVENT: temp_above_high_limit")
                above_limit_trigger_armed = False
                # Arm the below_limit trigger for when temp drops to low limit
                below_limit_trigger_armed = True
                print(f"    Triggers: below=True (armed for low limit), above=False")
            else:
                print(f"    No log (trigger disarmed)")
                print(f"    Triggers: below={below_limit_trigger_armed}, above={above_limit_trigger_armed}")
        else:
            print(f"    Logic: temp in range ({low} < {temp} < {high})")
            if in_range_trigger_armed:
                logs.append(f"LOG: temp_in_range at {temp}°F")
                print(f"    ✓ LOG EVENT: temp_in_range")
                in_range_trigger_armed = False
            else:
                print(f"    No log (in_range trigger disarmed)")
            # Do NOT rearm out-of-range triggers here
            print(f"    Triggers: below={below_limit_trigger_armed}, above={above_limit_trigger_armed} (UNCHANGED)")
            
        # Re-arm in_range trigger when out of range
        if temp < low or temp > high:
            in_range_trigger_armed = True
    
    print("\n" + "-" * 80)
    print("EVENT LOG:")
    print("-" * 80)
    for log in logs:
        print(f"  {log}")
    
    print("\n" + "-" * 80)
    print("ANALYSIS:")
    print("-" * 80)
    
    # Check if below_low_limit was logged multiple times
    below_logs = [log for log in logs if "below_low_limit" in log]
    above_logs = [log for log in logs if "above_high_limit" in log]
    
    print(f"\nBelow low limit events: {len(below_logs)}")
    for log in below_logs:
        print(f"  {log}")
    
    print(f"\nAbove high limit events: {len(above_logs)}")
    for log in above_logs:
        print(f"  {log}")
    
    # Expected: Only 2 below_low_limit events (initial at 73°F and again at 72°F after temp went to 75°F)
    if len(below_logs) == 2 and len(above_logs) == 1:
        print("\n✓ TEST PASSED: Triggers work correctly with proper hysteresis")
        return True
    else:
        print(f"\n✗ TEST FAILED: Expected 2 below_low events and 1 above_high event")
        print(f"  Got {len(below_logs)} below_low events and {len(above_logs)} above_high events")
        return False


if __name__ == '__main__':
    test1_passed = test_heater_pending_timeout()
    test2_passed = test_trigger_rearming()
    
    print("\n" + "=" * 80)
    print("OVERALL RESULTS")
    print("=" * 80)
    print(f"Test 1 (heater_pending timeout): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Test 2 (trigger rearming): {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✓ ALL TESTS PASSED")
        exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        exit(1)
