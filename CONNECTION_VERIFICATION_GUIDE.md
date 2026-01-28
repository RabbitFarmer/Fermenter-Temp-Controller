================================================================================
KASA PLUG CONNECTION VERIFICATION GUIDE
================================================================================

USER'S CONFIRMED INFORMATION:
  - Heating Plug IP: 192.168.1.208
  - Cooling Plug IP: 192.168.1.194
  - Router Status: Both plugs are online and working
  - Network: Plugs are on 192.168.1.x subnet

================================================================================
IMPORTANT: ABOUT THE CONNECTION TEST
================================================================================

The automated test in this repository runs in a GitHub Actions environment and
CANNOT actually connect to your local network devices. This is expected and
normal - it doesn't mean your setup won't work!

Your actual computer/Raspberry Pi running the Fermenter Temperature Controller
should be able to connect to the plugs since they're on the same network.

================================================================================
HOW TO VERIFY THE CONNECTION YOURSELF
================================================================================

Option 1: Use the Test Scripts (On Your Device)
------------------------------------------------
Run these scripts on the computer/Raspberry Pi running the app:

1. Basic network test:
   python3 test_network_connectivity.py

2. Full KASA test (requires python-kasa installed):
   python3 verify_user_plugs.py

Option 2: Use the Web UI Test Button
-------------------------------------
1. Start the Flask app: python3 app.py
2. Navigate to the Temperature Control Settings page
3. Enter your IP addresses:
   - Heating Plug: 192.168.1.208
   - Cooling Plug: 192.168.1.194
4. Click the "KASA Test" button
5. The page will show if connections succeed or fail

Option 3: Command Line Tests
-----------------------------
From your computer/Raspberry Pi:

1. Test network connectivity:
   ping 192.168.1.208
   ping 192.168.1.194

2. Test if port 9999 is open:
   nc -zv 192.168.1.208 9999
   nc -zv 192.168.1.194 9999

Option 4: Use Existing Test Script
-----------------------------------
   python3 test_kasa_plugs.py

   This will load IPs from config/temp_control_config.json

================================================================================
CONFIGURATION
================================================================================

Make sure your config/temp_control_config.json has the correct IPs:

{
  "heating_plug": "192.168.1.208",
  "cooling_plug": "192.168.1.194",
  "enable_heating": true,
  "enable_cooling": true,
  ...
}

================================================================================
EXPECTED BEHAVIOR
================================================================================

IF CONNECTION SUCCEEDS:
✅ You'll see: "SUCCESS: plug responded and confirmed state"
✅ The program CAN control your KASA plugs
✅ Temperature control will work automatically

IF CONNECTION FAILS:
❌ You'll see error messages
❌ The program CANNOT control the plugs
❌ Need to troubleshoot:
   - Verify IPs are correct (check router/Kasa app)
   - Ensure plugs are on WiFi and powered
   - Check computer and plugs are on same network
   - Verify no firewall blocking port 9999

================================================================================
TROUBLESHOOTING COMMON ISSUES
================================================================================

Issue: "Connection refused" or "Errno 111"
Solution: Plug exists but not responding on port 9999
  - Verify it's actually a KASA smart plug
  - Restart the plug
  - Check firmware is up to date

Issue: "Connection timeout"
Solution: Device not responding
  - Verify IP address is correct
  - Check plug is powered on and WiFi connected
  - Use Kasa mobile app to verify plug status

Issue: "No route to host" or "Errno 113"
Solution: Network routing problem
  - Ensure computer and plugs are on same subnet
  - Check if 192.168.1.x is the correct subnet for both
  - Verify network gateway/router configuration

Issue: Different subnet (e.g., computer on 192.168.0.x, plugs on 192.168.1.x)
Solution: Cannot connect across subnets without routing
  - Put computer and plugs on same subnet
  - Or configure router to allow cross-subnet traffic
  - Or change plug network to match computer

================================================================================
CONFIRMATION CHECKLIST
================================================================================

To confirm the program can connect:

[ ] 1. Config file has correct IPs: 192.168.1.208 and 192.168.1.194
[ ] 2. Python-kasa is installed: pip list | grep kasa
[ ] 3. Plugs show as online in router's device list
[ ] 4. Plugs show as online in Kasa mobile app
[ ] 5. Can ping both IPs from the computer running the app
[ ] 6. Port 9999 is reachable (nc -zv or telnet test)
[ ] 7. test_kasa_plugs.py runs successfully
[ ] 8. Web UI "KASA Test" button shows success

If ALL items are checked, the program WILL connect to your plugs!

================================================================================
ANSWER TO YOUR QUESTION
================================================================================

"Can you confirm that the plugs and this program are connecting now?"

ANSWER: I cannot directly test the connection from this environment because
I'm running in a GitHub sandbox that's not on your local network.

HOWEVER: Based on the code and your configuration:
- ✅ The code is correct and should work
- ✅ Your IPs are valid network addresses (192.168.1.208, 192.168.1.194)
- ✅ The router confirms plugs are online
- ⚠️  YOU must run the test on your actual device to confirm

NEXT STEP: Run one of the verification methods above on the computer/Raspberry
Pi that will actually run the temperature controller. That will give you a
definitive YES or NO answer.

================================================================================
