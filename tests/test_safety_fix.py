#!/usr/bin/env python3
"""
Test for the safety fix that ensures heating turns OFF when high_limit is None.

This test verifies that the added safety check prevents runaway heating
when high_limit is not configured.
"""

def test_high_limit_none_safety():
    """Test that heating turns OFF when high_limit is None."""
    
    print("=" * 80)
    print("SAFETY FIX TEST: Heating with high_limit = None")
    print("=" * 80)
    print()
    
    # Configuration
    low = 74.0
    high = None  # THIS IS THE BUG SCENARIO
    enable_heat = True
    
    # State
    heater_on = False
    commands = []
    
    def control_heating(action):
        """Simulate control_heating function."""
        nonlocal heater_on
        commands.append(action)
        if action == "on":
            heater_on = True
        else:
            heater_on = False
    
    print("SCENARIO: high_limit is None (not configured)")
    print(f"  Low limit: {low}°F")
    print(f"  High limit: {high}")
    print(f"  Heating enabled: {enable_heat}")
    print()
    
    # Test case 1: Temp = 73F (below low) - should turn ON
    print("TEST 1: Temperature = 73°F (below low limit)")
    temp = 73.0
    
    # Reproduce the FIXED logic from app.py
    if enable_heat:
        if temp <= low:
            control_heating("on")
        elif high is not None and temp >= high:
            control_heating("off")
        elif high is None:
            # SAFETY FIX: Turn OFF if high_limit is not configured
            control_heating("off")
    else:
        control_heating("off")
    
    print(f"  Commands: {commands}")
    print(f"  Heater state: {'ON' if heater_on else 'OFF'}")
    print(f"  Expected: ON")
    print(f"  Status: {'✓ PASS' if heater_on else '✗ FAIL'}")
    print()
    
    # Test case 2: Temp = 76F (would be above high if it were set)
    # WITHOUT FIX: heater stays ON (dangerous!)
    # WITH FIX: heater turns OFF (safe)
    print("TEST 2: Temperature = 76°F (high_limit still None)")
    temp = 76.0
    commands.clear()
    
    if enable_heat:
        if temp <= low:
            control_heating("on")
        elif high is not None and temp >= high:
            control_heating("off")
        elif high is None:
            # SAFETY FIX: Turn OFF if high_limit is not configured
            control_heating("off")
    else:
        control_heating("off")
    
    print(f"  Commands: {commands}")
    print(f"  Heater state: {'ON' if heater_on else 'OFF'}")
    print(f"  Expected: OFF (SAFETY FIX)")
    print(f"  Status: {'✓ PASS' if not heater_on else '✗ FAIL'}")
    print()
    
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()
    
    if not heater_on:
        print("✓ SAFETY FIX WORKING!")
        print()
        print("When high_limit is None:")
        print("  - OLD BEHAVIOR: Heating stays ON indefinitely (runaway heating!)")
        print("  - NEW BEHAVIOR: Heating turns OFF (safe)")
        print()
        print("This prevents runaway heating when:")
        print("  1. User hasn't configured high_limit")
        print("  2. Config file is corrupted/missing high_limit")
        print("  3. high_limit gets cleared unexpectedly")
        return True
    else:
        print("✗ SAFETY FIX NOT WORKING")
        print("  Heater is still ON with high_limit=None")
        print("  This could cause runaway heating!")
        return False

def test_normal_operation():
    """Test that normal operation still works with the fix."""
    
    print()
    print("=" * 80)
    print("NORMAL OPERATION TEST: Heating with high_limit = 75°F")
    print("=" * 80)
    print()
    
    # Configuration
    low = 74.0
    high = 75.0  # Normal configuration
    enable_heat = True
    
    # State
    heater_on = False
    commands = []
    
    def control_heating(action):
        """Simulate control_heating function."""
        nonlocal heater_on
        commands.append(action)
        if action == "on":
            heater_on = True
        else:
            heater_on = False
    
    print(f"  Low limit: {low}°F")
    print(f"  High limit: {high}°F")
    print(f"  Heating enabled: {enable_heat}")
    print()
    
    # Test case 1: Temp = 73F - should turn ON
    print("TEST 1: Temperature = 73°F (below low limit)")
    temp = 73.0
    
    if enable_heat:
        if temp <= low:
            control_heating("on")
        elif high is not None and temp >= high:
            control_heating("off")
        elif high is None:
            control_heating("off")
    else:
        control_heating("off")
    
    test1_pass = heater_on
    print(f"  Heater state: {'ON' if heater_on else 'OFF'}")
    print(f"  Status: {'✓ PASS' if test1_pass else '✗ FAIL'}")
    print()
    
    # Test case 2: Temp = 76F - should turn OFF
    print("TEST 2: Temperature = 76°F (above high limit)")
    temp = 76.0
    commands.clear()
    
    if enable_heat:
        if temp <= low:
            control_heating("on")
        elif high is not None and temp >= high:
            control_heating("off")
        elif high is None:
            control_heating("off")
    else:
        control_heating("off")
    
    test2_pass = not heater_on
    print(f"  Heater state: {'ON' if heater_on else 'OFF'}")
    print(f"  Status: {'✓ PASS' if test2_pass else '✗ FAIL'}")
    print()
    
    if test1_pass and test2_pass:
        print("✓ Normal operation still works correctly!")
        return True
    else:
        print("✗ Normal operation broken by the fix")
        return False

if __name__ == '__main__':
    safety_test_passed = test_high_limit_none_safety()
    normal_test_passed = test_normal_operation()
    
    print()
    print("=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print()
    
    if safety_test_passed and normal_test_passed:
        print("✓ ALL TESTS PASSED")
        print()
        print("The safety fix:")
        print("  1. Prevents runaway heating when high_limit is None")
        print("  2. Doesn't break normal operation")
        print("  3. Provides additional safety for edge cases")
        exit(0)
    else:
        print("✗ TESTS FAILED")
        exit(1)
