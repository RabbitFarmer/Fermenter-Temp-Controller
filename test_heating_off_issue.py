#!/usr/bin/env python3
"""
Test to reproduce the heating not turning off issue.

Scenario from user:
- Current temp: 71F
- Low limit: 74F
- High limit: 75F
- System correctly turned on heat
- Temp rose to 77F
- Heat is still ON (should have turned OFF at 75F)
"""

def test_temperature_control_logic():
    """Simulate the temperature control logic"""
    
    # Mock config
    temp_cfg = {
        "enable_heating": True,
        "enable_cooling": False,
        "temp_control_active": True,
        "low_limit": 74.0,
        "high_limit": 75.0,
        "current_temp": 71.0,
        "heater_on": False,
        "heater_pending": False,
    }
    
    commands_sent = []
    
    def mock_control_heating(state):
        commands_sent.append(("heating", state))
        if state == "on":
            temp_cfg["heater_on"] = True
        else:
            temp_cfg["heater_on"] = False
    
    def run_control_logic():
        """Simplified version of temperature_control_logic()"""
        enable_heat = temp_cfg.get("enable_heating")
        temp = temp_cfg.get("current_temp")
        low = temp_cfg.get("low_limit")
        high = temp_cfg.get("high_limit")
        
        if enable_heat:
            if temp <= low:
                mock_control_heating("on")
            elif temp >= high:
                mock_control_heating("off")
            # else: maintain current state
    
    # Test sequence
    print("=== Test Sequence ===")
    print(f"Initial state: temp={temp_cfg['current_temp']}F, heater_on={temp_cfg['heater_on']}")
    print(f"Limits: low={temp_cfg['low_limit']}F, high={temp_cfg['high_limit']}F")
    print()
    
    # Step 1: Temperature at 71F (below low limit of 74F)
    print("Step 1: Temp at 71F (below low limit)")
    run_control_logic()
    print(f"  Commands sent: {commands_sent}")
    print(f"  Heater state: {temp_cfg['heater_on']}")
    assert commands_sent[-1] == ("heating", "on"), "Should turn heating ON"
    assert temp_cfg["heater_on"] == True, "Heater should be ON"
    print("  ✓ Heater turned ON correctly")
    print()
    
    # Step 2: Temperature rises to 74.5F (between limits)
    print("Step 2: Temp rises to 74.5F (between limits)")
    temp_cfg["current_temp"] = 74.5
    commands_sent.clear()
    run_control_logic()
    print(f"  Commands sent: {commands_sent}")
    print(f"  Heater state: {temp_cfg['heater_on']}")
    assert len(commands_sent) == 0, "Should NOT send commands when between limits"
    assert temp_cfg["heater_on"] == True, "Heater should still be ON"
    print("  ✓ Heater maintains ON state (correct)")
    print()
    
    # Step 3: Temperature reaches 75F (at high limit)
    print("Step 3: Temp reaches 75F (at high limit)")
    temp_cfg["current_temp"] = 75.0
    commands_sent.clear()
    run_control_logic()
    print(f"  Commands sent: {commands_sent}")
    print(f"  Heater state: {temp_cfg['heater_on']}")
    assert commands_sent[-1] == ("heating", "off"), "Should turn heating OFF at high limit"
    assert temp_cfg["heater_on"] == False, "Heater should be OFF"
    print("  ✓ Heater turned OFF at high limit")
    print()
    
    # Step 4: Temperature continues to 77F (above high limit)
    print("Step 4: Temp at 77F (above high limit)")
    temp_cfg["current_temp"] = 77.0
    commands_sent.clear()
    run_control_logic()
    print(f"  Commands sent: {commands_sent}")
    print(f"  Heater state: {temp_cfg['heater_on']}")
    # Should not send redundant OFF command
    assert temp_cfg["heater_on"] == False, "Heater should still be OFF"
    print("  ✓ Heater remains OFF")
    print()
    
    print("=== All Tests Passed ===")
    print("The logic is CORRECT in isolation.")
    print()
    print("The issue must be in:")
    print("1. Redundancy checking preventing the OFF command")
    print("2. Pending flag blocking the OFF command")
    print("3. Kasa command not being sent/processed")
    print("4. State not being updated after command succeeds")

if __name__ == "__main__":
    test_temperature_control_logic()
