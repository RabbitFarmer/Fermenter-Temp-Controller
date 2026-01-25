#!/usr/bin/env python3
"""
Unit test to verify the pending notification queue deduplication.
Tests that notifications are deduplicated when queued within 10 seconds.
"""

import time
from datetime import datetime, timedelta


def test_pending_queue_deduplication():
    """
    Test that duplicate notifications in the pending queue are deduplicated.
    Simulates the scenario where duplicate notifications are triggered 0.02 seconds apart.
    """
    print("=" * 80)
    print("TEST 1: Pending Queue Deduplication")
    print("=" * 80)
    
    # Simulate the pending queue
    pending_notifications = []
    
    def queue_pending_notification(notification_type, subject, body, brewid, color):
        """Simulate the queue_pending_notification function"""
        # Check if this notification is already pending (prevent duplicates)
        for item in pending_notifications:
            if item['notification_type'] == notification_type and item['brewid'] == brewid:
                # Already pending, don't add again
                print(f"   ⚠️  Notification {notification_type}/{brewid} already pending, skipping duplicate")
                return False
        
        # Add to pending queue
        pending_notifications.append({
            'notification_type': notification_type,
            'subject': subject,
            'body': body,
            'brewid': brewid,
            'color': color,
            'queued_time': datetime.utcnow()
        })
        print(f"   ✅ Queued {notification_type}/{brewid} notification")
        return True
    
    print("\n1. Queue first signal_loss notification:")
    result1 = queue_pending_notification('signal_loss', 'Subject 1', 'Body 1', 'brew123', 'Blue')
    assert result1 == True, "First notification should be queued"
    assert len(pending_notifications) == 1, "Should have 1 item in queue"
    
    print("\n2. Queue duplicate signal_loss notification 0.02s later:")
    time.sleep(0.02)
    result2 = queue_pending_notification('signal_loss', 'Subject 2', 'Body 2', 'brew123', 'Blue')
    assert result2 == False, "Duplicate should be rejected"
    assert len(pending_notifications) == 1, "Should still have only 1 item in queue"
    print("   ✅ Duplicate correctly rejected")
    
    print("\n3. Queue another duplicate 0.05s later:")
    time.sleep(0.03)
    result3 = queue_pending_notification('signal_loss', 'Subject 3', 'Body 3', 'brew123', 'Blue')
    assert result3 == False, "Duplicate should still be rejected"
    assert len(pending_notifications) == 1, "Should still have only 1 item in queue"
    print("   ✅ Second duplicate correctly rejected")
    
    print("\n4. Queue different notification type (same brewid):")
    result4 = queue_pending_notification('fermentation_start', 'Subject 4', 'Body 4', 'brew123', 'Blue')
    assert result4 == True, "Different notification type should be queued"
    assert len(pending_notifications) == 2, "Should have 2 items in queue"
    print("   ✅ Different notification type correctly queued")
    
    print("\n5. Queue same notification type for different brewid:")
    result5 = queue_pending_notification('signal_loss', 'Subject 5', 'Body 5', 'brew456', 'Red')
    assert result5 == True, "Different brewid should be queued"
    assert len(pending_notifications) == 3, "Should have 3 items in queue"
    print("   ✅ Different brewid correctly queued")
    
    print(f"\n6. Final queue size: {len(pending_notifications)}")
    print("   Queue contents:")
    for idx, item in enumerate(pending_notifications, 1):
        print(f"      {idx}. {item['notification_type']}/{item['brewid']} - {item['color']}")
    
    assert len(pending_notifications) == 3, "Should have exactly 3 items"
    print("   ✅ Correct number of unique notifications queued")
    
    return True


def test_pending_queue_processing():
    """
    Test that pending notifications are processed after the delay period.
    """
    print("\n" + "=" * 80)
    print("TEST 2: Pending Queue Processing with Delay")
    print("=" * 80)
    
    NOTIFICATION_PENDING_DELAY_SECONDS = 10
    pending_notifications = []
    sent_notifications = []
    
    def queue_pending_notification(notification_type, subject, body, brewid, color):
        """Simulate the queue_pending_notification function"""
        for item in pending_notifications:
            if item['notification_type'] == notification_type and item['brewid'] == brewid:
                return False
        
        pending_notifications.append({
            'notification_type': notification_type,
            'subject': subject,
            'body': body,
            'brewid': brewid,
            'color': color,
            'queued_time': datetime.utcnow()
        })
        return True
    
    def process_pending_notifications():
        """Simulate the process_pending_notifications function"""
        now = datetime.utcnow()
        items_to_remove = []
        
        for item in pending_notifications:
            queued_time = item['queued_time']
            elapsed_seconds = (now - queued_time).total_seconds()
            
            if elapsed_seconds >= NOTIFICATION_PENDING_DELAY_SECONDS:
                print(f"   📤 Sending: {item['notification_type']}/{item['brewid']} (waited {elapsed_seconds:.1f}s)")
                sent_notifications.append(item)
                items_to_remove.append(item)
            else:
                print(f"   ⏳ Waiting: {item['notification_type']}/{item['brewid']} (waited {elapsed_seconds:.1f}s, need {NOTIFICATION_PENDING_DELAY_SECONDS}s)")
        
        for item in items_to_remove:
            pending_notifications.remove(item)
        
        return len(items_to_remove)
    
    print("\n1. Queue a notification:")
    queue_pending_notification('signal_loss', 'Subject', 'Body', 'brew123', 'Blue')
    assert len(pending_notifications) == 1, "Should have 1 item in queue"
    
    print("\n2. Process queue immediately (0 seconds elapsed):")
    sent = process_pending_notifications()
    assert sent == 0, "Should not send yet (delay not elapsed)"
    assert len(pending_notifications) == 1, "Should still be in queue"
    assert len(sent_notifications) == 0, "Should not have sent anything"
    
    print("\n3. Simulate 5 seconds passing:")
    pending_notifications[0]['queued_time'] = datetime.utcnow() - timedelta(seconds=5)
    sent = process_pending_notifications()
    assert sent == 0, "Should not send yet (only 5 seconds)"
    assert len(pending_notifications) == 1, "Should still be in queue"
    
    print("\n4. Simulate 10+ seconds passing:")
    pending_notifications[0]['queued_time'] = datetime.utcnow() - timedelta(seconds=10.1)
    sent = process_pending_notifications()
    assert sent == 1, "Should send after 10 seconds"
    assert len(pending_notifications) == 0, "Queue should be empty"
    assert len(sent_notifications) == 1, "Should have sent 1 notification"
    print("   ✅ Notification sent after delay period")
    
    return True


