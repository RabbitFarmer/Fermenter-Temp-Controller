#!/usr/bin/env python3
"""
Test to reproduce the exact issue from the bug report:
- Heating turns ON at startup when temp is below low limit
- Temperature rises and reaches high limit
- Heating SHOULD turn OFF but doesn't

From the user's log:
- Low limit: 74°F
- High limit: 75°F  
- Heater turned ON at 71°F ✓ Correct
- Temp rose to 74, 75, 76, 77°F
- Heater NEVER turned OFF ✗ BUG
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_heating_at_high_limit():
    """Test that heating turns OFF when temperature reaches high limit."""
    from app import temp_cfg, temperature_control_logic, ensure_temp_defaults, update_live_tilt
    from app import kasa_result_queue
    import queue
    
    print("=" * 80)
    print("HEATING CONTROL AT HIGH LIMIT - BUG REPRODUCTION TEST")
    print("=" * 80)
    print("\nSimulating the user's scenario:")
    print("- Low limit: 74°F, High limit: 75°F")
    print("- Heater turns ON at 71°F")
    print("- Temperature rises to 77°F")
    print("- Heater should turn OFF when temp >= 75°F")
    print("=" * 80)
    
    # Initialize temp config
    ensure_temp_defaults()
    
    # Configure temperature control
    temp_cfg.update({
        "low_limit": 74.0,
        "high_limit": 75.0,
        "enable_heating": True,
        "enable_cooling": False,
        "heating_plug": "192.168.1.100",  # Dummy plug address
        "cooling_plug": "",
        "tilt_color": "Black",  # User's tilt color
        "temp_control_enabled": True,
        "temp_control_active": True,
        "control_initialized": False,
        "heater_on": False,
        "heater_pending": False,
        "heater_pending_since": None,
        "heater_pending_action": None,
        "below_limit_trigger_armed": True,
        "above_limit_trigger_armed": True
    })
    
    # Simulate a Tilt reading to ensure we have a valid control tilt
    update_live_tilt("Black", gravity=1.0, temp_f=71.0, rssi=-75)
    
    print("\n[STEP 1] Temperature = 71°F (below low limit 74°F)")
    print("-" * 80)
    temp_cfg["current_temp"] = 71.0
    update_live_tilt("Black", gravity=1.0, temp_f=71.0, rssi=-75)
    
    # Run control logic
    temperature_control_logic()
    
    heater_pending_1 = temp_cfg.get("heater_pending", False)
    heater_on_1 = temp_cfg.get("heater_on", False)
    
    print(f"Result:")
    print(f"  heater_on: {heater_on_1}")
    print(f"  heater_pending: {heater_pending_1}")
    print(f"  status: {temp_cfg.get('status', 'Unknown')}")
    
    if heater_pending_1:
        print("  ✓ PASS: Heater ON command sent (pending)")
        # Simulate successful Kasa response
        temp_cfg["heater_pending"] = False
        temp_cfg["heater_pending_since"] = None
        temp_cfg["heater_pending_action"] = None
        temp_cfg["heater_on"] = True
        print("  → Simulating successful Kasa response: heater_on = True")
    elif heater_on_1:
        print("  ✓ PASS: Heater already ON")
    else:
        print("  ✗ FAIL: Heater should be ON or PENDING")
        return False
    
    # Clear the kasa_result_queue to avoid interference
    while not kasa_result_queue.empty():
        try:
            kasa_result_queue.get_nowait()
        except queue.Empty:
            break
    
    print("\n[STEP 2] Temperature = 75°F (AT high limit)")
    print("-" * 80)
    temp_cfg["current_temp"] = 75.0
    update_live_tilt("Black", gravity=1.0, temp_f=75.0, rssi=-75)
    
    print(f"Before control logic:")
    print(f"  current_temp: {temp_cfg['current_temp']}")
    print(f"  heater_on: {temp_cfg.get('heater_on')}")
    print(f"  heater_pending: {temp_cfg.get('heater_pending')}")
    
    # Run control logic
    temperature_control_logic()
    
    heater_pending_2 = temp_cfg.get("heater_pending", False)
    heater_on_2 = temp_cfg.get("heater_on", False)
    heater_pending_action_2 = temp_cfg.get("heater_pending_action")
    
    print(f"\nAfter control logic:")
    print(f"  heater_on: {heater_on_2}")
    print(f"  heater_pending: {heater_pending_2}")
    print(f"  heater_pending_action: {heater_pending_action_2}")
    print(f"  status: {temp_cfg.get('status', 'Unknown')}")
    
    # At 75°F (high limit), heating should turn OFF
    # Either heater_on should be False OR heater_pending with action="off" should be True
    if heater_pending_2 and heater_pending_action_2 == "off":
        print("  ✓ PASS: Heater OFF command sent (pending)")
        success = True
    elif not heater_on_2 and not heater_pending_2:
        print("  ✓ PASS: Heater is OFF")
        success = True
    else:
        print("  ✗ FAIL: Heater should be OFF or have OFF command pending")
        print(f"  >>> Expected: heater_on=False OR heater_pending_action='off'")
        print(f"  >>> Actual: heater_on={heater_on_2}, heater_pending={heater_pending_2}, action={heater_pending_action_2}")
        success = False
    
    # Simulate successful OFF response for next test
    if heater_pending_2 and heater_pending_action_2 == "off":
        temp_cfg["heater_pending"] = False
        temp_cfg["heater_pending_since"] = None
        temp_cfg["heater_pending_action"] = None
        temp_cfg["heater_on"] = False
        print("  → Simulating successful Kasa response: heater_on = False")
    
    print("\n[STEP 3] Temperature = 77°F (above high limit)")
    print("-" * 80)
    temp_cfg["current_temp"] = 77.0
    update_live_tilt("Black", gravity=1.0, temp_f=77.0, rssi=-75)
    
    print(f"Before control logic:")
    print(f"  current_temp: {temp_cfg['current_temp']}")
    print(f"  heater_on: {temp_cfg.get('heater_on')}")
    print(f"  heater_pending: {temp_cfg.get('heater_pending')}")
    
    # Run control logic
    temperature_control_logic()
    
    heater_pending_3 = temp_cfg.get("heater_pending", False)
    heater_on_3 = temp_cfg.get("heater_on", False)
    heater_pending_action_3 = temp_cfg.get("heater_pending_action")
    
    print(f"\nAfter control logic:")
    print(f"  heater_on: {heater_on_3}")
    print(f"  heater_pending: {heater_pending_3}")
    print(f"  heater_pending_action: {heater_pending_action_3}")
    print(f"  status: {temp_cfg.get('status', 'Unknown')}")
    
    # At 77°F (above high limit), heating should DEFINITELY be OFF
    if heater_on_3 or (heater_pending_3 and heater_pending_action_3 == "on"):
        print("  ✗ FAIL: Heater should be OFF at 77°F (above high limit 75°F)")
        print(f"  >>> This is the BUG reported by the user!")
        success = False
    else:
        print("  ✓ PASS: Heater correctly OFF at 77°F")
    
    print("\n" + "=" * 80)
    if success:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ TEST FAILED - BUG REPRODUCED")
    print("=" * 80)
    
    return success

if __name__ == '__main__':
    success = test_heating_at_high_limit()
    sys.exit(0 if success else 1)
