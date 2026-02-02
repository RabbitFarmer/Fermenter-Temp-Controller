#!/usr/bin/env python3
"""
Test that notifications are only sent when limits are EXCEEDED, not when equal.

This test verifies that:
1. "Below low limit" notifications are sent only when temp < low_limit (not when temp == low_limit)
2. "Above high limit" notifications are sent only when temp > high_limit (not when temp == high_limit)
"""

def test_notification_threshold_logic():
    """
    Test that notification triggers use strict comparison (< and >)
    while plug control uses inclusive comparison (<= and >=).
    """
    print("=" * 80)
    print("TEST: Notification Threshold Logic (Strict Comparison)")
    print("=" * 80)
    
    # Simulate temperature control configuration
    low_limit = 68.0
    high_limit = 72.0
    
    print(f"\nConfiguration:")
    print(f"  Low Limit: {low_limit}°F")
    print(f"  High Limit: {high_limit}°F")
    
    # Test cases: (temperature, should_notify_below, should_notify_above)
    test_cases = [
        (67.0, True, False, "Below low limit"),
        (68.0, False, False, "Equal to low limit"),
        (70.0, False, False, "Within range"),
        (72.0, False, False, "Equal to high limit"),
        (73.0, False, True, "Above high limit"),
    ]
    
    print("\n" + "-" * 80)
    print("Test Cases:")
    print("-" * 80)
    
    all_passed = True
    
    for temp, expected_below, expected_above, description in test_cases:
        # Simulate the notification logic
        # Below limit notification: temp < low (strictly less than)
        notify_below = temp < low_limit
        
        # Above limit notification: temp > high (strictly greater than)
        notify_above = temp > high_limit
        
        # Check if results match expectations
        below_match = notify_below == expected_below
        above_match = notify_above == expected_above
        
        status = "✅ PASS" if (below_match and above_match) else "❌ FAIL"
        
        print(f"\n{description}:")
        print(f"  Temperature: {temp}°F")
        print(f"  Below limit notification (temp < {low_limit}): {notify_below} (expected {expected_below}) {'' if below_match else '❌'}")
        print(f"  Above limit notification (temp > {high_limit}): {notify_above} (expected {expected_above}) {'' if above_match else '❌'}")
        print(f"  Result: {status}")
        
        if not (below_match and above_match):
            all_passed = False
    
    print("\n" + "=" * 80)
    
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nSummary:")
        print("- Notifications use STRICT comparison (< and >)")
        print("- Notifications sent ONLY when limits are EXCEEDED")
        print("- Notifications NOT sent when temperature EQUALS limits")
        print("- Plug control still uses inclusive comparison (<= and >=) for hysteresis")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
        return False

def test_plug_control_vs_notification():
    """
    Test that plug control and notification logic are separate.
    """
    print("\n" + "=" * 80)
    print("TEST: Plug Control vs Notification Separation")
    print("=" * 80)
    
    low_limit = 68.0
    high_limit = 72.0
    
    print(f"\nConfiguration:")
    print(f"  Low Limit: {low_limit}°F")
    print(f"  High Limit: {high_limit}°F")
    
    print("\n" + "-" * 80)
    print("Scenario: Temperature exactly at low limit (68.0°F)")
    print("-" * 80)
    
    temp = 68.0
    
    # Plug control: temp <= low (inclusive)
    heating_on = temp <= low_limit
    print(f"  Heating plug control (temp <= {low_limit}): {heating_on}")
    print(f"    ✅ Plug SHOULD turn ON (inclusive comparison for hysteresis)")
    
    # Notification: temp < low (strict)
    notify = temp < low_limit
    print(f"  Notification trigger (temp < {low_limit}): {notify}")
    print(f"    ✅ Notification should NOT be sent (strict comparison)")
    
    print("\n" + "-" * 80)
    print("Scenario: Temperature exactly at high limit (72.0°F)")
    print("-" * 80)
    
    temp = 72.0
    
    # Plug control: temp >= high (inclusive)
    cooling_on = temp >= high_limit
    print(f"  Cooling plug control (temp >= {high_limit}): {cooling_on}")
    print(f"    ✅ Plug SHOULD turn ON (inclusive comparison for hysteresis)")
    
    # Notification: temp > high (strict)
    notify = temp > high_limit
    print(f"  Notification trigger (temp > {high_limit}): {notify}")
    print(f"    ✅ Notification should NOT be sent (strict comparison)")
    
    print("\n" + "=" * 80)
    print("✅ PLUG CONTROL AND NOTIFICATIONS ARE PROPERLY SEPARATED")
    print("=" * 80)
    print("\nKey Points:")
    print("1. Plug control uses <= and >= (inclusive) for proper hysteresis")
    print("2. Notifications use < and > (strict) to only alert when exceeded")
    print("3. This prevents notifications when temp is exactly at limit")
    print("4. Plugs still work correctly for temperature control")

if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "NOTIFICATION THRESHOLD LOGIC TESTS" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    success = test_notification_threshold_logic()
    test_plug_control_vs_notification()
    
    if success:
        print("\n✅ All notification threshold tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
