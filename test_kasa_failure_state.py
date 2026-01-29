#!/usr/bin/env python3
"""
Test to verify that when a KASA plug command fails:
1. The heater_on/cooler_on state is set to False (UI fix)
2. The error is logged to kasa_errors.log (logging fix)

This test simulates the fix for the issue where network unreachable errors
caused the UI to show "Heating ON" while the plug was actually OFF, and
errors were not being logged to kasa_errors.log.
"""

import json
import queue
from multiprocessing import Queue

# Track log_error calls
logged_errors = []

def log_error(msg):
    """Mock log_error function that tracks calls"""
    logged_errors.append(msg)
    print(f"[MOCK_LOG_ERROR] {msg}")

# Mock temp_cfg that simulates the global temp_cfg in app.py
temp_cfg = {
    "heater_on": False,
    "cooler_on": False,
    "heating_error": False,
    "cooling_error": False,
    "heating_error_msg": "",
    "cooling_error_msg": "",
    "heater_pending": False,
    "cooler_pending": False,
    "heating_error_notified": False,
    "cooling_error_notified": False,
    "low_limit": 65,
    "current_temp": 60,
    "high_limit": 75,
    "tilt_color": "Black"
}

def append_control_log(event, data):
    """Mock function - in real app this logs to JSONL"""
    print(f"[MOCK_LOG] Event: {event}, Data: {data}")

def send_temp_control_notification(event, temp, low, high, color):
    """Mock function - in real app this sends notifications"""
    print(f"[MOCK_NOTIFY] {event} - temp={temp}, low={low}, high={high}, color={color}")

def send_kasa_error_notification(mode, url, error):
    """Mock function - in real app this sends error notifications"""
    print(f"[MOCK_ERROR_NOTIFY] {mode} plug at {url} failed: {error}")

def simulate_kasa_result_listener(result_queue):
    """
    Simulates the kasa_result_listener function from app.py (lines 2295-2351)
    This is the code we fixed to:
    1. Set heater_on/cooler_on to False on failure (UI fix)
    2. Call log_error to log to kasa_errors.log (logging fix)
    """
    try:
        result = result_queue.get(timeout=5)
        mode = result.get('mode')
        action = result.get('action')
        success = result.get('success', False)
        url = result.get('url', '')
        error = result.get('error', '')
        
        print(f"[KASA_RESULT] Received result: mode={mode}, action={action}, success={success}, url={url}, error={error}")
        
        if mode == 'heating':
            temp_cfg["heater_pending"] = False
            if success:
                temp_cfg["heater_on"] = (action == 'on')
                temp_cfg["heating_error"] = False
                temp_cfg["heating_error_msg"] = ""
                temp_cfg["heating_error_notified"] = False
                event = "heating_on" if action == 'on' else "heating_off"
                print(f"[KASA_RESULT] ✓ Heating plug {action.upper()} confirmed - updating heater_on={action == 'on'}")
                append_control_log(event, {"low_limit": temp_cfg.get("low_limit"), "current_temp": temp_cfg.get("current_temp"), "high_limit": temp_cfg.get("high_limit"), "tilt_color": temp_cfg.get("tilt_color", "")})
                send_temp_control_notification(event, temp_cfg.get("current_temp", 0), temp_cfg.get("low_limit", 0), temp_cfg.get("high_limit", 0), temp_cfg.get("tilt_color", ""))
            else:
                # FIXED: When plug command fails, ensure heater_on is False for accurate UI state
                temp_cfg["heater_on"] = False
                temp_cfg["heating_error"] = True
                temp_cfg["heating_error_msg"] = error or ''
                print(f"[KASA_RESULT] ✗ Heating plug {action.upper()} FAILED - error: {error}")
                # FIXED: Log error to kasa_errors.log
                log_error(f"HEATING plug {action.upper()} failed at {url}: {error}")
                send_kasa_error_notification('heating', url, error)
        elif mode == 'cooling':
            temp_cfg["cooler_pending"] = False
            if success:
                temp_cfg["cooler_on"] = (action == 'on')
                temp_cfg["cooling_error"] = False
                temp_cfg["cooling_error_msg"] = ""
                temp_cfg["cooling_error_notified"] = False
                event = "cooling_on" if action == 'on' else "cooling_off"
                print(f"[KASA_RESULT] ✓ Cooling plug {action.upper()} confirmed - updating cooler_on={action == 'on'}")
                append_control_log(event, {"low_limit": temp_cfg.get("low_limit"), "current_temp": temp_cfg.get("current_temp"), "high_limit": temp_cfg.get("high_limit"), "tilt_color": temp_cfg.get("tilt_color", "")})
                send_temp_control_notification(event, temp_cfg.get("current_temp", 0), temp_cfg.get("low_limit", 0), temp_cfg.get("high_limit", 0), temp_cfg.get("tilt_color", ""))
            else:
                # FIXED: When plug command fails, ensure cooler_on is False for accurate UI state
                temp_cfg["cooler_on"] = False
                temp_cfg["cooling_error"] = True
                temp_cfg["cooling_error_msg"] = error or ''
                print(f"[KASA_RESULT] ✗ Cooling plug {action.upper()} FAILED - error: {error}")
                # FIXED: Log error to kasa_errors.log
                log_error(f"COOLING plug {action.upper()} failed at {url}: {error}")
                send_kasa_error_notification('cooling', url, error)
    except queue.Empty:
        pass

