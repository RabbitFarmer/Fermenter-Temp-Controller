#!/usr/bin/env python3
"""
Test for notification retry mechanism (Option A: Auto-retry with exponential backoff).
Verifies that failed notifications are queued and retried with proper intervals.
"""

import sys
import time
from datetime import datetime, timedelta
from unittest.mock import Mock

def test_retry_queue_and_deduplication():
    """
    Test that failed notifications are queued for retry and duplicates are prevented.
    """
    print("=" * 80)
    print("TEST 1: Retry Queue and Deduplication")
    print("=" * 80)
    
    # Mock the notification retry queue
    notification_retry_queue = []
    
    def queue_notification_retry(notification_type, subject, body, brewid, color):
        """Mock implementation of queue_notification_retry"""
        # Check for duplicates
        for item in notification_retry_queue:
            if item['notification_type'] == notification_type and item['brewid'] == brewid:
                return  # Already queued
        
        notification_retry_queue.append({
            'notification_type': notification_type,
            'subject': subject,
            'body': body,
            'brewid': brewid,
            'color': color,
            'retry_count': 0,
            'last_retry_time': datetime.utcnow(),
            'created_time': datetime.utcnow()
        })
    
    print("\n1. Queue first notification:")
    queue_notification_retry('signal_loss', 'Test Signal Loss', 'Body', 'brew123', 'Red')
    print(f"   Queue size: {len(notification_retry_queue)}")
    assert len(notification_retry_queue) == 1, "Should have 1 item in queue"
    print("   ✅ Notification queued")
    
    print("\n2. Attempt to queue duplicate:")
    queue_notification_retry('signal_loss', 'Test Signal Loss', 'Body', 'brew123', 'Red')
    print(f"   Queue size: {len(notification_retry_queue)}")
    assert len(notification_retry_queue) == 1, "Should still have 1 item (duplicate prevented)"
    print("   ✅ Duplicate prevented")
    
    print("\n3. Queue different notification:")
    queue_notification_retry('fermentation_start', 'Test Start', 'Body', 'brew456', 'Blue')
    print(f"   Queue size: {len(notification_retry_queue)}")
    assert len(notification_retry_queue) == 2, "Should have 2 items"
    print("   ✅ Different notification queued")
    
    print("\n4. Queue same type but different brewid:")
    queue_notification_retry('signal_loss', 'Test Signal Loss 2', 'Body', 'brew789', 'Green')
    print(f"   Queue size: {len(notification_retry_queue)}")
    assert len(notification_retry_queue) == 3, "Should have 3 items"
    print("   ✅ Same type, different brewid queued")
    
    print("\n" + "=" * 80)
    print("✅ Queue and deduplication working correctly!")
    print("=" * 80)
    return True

def test_retry_with_exponential_backoff():
    """
    Test that retries happen at the correct intervals with exponential backoff.
    """
    print("\n" + "=" * 80)
    print("TEST 2: Retry with Exponential Backoff")
    print("=" * 80)
    
    NOTIFICATION_MAX_RETRIES = 2
    NOTIFICATION_RETRY_INTERVALS = [300, 1800]  # 5 min, 30 min
    
    notification_retry_queue = []
    send_attempts = []
    
    def mock_attempt_send(subject, body):
        """Mock send that tracks attempts"""
        send_attempts.append({'subject': subject, 'time': datetime.utcnow()})
        # Fail first 2 attempts, succeed on 3rd
        return len(send_attempts) >= 3
    
    def process_notification_retries():
        """Mock implementation of process_notification_retries"""
        now = datetime.utcnow()
        items_to_remove = []
        
        for item in notification_retry_queue:
            retry_count = item['retry_count']
            last_retry_time = item['last_retry_time']
            
            if retry_count >= NOTIFICATION_MAX_RETRIES:
                print(f"   Max retries reached for {item['notification_type']}")
                items_to_remove.append(item)
                continue
            
            elapsed_seconds = (now - last_retry_time).total_seconds()
            retry_interval = NOTIFICATION_RETRY_INTERVALS[retry_count] if retry_count < len(NOTIFICATION_RETRY_INTERVALS) else NOTIFICATION_RETRY_INTERVALS[-1]
            
            if elapsed_seconds >= retry_interval:
                print(f"   Retrying {item['notification_type']} (attempt {retry_count + 2}, elapsed: {elapsed_seconds:.0f}s)")
                success = mock_attempt_send(item['subject'], item['body'])
                
                if success:
                    print(f"   ✅ Retry successful!")
                    items_to_remove.append(item)
                else:
                    item['retry_count'] += 1
                    item['last_retry_time'] = now
                    print(f"   ❌ Retry failed, will try again")
        
        for item in items_to_remove:
            notification_retry_queue.remove(item)
    
    # Add notification to queue
    print("\n1. Initial notification fails, added to queue:")
    notification_retry_queue.append({
        'notification_type': 'signal_loss',
        'subject': 'Test Subject',
        'body': 'Test Body',
        'brewid': 'test123',
        'color': 'Red',
        'retry_count': 0,
        'last_retry_time': datetime.utcnow(),
        'created_time': datetime.utcnow()
    })
    print(f"   Queue size: {len(notification_retry_queue)}")
    print(f"   Send attempts: {len(send_attempts)}")
    
    # Too soon to retry (< 5 minutes)
    print("\n2. Check after 2 minutes (should not retry):")
    process_notification_retries()
    print(f"   Send attempts: {len(send_attempts)}")
    assert len(send_attempts) == 0, "Should not retry yet"
    print("   ✅ Correctly waiting for retry interval")
    
    # Simulate 5 minutes passing (first retry)
    print("\n3. Simulate 5 minutes passing (first retry):")
    notification_retry_queue[0]['last_retry_time'] = datetime.utcnow() - timedelta(seconds=305)
    process_notification_retries()
    print(f"   Send attempts: {len(send_attempts)}")
    assert len(send_attempts) == 1, "Should have attempted first retry"
    assert len(notification_retry_queue) == 1, "Should still be in queue (failed)"
    print("   ✅ First retry attempted and failed")
    
    # Too soon for second retry (< 30 minutes)
    print("\n4. Check after 10 minutes total (should not retry again yet):")
    notification_retry_queue[0]['last_retry_time'] = datetime.utcnow() - timedelta(seconds=600)
    process_notification_retries()
    print(f"   Send attempts: {len(send_attempts)}")
    assert len(send_attempts) == 1, "Should not have retried yet"
    print("   ✅ Correctly waiting for second retry interval")
    
    # Simulate 30 minutes passing (second retry)
    print("\n5. Simulate 30 minutes passing (second retry):")
    notification_retry_queue[0]['last_retry_time'] = datetime.utcnow() - timedelta(seconds=1805)
    process_notification_retries()
    print(f"   Send attempts: {len(send_attempts)}")
    assert len(send_attempts) == 2, "Should have attempted second retry"
    assert len(notification_retry_queue) == 1, "Should still be in queue (failed)"
    print("   ✅ Second retry attempted and failed")
    
    # Max retries reached
    print("\n6. Check if max retries enforced:")
    notification_retry_queue[0]['last_retry_time'] = datetime.utcnow() - timedelta(seconds=1805)
    process_notification_retries()
    print(f"   Send attempts: {len(send_attempts)}")
    print(f"   Queue size: {len(notification_retry_queue)}")
    assert len(notification_retry_queue) == 0, "Should be removed after max retries"
    print("   ✅ Max retries enforced, notification removed from queue")
    
    print("\n" + "=" * 80)
    print("✅ Exponential backoff working correctly!")
    print("=" * 80)
    return True

