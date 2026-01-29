#!/usr/bin/env python3
"""
VPN Access Verification Script for Fermenter Temperature Controller

This script verifies that the Flask application is properly configured
and accessible through a WireGuard VPN connection.

Run this on your Raspberry Pi to diagnose VPN connectivity issues.
"""

import subprocess
import socket
import sys
import os


def run_command(cmd):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", -1
    except Exception as e:
        return str(e), -1


def check_flask_running():
    """Check if Flask app is running."""
    print("\n1. Checking if Flask app is running...")
    output, code = run_command("ps aux | grep '[a]pp.py'")
    
    if output and "app.py" in output:
        print("   ✅ Flask app is running")
        return True
    else:
        print("   ❌ Flask app is NOT running")
        print("   Start it with: python3 app.py")
        print("   Or: sudo systemctl start fermenter")
        return False


def check_flask_listening():
    """Check what interface Flask is listening on."""
    print("\n2. Checking Flask listening address...")
    
    # Try netstat first, fall back to ss
    output, code = run_command("netstat -tulpn 2>/dev/null | grep 5000")
    if not output:
        output, code = run_command("ss -tulpn 2>/dev/null | grep 5000")
    
    if "0.0.0.0:5000" in output:
        print("   ✅ Flask is listening on 0.0.0.0:5000 (all interfaces)")
        return True
    elif "127.0.0.1:5000" in output:
        print("   ❌ Flask is listening on 127.0.0.1:5000 (localhost only)")
        print("   VPN clients cannot connect!")
        print("   Check app.py - it should have: app.run(host='0.0.0.0', port=5000)")
        return False
    elif not output:
        print("   ❌ Nothing is listening on port 5000")
        return False
    else:
        print(f"   ⚠️  Flask listening status unclear: {output}")
        return False


def check_wireguard_status():
    """Check WireGuard VPN status."""
    print("\n3. Checking WireGuard VPN status...")
    
    output, code = run_command("wg show wg0 2>/dev/null")
    
    if code == 0 and output:
        print("   ✅ WireGuard interface wg0 is active")
        
        # Get VPN IP address
        ip_output, _ = run_command("ip addr show wg0 2>/dev/null | grep 'inet ' | awk '{print $2}'")
        if ip_output:
            vpn_ip = ip_output.split('/')[0]
            print(f"   📍 VPN IP address: {vpn_ip}")
            
        # Count connected peers
        peers_output, _ = run_command("wg show wg0 peers 2>/dev/null | wc -l")
        if peers_output:
            peer_count = peers_output.strip()
            if int(peer_count) > 0:
                print(f"   👥 Connected peers: {peer_count}")
            else:
                print("   ⚠️  No peers currently connected")
        
        return True, vpn_ip if ip_output else None
    else:
        print("   ❌ WireGuard interface wg0 is NOT active")
        print("   Start it with: sudo wg-quick up wg0")
        print("   Enable on boot: sudo systemctl enable wg-quick@wg0")
        return False, None


def check_firewall_rules():
    """Check firewall rules for VPN access."""
    print("\n4. Checking firewall rules for VPN access to port 5000...")
    
    output, code = run_command("iptables -L INPUT -n 2>/dev/null | grep -E 'wg0.*5000|wg0.*ACCEPT'")
    
    if output and ("5000" in output or "ACCEPT" in output):
        if "5000" in output:
            print("   ✅ Firewall rule exists for wg0 -> port 5000")
        else:
            print("   ✅ Firewall allows all traffic from wg0")
        return True
    else:
        print("   ❌ No firewall rule found allowing VPN access to port 5000")
        print("   Add one with:")
        print("   sudo iptables -I INPUT -i wg0 -p tcp --dport 5000 -j ACCEPT")
        print("   sudo iptables-save | sudo tee /etc/iptables/rules.v4")
        return False


def check_blocking_rules():
    """Check for firewall rules that might block VPN."""
    print("\n5. Checking for blocking firewall rules...")
    
    output, code = run_command("iptables -L INPUT -n 2>/dev/null | grep 'DROP.*wg0'")
    
    if output:
        print("   ⚠️  WARNING: Found DROP rules for wg0")
        print(output)
        return False
    else:
        print("   ✅ No explicit DROP rules for wg0 interface")
        return True


def test_local_connectivity():
    """Test local connectivity to Flask app."""
    print("\n6. Testing local connectivity to Flask app...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 5000))
        sock.close()
        
        if result == 0:
            print("   ✅ Flask app accepts connections on port 5000")
            return True
        else:
            print("   ❌ Cannot connect to Flask app on port 5000")
            return False
    except Exception as e:
        print(f"   ❌ Error testing connectivity: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 50)
    print("VPN Access Verification for Flask App")
    print("=" * 50)
    
    # Check if running as root/sudo for some commands
    if os.geteuid() != 0:
        print("\n⚠️  Note: Some checks require sudo privileges.")
        print("   Run with: sudo python3 verify_vpn_access.py")
        print("   Continuing with limited checks...\n")
    
    results = []
    
    # Run all checks
    results.append(check_flask_running())
    results.append(check_flask_listening())
    wg_status, vpn_ip = check_wireguard_status()
    results.append(wg_status)
    results.append(check_firewall_rules())
    results.append(check_blocking_rules())
    results.append(test_local_connectivity())
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    print("\nFor VPN access to work, you need:")
    print("  ✓ Flask app running on 0.0.0.0:5000")
    print("  ✓ WireGuard VPN active (wg0 interface up)")
    print("  ✓ Firewall allowing wg0 → port 5000")
    print("  ✓ Client connected to VPN")
    
    if vpn_ip:
        print(f"\nTest from VPN client with:")
        print(f"  ping {vpn_ip}")
        print(f"  curl http://{vpn_ip}:5000")
        print(f"  Or open browser to: http://{vpn_ip}:5000")
    else:
        print("\nTest from VPN client with:")
        print("  ping <YOUR_VPN_IP>")
        print("  curl http://<YOUR_VPN_IP>:5000")
        print("  Or open browser to: http://<YOUR_VPN_IP>:5000")
    
    # Overall status
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All checks passed ({passed}/{total})")
        print("   VPN access should be working!")
        return 0
    else:
        print(f"⚠️  Some checks failed ({passed}/{total} passed)")
        print("   Fix the issues above and run this script again.")
        print("   See VPN_TROUBLESHOOTING_GUIDE.md for detailed help.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user.")
        sys.exit(1)
