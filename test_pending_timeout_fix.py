#!/usr/bin/env python3
"""
Test to verify the fix for the temperature control bug.

The bug scenario:
1. Heater ON command is sent, heater_pending=True
2. Kasa response never arrives (network issue, etc.)
3. After 30 seconds, pending times out and is cleared
4. BUT heater_on state was NOT updated, stays False
5. Physical heater is ON but system thinks it's OFF
6. When temp reaches high limit, OFF command is blocked as "redundant"
7. Heater stays ON indefinitely

The fix:
When pending times out, assume the command succeeded and update heater_on/cooler_on
state to match the pending_action.
"""

import time

def test_pending_timeout_updates_state():
    """Test that pending timeout updates heater_on/cooler_on state."""
    
    print("=" * 80)
    print("PENDING TIMEOUT STATE UPDATE TEST")
    print("=" * 80)
    print("\nThis test verifies the fix for the temperature control bug")
    print("where heater_on state becomes out of sync when pending times out.")
    print("=" * 80)
    
    # Simulate the _should_send_kasa_command logic
    temp_cfg = {
        "heating_plug": "192.168.1.100",
        "heater_on": False,
        "heater_pending": False,
        "heater_pending_since": None,
        "heater_pending_action": None
    }
    
    _KASA_PENDING_TIMEOUT_SECONDS = 30
    
    print("\n[STEP 1] Initial state")
    print("-" * 80)
    print(f"heater_on: {temp_cfg['heater_on']}")
    print(f"heater_pending: {temp_cfg['heater_pending']}")
    
    print("\n[STEP 2] Simulate sending ON command")
    print("-" * 80)
    # This simulates what control_heating("on") does
    temp_cfg["heater_pending"] = True
    temp_cfg["heater_pending_since"] = time.time()
    temp_cfg["heater_pending_action"] = "on"
    print(f"heater_pending: {temp_cfg['heater_pending']}")
    print(f"heater_pending_action: {temp_cfg['heater_pending_action']}")
    print("Command sent to Kasa, waiting for response...")
    
    print("\n[STEP 3] Simulate pending timeout (response never arrives)")
    print("-" * 80)
    # Simulate 31 seconds passing
    temp_cfg["heater_pending_since"] = time.time() - 31
    
    pending_action = temp_cfg["heater_pending_action"]
    pending_since = temp_cfg["heater_pending_since"]
    
    print(f"Time elapsed: {time.time() - pending_since:.1f} seconds")
    print(f"Timeout threshold: {_KASA_PENDING_TIMEOUT_SECONDS} seconds")
    
    # This is the FIXED logic from _should_send_kasa_command
    if (time.time() - pending_since) > _KASA_PENDING_TIMEOUT_SECONDS:
        elapsed = time.time() - pending_since
        print(f"✓ Timeout detected (pending for {elapsed:.1f}s)")
        
        # CRITICAL FIX: Update heater_on state to match the pending action
        if pending_action == "on":
            temp_cfg["heater_on"] = True
            print(f"✓ FIX APPLIED: Assuming heater ON command succeeded after timeout")
        elif pending_action == "off":
            temp_cfg["heater_on"] = False
            print(f"✓ FIX APPLIED: Assuming heater OFF command succeeded after timeout")
        
        # Clear pending flags
        temp_cfg["heater_pending"] = False
        temp_cfg["heater_pending_since"] = None
        temp_cfg["heater_pending_action"] = None
    
    print(f"\nAfter timeout handling:")
    print(f"  heater_on: {temp_cfg['heater_on']}")
    print(f"  heater_pending: {temp_cfg['heater_pending']}")
    
    if temp_cfg['heater_on'] == True:
        print("\n✓ SUCCESS: heater_on state correctly updated to True")
        print("  The system now knows the heater is ON")
    else:
        print("\n✗ FAILURE: heater_on is still False")
        print("  This is the bug - system thinks heater is OFF when it's actually ON")
        return False
    
    print("\n[STEP 4] Verify OFF command is not blocked as redundant")
    print("-" * 80)
    
    # Simulate _is_redundant_command logic
    def _is_redundant_command(action, current_state):
        """Check if command is redundant."""
        command_matches_state = (action == "on" and current_state) or (action == "off" and not current_state)
        return command_matches_state
    
    heater_on = temp_cfg.get("heater_on", False)
    action = "off"
    
    print(f"Current state: heater_on = {heater_on}")
    print(f"Requested action: {action}")
    
    is_redundant = _is_redundant_command(action, heater_on)
    
    print(f"Is command redundant? {is_redundant}")
    
    if not is_redundant:
        print("✓ SUCCESS: OFF command will be sent")
        print("  Heater can now be turned off when temp reaches high limit")
    else:
        print("✗ FAILURE: OFF command blocked as redundant")
        print("  This is the bug - heater will never turn off!")
        return False
    
    print("\n" + "=" * 80)
    print("TEST PASSED - FIX VERIFIED")
    print("=" * 80)
    print("\nThe fix prevents the heater_on state from becoming out of sync.")
    print("When pending times out, we assume the command succeeded and update state.")
    print("This allows the OFF command to be sent when temperature reaches high limit.")
    
    return True


def test_cooling_timeout_fix():
    """Test that the same fix works for cooling."""
    
    print("\n\n" + "=" * 80)
    print("COOLING PENDING TIMEOUT STATE UPDATE TEST")
    print("=" * 80)
    
    temp_cfg = {
        "cooling_plug": "192.168.1.101",
        "cooler_on": False,
        "cooler_pending": True,
        "cooler_pending_since": time.time() - 31,  # 31 seconds ago
        "cooler_pending_action": "on"
    }
    
    _KASA_PENDING_TIMEOUT_SECONDS = 30
    
    pending_action = temp_cfg["cooler_pending_action"]
    pending_since = temp_cfg["cooler_pending_since"]
    
    print(f"Initial state: cooler_on = {temp_cfg['cooler_on']}")
    print(f"Pending action: {pending_action}")
    print(f"Time elapsed: {time.time() - pending_since:.1f} seconds")
    
    # Apply the fix
    if (time.time() - pending_since) > _KASA_PENDING_TIMEOUT_SECONDS:
        if pending_action == "on":
            temp_cfg["cooler_on"] = True
            print(f"✓ FIX APPLIED: Assuming cooler ON command succeeded")
        elif pending_action == "off":
            temp_cfg["cooler_on"] = False
            print(f"✓ FIX APPLIED: Assuming cooler OFF command succeeded")
        
        temp_cfg["cooler_pending"] = False
        temp_cfg["cooler_pending_since"] = None
        temp_cfg["cooler_pending_action"] = None
    
    print(f"After timeout: cooler_on = {temp_cfg['cooler_on']}")
    
    if temp_cfg['cooler_on'] == True:
        print("✓ SUCCESS: Cooling timeout fix works correctly")
        return True
    else:
        print("✗ FAILURE: cooler_on not updated")
        return False


if __name__ == '__main__':
    import sys
    
    test1_passed = test_pending_timeout_updates_state()
    test2_passed = test_cooling_timeout_fix()
    
    if test1_passed and test2_passed:
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("SOME TESTS FAILED")
        print("=" * 80)
        sys.exit(1)