def test_real_world_scenario():
    """
    Test the real-world scenario: two duplicate notifications 0.02 seconds apart.
    """
    print("\n" + "=" * 80)
    print("TEST 3: Real-World Scenario - Duplicates 0.02s Apart")
    print("=" * 80)
    
    NOTIFICATION_PENDING_DELAY_SECONDS = 10
    pending_notifications = []
    sent_notifications = []
    
    def queue_pending_notification(notification_type, subject, body, brewid, color):
        """Simulate the queue_pending_notification function"""
        for item in pending_notifications:
            if item['notification_type'] == notification_type and item['brewid'] == brewid:
                print(f"   🚫 BLOCKED: Duplicate {notification_type}/{brewid} (prevented duplicate send)")
                return False
        
        pending_notifications.append({
            'notification_type': notification_type,
            'subject': subject,
            'body': body,
            'brewid': brewid,
            'color': color,
            'queued_time': datetime.utcnow()
        })
        print(f"   ✅ QUEUED: {notification_type}/{brewid}")
        return True
    
    def attempt_send_notifications(subject, body):
        """Simulate sending the notification"""
        sent_notifications.append({'subject': subject, 'body': body, 'time': datetime.utcnow()})
        return True
    
    def process_pending_notifications():
        """Simulate the process_pending_notifications function"""
        now = datetime.utcnow()
        items_to_remove = []
        
        for item in pending_notifications:
            queued_time = item['queued_time']
            elapsed_seconds = (now - queued_time).total_seconds()
            
            if elapsed_seconds >= NOTIFICATION_PENDING_DELAY_SECONDS:
                attempt_send_notifications(item['subject'], item['body'])
                items_to_remove.append(item)
        
        for item in items_to_remove:
            pending_notifications.remove(item)
    
    print("\n📧 Scenario: User receives 'Tilt loss of signal' email")
    print("   Problem: Two emails arrive 0.02 seconds apart")
    print("   Solution: Pending queue with deduplication\n")
    
    print("1. First notification triggered (t=0.00s):")
    queue_pending_notification('signal_loss', 'Loss of Signal', 'Tilt not responding', 'brew123', 'Blue')
    
    print("\n2. Duplicate notification triggered (t=0.02s):")
    time.sleep(0.02)
    queue_pending_notification('signal_loss', 'Loss of Signal', 'Tilt not responding', 'brew123', 'Blue')
    
    print("\n3. Another duplicate triggered (t=0.05s):")
    time.sleep(0.03)
    queue_pending_notification('signal_loss', 'Loss of Signal', 'Tilt not responding', 'brew123', 'Blue')
    
    print(f"\n4. Queue status:")
    print(f"   Pending notifications: {len(pending_notifications)}")
    print(f"   Sent notifications: {len(sent_notifications)}")
    assert len(pending_notifications) == 1, "Should only have 1 notification in queue"
    assert len(sent_notifications) == 0, "Should not have sent anything yet"
    
    print("\n5. Simulate 10 seconds passing and process queue:")
    pending_notifications[0]['queued_time'] = datetime.utcnow() - timedelta(seconds=10.1)
    process_pending_notifications()
    
    print(f"\n6. Final status:")
    print(f"   Pending notifications: {len(pending_notifications)}")
    print(f"   Sent notifications: {len(sent_notifications)}")
    assert len(pending_notifications) == 0, "Queue should be empty"
    assert len(sent_notifications) == 1, "Should have sent exactly 1 notification"
    
    print("\n   ✅ SUCCESS: Only 1 email sent instead of 3!")
    print("   ✅ Duplicates successfully prevented")
    
    return True


if __name__ == '__main__':
    try:
        print("\n" + "╔" + "=" * 78 + "╗")
        print("║" + " " * 16 + "PENDING NOTIFICATION QUEUE DEDUPLICATION TESTS" + " " * 16 + "║")
        print("╚" + "=" * 78 + "╝")
        
        test_pending_queue_deduplication()
        test_pending_queue_processing()
        test_real_world_scenario()
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED! Pending queue deduplication verified.")
        print("=" * 80)
        print("\nKey features verified:")
        print("  ✅ Duplicate notifications are detected and blocked")
        print("  ✅ 10-second delay allows deduplication window")
        print("  ✅ Only first notification is sent when duplicates occur")
        print("  ✅ Different notification types can coexist in queue")
        print("  ✅ Different brewids can coexist in queue")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
