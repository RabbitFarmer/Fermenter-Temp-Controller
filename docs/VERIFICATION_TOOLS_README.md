# KASA Plug Connection Verification Tools

This directory contains tools to verify that your Fermenter Temperature Controller can connect to your KASA smart plugs.

## Quick Answer

**Q: Can you confirm the plugs and program are connecting?**

**A: I cannot test from this GitHub environment, but I've created tools for YOU to verify on your device.**

## Your Setup

Based on your confirmations:
- **Heating Plug**: 192.168.1.208
- **Cooling Plug**: 192.168.1.194
- **Router Status**: Both plugs online ✅
- **Network**: 192.168.1.x subnet

## Verification Tools

### 1. `verify_user_plugs.py` (Recommended)
Full KASA protocol test - requires python-kasa installed.

```bash
python3 verify_user_plugs.py
```

**What it tests:**
- TCP connection to each IP
- KASA protocol communication
- Device information retrieval
- Current state (on/off)

**What you'll see if it works:**
```
✅ SUCCESS: Connected to device at 192.168.1.208
📋 Device Information:
   Name/Alias: Heating Plug
   Model: HS100(US)
   Current State: OFF
```

### 2. `test_network_connectivity.py` (Basic Test)
Network connectivity test - no dependencies needed.

```bash
python3 test_network_connectivity.py
```

**What it tests:**
- TCP port 9999 reachability
- Basic network connectivity

**What you'll see if it works:**
```
✅ SUCCESS: Port 9999 is open and accepting connections
   This indicates a KASA plug is likely listening at 192.168.1.208
```

### 3. `test_kasa_plugs.py` (Existing Tool)
Tests using configuration file.

```bash
python3 test_kasa_plugs.py
```

**What it does:**
- Loads IPs from `config/temp_control_config.json`
- Sends ON/OFF commands
- Verifies state changes

### 4. Web UI Test Button
From the Temperature Control Settings page:

1. Enter IPs in form fields
2. Click "KASA Test" button
3. See results immediately

## Expected Results

### ✅ Success (Connection Works)
```
✅ SUCCESS: Both KASA plugs are reachable and responding!
   The program CAN connect to your plugs at these IP addresses.
```

**This means:**
- The program WILL be able to control your plugs
- Temperature control WILL work
- You're all set! ✓

### ❌ Failure (Connection Doesn't Work)
```
❌ FAILED: Cannot connect to port 9999
```

**This means:**
- The program CANNOT control the plugs
- Need to troubleshoot (see guide below)

## Troubleshooting

If tests fail, check:

1. **IP Addresses**
   - Verify in router's DHCP client list
   - Or check in Kasa mobile app
   - Make sure you're using 192.168.1.208 and 192.168.1.194

2. **Network Connectivity**
   ```bash
   ping 192.168.1.208
   ping 192.168.1.194
   ```
   Both should respond

3. **Same Network**
   - Computer and plugs must be on same subnet
   - Both should be 192.168.1.x
   - Check with `ifconfig` or `ip addr`

4. **Port 9999**
   - KASA plugs use TCP port 9999
   - Check firewall isn't blocking it
   ```bash
   nc -zv 192.168.1.208 9999
   nc -zv 192.168.1.194 9999
   ```

5. **Plug Status**
   - Verify plugs are powered on
   - Check WiFi connection in Kasa app
   - Try restarting plugs if needed

## Configuration

Ensure `config/temp_control_config.json` contains:

```json
{
  "heating_plug": "192.168.1.208",
  "cooling_plug": "192.168.1.194",
  "enable_heating": true,
  "enable_cooling": true
}
```

## Running on Your Device

**IMPORTANT:** These tools must be run on the same computer/Raspberry Pi that will run the temperature controller, not from GitHub Actions or a remote system.

### On Raspberry Pi:
```bash
cd /path/to/Fermenter-Temp-Controller
python3 verify_user_plugs.py
```

### On Windows:
```bash
cd C:\path\to\Fermenter-Temp-Controller
python verify_user_plugs.py
```

### On macOS/Linux:
```bash
cd ~/Fermenter-Temp-Controller
python3 verify_user_plugs.py
```

## What Each File Does

| File | Purpose | Dependencies |
|------|---------|--------------|
| `verify_user_plugs.py` | Full KASA test with device info | python-kasa |
| `test_network_connectivity.py` | Basic TCP connectivity | None |
| `test_kasa_plugs.py` | Config-based full test | python-kasa |
| `diagnose_kasa.py` | Diagnostic tool with recommendations | python-kasa |
| `CONNECTION_VERIFICATION_GUIDE.md` | Detailed guide | N/A |

## Still Having Issues?

See `CONNECTION_VERIFICATION_GUIDE.md` for detailed troubleshooting steps and common solutions.

## Bottom Line

**To answer your question definitively:**

1. Run `python3 verify_user_plugs.py` on your device
2. If you see ✅ SUCCESS → Program CAN connect
3. If you see ❌ FAILED → Program CANNOT connect (yet)

The code is correct. If the verification succeeds on your device, the temperature controller will work!
