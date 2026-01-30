#!/usr/bin/env python3
"""
Test for Temperature Control Bug: Heating plug stays ON when temperature exceeds high limit.

This test reproduces the exact issue:
- Temperature range is set to 73°F - 75°F (heating mode)
- Current temperature is 76°F (above the high limit)
- BUG: Heating plug should be OFF but stays ON
- EXPECTED: Heating should turn OFF when temp > high_limit
"""

import sys
import os
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_heating_above_high_limit():
    """Test that heating turns OFF when temperature exceeds high limit."""
    from app import (
        temp_cfg, 
        temperature_control_logic,
        live_tilts,
        update_live_tilt,
        system_cfg
    )
    
    print("=" * 80)
    print("TEST: Heating Control Above High Limit")
    print("=" * 80)
    print("\nISSUE DESCRIPTION:")
    print("  'Temperature Controller is set up for heating within a temperature")
    print("   range of 73F to 75F. It is now reading 76F and the heating plug")
    print("   is still on.'")
    print("\n" + "=" * 80)
    
    # Clear any existing tilts
    live_tilts.clear()
    
    # Configure temperature control
    temp_cfg['temp_control_enabled'] = True
    temp_cfg['tilt_color'] = 'Red'
    temp_cfg['low_limit'] = 73.0
    temp_cfg['high_limit'] = 75.0
    temp_cfg['heating_plug'] = 'test_heating_plug'
    temp_cfg['enable_heating'] = True
    temp_cfg['enable_cooling'] = False
    temp_cfg['temp_control_active'] = True
    temp_cfg['control_initialized'] = True  # Skip initialization log
    
    print("\n[1] CONFIGURATION")
    print("-" * 80)
    print(f"Low Limit: {temp_cfg['low_limit']}°F")
    print(f"High Limit: {temp_cfg['high_limit']}°F")
    print(f"Midpoint: {(temp_cfg['low_limit'] + temp_cfg['high_limit']) / 2}°F")
    print(f"Heating Enabled: {temp_cfg['enable_heating']}")
    print(f"Cooling Enabled: {temp_cfg['enable_cooling']}")
    
    print("\n[2] SCENARIO: Temperature at 72°F (Below Low Limit)")
    print("-" * 80)
    
    # Simulate temperature at 72°F - heating should turn ON
    update_live_tilt('Red', gravity=1.050, temp_f=72.0, rssi=-75)
    temp_cfg['current_temp'] = 72.0
    
    # Manually trigger temp control logic (normally done by background thread)
    temperature_control_logic()
    
    heating_state_at_72 = temp_cfg.get('heater_on', False)
    print(f"Temperature: 72.0°F")
    print(f"Heating State: {'ON' if heating_state_at_72 else 'OFF'}")
    
    if heating_state_at_72:
        print("✓ Heating correctly turned ON (temp below low limit)")
    else:
        print(f"✗ UNEXPECTED: Heating is OFF, expected ON")
    
    print("\n[3] SCENARIO: Temperature at 74°F (At Midpoint)")
    print("-" * 80)
    
    # Simulate temperature at 74°F - heating should turn OFF (at midpoint)
    update_live_tilt('Red', gravity=1.050, temp_f=74.0, rssi=-75)
    temp_cfg['current_temp'] = 74.0
    temperature_control_logic()
    
    heating_state_at_74 = temp_cfg.get('heater_on', False)
    print(f"Temperature: 74.0°F")
    print(f"Heating State: {'ON' if heating_state_at_74 else 'OFF'}")
    
    if not heating_state_at_74:
        print("✓ Heating correctly turned OFF (temp at midpoint)")
    else:
        print(f"✗ UNEXPECTED: Heating is ON, expected OFF")
    
    print("\n[4] SCENARIO: Temperature at 76°F (Above High Limit) - THE BUG")
    print("-" * 80)
    
    # First turn heating ON by going below low limit
    update_live_tilt('Red', gravity=1.050, temp_f=72.0, rssi=-75)
    temp_cfg['current_temp'] = 72.0
    temperature_control_logic()
    
    # Now simulate temperature rising to 76°F (above high limit)
    update_live_tilt('Red', gravity=1.050, temp_f=76.0, rssi=-75)
    temp_cfg['current_temp'] = 76.0
    temperature_control_logic()
    
    heating_state_at_76 = temp_cfg.get('heater_on', False)
    print(f"Temperature: 76.0°F (exceeds high limit of 75.0°F)")
    print(f"Heating State: {'ON' if heating_state_at_76 else 'OFF'}")
    
    # This is the bug: heating should be OFF when temp > high_limit
    if not heating_state_at_76:
        print("✓ SUCCESS: Heating correctly turned OFF (temp above high limit)")
        print("\n[5] RESULT")
        print("-" * 80)
        print("✓ Bug is FIXED!")
        print("  - Heating turns OFF when temperature exceeds high limit")
        print("  - This prevents overheating beyond the configured range")
        return True
    else:
        print(f"✗ FAILED: Heating is ON, should be OFF")
        print("\n  This is the BUG:")
        print("  - Temperature (76°F) is above high limit (75°F)")
        print("  - Heating should turn OFF to prevent overheating")
        print("  - Currently heating stays ON, causing temperature to rise further")
        print("\n[5] RESULT")
        print("-" * 80)
        print("✗ Bug is NOT FIXED")
        return False

def demonstrate_expected_behavior():
    """Demonstrate the expected temperature control behavior."""
    print("\n" + "=" * 80)
    print("EXPECTED BEHAVIOR")
    print("=" * 80)
    print("\nWith heating range 73°F - 75°F (midpoint = 74°F):")
    print("\n  Temperature Range    | Heating State")
    print("  " + "-" * 52)
    print("  ≤ 73°F (low limit)   | ON  - Turn heating on")
    print("  73°F < temp < 74°F   | MAINTAIN - Keep current state")
    print("  ≥ 74°F (midpoint)    | OFF - Turn heating off")
    print("  > 75°F (high limit)  | OFF - MUST be off (safety)")
    print("\nThe bug: When temp > high_limit, heating should ALWAYS be OFF")
    print("to prevent the temperature from exceeding the maximum safe range.")

if __name__ == '__main__':
    try:
        success = test_heating_above_high_limit()
        if success:
            demonstrate_expected_behavior()
            print("\n" + "=" * 80)
            print("END-TO-END TEST PASSED ✓")
            print("=" * 80)
            sys.exit(0)
        else:
            demonstrate_expected_behavior()
            print("\n" + "=" * 80)
            print("END-TO-END TEST FAILED ✗")
            print("=" * 80)
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
