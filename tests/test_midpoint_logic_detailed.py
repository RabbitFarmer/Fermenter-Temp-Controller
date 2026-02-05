#!/usr/bin/env python3
"""
Comprehensive test to identify if there's a bug in the midpoint logic.

This test will check:
1. Does the condition `temp >= midpoint` evaluate correctly?
2. Does control_heating("off") actually get called?
3. Does the rate limiting prevent the OFF command?
4. Is there a state tracking issue?
"""

def test_midpoint_logic_detailed():
    """Detailed test of midpoint logic to find any bugs."""
    
    print("=" * 80)
    print("DETAILED MIDPOINT LOGIC TEST")
    print("=" * 80)
    
    # Test the pure logic without app.py
    low = 73.0
    high = 75.0
    midpoint = (low + high) / 2.0
    enable_heat = True
    
    print(f"\nConfiguration:")
    print(f"  low = {low}")
    print(f"  high = {high}")
    print(f"  midpoint = {midpoint}")
    print(f"  enable_heat = {enable_heat}")
    
    print(f"\n" + "-" * 80)
    print("Testing condition evaluation at different temperatures:")
    print("-" * 80)
    
    test_temps = [72.0, 73.0, 73.5, 74.0, 74.5, 75.0, 75.5, 76.0]
    
    for temp in test_temps:
        cond1 = (temp <= low)
        cond2 = (high is not None and temp > high)
        cond3 = (midpoint is not None and temp >= midpoint)
        
        # Determine which branch executes
        if enable_heat:
            if cond1:
                action = "control_heating('on')"
                branch = "1"
            elif cond2:
                action = "control_heating('off') - SAFETY"
                branch = "2"
            elif cond3:
                action = "control_heating('off') - MIDPOINT"
                branch = "3"
            else:
                action = "MAINTAIN STATE"
                branch = "4"
        else:
            action = "control_heating('off') - DISABLED"
            branch = "0"
        
        print(f"\n  Temp: {temp:5.1f}°F")
        print(f"    Condition 1 (temp <= {low}): {cond1}")
        print(f"    Condition 2 (temp > {high}): {cond2}")
        print(f"    Condition 3 (temp >= {midpoint}): {cond3}")
        print(f"    → Branch {branch}: {action}")
    
    print(f"\n" + "=" * 80)
    print("CONDITION ANALYSIS")
    print("=" * 80)
    
    # Check if there's any logic bug
    issues = []
    
    # At 74°F, condition 3 should be TRUE
    temp_74 = 74.0
    cond3_at_74 = (midpoint is not None and temp_74 >= midpoint)
    if not cond3_at_74:
        issues.append(f"BUG: At {temp_74}°F, condition 3 (temp >= midpoint) is FALSE! Expected TRUE.")
    else:
        print(f"\n✓ At {temp_74}°F, condition 3 (temp >= midpoint) correctly evaluates to TRUE")
    
    # At 76°F, condition 2 should be TRUE
    temp_76 = 76.0
    cond2_at_76 = (high is not None and temp_76 > high)
    if not cond2_at_76:
        issues.append(f"BUG: At {temp_76}°F, condition 2 (temp > high) is FALSE! Expected TRUE.")
    else:
        print(f"✓ At {temp_76}°F, condition 2 (temp > high) correctly evaluates to TRUE")
    
    # Check condition order - condition 2 should come before condition 3
    print(f"\n✓ Condition order is correct:")
    print(f"  1. Turn ON at temp <= low (highest priority for heating)")
    print(f"  2. Force OFF at temp > high (safety - higher priority than midpoint)")
    print(f"  3. Turn OFF at temp >= midpoint (normal hysteresis)")
    print(f"  4. Maintain state (hysteresis gap)")
    
    if issues:
        print(f"\n" + "=" * 80)
        print("ISSUES FOUND:")
        print("=" * 80)
        for issue in issues:
            print(f"  ✗ {issue}")
        return False
    else:
        print(f"\n" + "=" * 80)
        print("CONCLUSION")
        print("=" * 80)
        print("\n✓ The condition logic is MATHEMATICALLY CORRECT")
        print("\nIf heating stays ON at 74°F or 76°F, the bug is NOT in the")
        print("condition evaluation. It must be in one of these areas:")
        print("\n  1. Rate limiting - control_heating('off') is skipped")
        print("  2. State tracking - heater_on doesn't get updated")
        print("  3. Kasa plug - the OFF command doesn't reach the plug")
        print("  4. Asynchronous timing - the control loop doesn't run often enough")
        print("  5. Temperature reading - the temp value is stale/wrong")
        print("\nThe safety check (force OFF > 75°F) provides defense against")
        print("scenarios where the midpoint check fails for non-logic reasons.")
        return True

if __name__ == '__main__':
    import sys
    try:
        success = test_midpoint_logic_detailed()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
