#!/usr/bin/env python3
"""
Diagnostic script for KASA plug connectivity issues.
Helps identify why plugs are not responding.
"""

import asyncio
import json
import os
import sys

def check_config():
    """Check if actual config exists and show plug settings"""
    print("╔" + "="*68 + "╗")
    print("║" + " "*18 + "KASA PLUG DIAGNOSTIC TOOL" + " "*25 + "║")
    print("╚" + "="*68 + "╝\n")
    
    config_file = 'config/temp_control_config.json'
    template_file = 'config/temp_control_config.json.template'
    
    if os.path.exists(config_file):
        print("✅ Config file exists: config/temp_control_config.json")
        with open(config_file, 'r') as f:
            config = json.load(f)
    elif os.path.exists(template_file):
        print("⚠️  Using TEMPLATE config (actual config not found)")
        print("   The template has example IPs that won't work with real plugs")
        with open(template_file, 'r') as f:
            config = json.load(f)
    else:
        print("❌ No config file found!")
        return None
    
    print("\n" + "="*70)
    print("CONFIGURATION STATUS")
    print("="*70)
    
    heating_plug = config.get('heating_plug', '')
    cooling_plug = config.get('cooling_plug', '')
    enable_heating = config.get('enable_heating', False)
    enable_cooling = config.get('enable_cooling', False)
    
    print(f"\n🔥 HEATING PLUG:")
    print(f"   URL/IP: {heating_plug if heating_plug else '(not configured)'}")
    print(f"   Status: {'ENABLED' if enable_heating else 'DISABLED'}")
    
    # Check if it's a localhost address (template)
    if heating_plug and (heating_plug.startswith('127.') or heating_plug == 'localhost'):
        print(f"   ⚠️  WARNING: Localhost IP detected - this won't work with real plugs!")
        print(f"       You need to configure the actual IP address of your Kasa plug")
    
    print(f"\n❄️  COOLING PLUG:")
    print(f"   URL/IP: {cooling_plug if cooling_plug else '(not configured)'}")
    print(f"   Status: {'ENABLED' if enable_cooling else 'DISABLED'}")
    
    if cooling_plug and (cooling_plug.startswith('127.') or cooling_plug == 'localhost'):
        print(f"   ⚠️  WARNING: Localhost IP detected - this won't work with real plugs!")
        print(f"       You need to configure the actual IP address of your Kasa plug")
    
    return config

def check_kasa_library():
    """Check if python-kasa is properly installed"""
    print("\n" + "="*70)
    print("KASA LIBRARY STATUS")
    print("="*70 + "\n")
    
    try:
        import kasa
        print(f"✅ python-kasa is installed (version: {kasa.__version__})")
        
        # Check if we can import the necessary classes
        try:
            from kasa.iot import IotPlug
            print(f"✅ IotPlug class available (newer API)")
        except:
            print(f"⚠️  IotPlug not available, will try SmartPlug")
            
        try:
            from kasa import SmartPlug
            print(f"✅ SmartPlug class available (legacy API)")
        except:
            print(f"❌ SmartPlug not available")
        
        return True
    except ImportError:
        print("❌ python-kasa is NOT installed!")
        print("   Install it with: pip install python-kasa")
        return False

async def scan_network():
    """Try to discover KASA devices on the network"""
    print("\n" + "="*70)
    print("NETWORK SCAN FOR KASA DEVICES")
    print("="*70 + "\n")
    
    try:
        from kasa import Discover
        print("🔍 Scanning network for Kasa devices...")
        print("   (This may take up to 30 seconds...)\n")
        
        devices = await Discover.discover(timeout=10)
        
        if devices:
            print(f"✅ Found {len(devices)} Kasa device(s):\n")
            for ip, dev in devices.items():
                await dev.update()
                print(f"   📱 Device at {ip}")
                print(f"      Model: {dev.model}")
                print(f"      Alias: {dev.alias}")
                print(f"      State: {'ON' if dev.is_on else 'OFF'}")
                print()
        else:
            print("⚠️  No Kasa devices found on the network")
            print("\nPossible reasons:")
            print("  1. Devices are not powered on")
            print("  2. Devices are on a different network/VLAN")
            print("  3. Network doesn't support UDP broadcast")
            print("  4. Firewall is blocking discovery")
            
        return devices
    except Exception as e:
        print(f"❌ Error during network scan: {e}")
        return None

def print_recommendations(config):
    """Print recommendations based on findings"""
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70 + "\n")
    
    if not config:
        print("❌ Create config/temp_control_config.json from the template")
        print("   Copy config/temp_control_config.json.template")
        return
    
    heating_plug = config.get('heating_plug', '')
    cooling_plug = config.get('cooling_plug', '')
    
    needs_config = False
    
    if heating_plug and (heating_plug.startswith('127.') or heating_plug == 'localhost'):
        needs_config = True
        print("🔧 HEATING PLUG needs configuration:")
        print("   1. Find the actual IP address of your heating Kasa plug")
        print("      (Check your router's DHCP client list)")
        print(f"   2. Update 'heating_plug' in config/temp_control_config.json")
        print(f"   3. Replace '{heating_plug}' with the real IP (e.g., '192.168.1.100')")
        print()
    
    if cooling_plug and (cooling_plug.startswith('127.') or cooling_plug == 'localhost'):
        needs_config = True
        print("🔧 COOLING PLUG needs configuration:")
        print("   1. Find the actual IP address of your cooling Kasa plug")
        print("      (Check your router's DHCP client list)")
        print(f"   2. Update 'cooling_plug' in config/temp_control_config.json")
        print(f"   3. Replace '{cooling_plug}' with the real IP (e.g., '192.168.1.101')")
        print()
    
    if not needs_config:
        print("✅ Configuration looks OK")
        print("   If plugs still don't respond:")
        print("   1. Verify the IP addresses are correct")
        print("   2. Try pinging the plug IPs")
        print("   3. Check if plugs are on the same network")
        print("   4. Ensure no firewall is blocking port 9999")

async def main():
    """Main diagnostic routine"""
    # Check configuration
    config = check_config()
    
    # Check library
    library_ok = check_kasa_library()
    
    # Scan network if library is available
    devices = None
    if library_ok:
        devices = await scan_network()
    
    # Print recommendations
    print_recommendations(config)
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70 + "\n")
    
    if not config or not library_ok:
        print("❌ Fix the issues above before testing plugs")
    elif devices:
        print("✅ Found devices! Update your config with the discovered IPs above")
        print("   Then run: python3 test_kasa_plugs.py")
    else:
        print("⚠️  No devices found. After fixing network/config issues:")
        print("   Run this diagnostic again: python3 diagnose_kasa.py")
        print("   Then test plugs: python3 test_kasa_plugs.py")
    
    print()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
