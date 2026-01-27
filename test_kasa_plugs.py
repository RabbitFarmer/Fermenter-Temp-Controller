#!/usr/bin/env python3
"""
Test script to verify KASA plugs are responding.
Sends test commands to both heating and cooling plugs.
"""

import asyncio
import json
import os
import sys

# Import the kasa_control function from kasa_worker
try:
    from kasa_worker import kasa_control, PlugClass
except ImportError as e:
    print(f"❌ Failed to import kasa_worker: {e}")
    print("   Make sure python-kasa is installed: pip install python-kasa")
    sys.exit(1)

def load_temp_config():
    """Load temperature control config to get plug URLs"""
    config_file = 'config/temp_control_config.json'
    
    # Try actual config first
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    
    # Fall back to template
    template_file = 'config/temp_control_config.json.template'
    if os.path.exists(template_file):
        print(f"⚠️  Using template config (no actual config found)")
        with open(template_file, 'r') as f:
            return json.load(f)
    
    return {}

async def test_plug(url, mode, action='on'):
    """
    Test a single plug by sending a command and checking the result.
    
    Args:
        url: IP address or hostname of the plug
        mode: 'heating' or 'cooling'
        action: 'on' or 'off'
    
    Returns:
        (success, error_msg) tuple
    """
    print(f"\n{'='*70}")
    print(f"Testing {mode.upper()} plug at {url}")
    print(f"{'='*70}")
    
    if not url or url == "":
        print(f"❌ No URL configured for {mode} plug")
        return False, "No URL configured"
    
    print(f"📡 Sending '{action}' command to {url}...")
    
    try:
        # Use the same kasa_control function that the app uses
        error = await kasa_control(url, action, mode)
        
        if error is None:
            print(f"✅ SUCCESS: {mode} plug responded and confirmed '{action}' state")
            return True, None
        else:
            print(f"❌ FAILED: {error}")
            return False, error
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ EXCEPTION: {error_msg}")
        return False, error_msg

async def test_both_plugs():
    """Test both heating and cooling plugs"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*20 + "KASA PLUG CONNECTION TEST" + " "*23 + "║")
    print("╚" + "="*68 + "╝")
    
    # Load config
    config = load_temp_config()
    
    heating_url = config.get('heating_plug', '')
    cooling_url = config.get('cooling_plug', '')
    enable_heating = config.get('enable_heating', False)
    enable_cooling = config.get('enable_cooling', False)
    
    print(f"\n📋 Configuration:")
    print(f"   Heating plug: {heating_url} ({'ENABLED' if enable_heating else 'DISABLED'})")
    print(f"   Cooling plug: {cooling_url} ({'ENABLED' if enable_cooling else 'DISABLED'})")
    
    if not heating_url and not cooling_url:
        print("\n❌ ERROR: No plugs configured!")
        print("   Please configure plug URLs in config/temp_control_config.json")
        return False
    
    results = []
    
    # Test heating plug
    if heating_url:
        print(f"\n{'#'*70}")
        print(f"# TEST 1: HEATING PLUG")
        print(f"{'#'*70}")
        
        # Turn ON
        success, error = await test_plug(heating_url, 'heating', 'on')
        results.append(('Heating ON', success, error))
        
        if success:
            # Wait a bit
            await asyncio.sleep(2)
            
            # Turn OFF
            success, error = await test_plug(heating_url, 'heating', 'off')
            results.append(('Heating OFF', success, error))
    
    # Test cooling plug
    if cooling_url:
        print(f"\n{'#'*70}")
        print(f"# TEST 2: COOLING PLUG")
        print(f"{'#'*70}")
        
        # Turn ON
        success, error = await test_plug(cooling_url, 'cooling', 'on')
        results.append(('Cooling ON', success, error))
        
        if success:
            # Wait a bit
            await asyncio.sleep(2)
            
            # Turn OFF
            success, error = await test_plug(cooling_url, 'cooling', 'off')
            results.append(('Cooling OFF', success, error))
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    all_success = True
    for test_name, success, error in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if error:
            print(f"         Error: {error}")
        all_success = all_success and success
    
    print(f"{'='*70}")
    
    if all_success:
        print("\n🎉 ALL TESTS PASSED! Both plugs are responding correctly.")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED. Check errors above.")
        print("\nCommon issues:")
        print("  1. Plug IP addresses may have changed (check your router)")
        print("  2. Network connectivity issues")
        print("  3. Plugs may need to be reset/re-paired")
        print("  4. Firewall blocking communication")
        return False

if __name__ == '__main__':
    try:
        # Check if PlugClass is available
        if PlugClass is None:
            print("❌ ERROR: python-kasa library not available!")
            print("   Install it with: pip install python-kasa")
            sys.exit(1)
        
        # Run the async test
        success = asyncio.run(test_both_plugs())
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
