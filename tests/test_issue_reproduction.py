#!/usr/bin/env python3
"""
Test to reproduce the exact issue reported:
- Temperature range set at 73F to 75F
- Beginning temp was 71F
- System correctly turned on heat
- But heat never turned off even though temperature is now 80F
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_issue_reproduction():
    """Reproduce the exact issue step by step."""
    from app import (
        temp_cfg, 
        temperature_control_logic,
        live_tilts,
        update_live_tilt,
        system_cfg
    )
    
    print("=" * 80)
    print("ISSUE REPRODUCTION TEST")
    print("=" * 80)
    print("\nUser Report:")
    print("  'Started monitoring with the temperature range set at 73F to 75F.")
    print("   Beginning temp was 71F. System correctly turned on the heat.")
    print("   But it has never turned off the heat and the temperature is now 80F.'")
    print("\n" + "=" * 80)
    
    # Clear any existing tilts
    live_tilts.clear()
    
    # Step 1: Configure temperature control as user described
    print("\n[STEP 1] Configure Temperature Control")
    print("-" * 80)
    temp_cfg.clear()
    temp_cfg['temp_control_enabled'] = True
    temp_cfg['temp_control_active'] = True  # Monitor is ON
    temp_cfg['tilt_color'] = 'Red'
    temp_cfg['low_limit'] = 73.0
    temp_cfg['high_limit'] = 75.0
    temp_cfg['heating_plug'] = '192.168.1.100'  # Simulate real plug IP
    temp_cfg['enable_heating'] = True
    temp_cfg['enable_cooling'] = False
    temp_cfg['control_initialized'] = True  # Skip initialization log
    temp_cfg['heater_on'] = False  # Initially OFF
    temp_cfg['heater_pending'] = False
    
    print(f"Low Limit: {temp_cfg['low_limit']}°F")
    print(f"High Limit: {temp_cfg['high_limit']}°F")
    print(f"Heating Enabled: {temp_cfg['enable_heating']}")
    print(f"Heating Plug: {temp_cfg['heating_plug']}")
    print(f"Initial Heater State: {'ON' if temp_cfg['heater_on'] else 'OFF'}")
    
    # Step 2: Start with temperature at 71F (below low limit)
    print("\n[STEP 2] Temperature at 71°F (Below Low Limit)")
    print("-" * 80)
    update_live_tilt('Red', gravity=1.050, temp_f=71.0, rssi=-75)
    temp_cfg['current_temp'] = 71.0
    
    print(f"Temperature: 71.0°F")
    print(f"Expected: Heating should turn ON (temp < low_limit)")
    
    # Run temperature control logic
    temperature_control_logic()
    
    heater_on_at_71 = temp_cfg.get('heater_on', False)
    heater_pending_at_71 = temp_cfg.get('heater_pending', False)
    print(f"Result: Heater ON = {heater_on_at_71}, Heater Pending = {heater_pending_at_71}")
    
    if heater_pending_at_71:
        print("✓ Heating command sent (pending confirmation)")
        # Simulate successful KASA response
        temp_cfg['heater_on'] = True
        temp_cfg['heater_pending'] = False
        print("  [Simulated] KASA plug responded successfully - heater_on = True")
    elif heater_on_at_71:
        print("✓ Heating is ON")
    else:
        print("✗ UNEXPECTED: Heating did not turn on")
    
    # Step 3: Temperature rises to 74F (between limits)
    print("\n[STEP 3] Temperature at 74°F (Between Limits)")
    print("-" * 80)
    update_live_tilt('Red', gravity=1.050, temp_f=74.0, rssi=-75)
    temp_cfg['current_temp'] = 74.0
    
    print(f"Temperature: 74.0°F")
    print(f"Expected: Heating should MAINTAIN current state (within range)")
    print(f"Before: heater_on = {temp_cfg.get('heater_on')}")
    
    temperature_control_logic()
    
    heater_on_at_74 = temp_cfg.get('heater_on', False)
    print(f"After: heater_on = {heater_on_at_74}")
    
    if heater_on_at_74:
        print("✓ Heating maintained ON state (correct)")
    else:
        print("? Heating is OFF (might be OK depending on hysteresis)")
    
    # Step 4: Temperature rises to 76F (above high limit)
    print("\n[STEP 4] Temperature at 76°F (Above High Limit) - THE CRITICAL TEST")
    print("-" * 80)
    # Make sure heater is ON before this test
    temp_cfg['heater_on'] = True
    temp_cfg['heater_pending'] = False
    print(f"Setup: heater_on = {temp_cfg.get('heater_on')} (forcing ON for test)")
    
    update_live_tilt('Red', gravity=1.050, temp_f=76.0, rssi=-75)
    temp_cfg['current_temp'] = 76.0
    
    print(f"Temperature: 76.0°F (exceeds high limit of 75.0°F)")
    print(f"Expected: Heating MUST turn OFF (temp > high_limit)")
    
    temperature_control_logic()
    
    heater_on_at_76 = temp_cfg.get('heater_on', False)
    heater_pending_at_76 = temp_cfg.get('heater_pending', False)
    print(f"Result: Heater ON = {heater_on_at_76}, Heater Pending = {heater_pending_at_76}")
    
    # Check if OFF command was sent
    # Note: heater_on stays True until KASA confirms the command succeeded
    if heater_pending_at_76 and not heater_on_at_76:
        # Rare: command sent and state already False (maybe from previous confirmation)
        print("✓ Heating OFF command sent (pending confirmation)")
        success = True
    elif not heater_on_at_76 and not heater_pending_at_76:
        print("✓ Heating is OFF (already confirmed)")
        success = True
    elif heater_pending_at_76 and heater_on_at_76:
        # Expected: OFF command sent, waiting for KASA worker confirmation
        print("⚠ Heating OFF command sent but heater_on still True (waiting for confirmation)")
        success = True
    else:
        # Bug: heater_on=True and heater_pending=False means no OFF command was sent
        print("✗ BUG REPRODUCED: Heating is still ON even though temp > high_limit")
        print(f"   heater_on = {heater_on_at_76}")
        print(f"   heater_pending = {heater_pending_at_76}")
        success = False
    
    # Step 5: Temperature at 80F (way above high limit)
    print("\n[STEP 5] Temperature at 80°F (Way Above High Limit)")
    print("-" * 80)
    # Reset to simulate issue - heater is still ON
    temp_cfg['heater_on'] = True
    temp_cfg['heater_pending'] = False
    print(f"Setup: heater_on = {temp_cfg.get('heater_on')} (simulating stuck ON state)")
    
    update_live_tilt('Red', gravity=1.050, temp_f=80.0, rssi=-75)
    temp_cfg['current_temp'] = 80.0
    
    print(f"Temperature: 80.0°F (WAY above high limit of 75.0°F)")
    print(f"Expected: Heating MUST turn OFF immediately")
    
    temperature_control_logic()
    
    heater_on_at_80 = temp_cfg.get('heater_on', False)
    heater_pending_at_80 = temp_cfg.get('heater_pending', False)
    print(f"Result: Heater ON = {heater_on_at_80}, Heater Pending = {heater_pending_at_80}")
    
    if heater_pending_at_80 or not heater_on_at_80:
        print("✓ System attempting to turn heating OFF")
    else:
        print("✗ CRITICAL BUG: Heating still ON at 80°F!")
        success = False
    
    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    if success:
        print("✓ Temperature control logic appears correct")
        print("  The issue may be:")
        print("  1. KASA plug communication failure (commands not reaching plug)")
        print("  2. State synchronization issue (heater_on not updated after failure)")
        print("  3. Command deduplication preventing retry after failure")
    else:
        print("✗ Bug reproduced in temperature control logic")
        print("  The heating does not turn OFF when temp > high_limit")
    
    return success

if __name__ == '__main__':
    try:
        success = test_issue_reproduction()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