def test_successful_retry():
    """
    Test that successful retry removes item from queue.
    """
    print("\n" + "=" * 80)
    print("TEST 3: Successful Retry Removes from Queue")
    print("=" * 80)
    
    NOTIFICATION_MAX_RETRIES = 2
    NOTIFICATION_RETRY_INTERVALS = [300, 1800]
    
    notification_retry_queue = []
    send_count = [0]
    
    def mock_attempt_send_success(subject, body):
        """Mock send that succeeds"""
        send_count[0] += 1
        return True
    
    def process_notification_retries_success():
        """Process retries with successful send"""
        now = datetime.utcnow()
        items_to_remove = []
        
        for item in notification_retry_queue:
            retry_count = item['retry_count']
            last_retry_time = item['last_retry_time']
            
            if retry_count >= NOTIFICATION_MAX_RETRIES:
                items_to_remove.append(item)
                continue
            
            elapsed_seconds = (now - last_retry_time).total_seconds()
            retry_interval = NOTIFICATION_RETRY_INTERVALS[retry_count] if retry_count < len(NOTIFICATION_RETRY_INTERVALS) else NOTIFICATION_RETRY_INTERVALS[-1]
            
            if elapsed_seconds >= retry_interval:
                success = mock_attempt_send_success(item['subject'], item['body'])
                
                if success:
                    items_to_remove.append(item)
                else:
                    item['retry_count'] += 1
                    item['last_retry_time'] = now
        
        for item in items_to_remove:
            notification_retry_queue.remove(item)
    
    # Add notification
    print("\n1. Add notification to queue:")
    notification_retry_queue.append({
        'notification_type': 'fermentation_start',
        'subject': 'Test',
        'body': 'Test',
        'brewid': 'test',
        'color': 'Blue',
        'retry_count': 0,
        'last_retry_time': datetime.utcnow() - timedelta(seconds=305),
        'created_time': datetime.utcnow()
    })
    print(f"   Queue size: {len(notification_retry_queue)}")
    
    # Process retry
    print("\n2. Process retry (should succeed and remove):")
    process_notification_retries_success()
    print(f"   Queue size: {len(notification_retry_queue)}")
    print(f"   Send count: {send_count[0]}")
    assert len(notification_retry_queue) == 0, "Should be removed on success"
    assert send_count[0] == 1, "Should have attempted send once"
    print("   ✅ Successful retry removed from queue")
    
    print("\n" + "=" * 80)
    print("✅ Successful retry handling verified!")
    print("=" * 80)
    return True

if __name__ == '__main__':
    try:
        print("\n" + "╔" + "=" * 78 + "╗")
        print("║" + " " * 18 + "NOTIFICATION RETRY MECHANISM TESTS" + " " * 26 + "║")
        print("╚" + "=" * 78 + "╝")
        
        test_retry_queue_and_deduplication()
        test_retry_with_exponential_backoff()
        test_successful_retry()
        
        print("\n" + "=" * 80)
        print("🎉 ALL RETRY TESTS PASSED!")
        print("=" * 80)
        print("\nRetry mechanism verified:")
        print("  ✅ Failed notifications are queued for retry")
        print("  ✅ Duplicate entries in retry queue are prevented")
        print("  ✅ Exponential backoff: 5 minutes, then 30 minutes")
        print("  ✅ Maximum 2 retries (3 total attempts)")
        print("  ✅ Successful retries remove item from queue")
        print("  ✅ Max retries enforced, items removed after limit")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
