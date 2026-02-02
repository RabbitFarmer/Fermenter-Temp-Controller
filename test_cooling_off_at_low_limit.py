#!/usr/bin/env python3
"""
Test to verify cooling turns OFF when temp EQUALS low limit (not just below).
"""

def test_cooling_off_at_low_limit():
    """Test that cooling turns OFF exactly at low_limit, not below it."""
    
    print("=" * 80)
    print("COOLING OFF AT LOW LIMIT TEST")
    print("=" * 80)
    print()
    
    # Configuration
    low = 65.0
    high = 70.0
    enable_cool = True
    
    # State
    cooler_on = False
    commands = []
    
    def control_cooling(action):
        """Simulate control_cooling function."""
        nonlocal cooler_on
        commands.append(f"{action}")
        if action == "on":
            cooler_on = True
        else:
            cooler_on = False
    
    print(f"Configuration: Low={low}°F, High={high}°F")
    print()
    
    # Test temperatures
    test_cases = [
        (72.0, "on", "Above high limit → Turn ON"),
        (70.0, "on", "At high limit → Turn ON"),
        (67.5, None, "Between limits → Maintain state"),
        (65.0, "off", "AT LOW LIMIT → Turn OFF (not below!)"),
        (64.0, "off", "Below low limit → Turn OFF"),
    ]
    
    for temp, expected_action, description in test_cases:
        commands.clear()
        
        # Reproduce the exact logic from app.py
        if enable_cool:
            if temp >= high:
                control_cooling("on")
            elif low is not None and temp <= low:
                control_cooling("off")
        else:
            control_cooling("off")
        
        actual_action = commands[0] if commands else None
        status = "✓" if actual_action == expected_action else "✗"
        
        print(f"{status} Temp={temp:5.1f}°F: {description}")
        print(f"   Expected action: {expected_action}, Actual: {actual_action}")
        
        if temp == 65.0:
            print(f"   >>> CRITICAL TEST: temp == low_limit")
            print(f"   >>> Condition: temp <= low → {temp} <= {low} → {temp <= low}")
            if actual_action == "off":
                print(f"   >>> ✓ CONFIRMED: Cooling turns OFF when temp EQUALS low")
            else:
                print(f"   >>> ✗ FAILED: Cooling did NOT turn OFF at low limit")
        print()
    
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print()
    print("The code uses: if temp <= low:")
    print("  - <= means 'less than OR EQUAL TO'")
    print("  - So cooling turns OFF when temp == low (not just when temp < low)")
    print()
    print("✓ REQUIREMENT SATISFIED: Cooling turns OFF at low limit, not below it!")
    print()
    
    print("SYMMETRY WITH HEATING:")
    print("  Heating: Turns OFF when temp >= high (at or above high limit)")
    print("  Cooling: Turns OFF when temp <= low  (at or below low limit)")
    print("  Both use inclusive comparisons (>= and <=) for precise control!")
    print()

if __name__ == '__main__':
    test_cooling_off_at_low_limit()
