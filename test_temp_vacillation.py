#!/usr/bin/env python3
"""
Test to reproduce the issue where temperature vacillates between 72-73F
with low_limit=73F and high_limit=75F, and the kasa plug doesn't engage.
"""

def test_temp_vacillation():
    """
    Simulate temperature vacillating between 72F and 73F.
    Low limit = 73F, High limit = 75F
    Expected: Heating should turn ON and STAY ON until temp reaches 75F
    """
    print("=" * 80)
    print("TEMPERATURE VACILLATION TEST")
    print("=" * 80)
    
    low = 73.0
    high = 75.0
    enable_heat = True
    
    print(f"\nConfiguration:")
    print(f"  Low Limit: {low}°F")
    print(f"  High Limit: {high}°F")
    print(f"  Heating Enabled: {enable_heat}")
    
    print(f"\n" + "-" * 80)
    print("Simulating temperature readings:")
    print("-" * 80)
    
    # Simulate the scenario from the issue
    temps = [80.0, 75.0, 74.0, 73.0, 72.0, 73.0, 72.0, 73.0, 72.0]
    
    # Mock state
    heater_on = False
    heater_pending = False
    
    def control_heating(action):
        nonlocal heater_on, heater_pending
        
        # Simulate the logic from app.py
        if action == "on":
            # Check if should send command
            if heater_pending:
                print(f"      → BLOCKED: heater_pending is True")
                return
            if heater_on:
                print(f"      → SKIPPED: heater already ON (redundant)")
                return
            print(f"      → COMMAND SENT: Turn heating ON")
            heater_pending = True
            # Simulate successful response
            heater_on = True
            heater_pending = False
        elif action == "off":
            if heater_pending:
                print(f"      → BLOCKED: heater_pending is True")
                return
            if not heater_on:
                print(f"      → SKIPPED: heater already OFF (redundant)")
                return
            print(f"      → COMMAND SENT: Turn heating OFF")
            heater_pending = True
            # Simulate successful response
            heater_on = False
            heater_pending = False
    
    for temp in temps:
        print(f"\nTemp: {temp:5.1f}°F")
        
        # Reproduce heating control logic from app.py (lines 2608-2630)
        if enable_heat:
            if temp <= low:
                print(f"    Logic: temp <= low_limit ({temp} <= {low})")
                print(f"    Action: Turn heating ON")
                control_heating("on")
                current_action = "Heating"
            elif high is not None and temp >= high:
                print(f"    Logic: temp >= high_limit ({temp} >= {high})")
                print(f"    Action: Turn heating OFF")
                control_heating("off")
                current_action = None
            else:
                print(f"    Logic: temp between limits ({low} < {temp} < {high})")
                print(f"    Action: Maintain current state")
                current_action = "Heating" if heater_on else None
        else:
            control_heating("off")
            current_action = None
        
        # Check status logic (lines 2678-2701)
        if low <= temp <= high:
            status = "In Range"
        elif current_action == "Heating":
            status = "Heating"
        else:
            status = "Idle"
        
        print(f"    Status: {status}")
        print(f"    Heater State: {'ON' if heater_on else 'OFF'}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    print("\nExpected behavior:")
    print("  • At 72°F: Heating turns ON and STAYS ON")
    print("  • At 73°F: Heating STAYS ON (temp <= low_limit)")
    print("  • At 74°F: Heating STAYS ON (maintain state)")
    print("  • At 75°F: Heating turns OFF")
    
    print("\nActual behavior from simulation:")
    print("  • At 72°F and 73°F: Heating turns ON")
    print("  • Heater STAYS ON even when temp vacillates")
    print("  • This is CORRECT hysteresis control")
    
    print("\nPossible real-world issues:")
    print("  1. heater_pending stuck True (blocks future commands)")
    print("  2. kasa_worker not responding (heater_pending never clears)")
    print("  3. Network issues preventing plug communication")
    print("  4. _should_send_kasa_command blocking commands incorrectly")

if __name__ == '__main__':
    test_temp_vacillation()
