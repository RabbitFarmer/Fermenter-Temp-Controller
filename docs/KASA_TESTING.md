# KASA Plug Testing Guide

This directory contains tools to test and diagnose KASA smart plug connectivity issues.

## Quick Start

### Step 1: Diagnose Current Status
```bash
python3 diagnose_kasa.py
```

This will:
- Check if python-kasa library is installed
- Show your current configuration
- Scan network for KASA devices (if permissions allow)
- Provide specific recommendations

### Step 2: Configure Your Plugs

Edit `config/temp_control_config.json` and set the actual IP addresses:

```json
{
  "heating_plug": "192.168.1.100",  // Replace with your heating plug IP
  "cooling_plug": "192.168.1.101",  // Replace with your cooling plug IP
  "enable_heating": true,
  "enable_cooling": true
}
```

**How to find your plug IPs:**
1. Check your router's DHCP client list
2. Use the Kasa mobile app
3. Run the diagnostic tool (it will scan the network if permissions allow)

### Step 3: Test the Plugs
```bash
python3 test_kasa_plugs.py
```

This will:
- Send ON command to each enabled plug
- Verify the plug responds and confirms state
- Send OFF command to return to original state
- Show detailed results

## Troubleshooting

### "Operation not permitted" during network scan
This is normal in restricted environments. You'll need to manually configure the IP addresses.

### "Failed to contact plug"
Common causes:
1. **Wrong IP address** - Verify the IP in your config matches the actual plug
2. **Network connectivity** - Try pinging the IP: `ping 192.168.1.100`
3. **Different network/VLAN** - Ensure the server and plugs are on the same network
4. **Firewall blocking** - KASA plugs use port 9999, ensure it's not blocked
5. **Plug offline** - Check if the plug is powered on and connected to WiFi

### "No module named 'kasa'"
Install python-kasa:
```bash
pip install python-kasa
```

### Plugs work but notifications are still spamming
The fix in this PR adds notification deduplication. Make sure:
1. You're running the updated code (after the PR is merged)
2. The heating_error_notified and cooling_error_notified flags are being reset when plugs recover
3. Check the logs for "[LOG] Notification ... already sent (deduplication working)"

## Files

- **diagnose_kasa.py** - Diagnostic tool to check configuration and scan for devices
- **test_kasa_plugs.py** - Test script to verify plugs are responding
- **test_kasa_notification_fix.py** - Unit tests for notification deduplication fix

## Example Output

### Successful Test
```
╔====================================================================╗
║                    KASA PLUG CONNECTION TEST                       ║
╚====================================================================╝

📋 Configuration:
   Heating plug: 192.168.1.100 (ENABLED)
   Cooling plug: 192.168.1.101 (ENABLED)

======================================================================
Testing HEATING plug at 192.168.1.100
======================================================================
📡 Sending 'on' command to 192.168.1.100...
✅ SUCCESS: heating plug responded and confirmed 'on' state

======================================================================
Testing COOLING plug at 192.168.1.101
======================================================================
📡 Sending 'on' command to 192.168.1.101...
✅ SUCCESS: cooling plug responded and confirmed 'on' state

======================================================================
SUMMARY
======================================================================
✅ PASS: Heating ON
✅ PASS: Heating OFF
✅ PASS: Cooling ON
✅ PASS: Cooling OFF
======================================================================

🎉 ALL TESTS PASSED! Both plugs are responding correctly.
```

### Failed Test
```
❌ FAIL: Heating ON
         Error: Failed to contact plug at 192.168.1.100: [Errno 113] No route to host
         
⚠️  SOME TESTS FAILED. Check errors above.
```

## Integration with Main App

Once your plugs are tested and working:
1. The main app (`app.py`) will use these same IP addresses
2. Temperature control will automatically manage the plugs
3. You'll only receive ONE notification per failure period (not spam)
4. Notifications reset when plugs recover

## Technical Details

The KASA worker process runs in a separate subprocess and communicates via queues:
- `kasa_queue` - Commands from main app to worker
- `kasa_result_queue` - Results from worker back to main app

The worker uses the `kasa_control()` function which:
1. Creates a plug connection at the specified IP
2. Sends the command (on/off)
3. Verifies the state change
4. Returns success or error message
