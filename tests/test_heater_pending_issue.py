#!/usr/bin/env python3
"""
Test to reproduce the issue where heater_pending gets stuck, 
blocking all future heating commands.
"""

import time

def test_heater_pending_stuck():
    """
    Simulate a scenario where kasa_worker is slow/unresponsive,
    causing heater_pending to stay True and block future commands.
    """
    print("=" * 80)
    print("HEATER_PENDING STUCK TEST")
    print("=" * 80)
    
    low = 73.0
    high = 75.0
    enable_heat = True
    
    print(f"\nConfiguration:")
    print(f"  Low Limit: {low}°F")
    print(f"  High Limit: {high}°F")
    print(f"  Heating Enabled: {enable_heat}")
    
    print(f"\n" + "-" * 80)
    print("Simulating slow/unresponsive kasa_worker:")
    print("-" * 80)
    
    # Simulate the scenario from the issue
    temps = [80.0, 73.0, 72.0, 73.0, 72.0, 73.0]
    
    # Mock state
    heater_on = False
    heater_pending = False
    last_command_time = {}
    RATE_LIMIT_SECONDS = 10
    
    def _should_send_kasa_command(url, action):
        nonlocal heater_on, heater_pending, last_command_time
        
        # Reproduce logic from app.py _should_send_kasa_command
        if not url:
            return False
        
        # Check pending
        if heater_pending:
            print(f"      BLOCKED: heater_pending is True")
            return False
        
        # Check redundancy
        if heater_on and action == "on":
            print(f"      BLOCKED: heater already ON (redundant)")
            return False
        if (not heater_on) and action == "off":
            print(f"      BLOCKED: heater already OFF (redundant)")
            return False
        
        # Check rate limit
        last = last_command_time.get(url)
        if last and last.get("action") == action:
            if (time.time() - last.get("ts", 0.0)) < RATE_LIMIT_SECONDS:
                print(f"      BLOCKED: rate limited (last command {time.time() - last.get('ts', 0.0):.1f}s ago)")
                return False
        
        return True
    
    def control_heating(action, iteration):
        nonlocal heater_on, heater_pending, last_command_time
        
        url = "192.168.1.10"
        
        if not _should_send_kasa_command(url, action):
            return
        
        print(f"      ✓ COMMAND SENT: Turn heating {action.upper()}")
        heater_pending = True
        last_command_time[url] = {"action": action, "ts": time.time()}
        
        # Simulate kasa_worker response
        # NORMAL: Response comes quickly
        # BUG: Response never comes or comes very late
        
        # For this test, simulate that response NEVER comes on iteration 1
        if iteration == 1:
            print(f"      ⚠ kasa_worker HUNG - no response received!")
            print(f"      heater_pending stays True indefinitely...")
        else:
            # Simulate normal response
            print(f"      (simulating kasa_worker response)")
            heater_pending = False
            heater_on = (action == "on")
            print(f"      heater_on = {heater_on}, heater_pending = {heater_pending}")
    
    for i, temp in enumerate(temps):
        print(f"\n[Iteration {i}] Temp: {temp:5.1f}°F")
        
        # Reproduce heating control logic from app.py
        if enable_heat:
            if temp <= low:
                print(f"    Logic: temp <= low_limit → call control_heating('on')")
                control_heating("on", i)
            elif high is not None and temp >= high:
                print(f"    Logic: temp >= high_limit → call control_heating('off')")
                control_heating("off", i)
            else:
                print(f"    Logic: temp in range → maintain state")
        
        print(f"    State: heater_on={heater_on}, heater_pending={heater_pending}")
        
        # Small delay for rate limiting to be observable
        time.sleep(0.1)
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    print("\nWhat happened:")
    print("  1. At iteration 1 (temp=73°F), heating ON command sent")
    print("  2. kasa_worker hung - no response received")
    print("  3. heater_pending stayed True")
    print("  4. At iterations 2-5, all heating commands BLOCKED by heater_pending")
    print("  5. Plug never turned on because command was blocked!")
    
    print("\nRoot cause:")
    print("  heater_pending flag prevents commands when kasa_worker is unresponsive")
    
    print("\nPossible solutions:")
    print("  1. Add timeout to heater_pending (reset after X seconds)")
    print("  2. Remove heater_pending check from _should_send_kasa_command")
    print("  3. Improve kasa_worker reliability/timeout handling")
    
    if heater_pending:
        print("\n✗ BUG CONFIRMED: heater_pending is stuck True, blocking all commands")
        return False
    else:
        print("\n✓ heater_pending cleared normally")
        return True

if __name__ == '__main__':
    success = test_heater_pending_stuck()
    exit(0 if success else 1)