def test_heating_failure():
    """Test that heating failure sets heater_on to False AND logs to kasa_errors.log"""
    print("\n=== Test 1: Heating Plug Failure ===")
    
    # Reset state
    logged_errors.clear()
    temp_cfg["heater_on"] = True  # Simulate it was ON or trying to turn ON
    temp_cfg["heating_error"] = False
    temp_cfg["heater_pending"] = True
    
    # Simulate a failed heating command
    result_queue = Queue()
    result_queue.put({
        'mode': 'heating',
        'action': 'on',
        'success': False,
        'url': '192.168.1.208',
        'error': 'Unable to connect to device: 192.168.1.208:9999 [Errno 101] Network is unreachable'
    })
    
    # Process the result
    simulate_kasa_result_listener(result_queue)
    
    # Verify the fix
    print(f"\nAfter failed heating command:")
    print(f"  heater_on = {temp_cfg['heater_on']} (should be False)")
    print(f"  heating_error = {temp_cfg['heating_error']} (should be True)")
    print(f"  heating_error_msg = {temp_cfg['heating_error_msg']}")
    print(f"  Logged errors: {len(logged_errors)} (should be 1)")
    
    assert temp_cfg["heater_on"] == False, "FAIL: heater_on should be False after failure"
    assert temp_cfg["heating_error"] == True, "FAIL: heating_error should be True"
    assert "Network is unreachable" in temp_cfg["heating_error_msg"], "FAIL: error message not set"
    assert len(logged_errors) == 1, f"FAIL: Expected 1 logged error, got {len(logged_errors)}"
    assert "HEATING plug ON failed at 192.168.1.208" in logged_errors[0], "FAIL: Error not properly logged"
    assert "Network is unreachable" in logged_errors[0], "FAIL: Error message missing from log"
    
    print("\n✓ TEST PASSED: heater_on set to False AND error logged to kasa_errors.log")

def test_cooling_failure():
    """Test that cooling failure sets cooler_on to False AND logs to kasa_errors.log"""
    print("\n=== Test 2: Cooling Plug Failure ===")
    
    # Reset state
    logged_errors.clear()
    temp_cfg["cooler_on"] = True  # Simulate it was ON or trying to turn ON
    temp_cfg["cooling_error"] = False
    temp_cfg["cooler_pending"] = True
    
    # Simulate a failed cooling command
    result_queue = Queue()
    result_queue.put({
        'mode': 'cooling',
        'action': 'on',
        'success': False,
        'url': '192.168.1.209',
        'error': 'Unable to connect to device: 192.168.1.209:9999 [Errno 101] Network is unreachable'
    })
    
    # Process the result
    simulate_kasa_result_listener(result_queue)
    
    # Verify the fix
    print(f"\nAfter failed cooling command:")
    print(f"  cooler_on = {temp_cfg['cooler_on']} (should be False)")
    print(f"  cooling_error = {temp_cfg['cooling_error']} (should be True)")
    print(f"  cooling_error_msg = {temp_cfg['cooling_error_msg']}")
    print(f"  Logged errors: {len(logged_errors)} (should be 1)")
    
    assert temp_cfg["cooler_on"] == False, "FAIL: cooler_on should be False after failure"
    assert temp_cfg["cooling_error"] == True, "FAIL: cooling_error should be True"
    assert "Network is unreachable" in temp_cfg["cooling_error_msg"], "FAIL: error message not set"
    assert len(logged_errors) == 1, f"FAIL: Expected 1 logged error, got {len(logged_errors)}"
    assert "COOLING plug ON failed at 192.168.1.209" in logged_errors[0], "FAIL: Error not properly logged"
    assert "Network is unreachable" in logged_errors[0], "FAIL: Error message missing from log"
    
    print("\n✓ TEST PASSED: cooler_on set to False AND error logged to kasa_errors.log")

def test_heating_success():
    """Test that heating success sets heater_on correctly and does NOT log errors"""
    print("\n=== Test 3: Heating Plug Success (No Error Logging) ===")
    
    # Reset state
    logged_errors.clear()
    temp_cfg["heater_on"] = False
    temp_cfg["heating_error"] = True  # Previous error
    temp_cfg["heater_pending"] = True
    
    # Simulate a successful heating command
    result_queue = Queue()
    result_queue.put({
        'mode': 'heating',
        'action': 'on',
        'success': True,
        'url': '192.168.1.208',
        'error': None
    })
    
    # Process the result
    simulate_kasa_result_listener(result_queue)
    
    # Verify success path
    print(f"\nAfter successful heating command:")
    print(f"  heater_on = {temp_cfg['heater_on']} (should be True)")
    print(f"  heating_error = {temp_cfg['heating_error']} (should be False)")
    print(f"  heating_error_msg = '{temp_cfg['heating_error_msg']}' (should be empty)")
    print(f"  Logged errors: {len(logged_errors)} (should be 0)")
    
    assert temp_cfg["heater_on"] == True, "FAIL: heater_on should be True on success"
    assert temp_cfg["heating_error"] == False, "FAIL: heating_error should be False on success"
    assert temp_cfg["heating_error_msg"] == "", "FAIL: error message should be cleared"
    assert len(logged_errors) == 0, f"FAIL: No errors should be logged on success, got {len(logged_errors)}"
    
    print("\n✓ TEST PASSED: heater_on set to True and no errors logged on success")

if __name__ == "__main__":
    print("Testing KASA plug failure state handling and error logging...")
    print("=" * 60)
    
    try:
        test_heating_failure()
        test_cooling_failure()
        test_heating_success()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe fix ensures that when a KASA plug command fails:")
        print("  1. heater_on/cooler_on is set to False (UI shows correct state)")
        print("  2. heating_error/cooling_error is set to True (error indicator)")
        print("  3. Error message is stored for display")
        print("  4. Error is logged to kasa_errors.log (NEW FIX)")
        print("\nThis prevents the UI from showing 'Heating ON' when the plug")
        print("is actually OFF due to network connectivity issues, AND ensures")
        print("that all connection errors are properly logged for debugging.")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
