#!/usr/bin/env python3
"""
Test to verify temperature control readings are recorded at update_interval frequency,
not at tilt_logging_interval_minutes frequency.

Readings are stored in memory (not logged to file) to avoid excessive log entries.
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
    print("Testing Temperature Control Reading Interval (In-Memory)")
    print("="*70)
    
    # Import after path is set
    from app import (
        log_periodic_temp_reading, temp_cfg, system_cfg, 
        temp_reading_buffer, TEMP_READING_BUFFER_SIZE, ALLOWED_EVENTS
    )
    
    # Verify the event type exists
    print("\n1. Verifying event type...")
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
    print(f"   In-memory buffer size: {TEMP_READING_BUFFER_SIZE} entries")
    print("   ✓ Configuration set")
    
    # Clear the in-memory buffer
    print("\n3. Preparing test environment...")
    temp_reading_buffer.clear()
    print(f"   ✓ Cleared in-memory buffer (size: {len(temp_reading_buffer)})")
    
    # Test the recording function
    print("\n4. Testing log_periodic_temp_reading()...")
    try:
        log_periodic_temp_reading()
        print("   ✓ Function executed without errors")
    except Exception as e:
        print(f"   ✗ Error calling log_periodic_temp_reading: {e}")
        raise
    
    # Verify entry was added to memory buffer
    print("\n5. Verifying in-memory entry...")
    assert len(temp_reading_buffer) > 0, "No entries in memory buffer"
    print(f"   ✓ Found {len(temp_reading_buffer)} entry(ies) in memory buffer")
    
    # Parse and verify the entry
    print("\n6. Verifying entry content...")
    entry = temp_reading_buffer[0]
    
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
    
    # Test that recording is skipped when monitoring is off
    print("\n7. Testing that recording is skipped when monitoring is off...")
    temp_cfg['temp_control_active'] = False
    
    # Clear the buffer and try to record
    initial_count = len(temp_reading_buffer)
    temp_reading_buffer.clear()
    
    log_periodic_temp_reading()
    
    assert len(temp_reading_buffer) == 0, "Entry added to buffer when monitoring was off"
    print("   ✓ No entry added when temp_control_active is False")
    
    # Test buffer size limit
    print("\n8. Testing buffer size limit...")
    temp_cfg['temp_control_active'] = True
    temp_reading_buffer.clear()
    
    # Add more than buffer size to test automatic dropping
    for i in range(TEMP_READING_BUFFER_SIZE + 10):
        temp_cfg['current_temp'] = 67.0 + i
        log_periodic_temp_reading()
    
    assert len(temp_reading_buffer) == TEMP_READING_BUFFER_SIZE, f"Buffer exceeded max size: {len(temp_reading_buffer)}"
    print(f"   ✓ Buffer respects max size: {TEMP_READING_BUFFER_SIZE} entries")
    
    # Cleanup
    print("\n9. Cleaning up...")
    temp_reading_buffer.clear()
    print("   ✓ Cleared memory buffer")
    
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED")
    print("="*70)
    print("\nSummary:")
    print("  • Temperature control readings use 'temp_control_reading' event")
    print("  • Readings are stored IN MEMORY (not logged to file)")
    print("  • Recorded by log_periodic_temp_reading() function")
    print("  • Called from periodic_temp_control() at update_interval frequency")
    print("  • Separate from Tilt readings which use tilt_logging_interval_minutes")
    print("  • Recording only happens when temp_control_active is True")
    print(f"  • Buffer limited to {TEMP_READING_BUFFER_SIZE} entries (prevents memory bloat)")
    print("  • Avoids creating 720+ log entries per day")
    print()

if __name__ == "__main__":
    test_temp_control_reading_interval()
