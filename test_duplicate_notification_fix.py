#!/usr/bin/env python3
"""
Test for duplicate notification prevention.
Simulates rapid BLE callbacks to ensure only one notification is sent.
"""

import sys
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, call

def test_duplicate_notification_prevention():
    """
    Test that rapid successive calls to check_fermentation_starting
    only trigger one notification due to flag-before-send and debounce.
    """
    print("=" * 80)
    print("TEST: Duplicate Notification Prevention")
    print("=" * 80)
    
    # Mock the app module components
    with patch.dict('sys.modules', {'app': Mock()}):
        import app
        
        # Setup mock configurations
        app.system_cfg = {
            'brewery_name': 'Test Brewery',
            'warning_mode': 'BOTH',
            'batch_notifications': {
                'enable_fermentation_starting': True,
                'enable_fermentation_completion': True
            }
        }
        
        app.batch_notification_state = {}
        
        # Mock the notification function to track calls
        notification_calls = []
        def mock_attempt_send(subject, body):
            notification_calls.append({'subject': subject, 'body': body, 'time': datetime.utcnow()})
            return True
        
        app.attempt_send_notifications = mock_attempt_send
        
        # Mock save_notification_state_to_config
        config_saves = []
        def mock_save_config(color, brewid):
            config_saves.append({'color': color, 'brewid': brewid, 'time': datetime.utcnow()})
        
        app.save_notification_state_to_config = mock_save_config
        
        # Import the function under test
        from app import check_fermentation_starting
        
        # Setup test data
        brewid = "test123"
        color = "Black"
        cfg = {
            'actual_og': '1.060',
            'beer_name': 'Test IPA'
        }
        
        # Initialize state with readings that trigger notification
        state = {
            'last_reading_time': datetime.utcnow(),
            'signal_lost': False,
            'signal_loss_notified': False,
            'fermentation_started': False,
            'gravity_history': [
                {'gravity': 1.048, 'timestamp': datetime.utcnow() - timedelta(seconds=30)},
                {'gravity': 1.047, 'timestamp': datetime.utcnow() - timedelta(seconds=20)},
                {'gravity': 1.046, 'timestamp': datetime.utcnow() - timedelta(seconds=10)},
            ],
            'last_daily_report': None
        }
        
        app.batch_notification_state[brewid] = state
        
        print("\n1. First call - should send notification:")
        check_fermentation_starting(color, brewid, cfg, state)
        print(f"   Notifications sent: {len(notification_calls)}")
        print(f"   Flag set: {state.get('fermentation_start_datetime') is not None}")
        assert len(notification_calls) == 1, f"Expected 1 notification, got {len(notification_calls)}"
        assert state.get('fermentation_start_datetime'), "Flag should be set"
        print("   ✅ First notification sent successfully")
        
        print("\n2. Immediate second call (0.02s later) - should be blocked by flag:")
        time.sleep(0.02)
        check_fermentation_starting(color, brewid, cfg, state)
        print(f"   Notifications sent: {len(notification_calls)}")
        assert len(notification_calls) == 1, f"Expected still 1 notification, got {len(notification_calls)}"
        print("   ✅ Duplicate blocked by flag check")
        
        print("\n3. Reset flag and immediate call - should be blocked by debounce:")
        state['fermentation_start_datetime'] = None
        state['fermentation_started'] = False
        time.sleep(0.02)
        check_fermentation_starting(color, brewid, cfg, state)
        print(f"   Notifications sent: {len(notification_calls)}")
        assert len(notification_calls) == 1, f"Expected still 1 notification, got {len(notification_calls)}"
        print("   ✅ Duplicate blocked by 5-second debounce")
        
        print("\n4. After 5.1 seconds - should send new notification:")
        # Clear the last check timestamp to simulate 5+ seconds passing
        state['last_fermentation_start_check'] = datetime.utcnow() - timedelta(seconds=5.1)
        check_fermentation_starting(color, brewid, cfg, state)
        print(f"   Notifications sent: {len(notification_calls)}")
        assert len(notification_calls) == 2, f"Expected 2 notifications, got {len(notification_calls)}"
        print("   ✅ New notification sent after debounce period")
        
        # Check timing between notifications
        if len(notification_calls) >= 2:
            time_diff = (notification_calls[1]['time'] - notification_calls[0]['time']).total_seconds()
            print(f"\n5. Time between notifications: {time_diff:.2f} seconds")
            assert time_diff >= 5, f"Expected at least 5 seconds between notifications, got {time_diff:.2f}s"
            print("   ✅ Debounce timing verified")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Duplicate notification prevention working!")
        print("=" * 80)
        return True

def test_fermentation_completion_duplicate_prevention():
    """
    Test that rapid successive calls to check_fermentation_completion
    only trigger one notification.
    """
    print("\n" + "=" * 80)
    print("TEST: Fermentation Completion Duplicate Prevention")
    print("=" * 80)
    
    with patch.dict('sys.modules', {'app': Mock()}):
        import app
        
        app.system_cfg = {
            'brewery_name': 'Test Brewery',
            'warning_mode': 'BOTH',
            'batch_notifications': {
                'enable_fermentation_completion': True
            }
        }
        
        notification_calls = []
        def mock_attempt_send(subject, body):
            notification_calls.append({'subject': subject, 'body': body, 'time': datetime.utcnow()})
            return True
        
        app.attempt_send_notifications = mock_attempt_send
        app.save_notification_state_to_config = Mock()
        
        from app import check_fermentation_completion
        
        brewid = "test456"
        color = "Red"
        cfg = {
            'actual_og': '1.060',
            'beer_name': 'Test Stout'
        }
        
        # Create history with stable gravity over 24+ hours
        base_time = datetime.utcnow()
        state = {
            'fermentation_started': True,
            'gravity_history': [
                {'gravity': 1.015, 'timestamp': base_time - timedelta(hours=24.5)},
                {'gravity': 1.015, 'timestamp': base_time - timedelta(hours=24)},
                {'gravity': 1.015, 'timestamp': base_time - timedelta(hours=23.5)},
                {'gravity': 1.015, 'timestamp': base_time - timedelta(seconds=10)},
            ]
        }
        
        print("\n1. First call - should send notification:")
        check_fermentation_completion(color, brewid, cfg, state)
        print(f"   Notifications sent: {len(notification_calls)}")
        assert len(notification_calls) == 1, f"Expected 1 notification, got {len(notification_calls)}"
        print("   ✅ First notification sent")
        
        print("\n2. Immediate second call - should be blocked:")
        time.sleep(0.02)
        check_fermentation_completion(color, brewid, cfg, state)
        print(f"   Notifications sent: {len(notification_calls)}")
        assert len(notification_calls) == 1, f"Expected still 1 notification, got {len(notification_calls)}"
        print("   ✅ Duplicate blocked")
        
        print("\n" + "=" * 80)
        print("✅ Fermentation completion duplicate prevention working!")
        print("=" * 80)
        return True

if __name__ == '__main__':
    try:
        # Note: These tests use mocking and don't need the full app environment
        test_duplicate_notification_prevention()
        test_fermentation_completion_duplicate_prevention()
        print("\n" + "=" * 80)
        print("🎉 ALL DUPLICATE PREVENTION TESTS PASSED!")
        print("=" * 80)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
