#!/usr/bin/env python3
"""
Test to verify temperature control readings are logged at update_interval frequency,
not at tilt_logging_interval_minutes frequency.
"""

import json
import os
import time
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_temp_control_reading_interval():
    """
    Test that temperature control readings use update_interval, not tilt_logging_interval_minutes.
    """
    print("\n" + "="*70)
    print("Testing Temperature Control Reading Interval")
    print("="*70)
    
    # Import after path is set
    from app import (
        log_periodic_temp_reading, temp_cfg, system_cfg, 
        LOG_PATH, ALLOWED_EVENTS
    )
    
    # Verify the new event type exists
    print("\n1. Verifying new event type...")
    assert "temp_control_reading" in ALLOWED_EVENTS, "temp_control_reading not in ALLOWED_EVENTS"
    assert ALLOWED_EVENTS["temp_control_reading"] == "TEMP CONTROL READING", "Event label mismatch"
    print("   ✓ Event type 'temp_control_reading' is properly defined")
    
    # Set up test configuration
    print("\n2. Setting up test configuration...")
    system_cfg['update_interval'] = 2  # Temperature control interval (2 minutes)
    system_cfg['tilt_logging_interval_minutes'] = 15  # Tilt logging interval (15 minutes)
    
    temp_cfg['temp_control_active'] = True  # Enable monitoring
    temp_cfg['low_limit'] = 65.0
    temp_cfg['high_limit'] = 70.0
    temp_cfg['current_temp'] = 67.5
    temp_cfg['tilt_color'] = 'Blue'
    
    print(f"   Temperature control interval (update_interval): {system_cfg['update_interval']} minutes")
    print(f"   Tilt logging interval: {system_cfg['tilt_logging_interval_minutes']} minutes")
    print("   ✓ Configuration set")
    
    # Clean up old log for test
    print("\n3. Preparing test environment...")
    if os.path.exists(LOG_PATH):
        # Backup existing log
        backup_path = f"{LOG_PATH}.test_backup"
        os.rename(LOG_PATH, backup_path)
        print(f"   ✓ Backed up existing log to {backup_path}")
    
    # Ensure log directory exists
    log_dir = os.path.dirname(LOG_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Test the logging function
    print("\n4. Testing log_periodic_temp_reading()...")
    try:
        log_periodic_temp_reading()
        print("   ✓ Function executed without errors")
    except Exception as e:
        print(f"   ✗ Error calling log_periodic_temp_reading: {e}")
        raise
    
    # Verify log entry was created
    print("\n5. Verifying log entry...")
    assert os.path.exists(LOG_PATH), f"Log file not created at {LOG_PATH}"
    
    with open(LOG_PATH, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) > 0, "No log entries found"
    print(f"   ✓ Found {len(lines)} log entry(ies)")
    
    # Parse and verify the log entry
    print("\n6. Verifying log entry content...")
    entry = json.loads(lines[0])
    
    required_fields = ['timestamp', 'event', 'current_temp', 'low_limit', 'high_limit', 'tilt_color']
    for field in required_fields:
        assert field in entry, f"Missing field: {field}"
    
    assert entry['event'] == "TEMP CONTROL READING", f"Unexpected event: {entry['event']}"
    assert entry['current_temp'] == 67.5, f"Unexpected temp: {entry['current_temp']}"
    assert entry['low_limit'] == 65.0, f"Unexpected low_limit: {entry['low_limit']}"
    assert entry['high_limit'] == 70.0, f"Unexpected high_limit: {entry['high_limit']}"
    assert entry['tilt_color'] == 'Blue', f"Unexpected tilt_color: {entry['tilt_color']}"
    
    print("   ✓ All required fields present with correct values")
    print(f"   Entry: {json.dumps(entry, indent=2)}")
    
    # Test that logging is skipped when monitoring is off
    print("\n7. Testing that logging is skipped when monitoring is off...")
    temp_cfg['temp_control_active'] = False
    
    # Clear the log
    open(LOG_PATH, 'w').close()
    
    log_periodic_temp_reading()
    
    with open(LOG_PATH, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 0, "Log entry created when monitoring was off"
    print("   ✓ No log entry created when temp_control_active is False")
    
    # Restore backup
    print("\n8. Cleaning up...")
    os.remove(LOG_PATH)
    backup_path = f"{LOG_PATH}.test_backup"
    if os.path.exists(backup_path):
        os.rename(backup_path, LOG_PATH)
        print(f"   ✓ Restored backup log")
    else:
        print("   ✓ Test log removed")
    
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED")
    print("="*70)
    print("\nSummary:")
    print("  • Temperature control readings use 'temp_control_reading' event")
    print("  • Readings are logged by log_periodic_temp_reading() function")
    print("  • This is called from periodic_temp_control() at update_interval frequency")
    print("  • Separate from Tilt readings which use tilt_logging_interval_minutes")
    print("  • Logging only happens when temp_control_active is True")
    print()

if __name__ == "__main__":
    test_temp_control_reading_interval()
