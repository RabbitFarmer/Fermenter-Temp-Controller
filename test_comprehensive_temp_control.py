#!/usr/bin/env python3
"""
Comprehensive test for temperature control fix.
Tests both heating and cooling with pending command logic.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_heating_and_cooling():
    """Test that opposite commands can override pending commands for both heating and cooling."""
    from app import temp_cfg, temperature_control_logic, ensure_temp_defaults, update_live_tilt
    
    print("=" * 80)
    print("COMPREHENSIVE TEMPERATURE CONTROL TEST")
    print("=" * 80)
    print("\nTesting that opposite commands override pending commands")
    print("-" * 80)
    
    # Initialize temp config
    ensure_temp_defaults()
    
    # Test 1: Heating scenario
    print("\n[TEST 1] HEATING SCENARIO")
    print("-" * 80)
    
    temp_cfg.update({
        "low_limit": 68.0,
        "high_limit": 70.0,
        "enable_heating": True,
        "enable_cooling": False,
        "heating_plug": "192.168.1.100",
        "cooling_plug": "192.168.1.101",
        "tilt_color": "Red",
        "temp_control_enabled": True,
        "temp_control_active": True,
        "control_initialized": True
    })
    
    # Simulate a Tilt reading
    update_live_tilt("Red", gravity=1.050, temp_f=72.0, rssi=-75)
    
    print("Starting at 72°F (above high limit of 70°F)")
    temp_cfg["current_temp"] = 72.0
    temperature_control_logic()
    
    print("\nDropping to 67°F (below low limit of 68°F)")
    temp_cfg["current_temp"] = 67.0
    update_live_tilt("Red", gravity=1.050, temp_f=67.0, rssi=-75)
    temperature_control_logic()
    
    heater_pending = temp_cfg.get("heater_pending", False)
    heater_pending_action = temp_cfg.get("heater_pending_action")
    
    if heater_pending and heater_pending_action == "on":
        print(f"✓ PASS: Heating ON command sent (pending={heater_pending}, action={heater_pending_action})")
    else:
        print(f"✗ FAIL: Expected heating ON pending")
        return False
    
    # Test 2: Cooling scenario
    print("\n[TEST 2] COOLING SCENARIO")
    print("-" * 80)
    
    temp_cfg.update({
        "low_limit": 68.0,
        "high_limit": 70.0,
        "enable_heating": False,
        "enable_cooling": True,
        "current_temp": 67.0,
    })
    
    print("Starting at 67°F (below low limit of 68°F)")
    update_live_tilt("Red", gravity=1.050, temp_f=67.0, rssi=-75)
    temperature_control_logic()
    
    print("\nRising to 71°F (above high limit of 70°F)")
    temp_cfg["current_temp"] = 71.0
    update_live_tilt("Red", gravity=1.050, temp_f=71.0, rssi=-75)
    temperature_control_logic()
    
    cooler_pending = temp_cfg.get("cooler_pending", False)
    cooler_pending_action = temp_cfg.get("cooler_pending_action")
    
    if cooler_pending and cooler_pending_action == "on":
        print(f"✓ PASS: Cooling ON command sent (pending={cooler_pending}, action={cooler_pending_action})")
    else:
        print(f"✗ FAIL: Expected cooling ON pending")
        return False
    
    # Test 3: Both heating and cooling enabled
    print("\n[TEST 3] BOTH HEATING AND COOLING ENABLED")
    print("-" * 80)
    
    temp_cfg.update({
        "low_limit": 68.0,
        "high_limit": 70.0,
        "enable_heating": True,
        "enable_cooling": True,
        "current_temp": 69.0,  # In range
    })
    
    print("Starting at 69°F (in range 68-70°F)")
    update_live_tilt("Red", gravity=1.050, temp_f=69.0, rssi=-75)
    temperature_control_logic()
    
    status = temp_cfg.get("status", "")
    if "In Range" in status:
        print(f"✓ PASS: Status shows 'In Range': {status}")
    else:
        print(f"✗ FAIL: Expected 'In Range' status, got: {status}")
        return False
    
    print("\nDropping to 67°F (below low limit)")
    temp_cfg["current_temp"] = 67.0
    update_live_tilt("Red", gravity=1.050, temp_f=67.0, rssi=-75)
    temperature_control_logic()
    
    heater_pending = temp_cfg.get("heater_pending", False)
    cooler_on = temp_cfg.get("cooler_on", False)
    
    if heater_pending and not cooler_on:
        print(f"✓ PASS: Heating enabled, cooling off")
    else:
        print(f"✗ FAIL: Expected heating enabled, cooling off")
        return False
    
    print("\nRising to 71°F (above high limit)")
    temp_cfg["current_temp"] = 71.0
    update_live_tilt("Red", gravity=1.050, temp_f=71.0, rssi=-75)
    temperature_control_logic()
    
    cooler_pending = temp_cfg.get("cooler_pending", False)
    heater_on = temp_cfg.get("heater_on", False)
    
    if cooler_pending and not heater_on:
        print(f"✓ PASS: Cooling enabled, heating off")
    else:
        print(f"✗ FAIL: Expected cooling enabled, heating off")
        return False
    
    print("\n" + "=" * 80)
    print("ALL COMPREHENSIVE TESTS PASSED ✓")
    print("=" * 80)
    return True

if __name__ == '__main__':
    try:
        success = test_heating_and_cooling()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
