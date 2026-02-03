#!/usr/bin/env python3
"""
Test to verify the fix for stuck heating/cooling plugs.

This test validates the scenario described in the problem statement:
1. Heating ON command is sent → heater_pending = True
2. Command fails or response never arrives
3. heater_pending remains True
4. Temperature rises to 89°F (above high limit of 75°F)
5. Logic says "turn OFF"
6. OFF command MUST be allowed even though heater_pending = True with ON action
7. Pending flag cleared and reset for the new OFF action
8. Plug turns OFF
"""

import sys
import os
import time

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_opposite_command_override():
    """
    Test that an opposite command (OFF) can override a stuck pending command (ON).
    This is the critical fix that prevents plugs from getting stuck ON.
    """
    from app import temp_cfg, _should_send_kasa_command, ensure_temp_defaults
    
    print("=" * 80)
    print("TEST: Opposite Command Override (Stuck Heater Fix)")
    print("=" * 80)
    print("\nScenario: Heating ON command pending, but need to send OFF")
    print("Expected: OFF command should be allowed and clear pending ON")
    print("-" * 80)
    
    # Initialize temp config
    ensure_temp_defaults()
    
    # Configure heating - heater is physically ON
    temp_cfg.update({
        "heating_plug": "192.168.1.100",
        "enable_heating": True,
        "heater_on": True,  # Heater is physically ON
        "heater_pending": False,
        "heater_pending_action": None,
        "heater_pending_since": None,
        "low_limit": 73.0,
        "high_limit": 75.0,
        "current_temp": 72.0,
    })
    
    print("\n[Step 1] Initial state - heater is ON, heating beer:")
    print(f"  Current temp: {temp_cfg['current_temp']}°F")
    print(f"  High limit: {temp_cfg['high_limit']}°F")
    print(f"  heater_on: {temp_cfg.get('heater_on')} (physically ON)")
    print(f"  heater_pending: {temp_cfg.get('heater_pending')}")
    
    # Step 2: Simulate sending ON command (which gets stuck pending)
    # In a real scenario, this could be from a previous ON command that never got a response
    print("\n[Step 2] Simulate previous ON command stuck pending:")
    print("  (Perhaps from when temp was low and we sent ON)")
    print("  But the kasa_worker response never arrived")
    temp_cfg["heater_pending"] = True
    temp_cfg["heater_pending_action"] = "on"
    temp_cfg["heater_pending_since"] = time.time()
    print(f"  heater_pending: {temp_cfg['heater_pending']}")
    print(f"  heater_pending_action: {temp_cfg['heater_pending_action']}")
    
    # Step 3: Temperature rises above high limit
    print("\n[Step 3] Temperature rises to 89°F (well above high limit):")
    temp_cfg["current_temp"] = 89.0
    print(f"  Current temp: {temp_cfg['current_temp']}°F (HIGH LIMIT: {temp_cfg['high_limit']}°F)")
    print("  Logic determines: MUST TURN OFF heating")
    
    # Step 4: Verify OFF command is allowed despite pending ON
    print("\n[Step 4] Check if OFF command is allowed:")
    url = temp_cfg["heating_plug"]
    
    # Record state before
    pending_before = temp_cfg.get("heater_pending")
    pending_action_before = temp_cfg.get("heater_pending_action")
    
    print(f"  Before: heater_pending={pending_before}, pending_action={pending_action_before}")
    
    # Call the function that checks if command should be sent
    should_send = _should_send_kasa_command(url, "off")
    
    # Record state after
    pending_after = temp_cfg.get("heater_pending")
    pending_action_after = temp_cfg.get("heater_pending_action")
    
    print(f"  After:  heater_pending={pending_after}, pending_action={pending_action_after}")
    print(f"\n  Result: should_send = {should_send}")
    
    # Verify the fix works
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("=" * 80)
    
    if not should_send:
        print("❌ FAIL: OFF command was BLOCKED")
        print("   This means the plug would stay stuck ON!")
        print("   The fix is NOT working correctly.")
        return False
    
    if temp_cfg.get("heater_pending"):
        print("❌ FAIL: heater_pending is still True")
        print("   The pending flag should have been cleared when allowing opposite command")
        return False
    
    print("✓ PASS: OFF command was ALLOWED")
    print("✓ PASS: Old pending state was cleared (heater_pending = False)")
    print("\nThe fix is working correctly!")
    print("Opposite commands can override stuck pending commands.")
    
    return True


