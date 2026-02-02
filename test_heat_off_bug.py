#!/usr/bin/env python3
"""
Test to reproduce the heating OFF bug.

Issue: Set low limit is 74F, high limit is 75F.
Start temp was 73F - heating turned ON (correct).
Current temp is 76F - heating is still ON (BUG - should be OFF).
"""

def test_logic():
    """Test the temperature control logic directly."""
    
    # Configuration
    low = 74.0
    high = 75.0
    enable_heat = True
    
    # Test temperatures
    test_cases = [
        (73.0, "ON", "Temp below low limit"),
        (74.0, "ON", "Temp at low limit"),
        (74.5, "MAINTAIN", "Temp between limits"),
        (75.0, "OFF", "Temp at high limit"),
        (76.0, "OFF", "Temp above high limit - THE BUG"),
    ]
    
    print("=" * 80)
    print("HEATING CONTROL LOGIC TEST")
    print("=" * 80)
    print(f"Configuration: Low={low}°F, High={high}°F")
    print(f"Heating Enabled: {enable_heat}\n")
    
    for temp, expected_action, description in test_cases:
        # Reproduce the EXACT logic from app.py lines 2717-2738
        if enable_heat:
            if temp <= low:
                action = "ON"
            elif high is not None and temp >= high:
                action = "OFF"
            else:
                action = "MAINTAIN"
        else:
            action = "OFF"
        
        status = "✓" if action == expected_action else "✗ BUG"
        print(f"{status} Temp={temp:5.1f}°F: {action:8s} (expected: {expected_action:8s}) - {description}")
    
    print("\n" + "=" * 80)
    print("EXPECTED BEHAVIOR:")
    print("=" * 80)
    print("When temp=76°F (above high limit of 75°F):")
    print("  - The condition 'temp >= high' (76 >= 75) is TRUE")
    print("  - The action should be: Turn heating OFF")
    print("  - The plug should be turned OFF")
    print("\nIf the plug stays ON, the bug is NOT in the logic but in:")
    print("  1. The control_heating() function not executing the OFF command")
    print("  2. Rate limiting or pending state blocking the OFF command")
    print("  3. Some other issue preventing the Kasa plug from turning off")

if __name__ == '__main__':
    test_logic()
