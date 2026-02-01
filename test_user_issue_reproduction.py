#!/usr/bin/env python3
"""
Reproduce the exact issue described by the user:
- Started at 76F with a set range of 75F to 73F (low=73, high=75)
- Temperature dropped to 72F but heating didn't turn on
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_user_scenario():
    """Test the exact scenario described by the user."""
    from app import temp_cfg, temperature_control_logic, ensure_temp_defaults, update_live_tilt
    from datetime import datetime
    
    print("=" * 80)
    print("USER ISSUE REPRODUCTION TEST")
    print("=" * 80)
    print("\nIssue: Started at 76F with range 73F-75F, now at 72F but no heating")
    print("\nExpected: Heating should turn ON when temp <= 73F (low limit)")
    print("-" * 80)
    
    # Initialize temp config
    ensure_temp_defaults()
    
    # Configure temperature control
    temp_cfg.update({
        "low_limit": 73.0,
        "high_limit": 75.0,
        "enable_heating": True,
        "enable_cooling": False,
        "heating_plug": "192.168.1.100",  # Dummy plug address
        "cooling_plug": "",
        "tilt_color": "Red",  # Assign a specific tilt
        "temp_control_enabled": True,
        "temp_control_active": True,
        "control_initialized": True
    })
    
    # Simulate a Tilt reading to ensure we have a valid control tilt
    update_live_tilt("Red", gravity=1.050, temp_f=76.0, rssi=-75)
    
    print("\n[1] INITIAL STATE: Temperature at 76F")
    print("-" * 80)
    temp_cfg["current_temp"] = 76.0
    
    print(f"Configuration:")
    print(f"  Low Limit: {temp_cfg['low_limit']}°F")
    print(f"  High Limit: {temp_cfg['high_limit']}°F")
    print(f"  Current Temp: {temp_cfg['current_temp']}°F")
    print(f"  Heating Enabled: {temp_cfg['enable_heating']}")
    print(f"  Heating Plug: {temp_cfg['heating_plug']}")
    print(f"  Monitor Active: {temp_cfg['temp_control_active']}")
    
    # Run control logic
    temperature_control_logic()
    
    heater_state_1 = temp_cfg.get("heater_on", False)
    print(f"\nResult:")
    print(f"  Heater On: {heater_state_1}")
    print(f"  Status: {temp_cfg.get('status', 'Unknown')}")
    print(f"  Expected: Heater OFF (temp 76F > high limit 75F)")
    
    if heater_state_1:
        print("  ✗ FAIL: Heater should be OFF at 76F")
        return False
    else:
        print("  ✓ PASS: Heater correctly OFF at 76F")
    
    print("\n[2] TEMPERATURE DROPS TO 72F")
    print("-" * 80)
    temp_cfg["current_temp"] = 72.0
    update_live_tilt("Red", gravity=1.050, temp_f=72.0, rssi=-75)
    
    print(f"Current Temp: {temp_cfg['current_temp']}°F")
    print(f"  This is BELOW low limit of {temp_cfg['low_limit']}°F")
    print(f"  Heating Plug: {temp_cfg['heating_plug']}")
    print(f"  Heating SHOULD turn ON")
    
    # Run control logic again
    temperature_control_logic()
    
    heater_state_2 = temp_cfg.get("heater_on", False)
    heater_pending_2 = temp_cfg.get("heater_pending", False)
    print(f"\nResult:")
    print(f"  Heater On: {heater_state_2}")
    print(f"  Heater Pending: {heater_pending_2}")
    print(f"  Status: {temp_cfg.get('status', 'Unknown')}")
    print(f"  Expected: Heater ON or PENDING (temp 72F < low limit 73F)")
    
    # Accept either heater_on=True or heater_pending=True as success
    # heater_pending means the command was sent and is waiting for confirmation
    if not (heater_state_2 or heater_pending_2):
        print("  ✗ FAIL: Heater should be ON or PENDING at 72F")
        print("\nDEBUG INFO:")
        print(f"  below_limit_trigger_armed: {temp_cfg.get('below_limit_trigger_armed')}")
        print(f"  above_limit_trigger_armed: {temp_cfg.get('above_limit_trigger_armed')}")
        print(f"  heater_pending: {temp_cfg.get('heater_pending')}")
        print(f"  heater_on: {temp_cfg.get('heater_on')}")
        return False
    else:
        if heater_pending_2:
            print("  ✓ PASS: Heater command sent and PENDING at 72F")
        else:
            print("  ✓ PASS: Heater correctly ON at 72F")
    
    print("\n[3] TEMPERATURE RISES TO 75F")
    print("-" * 80)
    temp_cfg["current_temp"] = 75.0
    update_live_tilt("Red", gravity=1.050, temp_f=75.0, rssi=-75)
    
    print(f"Current Temp: {temp_cfg['current_temp']}°F")
    print(f"  This is AT high limit of {temp_cfg['high_limit']}°F")
    print(f"  Heating SHOULD turn OFF")
    
    # Run control logic again
    temperature_control_logic()
    
    heater_state_3 = temp_cfg.get("heater_on", False)
    print(f"\nResult:")
    print(f"  Heater On: {heater_state_3}")
    print(f"  Status: {temp_cfg.get('status', 'Unknown')}")
    print(f"  Expected: Heater OFF (temp 75F >= high limit 75F)")
    
    if heater_state_3:
        print("  ✗ FAIL: Heater should be OFF at 75F")
        return False
    else:
        print("  ✓ PASS: Heater correctly OFF at 75F")
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)
    return True

if __name__ == '__main__':
    try:
        success = test_user_scenario()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
