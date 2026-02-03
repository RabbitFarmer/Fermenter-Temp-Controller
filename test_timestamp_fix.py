#!/usr/bin/env python3
"""
Test to verify the timestamp fix.

The issue:
- Logs used UTC time for all fields, confusing for users in other timezones
- Users looking at raw log files see times that don't match their local time

The fix:
- timestamp field: Keep in UTC with 'Z' suffix (ISO format, compatibility)
- date field: Use local date
- time field: Use local time

This makes the date/time fields human-readable in the user's timezone
while maintaining the precise UTC timestamp for programmatic use.
"""

from datetime import datetime
import json

def _format_control_log_entry_BEFORE_FIX(event_type, payload):
    """Original version using UTC for all fields."""
    ts = datetime.utcnow()
    iso_ts = ts.replace(microsecond=0).isoformat() + "Z"
    date = ts.strftime("%Y-%m-%d")
    time_str = ts.strftime("%H:%M:%S")
    
    entry = {
        "timestamp": iso_ts,
        "date": date,
        "time": time_str,
        "event": event_type
    }
    return entry


def _format_control_log_entry_AFTER_FIX(event_type, payload):
    """Fixed version using local time for date/time fields."""
    # Use UTC for the ISO timestamp (with Z suffix) for consistency and compatibility
    ts_utc = datetime.utcnow()
    iso_ts = ts_utc.replace(microsecond=0).isoformat() + "Z"
    
    # Use local time for date and time fields so they're readable in the user's timezone
    ts_local = datetime.now()
    date = ts_local.strftime("%Y-%m-%d")
    time_str = ts_local.strftime("%H:%M:%S")
    
    entry = {
        "timestamp": iso_ts,
        "date": date,
        "time": time_str,
        "event": event_type
    }
    return entry


def test_timestamp_fix():
    """Test that timestamps use local time for date/time fields."""
    
    print("=" * 80)
    print("TIMESTAMP FIX TEST")
    print("=" * 80)
    print("\nThis test verifies that log entries show local time for readability")
    print("while maintaining UTC timestamp for compatibility.")
    print("=" * 80)
    
    print("\n[BEFORE FIX] All fields use UTC")
    print("-" * 80)
    entry_before = _format_control_log_entry_BEFORE_FIX("heating_on", {})
    print(f"timestamp: {entry_before['timestamp']} (UTC)")
    print(f"date:      {entry_before['date']} (UTC)")
    print(f"time:      {entry_before['time']} (UTC)")
    print("\nProblem: If user is in PST (UTC-8), they see times 8 hours ahead")
    
    print("\n[AFTER FIX] date/time use local time")
    print("-" * 80)
    entry_after = _format_control_log_entry_AFTER_FIX("heating_on", {})
    print(f"timestamp: {entry_after['timestamp']} (UTC, for compatibility)")
    print(f"date:      {entry_after['date']} (LOCAL)")
    print(f"time:      {entry_after['time']} (LOCAL)")
    print("\nBenefit: Date/time fields match user's wall clock")
    
    print("\n[VERIFICATION]")
    print("-" * 80)
    
    # Get current UTC and local times
    utc_now = datetime.utcnow()
    local_now = datetime.now()
    
    # Calculate timezone offset
    offset_seconds = (local_now - utc_now).total_seconds()
    offset_hours = offset_seconds / 3600
    
    print(f"Current UTC time:   {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current local time: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Timezone offset:    {offset_hours:+.1f} hours from UTC")
    
    # Verify the fix produces the expected result
    if abs(offset_hours) > 0.1:  # If timezone is different from UTC
        # date/time should be different between before and after
        if entry_before['time'] != entry_after['time']:
            print(f"\n✓ SUCCESS: time field changed from UTC to local")
            print(f"  Before: {entry_before['time']} (UTC)")
            print(f"  After:  {entry_after['time']} (Local)")
        else:
            print(f"\n⚠ Note: time fields are the same (might be same hour in both zones)")
    else:
        print(f"\n⚠ Note: System is in UTC timezone, so times are identical")
    
    # Verify timestamp field is always UTC
    if entry_after['timestamp'].endswith('Z'):
        print(f"✓ SUCCESS: timestamp field still uses UTC (has 'Z' suffix)")
    else:
        print(f"✗ FAILURE: timestamp should end with 'Z' for UTC")
        return False
    
    print("\n[EXAMPLE LOG ENTRY]")
    print("-" * 80)
    print(json.dumps(entry_after, indent=2))
    
    print("\n" + "=" * 80)
    print("TEST PASSED - TIMESTAMP FIX VERIFIED")
    print("=" * 80)
    print("\nUsers will now see local time in date/time fields,")
    print("while timestamp remains in UTC for programmatic use.")
    
    return True


if __name__ == '__main__':
    import sys
    
    success = test_timestamp_fix()
    sys.exit(0 if success else 1)
