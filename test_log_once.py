#!/usr/bin/env python3
"""
Test that logs and notifications are sent only ONCE per incident.

This test verifies the fix for:
"Every 2 minutes????? Once is enough until corrected."

The system should:
1. Log the event ONCE when it first happens
2. Send notification ONCE when it first happens
3. NOT log or notify again on subsequent checks (every 2 minutes)
4. Reset and allow new log/notification when issue is corrected and happens again
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def count_log_entries(log_path, event_type):
    """Count how many times an event appears in the log."""
    count = 0
    try:
        import json
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if event_type in entry.get('event', ''):
                        count += 1
                except:
                    pass
    except FileNotFoundError:
        pass
    return count

def test_log_and_notify_once():
    """Test that logs and notifications happen only once per incident."""
    from app import (
        is_control_tilt_active,
        live_tilts,
        system_cfg,
        temp_cfg,
        control_heating,
        control_cooling,
        kasa_queue,
        pending_notifications,
        LOG_PATH
    )
    
    print("=" * 80)
    print("LOG AND NOTIFY ONCE TEST")
    print("=" * 80)
    print("\nRequirement: Once is enough until corrected")
    print("- First time: Log ✓ and Notify ✓")
    print("- Subsequent times (every 2 min): Neither log nor notify")
    print("- After correction: Reset, can log/notify again for new incident")
    print("=" * 80)
    
    # Store original values
    original_tilts = dict(live_tilts)
    original_temp_cfg = dict(temp_cfg)
    original_timeout = system_cfg.get('tilt_inactivity_timeout_minutes')
    original_update_interval = system_cfg.get('update_interval')
    
    # Clear or backup log file
    import os
    import tempfile
    import shutil
    
    # Use a temporary log file for testing
    test_log = tempfile.mktemp(suffix='.jsonl')
    original_log_path = LOG_PATH
    
    try:
        # Temporarily point to test log
        import app
        app.LOG_PATH = test_log
        
        # Setup
        system_cfg['tilt_inactivity_timeout_minutes'] = 30
        system_cfg['update_interval'] = 2
        
        # Clear state
        live_tilts.clear()
        temp_cfg.clear()
        pending_notifications.clear()
        
        # Clear kasa queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        now = datetime.utcnow()
        
        print("\n[TEST 1] First Blocked ON - Should Log and Notify ONCE")
        print("-" * 80)
        
        # Setup: Red Tilt is inactive (beyond grace period and timeout)
        temp_cfg.update({
            'tilt_color': 'Red',
            'tilt_assignment_time': (now - timedelta(minutes=20)).isoformat(),
            'temp_control_enabled': True,
            'enable_heating': True,
            'enable_cooling': False,
            'low_limit': 50.0,
            'high_limit': 54.0,
            'heating_plug': '192.168.1.100',
            'cooling_plug': '192.168.1.101',
            'heater_on': False,
            'cooler_on': False
        })
        
        # Red Tilt is inactive (10 minutes old)
        inactive_timestamp = (now - timedelta(minutes=10)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red'] = {
            'timestamp': inactive_timestamp,
            'temp_f': 52.0,
            'gravity': 1.050,
            'beer_name': 'Test IPA',
            'brewid': 'test123'
        }
        
        print(f"  - Red Tilt: INACTIVE")
        print(f"  - is_control_tilt_active(): {is_control_tilt_active()}")
        assert not is_control_tilt_active(), "Tilt should be inactive"
        
        # Try to turn heating ON - should be blocked
        print(f"\n  Attempt 1: Trying to turn heating ON...")
        control_heating("on")
        
        # Count log entries
        blocked_logs_1 = count_log_entries(test_log, "BLOCKED ON COMMAND")
        print(f"  - Log entries for 'BLOCKED ON': {blocked_logs_1}")
        assert blocked_logs_1 == 1, f"Should have 1 log entry, got {blocked_logs_1}"
        print(f"  ✓ Logged ONCE")
        
        # Count notifications
        blocked_notifs = [n for n in pending_notifications if 'plug_blocked' in n.get('notification_type', '')]
        print(f"  - Pending notifications: {len(blocked_notifs)}")
        assert len(blocked_notifs) == 1, f"Should have 1 notification, got {len(blocked_notifs)}"
        print(f"  ✓ Notified ONCE")
        
        print("\n[TEST 2] Subsequent Attempts - Should NOT Log or Notify Again")
        print("-" * 80)
        print("Simulating temperature control running every 2 minutes...")
        
        # Clear queue
        while not kasa_queue.empty():
            kasa_queue.get()
        
        # Try to turn heating ON again (2 minutes later)
        print(f"\n  Attempt 2 (T+2 min): Trying to turn heating ON...")
        control_heating("on")
        
        blocked_logs_2 = count_log_entries(test_log, "BLOCKED ON COMMAND")
        print(f"  - Log entries: {blocked_logs_2}")
        assert blocked_logs_2 == 1, f"Should still have only 1 log entry, got {blocked_logs_2}"
        print(f"  ✓ Did NOT log again")
        
        blocked_notifs_2 = [n for n in pending_notifications if 'plug_blocked' in n.get('notification_type', '')]
        print(f"  - Pending notifications: {len(blocked_notifs_2)}")
        assert len(blocked_notifs_2) == 1, f"Should still have only 1 notification, got {len(blocked_notifs_2)}"
        print(f"  ✓ Did NOT notify again")
        
        # Try again (4 minutes later)
        print(f"\n  Attempt 3 (T+4 min): Trying to turn heating ON...")
        control_heating("on")
        
        blocked_logs_3 = count_log_entries(test_log, "BLOCKED ON COMMAND")
        print(f"  - Log entries: {blocked_logs_3}")
        assert blocked_logs_3 == 1, f"Should still have only 1 log entry, got {blocked_logs_3}"
        print(f"  ✓ Did NOT log again")
        
        blocked_notifs_3 = [n for n in pending_notifications if 'plug_blocked' in n.get('notification_type', '')]
        print(f"  - Pending notifications: {len(blocked_notifs_3)}")
        assert len(blocked_notifs_3) == 1, f"Should still have only 1 notification, got {len(blocked_notifs_3)}"
        print(f"  ✓ Did NOT notify again")
        
        print("\n[TEST 3] Connection Restored - Reset Flags")
        print("-" * 80)
        
        # Tilt becomes active again
        active_timestamp = now.replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = active_timestamp
        
        print(f"  - Red Tilt: ACTIVE (connection restored)")
        assert is_control_tilt_active(), "Tilt should be active"
        
        # Try to turn heating ON - should succeed and reset flags
        print(f"\n  Turning heating ON with active Tilt...")
        control_heating("on")
        
        print(f"  ✓ Flags reset when connection restored")
        
        # Verify flags are reset
        assert not temp_cfg.get("heating_blocked_logged"), "Logged flag should be reset"
        assert not temp_cfg.get("heating_blocked_notified"), "Notified flag should be reset"
        print(f"  ✓ Flags confirmed reset")
        
        print("\n[TEST 4] New Incident - Should Log and Notify Again")
        print("-" * 80)
        
        # Make Tilt inactive again (new incident)
        inactive_timestamp = (now - timedelta(minutes=10)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red']['timestamp'] = inactive_timestamp
        
        print(f"  - Red Tilt: INACTIVE (new incident)")
        assert not is_control_tilt_active(), "Tilt should be inactive again"
        
        # Clear queue and notifications from previous tests
        while not kasa_queue.empty():
            kasa_queue.get()
        pending_notifications.clear()
        
        # Try to turn heating ON - should log and notify for NEW incident
        print(f"\n  New incident: Trying to turn heating ON...")
        control_heating("on")
        
        blocked_logs_4 = count_log_entries(test_log, "BLOCKED ON COMMAND")
        print(f"  - Log entries: {blocked_logs_4}")
        assert blocked_logs_4 == 2, f"Should have 2 log entries (new incident), got {blocked_logs_4}"
        print(f"  ✓ Logged for NEW incident")
        
        blocked_notifs_4 = [n for n in pending_notifications if 'plug_blocked' in n.get('notification_type', '')]
        print(f"  - Pending notifications: {len(blocked_notifs_4)}")
        assert len(blocked_notifs_4) == 1, f"Should have 1 notification (new incident), got {len(blocked_notifs_4)}"
        print(f"  ✓ Notified for NEW incident")
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        print("\nSummary:")
        print("  ✓ First occurrence: Log and notify ONCE")
        print("  ✓ Subsequent checks: NO additional logs or notifications")
        print("  ✓ After correction: Flags reset")
        print("  ✓ New incident: Can log and notify again")
        print("\nOnce is enough until corrected! ✓")
        
        return True
        
    finally:
        # Restore original log path
        import app
        app.LOG_PATH = original_log_path
        
        # Clean up test log
        try:
            os.remove(test_log)
        except:
            pass
        
        # Restore original values
        pending_notifications.clear()
        live_tilts.clear()
        live_tilts.update(original_tilts)
        temp_cfg.clear()
        temp_cfg.update(original_temp_cfg)
        if original_timeout is not None:
            system_cfg['tilt_inactivity_timeout_minutes'] = original_timeout
        if original_update_interval is not None:
            system_cfg['update_interval'] = original_update_interval
        
        # Clear queue
        while not kasa_queue.empty():
            kasa_queue.get()

if __name__ == '__main__':
    try:
        success = test_log_and_notify_once()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
