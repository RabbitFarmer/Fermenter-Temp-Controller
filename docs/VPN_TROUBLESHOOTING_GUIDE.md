# WireGuard VPN Connection Troubleshooting Guide

This guide helps you troubleshoot connection issues when accessing the Fermenter Temperature Controller through a WireGuard VPN tunnel.

## Common Issue: "Connection Refused" Error

When you see "connection refused" or "ERR_CONNECTION_REFUSED" errors while trying to access the Flask application through VPN (e.g., at `10.215.222.2:5000`), this typically means one of the following:

1. The Flask application isn't running
2. The Flask application isn't listening on the VPN interface
3. A firewall is blocking the connection
4. The VPN routing isn't configured correctly

## Quick Diagnosis Steps

### Step 1: Verify Flask Application is Running

On the Raspberry Pi, check if the Flask app is running:

```bash
# Check if Python is running the app
ps aux | grep app.py

# Or check the systemd service status
sudo systemctl status fermenter
```

**Expected Result:** You should see the Flask app running on port 5000.

If not running, start it:
```bash
# Using systemd
sudo systemctl start fermenter

# Or manually
cd /home/pi/Fermenter-Temp-Controller
python3 app.py
```

### Step 2: Verify Flask is Listening on 0.0.0.0

Check which interfaces the Flask app is bound to:

```bash
sudo netstat -tulpn | grep 5000
# Or alternatively:
sudo ss -tulpn | grep 5000
```

**Expected Result:**
```
tcp        0      0 0.0.0.0:5000            0.0.0.0:*               LISTEN      12345/python3
```

The key is `0.0.0.0:5000` - this means it's listening on ALL interfaces (including VPN).

**❌ Bad Result:**
```
tcp        0      0 127.0.0.1:5000          0.0.0.0:*               LISTEN      12345/python3
```

If you see `127.0.0.1:5000`, the app is only listening on localhost and won't accept VPN connections.

**Solution:** The `app.py` file should have `app.run(host='0.0.0.0', port=5000, debug=True)` at the bottom. This is already configured correctly in this repository.

### Step 3: Verify WireGuard VPN is Active

On the Raspberry Pi:
```bash
# Check WireGuard status
sudo wg show

# Check if the WireGuard interface is up
ip addr show wg0
```

**Expected Result:** You should see the WireGuard interface (wg0) with your VPN IP address and connected peers.

On the client (your computer/phone):
```bash
# Check WireGuard status
wg show
# Or on mobile, check the WireGuard app
```

**Expected Result:** Status should show as "Connected" or "Active" with recent handshake times.

### Step 4: Test VPN Connectivity

From your client device, test if you can reach the Raspberry Pi through the VPN:

```bash
# Ping the Raspberry Pi's VPN IP
ping 10.215.222.2

# Or if using the example from the docs:
ping 10.0.0.1
```

**Expected Result:** You should receive ping responses.

**If ping fails:**
- Check that the VPN tunnel is actually connected (see Step 3)
- Verify the IP address is correct (it should match your WireGuard server configuration)
- Check routing on both client and server

### Step 5: Check Firewall Rules

The most common cause of "connection refused" with VPN is firewall blocking the connection.

#### On Raspberry Pi - Check iptables

```bash
# View all current firewall rules
sudo iptables -L -n -v

# Check if there's a rule allowing connections from VPN interface to port 5000
sudo iptables -L INPUT -n -v | grep 5000
```

#### Add Firewall Rule to Allow VPN Access

If there's no rule allowing VPN access to port 5000, add one:

```bash
# Allow connections from WireGuard interface (wg0) to Flask port 5000
sudo iptables -I INPUT -i wg0 -p tcp --dport 5000 -j ACCEPT

# Save the rule (Debian/Ubuntu/Raspberry Pi OS)
sudo iptables-save | sudo tee /etc/iptables/rules.v4

# Alternative for systems using netfilter-persistent:
sudo netfilter-persistent save
```

**Note:** The `-I INPUT` inserts the rule at the beginning of the INPUT chain, ensuring it's evaluated before any DROP rules.

#### Alternative: Allow All Traffic from VPN Interface

For a more permissive approach (suitable for private VPN):

```bash
# Allow all traffic from the WireGuard interface
sudo iptables -I INPUT -i wg0 -j ACCEPT

# Save the rule
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

### Step 6: Test Port Connectivity

From your client device, test if port 5000 is reachable:

```bash
# Using netcat (if available)
nc -zv 10.215.222.2 5000

# Using telnet
telnet 10.215.222.2 5000

# Using curl
curl http://10.215.222.2:5000
```

**Expected Result with netcat:**
```
Connection to 10.215.222.2 5000 port [tcp/*] succeeded!
```

**Expected Result with curl:** You should see HTML content from the Flask app.

**If connection is refused:**
- Go back to Step 5 and verify firewall rules
- Verify Flask is running (Step 1)
- Verify Flask is listening on 0.0.0.0 (Step 2)

### Step 7: Check Browser Access

Once the above steps work, try accessing from your browser:

```
http://10.215.222.2:5000
```

Or with your specific VPN IP address.

**Note:** Use `http://` not `https://` - the Flask app doesn't use SSL by default.

## Complete Verification Script

Save this as `verify_vpn_access.sh` on your Raspberry Pi:

```bash
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
if sudo wg show | grep -q "interface: wg0"; then
    echo "   ✅ WireGuard interface wg0 is active"
    WG_IP=$(ip addr show wg0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
    if [ -n "$WG_IP" ]; then
        echo "   📍 VPN IP address: $WG_IP"
    fi
else
    echo "   ❌ WireGuard interface wg0 is NOT active"
    echo "   Start it with: sudo wg-quick up wg0"
fi
echo ""

# Check firewall rules for VPN access
echo "4. Checking firewall rules for VPN access to port 5000..."
if sudo iptables -L INPUT -n | grep -q "wg0.*5000"; then
    echo "   ✅ Firewall rule exists for wg0 -> port 5000"
elif sudo iptables -L INPUT -n | grep -q "wg0.*ACCEPT"; then
    echo "   ✅ Firewall allows all traffic from wg0"
else
    echo "   ❌ No firewall rule found allowing VPN access to port 5000"
    echo "   Add one with: sudo iptables -I INPUT -i wg0 -p tcp --dport 5000 -j ACCEPT"
fi
echo ""

# Check for any DROP rules that might block VPN
echo "5. Checking for blocking firewall rules..."
if sudo iptables -L INPUT -n | grep -q "DROP.*wg0"; then
    echo "   ⚠️  WARNING: Found DROP rules for wg0"
    sudo iptables -L INPUT -n | grep "DROP.*wg0"
else
    echo "   ✅ No explicit DROP rules for wg0 interface"
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
echo "Test from client with:"
echo "  ping $WG_IP"
echo "  curl http://$WG_IP:5000"
echo "  Or open browser to: http://$WG_IP:5000"
echo ""
