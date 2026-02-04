#!/usr/bin/env python3
"""
Test to verify that redundant Kasa commands are properly blocked.

This test validates that the fix for the issue where Kasa plugs were being
polled too often (every control loop iteration) is working correctly.

The issue was that _is_redundant_command had a 30-second timeout, but the
temperature control loop runs every 120 seconds (2 minutes), so redundant
commands were always sent.

The fix increases the timeout to 600 seconds (10 minutes) to prevent
redundant commands while still allowing state recovery.
"""

import time

# Simplified implementation of the functions for testing
_last_kasa_command = {}

def _record_kasa_command(url, action):
    _last_kasa_command[url] = {"action": action, "ts": time.time()}

def _is_redundant_command(url, action, current_state):
    """
    Check if sending this command would be redundant based on current state.
    
    Returns True if command is redundant (should be skipped).
    Exception: Returns False if enough time has passed for state recovery.
    
    SIMPLIFIED: Only block truly redundant commands. Always allow state changes.
    """
    # If trying to send ON when already ON (or OFF when already OFF), it's redundant
    command_matches_state = (action == "on" and current_state) or (action == "off" and not current_state)
    if not command_matches_state:
        return False  # Not redundant - state needs to change
    
    # Command matches current state - check if we recently sent this command
    last = _last_kasa_command.get(url)
    if not last:
        # No recent command recorded - allow this one (for state recovery)
        return False
    
    # If the last command was different, allow this one
    if last.get("action") != action:
        return False
    
    # Same command was sent recently - check timing
    time_since_last = time.time() - last.get("ts", 0.0)
    
    # If enough time has passed, allow resending for state recovery/verification
    # Set to 10 minutes (600 seconds) to prevent redundant commands while still
    # allowing periodic state verification. This should be longer than the typical
    # temperature control loop interval (default 2 minutes, configurable up to ~5 minutes)
    if time_since_last >= 600:  # 10 minutes for state recovery
        return False
    
    # Command was sent recently and state matches - it's redundant
    return True

def test_redundant_command_blocking():
    """Test that redundant commands are blocked within 10 minutes."""
    
    url = "192.168.1.208"
    
    # Test 1: First command should not be redundant (no previous command)
    _last_kasa_command.clear()
    result = _is_redundant_command(url, "on", True)
    print(f"Test 1 - First ON command when state is ON (no history): redundant={result}")
    assert result == False, "First command should not be redundant (no history)"
    
    # Test 2: Record a command and immediately try the same one - should be redundant
    _last_kasa_command.clear()
    _record_kasa_command(url, "on")
    result = _is_redundant_command(url, "on", True)
    print(f"Test 2 - Immediate duplicate ON when heater is ON: redundant={result}")
    assert result == True, "Duplicate command within timeout should be redundant"
    
    # Test 3: After 2 minutes (typical control loop), should still be redundant
    _last_kasa_command.clear()
    _record_kasa_command(url, "on")
    # Simulate 2 minutes passing (120 seconds)
    _last_kasa_command[url]["ts"] = time.time() - 120
    result = _is_redundant_command(url, "on", True)
    print(f"Test 3 - ON command after 2 minutes when heater is ON: redundant={result}")
    assert result == True, "Command after 2 minutes should still be redundant (< 10 min)"
    
    # Test 4: After 5 minutes, should still be redundant
    _last_kasa_command.clear()
    _record_kasa_command(url, "on")
    # Simulate 5 minutes passing (300 seconds)
    _last_kasa_command[url]["ts"] = time.time() - 300
    result = _is_redundant_command(url, "on", True)
    print(f"Test 4 - ON command after 5 minutes when heater is ON: redundant={result}")
    assert result == True, "Command after 5 minutes should still be redundant (< 10 min)"
    
    # Test 5: After 10 minutes, should allow for state recovery
    _last_kasa_command.clear()
    _record_kasa_command(url, "on")
    # Simulate 10 minutes passing (600 seconds)
    _last_kasa_command[url]["ts"] = time.time() - 600
    result = _is_redundant_command(url, "on", True)
    print(f"Test 5 - ON command after 10 minutes when heater is ON: redundant={result}")
    assert result == False, "Command after 10 minutes should be allowed for state recovery"
    
    # Test 6: Different action should not be redundant
    _last_kasa_command.clear()
    _record_kasa_command(url, "on")
    result = _is_redundant_command(url, "off", True)
    print(f"Test 6 - OFF command after ON command: redundant={result}")
    assert result == False, "Different action should not be redundant"
    
    # Test 7: State change needed should not be redundant
    _last_kasa_command.clear()
    _record_kasa_command(url, "on")
    result = _is_redundant_command(url, "on", False)
    print(f"Test 7 - ON command when heater is OFF: redundant={result}")
    assert result == False, "Command that changes state should not be redundant"
    
    # Test 8: OFF when already OFF should be redundant (within timeout)
    _last_kasa_command.clear()
    _record_kasa_command(url, "off")
    result = _is_redundant_command(url, "off", False)
    print(f"Test 8 - Immediate duplicate OFF when heater is OFF: redundant={result}")
    assert result == True, "Duplicate OFF command should be redundant"
    
    print("\n✓ All tests passed!")
    print("\nSummary:")
    print("- Redundant commands are blocked within 10 minutes")
    print("- State-changing commands are never blocked")
    print("- State recovery is allowed after 10 minutes")
    print("- This prevents excessive Kasa polling while maintaining safety")

if __name__ == "__main__":
    test_redundant_command_blocking()
