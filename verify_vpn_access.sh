#!/bin/bash

echo "=========================================="
echo "VPN Access Verification for Flask App"
echo "=========================================="
echo ""

# Check if Flask is running
echo "1. Checking if Flask app is running..."
if ps aux | grep -q "[a]pp.py"; then
    echo "   ✅ Flask app is running"
else
    echo "   ❌ Flask app is NOT running"
    echo "   Start it with: python3 app.py"
fi
echo ""

# Check what Flask is listening on
echo "2. Checking Flask listening address..."
FLASK_LISTEN=$(sudo netstat -tulpn 2>/dev/null | grep 5000 | head -1)
if echo "$FLASK_LISTEN" | grep -q "0.0.0.0:5000"; then
    echo "   ✅ Flask is listening on 0.0.0.0:5000 (all interfaces)"
elif echo "$FLASK_LISTEN" | grep -q "127.0.0.1:5000"; then
    echo "   ❌ Flask is listening on 127.0.0.1:5000 (localhost only)"
    echo "   VPN clients cannot connect! Check app.py configuration."
elif [ -z "$FLASK_LISTEN" ]; then
    echo "   ❌ Nothing is listening on port 5000"
else
    echo "   ⚠️  Flask listening status: $FLASK_LISTEN"
fi
echo ""

# Check WireGuard status
echo "3. Checking WireGuard VPN status..."
if sudo wg show 2>/dev/null | grep -q "interface: wg0"; then
    echo "   ✅ WireGuard interface wg0 is active"
    WG_IP=$(ip addr show wg0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
    if [ -n "$WG_IP" ]; then
        echo "   📍 VPN IP address: $WG_IP"
    fi
    
    # Show connected peers
    PEER_COUNT=$(sudo wg show wg0 peers 2>/dev/null | wc -l)
    if [ "$PEER_COUNT" -gt 0 ]; then
        echo "   👥 Connected peers: $PEER_COUNT"
    else
        echo "   ⚠️  No peers currently connected"
    fi
else
    echo "   ❌ WireGuard interface wg0 is NOT active"
    echo "   Start it with: sudo wg-quick up wg0"
fi
echo ""

# Check firewall rules for VPN access
echo "4. Checking firewall rules for VPN access to port 5000..."
if sudo iptables -L INPUT -n 2>/dev/null | grep -q "wg0.*5000"; then
    echo "   ✅ Firewall rule exists for wg0 -> port 5000"
elif sudo iptables -L INPUT -n 2>/dev/null | grep -q "wg0.*ACCEPT"; then
    echo "   ✅ Firewall allows all traffic from wg0"
else
    echo "   ❌ No firewall rule found allowing VPN access to port 5000"
    echo "   Add one with: sudo iptables -I INPUT -i wg0 -p tcp --dport 5000 -j ACCEPT"
    echo "   Then save it: sudo iptables-save | sudo tee /etc/iptables/rules.v4"
fi
echo ""

# Check for any DROP rules that might block VPN
echo "5. Checking for blocking firewall rules..."
if sudo iptables -L INPUT -n 2>/dev/null | grep -q "DROP.*wg0"; then
    echo "   ⚠️  WARNING: Found DROP rules for wg0"
    sudo iptables -L INPUT -n 2>/dev/null | grep "DROP.*wg0"
else
    echo "   ✅ No explicit DROP rules for wg0 interface"
fi
echo ""

# Test local connectivity
echo "6. Testing local connectivity to Flask app..."
if command -v curl &> /dev/null; then
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000 | grep -q "200\|302"; then
        echo "   ✅ Flask app responds to local requests"
    else
        echo "   ❌ Flask app not responding to local requests"
    fi
else
    echo "   ⚠️  curl not installed, skipping local connectivity test"
fi
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "For VPN access to work, you need:"
echo "  ✓ Flask app running on 0.0.0.0:5000"
echo "  ✓ WireGuard VPN active (wg0 interface up)"
echo "  ✓ Firewall allowing wg0 → port 5000"
echo "  ✓ Client connected to VPN"
echo ""

if [ -n "$WG_IP" ]; then
    echo "Test from VPN client with:"
    echo "  ping $WG_IP"
    echo "  curl http://$WG_IP:5000"
    echo "  Or open browser to: http://$WG_IP:5000"
else
    echo "Test from VPN client with:"
    echo "  ping <YOUR_VPN_IP>"
    echo "  curl http://<YOUR_VPN_IP>:5000"
    echo "  Or open browser to: http://<YOUR_VPN_IP>:5000"
fi
echo ""
