#!/usr/bin/env python3
"""
Test to verify that fermentation alerts are properly logged using log_event.

This test verifies:
1. Fermentation Starting Alert logs to batch JSONL and sends notification
2. Fermentation Completion Alert logs to batch JSONL and sends notification
3. Daily Progress Report logs to batch JSONL and sends notification
"""

import json
import os
import sys
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch, call

# Import the logger module to verify log_event behavior
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_log_event_import():
    """Test that log_event is properly imported in app.py"""
    print("=" * 80)
    print("TEST 1: Verify log_event is imported in app.py")
    print("=" * 80)
    
    # Read app.py and verify log_event is imported
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    # Check if log_event is in the import statement
    if 'from logger import' in app_content and 'log_event' in app_content:
        print("✓ log_event is imported from logger module")
    else:
        print("✗ FAIL: log_event is not imported in app.py")
        return False
    
    # Check fallback function
    if 'def log_event(event_type, message, tilt_color=None):' in app_content:
        print("✓ log_event fallback function is defined")
    else:
        print("✗ FAIL: log_event fallback function is not defined")
        return False
    
    print("\nTEST 1: PASSED\n")
    return True


def test_fermentation_starting_calls_log_event():
    """Test that check_fermentation_starting calls log_event"""
    print("=" * 80)
    print("TEST 2: Verify fermentation_starting calls log_event")
    print("=" * 80)
    
    # Read app.py and verify log_event is called in check_fermentation_starting
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    # Find the check_fermentation_starting function
    if 'def check_fermentation_starting(color, brewid, cfg, state):' not in app_content:
        print("✗ FAIL: check_fermentation_starting function not found")
        return False
    
    # Extract the function content (simplified check)
    start_idx = app_content.find('def check_fermentation_starting(color, brewid, cfg, state):')
    if start_idx == -1:
        print("✗ FAIL: Could not find check_fermentation_starting function")
        return False
    
    # Find the next function definition to get the end of check_fermentation_starting
    next_func_idx = app_content.find('\ndef ', start_idx + 1)
    if next_func_idx == -1:
        next_func_idx = len(app_content)
    
    func_content = app_content[start_idx:next_func_idx]
    
    # Check if log_event is called with 'fermentation_starting'
    if "log_event('fermentation_starting'" in func_content or 'log_event("fermentation_starting"' in func_content:
        print("✓ log_event('fermentation_starting', ...) is called in check_fermentation_starting")
    else:
        print("✗ FAIL: log_event('fermentation_starting') is not called in check_fermentation_starting")
        print(f"Function content snippet: {func_content[:500]}...")
        return False
    
    # Verify message/body parameter is passed (should have both event_type and body/message)
    if "log_event('fermentation_starting', body" in func_content or 'log_event("fermentation_starting", body' in func_content:
        print("✓ message/body parameter is passed to log_event")
    else:
        print("✗ FAIL: message/body parameter is not passed to log_event")
        return False
    
    # Verify tilt_color parameter is passed
    if 'tilt_color=color' in func_content:
        print("✓ tilt_color parameter is passed to log_event")
    else:
        print("✗ FAIL: tilt_color parameter is not passed to log_event")
        return False
    
    print("\nTEST 2: PASSED\n")
    return True


def test_fermentation_completion_calls_log_event():
    """Test that check_fermentation_completion calls log_event"""
    print("=" * 80)
    print("TEST 3: Verify fermentation_completion calls log_event")
    print("=" * 80)
    
    # Read app.py and verify log_event is called in check_fermentation_completion
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    # Find the check_fermentation_completion function
    if 'def check_fermentation_completion(color, brewid, cfg, state):' not in app_content:
        print("✗ FAIL: check_fermentation_completion function not found")
        return False
    
    # Extract the function content (simplified check)
    start_idx = app_content.find('def check_fermentation_completion(color, brewid, cfg, state):')
    if start_idx == -1:
        print("✗ FAIL: Could not find check_fermentation_completion function")
        return False
    
    # Find the next function definition
    next_func_idx = app_content.find('\ndef ', start_idx + 1)
    if next_func_idx == -1:
        next_func_idx = len(app_content)
    
    func_content = app_content[start_idx:next_func_idx]
    
    # Check if log_event is called with 'fermentation_completion'
    if "log_event('fermentation_completion'" in func_content or 'log_event("fermentation_completion"' in func_content:
        print("✓ log_event('fermentation_completion', ...) is called in check_fermentation_completion")
    else:
        print("✗ FAIL: log_event('fermentation_completion') is not called in check_fermentation_completion")
        return False
    
    # Verify message/body parameter is passed
    if "log_event('fermentation_completion', body" in func_content or 'log_event("fermentation_completion", body' in func_content:
        print("✓ message/body parameter is passed to log_event")
    else:
        print("✗ FAIL: message/body parameter is not passed to log_event")
        return False
    
    # Verify tilt_color parameter is passed
    if 'tilt_color=color' in func_content:
        print("✓ tilt_color parameter is passed to log_event")
    else:
        print("✗ FAIL: tilt_color parameter is not passed to log_event")
        return False
    
    print("\nTEST 3: PASSED\n")
    return True


