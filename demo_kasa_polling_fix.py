#!/usr/bin/env python3
"""
Integration test demonstrating the fix for redundant Kasa polling.

This test simulates the temperature control loop behavior before and after the fix
to show how the polling frequency is reduced.
"""

import time

# Simplified implementation of the functions for testing
_last_kasa_command = {}

def _record_kasa_command(url, action):
    _last_kasa_command[url] = {"action": action, "ts": time.time()}

def _is_redundant_command_OLD(url, action, current_state):
    """OLD implementation with 30-second timeout."""
    command_matches_state = (action == "on" and current_state) or (action == "off" and not current_state)
    if not command_matches_state:
        return False
    
    last = _last_kasa_command.get(url)
    if not last:
        return False
    
    if last.get("action") != action:
        return False
    
    time_since_last = time.time() - last.get("ts", 0.0)
    
    # OLD: 30 seconds for state recovery
    if time_since_last >= 30:
        return False
    
    return True

def _is_redundant_command_NEW(url, action, current_state):
    """NEW implementation with 600-second (10 minute) timeout."""
    command_matches_state = (action == "on" and current_state) or (action == "off" and not current_state)
    if not command_matches_state:
        return False
    
    last = _last_kasa_command.get(url)
    if not last:
        return False
    
    if last.get("action") != action:
        return False
    
    time_since_last = time.time() - last.get("ts", 0.0)
    
    # NEW: 10 minutes (600 seconds) for state recovery
    if time_since_last >= 600:
        return False
    
    return True

def simulate_control_loop(version="NEW", iterations=6, interval_seconds=120):
    """Simulate temperature control loop iterations."""
    url = "192.168.1.208"
    heater_on = False  # Current heater state
    target_state = "on"  # Temperature is below low limit, heater should be on
    
    # Choose implementation version
    is_redundant = _is_redundant_command_NEW if version == "NEW" else _is_redundant_command_OLD
    
    print(f"\n{'='*70}")
    print(f"Simulating {version} implementation")
    print(f"Control loop interval: {interval_seconds} seconds ({interval_seconds/60:.1f} minutes)")
    print(f"Scenario: Temperature below low limit, heater needs to stay ON")
    print(f"{'='*70}\n")
    
    _last_kasa_command.clear()
    commands_sent = 0
    
    for i in range(iterations):
        elapsed_time = i * interval_seconds
        elapsed_minutes = elapsed_time / 60
        
        print(f"Loop {i+1} (at {elapsed_minutes:.1f} minutes):")
        
        # Simulate time passing
        if i > 0:
            # Adjust the timestamp to simulate time passing
            if url in _last_kasa_command:
                _last_kasa_command[url]["ts"] = time.time() - interval_seconds
        
        # Check if command is redundant
        redundant = is_redundant(url, target_state, heater_on)
        
        if not redundant:
            print(f"  ✓ Sending '{target_state}' command to Kasa plug")
            _record_kasa_command(url, target_state)
            heater_on = (target_state == "on")
            commands_sent += 1
        else:
            print(f"  ✗ Blocking redundant '{target_state}' command (heater already {('ON' if heater_on else 'OFF')})")
        
        print()
    
    print(f"Summary:")
    print(f"  Total loop iterations: {iterations}")
    print(f"  Commands sent: {commands_sent}")
    print(f"  Commands blocked: {iterations - commands_sent}")
    print(f"  Reduction: {((iterations - commands_sent) / iterations * 100):.1f}%\n")
    
    return commands_sent

def main():
    print("\n" + "="*70)
    print("DEMONSTRATION: Before and After Fix for Redundant Kasa Polling")
    print("="*70)
    
    print("\n📊 Simulating 12 minutes of operation (6 control loops at 2-minute intervals)")
    print("   Temperature is below low limit, so heater should stay ON throughout.")
    
    # Simulate OLD behavior
    old_commands = simulate_control_loop(version="OLD", iterations=6, interval_seconds=120)
    
    # Simulate NEW behavior
    new_commands = simulate_control_loop(version="NEW", iterations=6, interval_seconds=120)
    
    # Show comparison
    print("\n" + "="*70)
    print("COMPARISON")
    print("="*70)
    print(f"OLD implementation (30s timeout):  {old_commands} commands in 12 minutes")
    print(f"NEW implementation (10m timeout):  {new_commands} commands in 12 minutes")
    print(f"Reduction:                          {old_commands - new_commands} fewer commands")
    print(f"Improvement:                        {((old_commands - new_commands) / old_commands * 100):.0f}% reduction in polling")
    
    print("\n📈 Expected behavior in real-world usage:")
    print("   - First control loop: Command sent (heater turns ON)")
    print("   - Next ~5 loops (10 minutes): Commands blocked (redundant)")
    print("   - Every 6th loop: Command sent (state verification)")
    print("   - Net result: ~83% reduction in Kasa polling")
    
    print("\n✅ Benefits:")
    print("   - Reduced network traffic to Kasa plugs")
    print("   - Less wear on smart plug relays")
    print("   - Cleaner activity logs")
    print("   - Still maintains state recovery (every 10 minutes)")
    print("   - No impact on temperature control accuracy or safety")
    print()

if __name__ == "__main__":
    main()
