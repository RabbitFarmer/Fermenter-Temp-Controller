#!/usr/bin/env python3
"""
Manual verification script for the heating plug fix.

This script simulates the exact scenario from the bug report:
- Temperature control enabled
- Heating enabled
- No Tilt configured (tilt_color is empty)
- Current temperature below low_limit

Expected result: Heating commands should be sent to Kasa queue
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_fix():
    """Verify that heating works without a Tilt configured."""
    from app import (
        is_control_tilt_active,
        temp_cfg,
        temperature_control_logic,
        kasa_queue
    )
    
    print("\n" + "=" * 80)
    print("MANUAL VERIFICATION: Heating Plug Fix")
    print("=" * 80)
    print("\nScenario: Temperature control with NO Tilt configured")
    print("-" * 80)
    
    # Store original config
    original_cfg = dict(temp_cfg)
    
    try:
        # Clear the kasa queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        # Simulate user's configuration from the bug report
        print("\n1. Configuration:")
        temp_cfg['tilt_color'] = ''  # NO TILT CONFIGURED (this was the bug)
        temp_cfg['temp_control_enabled'] = True
        temp_cfg['enable_heating'] = True
        temp_cfg['enable_cooling'] = False
        temp_cfg['low_limit'] = 65.0
        temp_cfg['high_limit'] = 70.0
        temp_cfg['current_temp'] = 60.0  # Below low limit - should heat!
        temp_cfg['heating_plug'] = '192.168.1.100'
        temp_cfg['cooling_plug'] = ''
        temp_cfg['heater_on'] = False
        temp_cfg['cooler_on'] = False
        
        print(f"   tilt_color: '{temp_cfg['tilt_color']}' (empty - no Tilt)")
        print(f"   temp_control_enabled: {temp_cfg['temp_control_enabled']}")
        print(f"   enable_heating: {temp_cfg['enable_heating']}")
        print(f"   low_limit: {temp_cfg['low_limit']}°F")
        print(f"   high_limit: {temp_cfg['high_limit']}°F")
        print(f"   current_temp: {temp_cfg['current_temp']}°F")
        print(f"   heating_plug: {temp_cfg['heating_plug']}")
        
        # Check is_control_tilt_active
        print("\n2. Tilt Activity Check:")
        tilt_active = is_control_tilt_active()
        print(f"   is_control_tilt_active() = {tilt_active}")
        
        if not tilt_active:
            print("   ✗ FAIL: Should return True when no Tilt configured")
            print("   This would cause safety shutdown and prevent heating!")
            return False
        else:
            print("   ✓ PASS: Returns True (allows temperature control)")
        
        # Run temperature control logic
        print("\n3. Running Temperature Control Logic:")
        temperature_control_logic()
        
        status = temp_cfg.get('status')
        print(f"   Status: {status}")
        
        # Check for safety shutdown
        if status == "Control Tilt Inactive - Safety Shutdown":
            print("   ✗ FAIL: Triggered safety shutdown!")
            print("   This is the BUG - should not happen when no Tilt configured")
            return False
        else:
            print("   ✓ PASS: No safety shutdown")
        
        # Check if heating command was sent
        print("\n4. Heating Command Check:")
        heater_pending = temp_cfg.get('heater_pending')
        print(f"   heater_pending: {heater_pending}")
        
        if not heater_pending:
            print("   ✗ FAIL: No heating command was sent!")
            print("   This was the original bug - no heating commands")
            return False
        else:
            print("   ✓ PASS: Heating command sent to Kasa worker")
        
        # Check expected status
        if status == "Heating":
            print("   ✓ PASS: Status correctly shows 'Heating'")
        else:
            print(f"   ⚠ WARNING: Expected 'Heating' status, got '{status}'")
        
        print("\n" + "=" * 80)
        print("✓ VERIFICATION PASSED")
        print("=" * 80)
        print("\nSummary:")
        print("  - Temperature control works WITHOUT a Tilt configured")
        print("  - Heating commands ARE sent when temp < low_limit")
        print("  - No false safety shutdowns")
        print("  - Bug is FIXED! 🎉")
        print("\nThe heating plug will now turn on as expected.")
        
        return True
        
    finally:
        # Clear queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        # Restore original config
        temp_cfg.clear()
        temp_cfg.update(original_cfg)

if __name__ == '__main__':
    try:
        success = verify_fix()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