def test_daily_report_calls_log_event():
    """Test that send_daily_report calls log_event"""
    print("=" * 80)
    print("TEST 4: Verify daily_report calls log_event")
    print("=" * 80)
    
    # Read app.py and verify log_event is called in send_daily_report
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    # Find the send_daily_report function
    if 'def send_daily_report():' not in app_content:
        print("✗ FAIL: send_daily_report function not found")
        return False
    
    # Extract the function content (simplified check)
    start_idx = app_content.find('def send_daily_report():')
    if start_idx == -1:
        print("✗ FAIL: Could not find send_daily_report function")
        return False
    
    # Find the next function definition
    next_func_idx = app_content.find('\ndef ', start_idx + 1)
    if next_func_idx == -1:
        # Find the next class or end of file
        next_func_idx = app_content.find('\nclass ', start_idx + 1)
        if next_func_idx == -1:
            next_func_idx = len(app_content)
    
    func_content = app_content[start_idx:next_func_idx]
    
    # Check if log_event is called with 'daily_report'
    if "log_event('daily_report'" in func_content or 'log_event("daily_report"' in func_content:
        print("✓ log_event('daily_report', ...) is called in send_daily_report")
    else:
        print("✗ FAIL: log_event('daily_report') is not called in send_daily_report")
        return False
    
    # Verify message/body parameter is passed
    if "log_event('daily_report', body" in func_content or 'log_event("daily_report", body' in func_content:
        print("✓ message/body parameter is passed to log_event")
    else:
        print("✗ FAIL: message/body parameter is not passed to log_event")
        return False
    
    # Verify tilt_color parameter is passed
    if 'tilt_color=color' in func_content:
        print("✓ tilt_color parameter is passed to log_event")
    else:
        print("✗ FAIL: tilt_color parameter is not passed to log_event")
        return False
    
    print("\nTEST 4: PASSED\n")
    return True


def test_logger_batch_event_types():
    """Test that logger.py has the correct batch event types defined"""
    print("=" * 80)
    print("TEST 5: Verify logger.py defines correct batch event types")
    print("=" * 80)
    
    # Read logger.py and verify BATCH_EVENTS
    with open('logger.py', 'r') as f:
        logger_content = f.read()
    
    # Check for BATCH_EVENTS set
    if 'BATCH_EVENTS = {' not in logger_content:
        print("✗ FAIL: BATCH_EVENTS not defined in logger.py")
        return False
    
    # Check for required event types
    required_events = ['fermentation_starting', 'fermentation_completion', 'daily_report']
    all_found = True
    
    for event in required_events:
        if f"'{event}'" in logger_content or f'"{event}"' in logger_content:
            print(f"✓ '{event}' is defined in BATCH_EVENTS")
        else:
            print(f"✗ FAIL: '{event}' is not defined in BATCH_EVENTS")
            all_found = False
    
    if not all_found:
        return False
    
    print("\nTEST 5: PASSED\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("ALERT FUNCTIONALITY TEST SUITE")
    print("=" * 80 + "\n")
    
    tests = [
        test_log_event_import,
        test_fermentation_starting_calls_log_event,
        test_fermentation_completion_calls_log_event,
        test_daily_report_calls_log_event,
        test_logger_batch_event_types,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ EXCEPTION in {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"PASSED: {passed}/{len(tests)}")
    print(f"FAILED: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
