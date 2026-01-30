#!/usr/bin/env python3
"""
Simple test to verify the heating control logic bug.
"""

# Test the logic directly without running the full app
def test_heating_logic():
    """Test heating control logic with different temperatures."""
    
    low = 73.0
    high = 75.0
    midpoint = (low + high) / 2.0  # 74.0
    enable_heat = True
    
    print("=" * 80)
    print("HEATING CONTROL LOGIC TEST")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Low Limit: {low}°F")
    print(f"  High Limit: {high}°F")
    print(f"  Midpoint: {midpoint}°F")
    print(f"  Heating Enabled: {enable_heat}")
    
    print(f"\n" + "-" * 80)
    print("Testing logic at different temperatures:")
    print("-" * 80)
    
    test_temps = [72.0, 73.0, 73.5, 74.0, 74.5, 75.0, 76.0]
    
    for temp in test_temps:
        # Reproduce the exact logic from app.py lines 2606-2625
        action = None
        if enable_heat:
            if temp <= low:
                action = "Turn heating ON"
            elif midpoint is not None and temp >= midpoint:
                action = "Turn heating OFF"
            else:
                action = "Maintain current state"
        else:
            action = "Turn heating OFF (heating disabled)"
        
        print(f"  Temp: {temp:5.1f}°F  →  {action}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print("\nThe current logic:")
    print("  • Turns heating ON when temp ≤ 73°F (low_limit)")
    print("  • Turns heating OFF when temp ≥ 74°F (midpoint)")
    print("  • Maintains state when 73°F < temp < 74°F")
    
    print("\nAt 76°F (above high_limit of 75°F):")
    print("  • Logic says: Turn heating OFF ✓")
    print("  • This is CORRECT behavior")
    
    print("\nSo the heating SHOULD turn off at 76°F.")
    print("If it doesn't, the bug is likely in:")
    print("  1. The control_heating() function not actually turning off the plug")
    print("  2. Rate limiting preventing the command from executing")
    print("  3. Some other code path turning heating back on")
    print("  4. State not being tracked correctly")

if __name__ == '__main__':
    test_heating_logic()
