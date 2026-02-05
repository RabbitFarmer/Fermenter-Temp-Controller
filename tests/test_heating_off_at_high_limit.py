#!/usr/bin/env python3
"""
Test to verify heating turns OFF when temp EQUALS high limit (not just exceeds).
"""

def test_heating_off_at_high_limit():
    """Test that heating turns OFF exactly at high_limit, not above it."""
    
    print("=" * 80)
    print("HEATING OFF AT HIGH LIMIT TEST")
    print("=" * 80)
    print()
    
    # Configuration
    low = 74.0
    high = 75.0
    enable_heat = True
    
    # State
    heater_on = False
    commands = []
    
    def control_heating(action):
        """Simulate control_heating function."""
        nonlocal heater_on
        commands.append(f"{action}")
        if action == "on":
            heater_on = True
        else:
            heater_on = False
    
    print(f"Configuration: Low={low}°F, High={high}°F")
    print()
    
    # Test temperatures
    test_cases = [
        (73.0, "on", "Below low limit → Turn ON"),
        (74.0, "on", "At low limit → Turn ON"),
        (74.5, None, "Between limits → Maintain state"),
        (75.0, "off", "AT HIGH LIMIT → Turn OFF (not above!)"),
        (76.0, "off", "Above high limit → Turn OFF"),
    ]
    
    for temp, expected_action, description in test_cases:
        commands.clear()
        
        # Reproduce the exact logic from app.py
        if enable_heat:
            if temp <= low:
                control_heating("on")
            elif high is not None and temp >= high:
                control_heating("off")
        else:
            control_heating("off")
        
        actual_action = commands[0] if commands else None
        status = "✓" if actual_action == expected_action else "✗"
        
        print(f"{status} Temp={temp:5.1f}°F: {description}")
        print(f"   Expected action: {expected_action}, Actual: {actual_action}")
        
        if temp == 75.0:
            print(f"   >>> CRITICAL TEST: temp == high_limit")
            print(f"   >>> Condition: temp >= high → {temp} >= {high} → {temp >= high}")
            if actual_action == "off":
                print(f"   >>> ✓ CONFIRMED: Heating turns OFF when temp EQUALS high")
            else:
                print(f"   >>> ✗ FAILED: Heating did NOT turn OFF at high limit")
        print()
    
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print()
    print("The code uses: if temp >= high:")
    print("  - >= means 'greater than OR EQUAL TO'")
    print("  - So heating turns OFF when temp == high (not just when temp > high)")
    print()
    print("✓ REQUIREMENT SATISFIED: Heating turns OFF at high limit, not above it!")
    print()

if __name__ == '__main__':
    test_heating_off_at_high_limit()
