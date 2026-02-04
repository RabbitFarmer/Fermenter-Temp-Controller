#!/usr/bin/env python3
"""
Test to verify that temperature control tilt readings are logged at update_interval
instead of tilt_logging_interval_minutes.

This test simulates the scenario where:
- A tilt is assigned to temperature control
- The tilt sends readings every few seconds (via BLE)
- log_tilt_reading() should rate-limit based on update_interval (2 min) for control tilt
- log_tilt_reading() should rate-limit based on tilt_logging_interval_minutes (15 min) for other tilts
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_test_environment(app_module):
    """Setup test environment with known configuration."""
    # Set system config
    app_module.system_cfg['update_interval'] = 2  # 2 minutes for temp control
    app_module.system_cfg['tilt_logging_interval_minutes'] = 15  # 15 minutes for fermentation
    
    # Setup temp control config with Black tilt assigned
    app_module.temp_cfg['tilt_color'] = 'Black'
    app_module.temp_cfg['temp_control_enabled'] = True
    app_module.temp_cfg['enable_heating'] = True
    
    # Setup tilt config for Black and Red tilts
    app_module.tilt_cfg['Black'] = {
        'brewid': 'test-black-001',
        'beer_name': 'Test Beer Black'
    }
    app_module.tilt_cfg['Red'] = {
        'brewid': 'test-red-001',
        'beer_name': 'Test Beer Red'
    }
    
    # Clear last log timestamps
    app_module.last_tilt_log_ts.clear()
    
    # Ensure log directory exists
    os.makedirs('temp_control', exist_ok=True)
    
    # Clear the control log for clean test
    if os.path.exists(app_module.LOG_PATH):
        os.remove(app_module.LOG_PATH)

def read_control_log(app_module):
    """Read all entries from the control log."""
    if not os.path.exists(app_module.LOG_PATH):
        return []
    
    entries = []
    with open(app_module.LOG_PATH, 'r') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries

def test_control_tilt_interval(app_module):
    """Test that control tilt logs at update_interval (2 min)."""
    print("\n=== Testing Temperature Control Tilt Interval ===")
    
    setup_test_environment(app_module)
    
    # Simulate tilt readings for Black tilt (assigned to temp control)
    print("\nSimulating Black tilt readings (assigned to temp control)...")
    
    # First reading - should log immediately
    app_module.log_tilt_reading('Black', 1.050, 68.0, -75)
    time.sleep(0.1)
    
    entries = read_control_log(app_module)
    print(f"After 1st reading: {len(entries)} entries")
    assert len(entries) == 1, f"Expected 1 entry after first reading, got {len(entries)}"
    
    # Second reading at 1 minute - should NOT log (interval is 2 min)
    print("Simulating reading at 1 minute - should NOT log")
    app_module.last_tilt_log_ts['Black'] = datetime.utcnow() - timedelta(minutes=1)
    app_module.log_tilt_reading('Black', 1.050, 68.1, -75)
    time.sleep(0.1)
    
    entries = read_control_log(app_module)
    print(f"After 2nd reading (1 min): {len(entries)} entries")
    assert len(entries) == 1, f"Expected 1 entry (no new log), got {len(entries)}"
    
    # Third reading at 2 minutes - SHOULD log (interval is 2 min)
    print("Simulating reading at 2 minutes - SHOULD log")
    app_module.last_tilt_log_ts['Black'] = datetime.utcnow() - timedelta(minutes=2)
    app_module.log_tilt_reading('Black', 1.050, 68.2, -75)
    time.sleep(0.1)
    
    entries = read_control_log(app_module)
    print(f"After 3rd reading (2 min): {len(entries)} entries")
    assert len(entries) == 2, f"Expected 2 entries, got {len(entries)}"
    
    # Verify both entries are for Black tilt
    for entry in entries:
        assert entry['tilt_color'] == 'Black', f"Expected Black tilt, got {entry['tilt_color']}"
        assert entry['event'] == 'SAMPLE', f"Expected SAMPLE event, got {entry['event']}"
    
    print("✓ PASS: Control tilt logs at 2-minute interval")
    return True

def test_non_control_tilt_interval(app_module):
    """Test that non-control tilt logs at tilt_logging_interval_minutes (15 min)."""
    print("\n=== Testing Non-Control Tilt Interval ===")
    
    setup_test_environment(app_module)
    
    # Simulate tilt readings for Red tilt (NOT assigned to temp control)
    print("\nSimulating Red tilt readings (NOT assigned to temp control)...")
    
    # First reading - should log immediately
    app_module.log_tilt_reading('Red', 1.055, 70.0, -70)
    time.sleep(0.1)
    
    entries = read_control_log(app_module)
    red_entries = [e for e in entries if e['tilt_color'] == 'Red']
    print(f"After 1st reading: {len(red_entries)} Red entries")
    assert len(red_entries) == 1, f"Expected 1 Red entry after first reading, got {len(red_entries)}"
    
    # Second reading at 2 minutes - should NOT log (interval is 15 min for non-control tilts)
    print("Simulating reading at 2 minutes - should NOT log")
    app_module.last_tilt_log_ts['Red'] = datetime.utcnow() - timedelta(minutes=2)
    app_module.log_tilt_reading('Red', 1.055, 70.1, -70)
    time.sleep(0.1)
    
    entries = read_control_log(app_module)
    red_entries = [e for e in entries if e['tilt_color'] == 'Red']
    print(f"After 2nd reading (2 min): {len(red_entries)} Red entries")
    assert len(red_entries) == 1, f"Expected 1 Red entry (no new log), got {len(red_entries)}"
    
    # Third reading at 15 minutes - SHOULD log (interval is 15 min)
    print("Simulating reading at 15 minutes - SHOULD log")
    app_module.last_tilt_log_ts['Red'] = datetime.utcnow() - timedelta(minutes=15)
    app_module.log_tilt_reading('Red', 1.055, 70.2, -70)
    time.sleep(0.1)
    
    entries = read_control_log(app_module)
    red_entries = [e for e in entries if e['tilt_color'] == 'Red']
    print(f"After 3rd reading (15 min): {len(red_entries)} Red entries")
    assert len(red_entries) == 2, f"Expected 2 Red entries, got {len(red_entries)}"
    
    print("✓ PASS: Non-control tilt logs at 15-minute interval")
    return True

def test_mixed_tilt_intervals(app_module):
    """Test that both tilts log at their respective intervals simultaneously."""
    print("\n=== Testing Mixed Tilt Intervals ===")
    
    setup_test_environment(app_module)
    
    # Log both tilts at the same time
    print("\nLogging Black (control) and Red (fermentation) tilts...")
    app_module.log_tilt_reading('Black', 1.050, 68.0, -75)
    app_module.log_tilt_reading('Red', 1.055, 70.0, -70)
    time.sleep(0.1)
    
    entries = read_control_log(app_module)
    print(f"Initial: {len(entries)} total entries")
    assert len(entries) == 2, f"Expected 2 entries, got {len(entries)}"
    
    # After 2 minutes, only Black should log (not Red)
    print("\nAfter 2 minutes - only Black should log")
    app_module.last_tilt_log_ts['Black'] = datetime.utcnow() - timedelta(minutes=2)
    app_module.last_tilt_log_ts['Red'] = datetime.utcnow() - timedelta(minutes=2)
    app_module.log_tilt_reading('Black', 1.050, 68.1, -75)
    app_module.log_tilt_reading('Red', 1.055, 70.1, -70)
    time.sleep(0.1)
    
    entries = read_control_log(app_module)
    black_entries = [e for e in entries if e['tilt_color'] == 'Black']
    red_entries = [e for e in entries if e['tilt_color'] == 'Red']
    print(f"After 2 min: {len(black_entries)} Black, {len(red_entries)} Red")
    assert len(black_entries) == 2, f"Expected 2 Black entries, got {len(black_entries)}"
    assert len(red_entries) == 1, f"Expected 1 Red entry, got {len(red_entries)}"
    
    # After 15 minutes, both should log
    print("\nAfter 15 minutes - both should log")
    app_module.last_tilt_log_ts['Black'] = datetime.utcnow() - timedelta(minutes=15)
    app_module.last_tilt_log_ts['Red'] = datetime.utcnow() - timedelta(minutes=15)
    app_module.log_tilt_reading('Black', 1.050, 68.2, -75)
    app_module.log_tilt_reading('Red', 1.055, 70.2, -70)
    time.sleep(0.1)
    
    entries = read_control_log(app_module)
    black_entries = [e for e in entries if e['tilt_color'] == 'Black']
    red_entries = [e for e in entries if e['tilt_color'] == 'Red']
    print(f"After 15 min: {len(black_entries)} Black, {len(red_entries)} Red")
    assert len(black_entries) == 3, f"Expected 3 Black entries, got {len(black_entries)}"
    assert len(red_entries) == 2, f"Expected 2 Red entries, got {len(red_entries)}"
    
    print("✓ PASS: Mixed tilt intervals work correctly")
    return True

def main():
    """Run all tests."""
    print("=" * 70)
    print("Temperature Control Tilt Refresh Interval Test")
    print("=" * 70)
    
    try:
        # Import app module
        from app import (log_tilt_reading, LOG_PATH, system_cfg, temp_cfg, 
                        tilt_cfg, last_tilt_log_ts)
        
        # Create a simple namespace to pass around
        class AppModule:
            pass
        
        app_module = AppModule()
        app_module.log_tilt_reading = log_tilt_reading
        app_module.LOG_PATH = LOG_PATH
        app_module.system_cfg = system_cfg
        app_module.temp_cfg = temp_cfg
        app_module.tilt_cfg = tilt_cfg
        app_module.last_tilt_log_ts = last_tilt_log_ts
        
        # Run tests
        test_control_tilt_interval(app_module)
        test_non_control_tilt_interval(app_module)
        test_mixed_tilt_intervals(app_module)
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nSummary:")
        print("- Control tilt (Black) logs at update_interval (2 min) ✓")
        print("- Non-control tilt (Red) logs at tilt_logging_interval (15 min) ✓")
        print("- Both intervals work independently ✓")
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
