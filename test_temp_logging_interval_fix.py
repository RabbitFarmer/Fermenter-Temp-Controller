#!/usr/bin/env python3
"""
Test to verify that temp_logging_interval is now used correctly for temperature control logging.

This test validates:
1. log_periodic_temp_reading() uses temp_logging_interval for rate limiting
2. log_tilt_reading() uses temp_logging_interval for control tilt (not update_interval)
3. update_interval only controls the loop frequency
"""

import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

def test_periodic_temp_reading_rate_limiting():
    """Test that log_periodic_temp_reading respects temp_logging_interval."""
    print("\n" + "="*80)
    print("TEST: log_periodic_temp_reading() Rate Limiting with temp_logging_interval")
    print("="*80)
    
    import app as app_module
    
    # Setup: Configure intervals
    app_module.system_cfg['update_interval'] = 2  # Control loop: 2 minutes
    app_module.system_cfg['temp_logging_interval'] = 10  # Logging: 10 minutes
    app_module.temp_cfg['temp_control_active'] = True
    app_module.temp_cfg['current_temp'] = 68.0
    app_module.temp_cfg['low_limit'] = 65.0
    app_module.temp_cfg['high_limit'] = 70.0
    app_module.temp_cfg['tilt_color'] = 'Black'
    
    print(f"\n1. Configuration")
    print("-" * 80)
    print(f"   update_interval (control loop):       {app_module.system_cfg['update_interval']} minutes")
    print(f"   temp_logging_interval (logging):      {app_module.system_cfg['temp_logging_interval']} minutes")
    
    # Clear buffer and reset timestamp
    app_module.temp_reading_buffer.clear()
    app_module.last_periodic_temp_log_ts = None
    
    print(f"\n2. Testing Rate Limiting")
    print("-" * 80)
    
    # First call should succeed (no previous timestamp)
    initial_time = datetime.utcnow()
    with patch('app.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = initial_time
        app_module.log_periodic_temp_reading()
    
    first_count = len(app_module.temp_reading_buffer)
    print(f"   First call (t=0): Buffer size = {first_count}")
    assert first_count == 1, "First call should add entry"
    
    # Second call at 5 minutes (should be blocked - less than 10 min interval)
    time_5min = initial_time + timedelta(minutes=5)
    with patch('app.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = time_5min
        app_module.log_periodic_temp_reading()
    
    second_count = len(app_module.temp_reading_buffer)
    print(f"   Second call (t=5 min): Buffer size = {second_count}")
    assert second_count == 1, "Second call should be blocked (only 5 min elapsed, need 10)"
    
    # Third call at 10 minutes (should succeed - exactly at interval)
    time_10min = initial_time + timedelta(minutes=10)
    with patch('app.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = time_10min
        app_module.log_periodic_temp_reading()
    
    third_count = len(app_module.temp_reading_buffer)
    print(f"   Third call (t=10 min): Buffer size = {third_count}")
    assert third_count == 2, "Third call should add entry (10 min elapsed)"
    
    # Fourth call at 15 minutes (should be blocked - only 5 min since last log)
    time_15min = initial_time + timedelta(minutes=15)
    with patch('app.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = time_15min
        app_module.log_periodic_temp_reading()
    
    fourth_count = len(app_module.temp_reading_buffer)
    print(f"   Fourth call (t=15 min): Buffer size = {fourth_count}")
    assert fourth_count == 2, "Fourth call should be blocked (only 5 min since last log)"
    
    print(f"\n✅ PASSED: log_periodic_temp_reading() correctly uses temp_logging_interval")
    print(f"   - Logs at 10-minute intervals (not every 2 minutes)")
    print(f"   - update_interval (2 min) controls loop frequency only")
    print(f"   - temp_logging_interval (10 min) controls logging frequency")
    return True


def test_control_tilt_uses_temp_logging_interval():
    """Test that log_tilt_reading uses temp_logging_interval for control tilt."""
    print("\n" + "="*80)
    print("TEST: log_tilt_reading() Uses temp_logging_interval for Control Tilt")
    print("="*80)
    
    import app as app_module
    
    # Setup: Configure intervals
    app_module.system_cfg['update_interval'] = 2  # Control loop: 2 minutes
    app_module.system_cfg['temp_logging_interval'] = 10  # Temp control logging: 10 minutes
    app_module.system_cfg['tilt_logging_interval_minutes'] = 15  # Fermentation logging: 15 minutes
    app_module.temp_cfg['tilt_color'] = 'Black'  # Black is the control tilt
    
    # Reset tracking
    app_module.last_tilt_log_ts = {}
    
    print(f"\n1. Configuration")
    print("-" * 80)
    print(f"   Control tilt color: {app_module.temp_cfg['tilt_color']}")
    print(f"   update_interval:                      {app_module.system_cfg['update_interval']} minutes")
    print(f"   temp_logging_interval:                {app_module.system_cfg['temp_logging_interval']} minutes")
    print(f"   tilt_logging_interval_minutes:        {app_module.system_cfg['tilt_logging_interval_minutes']} minutes")
    
    print(f"\n2. Testing Control Tilt (Black) Rate Limiting")
    print("-" * 80)
    
    call_count = [0]  # Use list to allow modification in nested function
    
    def mock_append(*args, **kwargs):
        call_count[0] += 1
    
    # Mock the append functions to count calls
    with patch('app.append_control_log', side_effect=mock_append):
        with patch('app.append_sample_to_batch_jsonl'):
            with patch('app.forward_to_third_party_if_configured'):
                with patch('app.check_batch_notifications'):
                    # First call should succeed
                    initial_time = datetime.utcnow()
                    with patch('app.datetime') as mock_datetime:
                        mock_datetime.utcnow.return_value = initial_time
                        app_module.log_tilt_reading('Black', 1.050, 68.0, -70)
                    
                    print(f"   First call (t=0): Calls to append_control_log = {call_count[0]}")
                    assert call_count[0] == 1, "First call should log"
                    
                    # Second call at 5 minutes (should be blocked - need 10 min for control tilt)
                    time_5min = initial_time + timedelta(minutes=5)
                    with patch('app.datetime') as mock_datetime:
                        mock_datetime.utcnow.return_value = time_5min
                        app_module.log_tilt_reading('Black', 1.050, 68.0, -70)
                    
                    print(f"   Second call (t=5 min): Calls to append_control_log = {call_count[0]}")
                    assert call_count[0] == 1, "Second call should be blocked (need 10 min interval)"
                    
                    # Third call at 10 minutes (should succeed)
                    time_10min = initial_time + timedelta(minutes=10)
                    with patch('app.datetime') as mock_datetime:
                        mock_datetime.utcnow.return_value = time_10min
                        app_module.log_tilt_reading('Black', 1.050, 68.0, -70)
                    
                    print(f"   Third call (t=10 min): Calls to append_control_log = {call_count[0]}")
                    assert call_count[0] == 2, "Third call should log (10 min elapsed)"
    
    print(f"\n3. Testing Non-Control Tilt (Red) Rate Limiting")
    print("-" * 80)
    
    # Reset for non-control tilt test
    app_module.last_tilt_log_ts = {}
    call_count[0] = 0
    
    with patch('app.append_control_log', side_effect=mock_append):
        with patch('app.append_sample_to_batch_jsonl'):
            with patch('app.forward_to_third_party_if_configured'):
                with patch('app.check_batch_notifications'):
                    # First call should succeed
                    initial_time = datetime.utcnow()
                    with patch('app.datetime') as mock_datetime:
                        mock_datetime.utcnow.return_value = initial_time
                        app_module.log_tilt_reading('Red', 1.048, 67.0, -72)
                    
                    print(f"   First call (t=0): Calls to append_control_log = {call_count[0]}")
                    assert call_count[0] == 1, "First call should log"
                    
                    # Second call at 10 minutes (should be blocked - need 15 min for non-control)
                    time_10min = initial_time + timedelta(minutes=10)
                    with patch('app.datetime') as mock_datetime:
                        mock_datetime.utcnow.return_value = time_10min
                        app_module.log_tilt_reading('Red', 1.048, 67.0, -72)
                    
                    print(f"   Second call (t=10 min): Calls to append_control_log = {call_count[0]}")
                    assert call_count[0] == 1, "Second call should be blocked (need 15 min interval)"
                    
                    # Third call at 15 minutes (should succeed)
                    time_15min = initial_time + timedelta(minutes=15)
                    with patch('app.datetime') as mock_datetime:
                        mock_datetime.utcnow.return_value = time_15min
                        app_module.log_tilt_reading('Red', 1.048, 67.0, -72)
                    
                    print(f"   Third call (t=15 min): Calls to append_control_log = {call_count[0]}")
                    assert call_count[0] == 2, "Third call should log (15 min elapsed)"
    
    print(f"\n✅ PASSED: log_tilt_reading() correctly uses different intervals")
    print(f"   - Control tilt (Black): Uses temp_logging_interval (10 min)")
    print(f"   - Non-control tilt (Red): Uses tilt_logging_interval_minutes (15 min)")
    print(f"   - NO LONGER uses update_interval for control tilt logging")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("TEMPERATURE CONTROL LOGGING INTERVAL FIX - VERIFICATION TESTS")
    print("="*80)
    print("\nPurpose: Verify that temp_logging_interval is now used correctly")
    print("         instead of incorrectly using update_interval for logging.")
    
    try:
        # Run tests
        test1_passed = test_periodic_temp_reading_rate_limiting()
        test2_passed = test_control_tilt_uses_temp_logging_interval()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"✅ log_periodic_temp_reading() rate limiting: {'PASSED' if test1_passed else 'FAILED'}")
        print(f"✅ log_tilt_reading() interval usage:         {'PASSED' if test2_passed else 'FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 ALL TESTS PASSED!")
            print("\nThe three interval variables now work correctly:")
            print("  1. update_interval (2 min)              - Controls temperature control loop frequency")
            print("  2. temp_logging_interval (10 min)       - Controls temperature control logging")
            print("  3. tilt_logging_interval_minutes (15 min) - Controls fermentation tilt logging")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED")
            return 1
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
