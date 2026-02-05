#!/usr/bin/env python3
"""
Test to identify the redundancy checking issue that prevents heating from turning off.
"""
import time

def test_redundancy_logic():
    """Test the _is_redundant_command and _should_send_kasa_command logic"""
    
    # Mock configuration
    temp_cfg = {
        "heating_plug": "http://192.168.1.100",
        "enable_heating": True,
        "heater_on": True,  # Heater is currently ON
        "heater_pending": False,
        "heater_pending_action": None,
        "heater_pending_since": None,
    }
    
    _last_kasa_command = {}
    _KASA_RATE_LIMIT_SECONDS = 10
    _KASA_PENDING_TIMEOUT_SECONDS = 30
    
    def _is_redundant_command(url, action, current_state):
        """
        Check if sending this command would be redundant based on current state.
        
        Returns True if command is redundant (should be skipped).
        """
        # If trying to send ON when already ON (or OFF when already OFF), it's redundant
        command_matches_state = (action == "on" and current_state) or (action == "off" and not current_state)
        print(f"    _is_redundant_command: action={action}, current_state={current_state}, command_matches_state={command_matches_state}")
        
        if not command_matches_state:
            print(f"    → Command does NOT match state, not redundant")
            return False  # Not redundant - state needs to change
        
        # Command matches current state, but allow recovery after timeout
        last = _last_kasa_command.get(url)
        if last and last.get("action") == action:
            time_since_last = time.time() - last.get("ts", 0.0)
            if time_since_last >= _KASA_RATE_LIMIT_SECONDS:
                # Enough time has passed - allow resending for state recovery
                print(f"    → Command matches state but timeout passed, not redundant")
                return False
        
        # Command is redundant - skip it
        print(f"    → Command IS redundant, skip it")
        return True
    
    def _should_send_kasa_command(url, action):
        """Check if we should send the command"""
        print(f"  _should_send_kasa_command(url={url}, action={action})")
        
        if not url:
            print(f"  → No URL, return False")
            return False
        
        # Check for timed-out pending flags and clear them
        if url == temp_cfg.get("heating_plug") and temp_cfg.get("heater_pending"):
            pending_action = temp_cfg.get("heater_pending_action")
            pending_since = temp_cfg.get("heater_pending_since")
            
            print(f"    Heater is pending: pending_action={pending_action}, pending_since={pending_since}")
            
            # If pending action is different from requested action, allow the new command
            if pending_action != action:
                print(f"    → Pending action differs from requested action, clearing pending state")
                temp_cfg["heater_pending"] = False
                temp_cfg["heater_pending_since"] = None
                temp_cfg["heater_pending_action"] = None
            elif pending_since and (time.time() - pending_since) > _KASA_PENDING_TIMEOUT_SECONDS:
                elapsed = time.time() - pending_since
                print(f"    → Pending timeout exceeded ({elapsed:.1f}s), clearing pending state")
                temp_cfg["heater_pending"] = False
                temp_cfg["heater_pending_since"] = None
                temp_cfg["heater_pending_action"] = None
            elif temp_cfg.get("heater_pending"):
                print(f"    → Still pending, return False")
                return False
        
        # Check for redundant commands based on current state
        if url == temp_cfg.get("heating_plug"):
            heater_on = temp_cfg.get("heater_on", False)
            if _is_redundant_command(url, action, heater_on):
                print(f"  → Redundant command, return False")
                return False
        
        # Rate limiting: prevent the same command from being sent too frequently
        last = _last_kasa_command.get(url)
        if last and last.get("action") == action:
            time_since_last = time.time() - last.get("ts", 0.0)
            if time_since_last < _KASA_RATE_LIMIT_SECONDS:
                print(f"  → Rate limited (last command {time_since_last:.1f}s ago), return False")
                return False
        
        print(f"  → Should send command, return True")
        return True
    
    print("=" * 60)
    print("TEST: Heater is ON, want to turn it OFF")
    print("=" * 60)
    print(f"Initial state:")
    print(f"  heater_on: {temp_cfg['heater_on']}")
    print(f"  heater_pending: {temp_cfg['heater_pending']}")
    print()
    
    # Test 1: Try to send OFF command when heater is ON
    print("Test 1: Send OFF command (heater is currently ON)")
    result = _should_send_kasa_command(temp_cfg['heating_plug'], "off")
    print(f"Result: {result}")
    assert result == True, "Should allow OFF command when heater is ON"
    print("✓ Test 1 passed\n")
    
    # Simulate command being sent
    print("Simulating command sent, setting pending flag...")
    temp_cfg["heater_pending"] = True
    temp_cfg["heater_pending_action"] = "off"
    temp_cfg["heater_pending_since"] = time.time()
    _last_kasa_command[temp_cfg['heating_plug']] = {"action": "off", "ts": time.time()}
    print(f"  heater_pending: {temp_cfg['heater_pending']}")
    print(f"  heater_pending_action: {temp_cfg['heater_pending_action']}")
    print()
    
    # Test 2: Try to send OFF command again while still pending
    print("Test 2: Try to send OFF command again (same command still pending)")
    result = _should_send_kasa_command(temp_cfg['heating_plug'], "off")
    print(f"Result: {result}")
    assert result == False, "Should NOT send duplicate OFF command while pending"
    print("✓ Test 2 passed\n")
    
    # Test 3: Simulate command failure (heater_on not updated, pending cleared)
    print("Test 3: Simulate command FAILURE (pending cleared, heater_on still True)")
    temp_cfg["heater_pending"] = False
    temp_cfg["heater_pending_action"] = None
    temp_cfg["heater_pending_since"] = None
    # heater_on remains True because command failed!
    print(f"  heater_on: {temp_cfg['heater_on']} (still ON because command failed)")
    print(f"  heater_pending: {temp_cfg['heater_pending']}")
    print()
    
    # Test 4: Try to send OFF command again after failure
    print("Test 4: Try to send OFF command again after failure")
    result = _should_send_kasa_command(temp_cfg['heating_plug'], "off")
    print(f"Result: {result}")
    print()
    
    if result == False:
        print("❌ BUG FOUND!")
        print("The command is being blocked even though:")
        print("  - Heater is ON (should turn it OFF)")
        print("  - No pending command")
        print("  - Previous command failed")
        print()
        print("This is the issue! The redundancy check is blocking the retry.")
        print("The _is_redundant_command function sees:")
        print("  - action='off'")
        print("  - current_state=True (heater is ON)")
        print("  - command_matches_state = False (OFF doesn't match ON)")
        print("  - So it should return False (not redundant)")
        print()
        print("But wait... let me check the rate limiting...")
        
        # Check rate limiting
        last = _last_kasa_command.get(temp_cfg['heating_plug'])
        if last:
            time_since_last = time.time() - last.get("ts", 0.0)
            print(f"  Last command: action={last.get('action')}, time_since={time_since_last:.1f}s")
            if time_since_last < _KASA_RATE_LIMIT_SECONDS:
                print(f"  ❌ RATE LIMITING IS BLOCKING THE RETRY!")
                print(f"     Last OFF command was {time_since_last:.1f}s ago")
                print(f"     Rate limit is {_KASA_RATE_LIMIT_SECONDS}s")
                print()
                print("  ROOT CAUSE: Failed commands are still recorded in _last_kasa_command,")
                print("              which triggers rate limiting and prevents retries!")
    else:
        print("✓ Test 4 passed - command would be allowed")
        print("  The bug is NOT in the retry logic")

if __name__ == "__main__":
    test_redundancy_logic()
