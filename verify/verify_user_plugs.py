#!/usr/bin/env python3
"""
Verification script to test connection to specific KASA plug IP addresses.
This script tests the user's confirmed IP addresses: 192.168.1.208 and 192.168.1.194
"""

import asyncio
import sys

# Test the specific IPs the user confirmed
HEATING_PLUG_IP = "192.168.1.208"
COOLING_PLUG_IP = "192.168.1.194"

print("=" * 80)
print("KASA PLUG CONNECTION VERIFICATION")
print("=" * 80)
print(f"\nTesting connection to your confirmed KASA plug IP addresses:")
print(f"  Heating Plug: {HEATING_PLUG_IP}")
print(f"  Cooling Plug: {COOLING_PLUG_IP}")
print("=" * 80)

# Check if python-kasa is available
try:
    from kasa.iot import IotPlug
    print("\n✅ python-kasa library is available")
except ImportError:
    print("\n❌ ERROR: python-kasa library not found!")
    print("   Install it with: pip install python-kasa")
    sys.exit(1)

async def test_connection(ip_address, device_name):
    """
    Test connection to a KASA plug at the specified IP address.
    
    Args:
        ip_address: The IP address to test
        device_name: Description of the device (for display)
    
    Returns:
        Tuple of (success, details_dict)
    """
    print(f"\n{'─' * 80}")
    print(f"Testing {device_name} at {ip_address}")
    print(f"{'─' * 80}")
    
    try:
        # Create plug instance
        print(f"  ⏳ Creating connection to {ip_address}...")
        plug = IotPlug(ip_address)
        
        # Attempt to update (retrieve device info) with timeout
        print(f"  ⏳ Attempting to connect (timeout: 10 seconds)...")
        await asyncio.wait_for(plug.update(), timeout=10)
        
        # If we get here, connection succeeded
        print(f"  ✅ SUCCESS: Connected to device at {ip_address}")
        
        # Get device details
        details = {
            'ip': ip_address,
            'alias': getattr(plug, 'alias', 'Unknown'),
            'model': getattr(plug, 'model', 'Unknown'),
            'is_on': getattr(plug, 'is_on', None),
            'has_emeter': getattr(plug, 'has_emeter', False)
        }
        
        print(f"  📋 Device Information:")
        print(f"     Name/Alias: {details['alias']}")
        print(f"     Model: {details['model']}")
        print(f"     Current State: {'ON' if details['is_on'] else 'OFF' if details['is_on'] is not None else 'Unknown'}")
        print(f"     Has Energy Meter: {'Yes' if details['has_emeter'] else 'No'}")
        
        return True, details
        
    except asyncio.TimeoutError:
        print(f"  ❌ FAILED: Connection timed out after 10 seconds")
        print(f"     This means the device is not responding at {ip_address}")
        print(f"     Possible causes:")
        print(f"       - IP address is incorrect")
        print(f"       - Device is offline/powered off")
        print(f"       - Network connectivity issue")
        print(f"       - Firewall blocking port 9999")
        return False, {'error': 'timeout', 'ip': ip_address}
        
    except Exception as e:
        error_str = str(e)
        print(f"  ❌ FAILED: {error_str}")
        
        # Provide specific guidance based on error
        if 'Errno 111' in error_str or 'Connection refused' in error_str:
            print(f"     Connection refused - device exists but not responding on port 9999")
        elif 'Errno 113' in error_str or 'No route to host' in error_str:
            print(f"     Network error - cannot reach {ip_address}")
            print(f"     Check that device is on the same network")
        elif 'Name or service not known' in error_str:
            print(f"     Cannot resolve hostname")
        
        return False, {'error': error_str, 'ip': ip_address}

async def main():
    """Run the verification test"""
    
    results = []
    
    # Test heating plug
    print("\n" + "=" * 80)
    print("TEST 1: HEATING PLUG")
    print("=" * 80)
    heating_success, heating_details = await test_connection(HEATING_PLUG_IP, "Heating Plug")
    results.append(('Heating', heating_success, heating_details))
    
    # Test cooling plug
    print("\n" + "=" * 80)
    print("TEST 2: COOLING PLUG")
    print("=" * 80)
    cooling_success, cooling_details = await test_connection(COOLING_PLUG_IP, "Cooling Plug")
    results.append(('Cooling', cooling_success, cooling_details))
    
    # Print summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    all_success = True
    for name, success, details in results:
        status = "✅ CONNECTED" if success else "❌ FAILED"
        print(f"{name} Plug ({details.get('ip', 'unknown')}): {status}")
        if success:
            print(f"   Device Name: {details.get('alias', 'Unknown')}")
        all_success = all_success and success
    
    print("=" * 80)
    
    if all_success:
        print("\n✅ SUCCESS: Both KASA plugs are reachable and responding!")
        print("   The program CAN connect to your plugs at these IP addresses.")
        print("\n📝 Next steps:")
        print("   1. Make sure these IPs are configured in config/temp_control_config.json")
        print("   2. The temperature control will use these IPs to control your plugs")
        print("   3. You can also test via the web UI using the 'KASA Test' button")
        return 0
    else:
        print("\n⚠️  WARNING: Some or all plugs are not reachable!")
        print("   The program CANNOT connect to plugs that failed the test.")
        print("\n📝 Troubleshooting:")
        print("   1. Verify the IP addresses are correct")
        print("   2. Check that plugs are powered on and connected to WiFi")
        print("   3. Ensure this computer and the plugs are on the same network")
        print("   4. Try pinging the IPs: ping 192.168.1.208")
        print("   5. Check if firewall is blocking port 9999")
        return 1

if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