def test_cooling_opposite_command_override():
    """
    Test the same scenario for cooling plugs.
    """
    from app import temp_cfg, _should_send_kasa_command, ensure_temp_defaults
    
    print("\n" + "=" * 80)
    print("TEST: Cooling Opposite Command Override")
    print("=" * 80)
    print("\nScenario: Cooling ON command pending, but need to send OFF")
    print("Expected: OFF command should be allowed and clear pending ON")
    print("-" * 80)
    
    # Initialize temp config
    ensure_temp_defaults()
    
    # Configure cooling - cooler is physically ON
    temp_cfg.update({
        "cooling_plug": "192.168.1.101",
        "enable_cooling": True,
        "cooler_on": True,  # Cooler is physically ON
        "cooler_pending": False,
        "cooler_pending_action": None,
        "cooler_pending_since": None,
        "low_limit": 68.0,
        "high_limit": 70.0,
        "current_temp": 71.0,
    })
    
    print("\n[Step 1] Initial state - cooler is ON, cooling beer:")
    print(f"  Current temp: {temp_cfg['current_temp']}°F")
    print(f"  Low limit: {temp_cfg['low_limit']}°F")
    print(f"  cooler_on: {temp_cfg.get('cooler_on')} (physically ON)")
    print(f"  cooler_pending: {temp_cfg.get('cooler_pending')}")
    
    # Simulate sending ON command (which gets stuck pending)
    print("\n[Step 2] Simulate previous ON command stuck pending:")
    print("  But the kasa_worker response never arrived")
    temp_cfg["cooler_pending"] = True
    temp_cfg["cooler_pending_action"] = "on"
    temp_cfg["cooler_pending_since"] = time.time()
    print(f"  cooler_pending: {temp_cfg['cooler_pending']}")
    print(f"  cooler_pending_action: {temp_cfg['cooler_pending_action']}")
    
    # Temperature drops below low limit
    print("\n[Step 3] Temperature drops to 65°F (below low limit):")
    temp_cfg["current_temp"] = 65.0
    print(f"  Current temp: {temp_cfg['current_temp']}°F (LOW LIMIT: {temp_cfg['low_limit']}°F)")
    print("  Logic determines: MUST TURN OFF cooling")
    
    # Verify OFF command is allowed
    print("\n[Step 4] Check if OFF command is allowed:")
    url = temp_cfg["cooling_plug"]
    
    should_send = _should_send_kasa_command(url, "off")
    
    print(f"\n  Result: should_send = {should_send}")
    
    # Verify the fix works
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("=" * 80)
    
    if not should_send:
        print("❌ FAIL: OFF command was BLOCKED")
        return False
    
    if temp_cfg.get("cooler_pending"):
        print("❌ FAIL: cooler_pending is still True")
        return False
    
    print("✓ PASS: OFF command was ALLOWED")
    print("✓ PASS: Old pending state was cleared (cooler_pending = False)")
    
    return True


def test_same_command_still_blocked():
    """
    Verify that the same command is still blocked (rate limiting still works).
    We only want to allow OPPOSITE commands.
    """
    from app import temp_cfg, _should_send_kasa_command, ensure_temp_defaults
    
    print("\n" + "=" * 80)
    print("TEST: Same Command Still Blocked (Rate Limiting)")
    print("=" * 80)
    print("\nScenario: ON command pending, try to send another ON")
    print("Expected: Second ON should be blocked (rate limiting)")
    print("-" * 80)
    
    # Initialize
    ensure_temp_defaults()
    
    temp_cfg.update({
        "heating_plug": "192.168.1.100",
        "heater_pending": True,
        "heater_pending_action": "on",
        "heater_pending_since": time.time(),
    })
    
    print("\n[Step 1] ON command is pending:")
    print(f"  heater_pending: {temp_cfg['heater_pending']}")
    print(f"  heater_pending_action: {temp_cfg['heater_pending_action']}")
    
    print("\n[Step 2] Try to send another ON command:")
    url = temp_cfg["heating_plug"]
    should_send = _should_send_kasa_command(url, "on")
    
    print(f"\n  Result: should_send = {should_send}")
    
    # Verify same command is blocked
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("=" * 80)
    
    if should_send:
        print("❌ FAIL: Second ON command was ALLOWED")
        print("   Rate limiting is not working!")
        return False
    
    print("✓ PASS: Second ON command was BLOCKED")
    print("   Rate limiting still works correctly")
    
    return True


if __name__ == '__main__':
    try:
        print("Running tests for stuck heater fix...\n")
        
        # Test 1: Heating opposite command override
        test1_passed = test_opposite_command_override()
        
        # Test 2: Cooling opposite command override
        test2_passed = test_cooling_opposite_command_override()
        
        # Test 3: Same command still blocked
        test3_passed = test_same_command_still_blocked()
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Test 1 (Heating opposite override): {'✓ PASS' if test1_passed else '❌ FAIL'}")
        print(f"Test 2 (Cooling opposite override): {'✓ PASS' if test2_passed else '❌ FAIL'}")
        print(f"Test 3 (Same command blocked):      {'✓ PASS' if test3_passed else '❌ FAIL'}")
        
        all_passed = test1_passed and test2_passed and test3_passed
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED")
            print("The stuck heater/cooler fix is working correctly!")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
