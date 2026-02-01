#!/usr/bin/env python3
"""
Test to verify backward compatibility - existing log files without periodic readings
should still work correctly.
"""

import json
import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_backward_compatibility():
    """
    Test that chart_data endpoint still works with old log files
    that don't have periodic temperature control readings.
    """
    print("\n" + "="*70)
    print("Testing Backward Compatibility with Existing Logs")
    print("="*70)
    
    # Import Flask app for testing
    from app import app, LOG_PATH, ALLOWED_EVENT_VALUES
    
    # Create a test client
    client = app.test_client()
    
    print("\n1. Verifying all old event types are still supported...")
    old_event_types = [
        "SAMPLE",
        "HEATING-PLUG TURNED ON",
        "HEATING-PLUG TURNED OFF",
        "COOLING-PLUG TURNED ON",
        "COOLING-PLUG TURNED OFF",
        "TEMP BELOW LOW LIMIT",
        "TEMP ABOVE HIGH LIMIT",
        "IN RANGE",
        "MODE_SELECTED",
        "MODE_CHANGED",
        "TEMP CONTROL STARTED",
        "SAFETY SHUTDOWN - CONTROL TILT INACTIVE",
        "SAFETY - BLOCKED ON COMMAND (NO TILT CONNECTION)",
        "SAFETY - TURNING OFF (NO TILT CONNECTION)",
        "KASA COMMAND TIMEOUT - PENDING FLAG CLEARED",
    ]
    
    for event in old_event_types:
        assert event in ALLOWED_EVENT_VALUES, f"Old event type not supported: {event}"
    
    print(f"   ✓ All {len(old_event_types)} old event types are still supported")
    
    # Backup existing log
    print("\n2. Preparing test environment...")
    backup_path = None
    if os.path.exists(LOG_PATH):
        backup_path = f"{LOG_PATH}.compat_test_backup"
        os.rename(LOG_PATH, backup_path)
        print(f"   ✓ Backed up existing log to {backup_path}")
    
    # Ensure log directory exists
    log_dir = os.path.dirname(LOG_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Create a legacy log file with only event-based entries (no periodic readings)
    print("\n3. Creating legacy log file (no periodic readings)...")
    base_time = datetime.utcnow() - timedelta(hours=1)
    
    legacy_entries = [
        {
            "timestamp": (base_time + timedelta(minutes=0)).replace(microsecond=0).isoformat() + "Z",
            "date": (base_time + timedelta(minutes=0)).strftime("%Y-%m-%d"),
            "time": (base_time + timedelta(minutes=0)).strftime("%H:%M:%S"),
            "tilt_color": "Blue",
            "brewid": "",
            "low_limit": 65.0,
            "current_temp": 68.0,
            "temp_f": 68.0,
            "gravity": 1.050,
            "high_limit": 70.0,
            "event": "MODE_CHANGED"
        },
        {
            "timestamp": (base_time + timedelta(minutes=5)).replace(microsecond=0).isoformat() + "Z",
            "date": (base_time + timedelta(minutes=5)).strftime("%Y-%m-%d"),
            "time": (base_time + timedelta(minutes=5)).strftime("%H:%M:%S"),
            "tilt_color": "Blue",
            "brewid": "",
            "low_limit": 65.0,
            "current_temp": 64.5,
            "temp_f": 64.5,
            "gravity": 1.049,
            "high_limit": 70.0,
            "event": "TEMP BELOW LOW LIMIT"
        },
        {
            "timestamp": (base_time + timedelta(minutes=10)).replace(microsecond=0).isoformat() + "Z",
            "date": (base_time + timedelta(minutes=10)).strftime("%Y-%m-%d"),
            "time": (base_time + timedelta(minutes=10)).strftime("%H:%M:%S"),
            "tilt_color": "Blue",
            "brewid": "",
            "low_limit": 65.0,
            "current_temp": 65.5,
            "temp_f": 65.5,
            "gravity": None,
            "high_limit": 70.0,
            "event": "HEATING-PLUG TURNED ON"
        },
        {
            "timestamp": (base_time + timedelta(minutes=20)).replace(microsecond=0).isoformat() + "Z",
            "date": (base_time + timedelta(minutes=20)).strftime("%Y-%m-%d"),
            "time": (base_time + timedelta(minutes=20)).strftime("%H:%M:%S"),
            "tilt_color": "Blue",
            "brewid": "",
            "low_limit": 65.0,
            "current_temp": 67.0,
            "temp_f": 67.0,
            "gravity": None,
            "high_limit": 70.0,
            "event": "IN RANGE"
        },
        {
            "timestamp": (base_time + timedelta(minutes=25)).replace(microsecond=0).isoformat() + "Z",
            "date": (base_time + timedelta(minutes=25)).strftime("%Y-%m-%d"),
            "time": (base_time + timedelta(minutes=25)).strftime("%H:%M:%S"),
            "tilt_color": "Blue",
            "brewid": "",
            "low_limit": 65.0,
            "current_temp": 70.2,
            "temp_f": 70.2,
            "gravity": None,
            "high_limit": 70.0,
            "event": "HEATING-PLUG TURNED OFF"
        },
    ]
    
    with open(LOG_PATH, 'w') as f:
        for entry in legacy_entries:
            f.write(json.dumps(entry) + "\n")
    
    print(f"   ✓ Created legacy log with {len(legacy_entries)} event-based entries")
    print("   ✓ No periodic readings (simulating old log format)")
    
    # Test the chart_data endpoint with legacy log
    print("\n4. Testing chart_data endpoint with legacy log...")
    response = client.get('/chart_data/Fermenter?limit=1000')
    
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    print("   ✓ Endpoint returned 200 OK")
    
    # Parse the response
    data = json.loads(response.data)
    
    print(f"\n5. Verifying legacy log is processed correctly...")
    print(f"   Total points returned: {len(data['points'])}")
    print(f"   Matched entries: {data['matched']}")
    
    assert len(data['points']) == 5, f"Expected 5 points, got {len(data['points'])}"
    assert data['matched'] == 5, f"Expected 5 matched entries, got {data['matched']}"
    
    # Verify all events are included
    events = [p['event'] for p in data['points']]
    expected_events = [
        "MODE_CHANGED",
        "TEMP BELOW LOW LIMIT",
        "HEATING-PLUG TURNED ON",
        "IN RANGE",
        "HEATING-PLUG TURNED OFF"
    ]
    
    for expected in expected_events:
        assert expected in events, f"Missing event: {expected}"
    
    print("   ✓ All legacy events are processed correctly")
    
    # Verify data structure is correct
    print("\n6. Verifying data structure...")
    sample = data['points'][0]
    
    required_fields = ['timestamp', 'event', 'temp_f', 'low_limit', 'high_limit', 'tilt_color']
    for field in required_fields:
        assert field in sample, f"Missing field: {field}"
    
    print("   ✓ All required fields present in legacy data")
    
    # Test mixed log (legacy + new periodic readings)
    print("\n7. Testing mixed log (legacy + new periodic readings)...")
    
    # Add some periodic readings to the existing log
    new_entry = {
        "timestamp": (base_time + timedelta(minutes=30)).replace(microsecond=0).isoformat() + "Z",
        "date": (base_time + timedelta(minutes=30)).strftime("%Y-%m-%d"),
        "time": (base_time + timedelta(minutes=30)).strftime("%H:%M:%S"),
        "tilt_color": "Blue",
        "brewid": "",
        "low_limit": 65.0,
        "current_temp": 68.5,
        "temp_f": 68.5,
        "gravity": None,
        "high_limit": 70.0,
        "event": "TEMP CONTROL READING"
    }
    
    with open(LOG_PATH, 'a') as f:
        f.write(json.dumps(new_entry) + "\n")
    
    print("   ✓ Added new periodic reading to legacy log")
    
    # Test again
    response = client.get('/chart_data/Fermenter?limit=1000')
    data = json.loads(response.data)
    
    assert len(data['points']) == 6, f"Expected 6 points (5 legacy + 1 new), got {len(data['points'])}"
    assert data['matched'] == 6, f"Expected 6 matched entries, got {data['matched']}"
    
    # Verify both old and new event types are present
    events = [p['event'] for p in data['points']]
    assert "TEMP CONTROL READING" in events, "New periodic reading not found"
    assert "MODE_CHANGED" in events, "Legacy event not found"
    
    print("   ✓ Mixed log (legacy + new) works correctly")
    print("   ✓ Both old event types and new periodic readings coexist")
    
    # Cleanup
    print("\n8. Cleaning up...")
    os.remove(LOG_PATH)
    if backup_path and os.path.exists(backup_path):
        os.rename(backup_path, LOG_PATH)
        print(f"   ✓ Restored backup log")
    else:
        print("   ✓ Test log removed")
    
    print("\n" + "="*70)
    print("✓ ALL BACKWARD COMPATIBILITY TESTS PASSED")
    print("="*70)
    print("\nSummary:")
    print("  • All existing event types remain supported")
    print("  • Legacy logs without periodic readings work correctly")
    print("  • New periodic readings can coexist with legacy events")
    print("  • Chart data endpoint handles both old and new formats")
    print("  • No breaking changes - fully backward compatible")
    print()

if __name__ == "__main__":
    test_backward_compatibility()
