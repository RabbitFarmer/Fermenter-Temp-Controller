#!/usr/bin/env python3
"""
Test to understand the root cause: Why doesn't heating turn OFF at midpoint?

This simulates a real temperature progression scenario:
1. Start at 72°F (below low) - heating should turn ON
2. Temp rises to 73°F - heating should stay ON
3. Temp rises to 73.5°F - heating should stay ON (in hysteresis gap)
4. Temp rises to 74°F - heating should turn OFF (at midpoint)
5. Temp rises to 75°F - heating should stay OFF
6. Temp rises to 76°F - heating should stay OFF

This tests whether the heating actually turns OFF at step 4 (the midpoint).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_temperature_progression():
    """Test heating control through a realistic temperature progression."""
    from app import (
        temp_cfg,
        temperature_control_logic,
        live_tilts,
        update_live_tilt,
    )
    
    print("=" * 80)
    print("ROOT CAUSE TEST: Temperature Progression")
    print("=" * 80)
    print("\nSimulating realistic temperature rise with heating control")
    print("Range: 73°F - 75°F (midpoint = 74°F)")
    
    # Setup
    live_tilts.clear()
    temp_cfg['temp_control_enabled'] = True
    temp_cfg['tilt_color'] = 'Red'
    temp_cfg['low_limit'] = 73.0
    temp_cfg['high_limit'] = 75.0
    temp_cfg['heating_plug'] = 'test_heating_plug'
    temp_cfg['enable_heating'] = True
    temp_cfg['enable_cooling'] = False
    temp_cfg['temp_control_active'] = True
    temp_cfg['control_initialized'] = True
    temp_cfg['heater_on'] = False  # Start with heater OFF
    temp_cfg['heater_pending'] = False
    
    # Temperature progression: heating turns on, temp rises, heating should turn off
    temps = [
        (72.0, "Below low limit - expect heating ON"),
        (73.0, "At low limit - expect heating ON"),
        (73.5, "In hysteresis gap - expect heating to STAY ON"),
        (74.0, "At midpoint - expect heating to turn OFF ← CRITICAL"),
        (74.5, "Above midpoint - expect heating to STAY OFF"),
        (75.0, "At high limit - expect heating to STAY OFF"),
        (76.0, "Above high limit - expect heating to STAY OFF (safety)"),
    ]
    
    print("\n" + "-" * 80)
    print("Temperature Progression Test:")
    print("-" * 80)
    
    results = []
    for temp, description in temps:
        # Update temperature
        update_live_tilt('Red', gravity=1.050, temp_f=temp, rssi=-75)
        temp_cfg['current_temp'] = temp
        
        # Store state BEFORE control logic runs
        heater_before = temp_cfg.get('heater_on', False)
        
        # Run control logic
        temperature_control_logic()
        
        # Store state AFTER control logic runs
        heater_after = temp_cfg.get('heater_on', False)
        
        # Determine what happened
        if heater_before == heater_after:
            state_change = f"(no change: {'ON' if heater_after else 'OFF'})"
        else:
            state_change = f"({'ON' if heater_before else 'OFF'} → {'ON' if heater_after else 'OFF'})"
        
        status = "✓" if (
            (temp <= 73.0 and heater_after) or  # Should be ON below/at low
            (temp >= 74.0 and not heater_after)  # Should be OFF at/above midpoint
        ) else "✗"
        
        result_line = f"{status} Temp: {temp:5.1f}°F - Heater: {'ON ' if heater_after else 'OFF'} {state_change}"
        print(f"  {result_line}")
        print(f"     {description}")
        
        results.append({
            'temp': temp,
            'heater_on': heater_after,
            'expected': temp < 74.0 if temp <= 73.0 or heater_before else temp < 74.0,
            'description': description
        })
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    # Check critical transition at 74°F
    temp_74_result = [r for r in results if r['temp'] == 74.0][0]
    
    if temp_74_result['heater_on']:
        print("\n✗ PROBLEM FOUND!")
        print("  At 74°F (midpoint), heating should turn OFF but it stayed ON")
        print("  This is the ROOT CAUSE of the bug:")
        print("    - Heating turns ON at 72°F")
        print("    - Temp rises through the hysteresis gap (73-74°F)")
        print("    - At 74°F, heating SHOULD turn OFF but doesn't")
        print("    - Temp continues to rise past 75°F to 76°F")
        print("    - Heating stays ON even at 76°F (the reported bug)")
        print("\n  The safety check (force OFF > 75°F) is a band-aid.")
        print("  The real fix should make heating turn OFF at 74°F properly.")
        return False
    else:
        print("\n✓ Logic appears correct!")
        print("  At 74°F (midpoint), heating turned OFF as expected")
        print("  This suggests the logic itself is correct, but there may be:")
        print("    1. A race condition or timing issue")
        print("    2. State tracking problem (heater_on not updating)")
        print("    3. Rate limiting preventing the OFF command")
        print("    4. The Kasa plug not responding to the OFF command")
        print("\n  The safety check (force OFF > 75°F) provides defense-in-depth")
        print("  against edge cases where the midpoint check fails.")
        return True

if __name__ == '__main__':
    try:
        success = test_temperature_progression()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
