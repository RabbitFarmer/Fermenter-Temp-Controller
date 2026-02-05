#!/usr/bin/env python3
"""
Basic network connectivity test for KASA plug IP addresses.
Tests if the IPs are reachable on the network without requiring python-kasa.
"""

import socket
import sys

HEATING_PLUG_IP = "192.168.1.208"
COOLING_PLUG_IP = "192.168.1.194"
KASA_PORT = 9999  # KASA plugs listen on port 9999

print("=" * 80)
print("KASA PLUG NETWORK CONNECTIVITY TEST")
print("=" * 80)
print(f"\nTesting network connectivity to your confirmed IP addresses:")
print(f"  Heating Plug: {HEATING_PLUG_IP}")
print(f"  Cooling Plug: {COOLING_PLUG_IP}")
print(f"  Port: {KASA_PORT} (KASA protocol port)")
print("=" * 80)

def test_tcp_connection(ip_address, port, timeout=5):
    """
    Test if we can establish a TCP connection to the IP:port.
    
    Args:
        ip_address: IP to test
        port: Port to test
        timeout: Connection timeout in seconds
    
    Returns:
        Tuple of (success, message)
    """
    print(f"\n{'─' * 80}")
    print(f"Testing TCP connection to {ip_address}:{port}")
    print(f"{'─' * 80}")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        print(f"  ⏳ Attempting connection (timeout: {timeout}s)...")
        result = sock.connect_ex((ip_address, port))
        
        if result == 0:
            print(f"  ✅ SUCCESS: Port {port} is open and accepting connections")
            print(f"     This indicates a KASA plug is likely listening at {ip_address}")
            sock.close()
            return True, "Connection successful"
        else:
            print(f"  ❌ FAILED: Cannot connect to port {port}")
            print(f"     Error code: {result}")
            if result == 111:
                print(f"     Connection refused - device may not be a KASA plug or is offline")
            elif result == 113:
                print(f"     No route to host - IP may be wrong or device offline")
            sock.close()
            return False, f"Connection failed with error {result}"
            
    except socket.timeout:
        print(f"  ❌ FAILED: Connection timed out")
        print(f"     Device is not responding at {ip_address}:{port}")
        sock.close()
        return False, "Connection timeout"
        
    except socket.gaierror as e:
        print(f"  ❌ FAILED: Address resolution error: {e}")
        sock.close()
        return False, f"Address error: {e}"
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        sock.close()
        return False, str(e)

def main():
    """Run the connectivity test"""
    
    results = []
    
    # Test heating plug
    print("\n" + "=" * 80)
    print("TEST 1: HEATING PLUG")
    print("=" * 80)
    heating_success, heating_msg = test_tcp_connection(HEATING_PLUG_IP, KASA_PORT)
    results.append(('Heating', HEATING_PLUG_IP, heating_success, heating_msg))
    
    # Test cooling plug
    print("\n" + "=" * 80)
    print("TEST 2: COOLING PLUG")
    print("=" * 80)
    cooling_success, cooling_msg = test_tcp_connection(COOLING_PLUG_IP, KASA_PORT)
    results.append(('Cooling', COOLING_PLUG_IP, cooling_success, cooling_msg))
    
    # Print summary
    print("\n" + "=" * 80)
    print("CONNECTIVITY TEST SUMMARY")
    print("=" * 80)
    
    all_success = True
    for name, ip, success, msg in results:
        status = "✅ REACHABLE" if success else "❌ UNREACHABLE"
        print(f"{name} Plug ({ip}): {status}")
        all_success = all_success and success
    
    print("=" * 80)
    
    if all_success:
        print("\n✅ SUCCESS: Both IP addresses are reachable on port 9999!")
        print("   This indicates KASA plugs are present and listening.")
        print("   The program SHOULD be able to connect to these plugs.")
        print("\n📝 Next steps:")
        print("   1. Make sure these IPs are in config/temp_control_config.json:")
        print(f'      "heating_plug": "{HEATING_PLUG_IP}"')
        print(f'      "cooling_plug": "{COOLING_PLUG_IP}"')
        print("   2. Start the Flask app and use the 'KASA Test' button to verify")
        print("   3. The temperature control will use these IPs automatically")
        return 0
    else:
        print("\n⚠️  WARNING: Some or all IP addresses are unreachable!")
        print("   The program CANNOT connect to unreachable devices.")
        print("\n📝 Troubleshooting:")
        print("   1. Verify IP addresses are correct:")
        print("      - Check router's DHCP client list")
        print("      - Or use Kasa mobile app")
        print("   2. Verify plugs are powered on and WiFi connected")
        print("   3. Check network connectivity:")
        print(f"      ping {HEATING_PLUG_IP}")
        print(f"      ping {COOLING_PLUG_IP}")
        print("   4. Ensure computer and plugs are on same network/subnet")
        print("   5. Check firewall isn't blocking port 9999")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
