#!/usr/bin/env python3
"""
Integration test to verify the temperature control tilt reading timing fix.

This test simulates a realistic scenario where:
1. Fermentation tracking logs every 15 minutes (tilt_logging_interval_minutes)
2. Temperature control logs every 2 minutes (update_interval)
3. Both should work independently without interfering with each other
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the hardware dependencies
class MockBleakScanner:
    def __init__(self, callback):
        pass
    async def start(self):
        pass

sys.modules['bleak'] = type('MockBleak', (), {'BleakScanner': MockBleakScanner})()

# Import app after mocking
import app

def setup_test_environment():
    """Set up test environment"""
    os.makedirs('temp_control', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('batches', exist_ok=True)
    
    # Clear existing logs
    for log_file in ['logs/temp_control_tilt.jsonl', 'temp_control/temp_control_log.jsonl']:
        if os.path.exists(log_file):
            os.remove(log_file)
    
    # Configure system with different intervals
    app.system_cfg['tilt_logging_interval_minutes'] = 15  # Fermentation: 15 minutes
    app.system_cfg['update_interval'] = 2  # Temp control: 2 minutes
    
    # Configure temp control
    app.temp_cfg['temp_control_enabled'] = True
    app.temp_cfg['temp_control_active'] = True
    app.temp_cfg['enable_heating'] = True
    app.temp_cfg['tilt_color'] = 'Red'
    app.temp_cfg['low_limit'] = 65.0
    app.temp_cfg['high_limit'] = 70.0
    app.temp_cfg['current_temp'] = 67.5
    
    # Configure tilt
    app.tilt_cfg['Red'] = {
        'brewid': 'test-brew-123',
        'beer_name': 'Test IPA'
    }
    
    # Simulate live tilt data
    app.live_tilts['Red'] = {
        'temperature': 67.5,
        'gravity': 1.050,
        'last_seen': datetime.utcnow()
    }
    
    print("\n" + "="*80)
    print("TEMPERATURE CONTROL TIMING INTEGRATION TEST")
    print("="*80)
    print("\nConfiguration:")
    print(f"  - Fermentation tracking interval: {app.system_cfg['tilt_logging_interval_minutes']} minutes")
    print(f"  - Temperature control interval:   {app.system_cfg['update_interval']} minutes")
    print(f"  - Control tilt: {app.temp_cfg['tilt_color']}")
    print()

def test_scenario():
    """Test that both logging mechanisms work independently"""
    
    print("Test Scenario: Simulate 6 minutes of operation")
    print("-" * 80)
    
    # Reset timestamps
    app.last_temp_control_log_ts = None
    app.last_tilt_log_ts.clear()
    
    # Simulate time progression: 0, 2, 4, 6 minutes
    # At 2, 4, 6: temp control should log (every 2 min)
    # At 0: fermentation tracking should log (first time)
    # At 15+: fermentation tracking would log again (but not in this test window)
    
    log_file = 'logs/temp_control_tilt.jsonl'
    
    for minute in [0, 2, 4, 6]:
        print(f"\n[Minute {minute}] Running temperature control logic...")
        
        # Simulate time passing by adjusting last log timestamp
        if app.last_temp_control_log_ts is not None and minute > 0:
            app.last_temp_control_log_ts = datetime.utcnow() - timedelta(minutes=2)
        
        # Run temperature control logic
        app.temperature_control_logic()
        
        # Check log
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    latest = json.loads(lines[-1])
                    print(f"  ✓ Logged: timestamp={latest['timestamp']}, temp={latest['temperature']}, gravity={latest['gravity']}")
                else:
                    print(f"  - No log entries yet")
        else:
            print(f"  - Log file doesn't exist yet")
    
    print("\n" + "-" * 80)
    print("Verification:")
    print("-" * 80)
    
    # Verify logs
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
            total_entries = len(lines)
            
            print(f"\nTotal log entries: {total_entries}")
            print(f"Expected: 4 (one at 0, 2, 4, and 6 minutes)")
            
            if total_entries == 4:
                print("✓ PASS: Correct number of entries")
                
                # Verify all entries have correct format
                all_valid = True
                for i, line in enumerate(lines):
                    try:
                        entry = json.loads(line)
                        required_fields = ['timestamp', 'local_time', 'tilt_color', 'temperature', 'gravity']
                        if not all(field in entry for field in required_fields):
                            print(f"✗ FAIL: Entry {i+1} missing required fields")
                            all_valid = False
                        elif entry['tilt_color'] != 'Red':
                            print(f"✗ FAIL: Entry {i+1} has wrong tilt color: {entry['tilt_color']}")
                            all_valid = False
                    except json.JSONDecodeError:
                        print(f"✗ FAIL: Entry {i+1} is not valid JSON")
                        all_valid = False
                
                if all_valid:
                    print("✓ PASS: All entries have correct format")
                    return True
                else:
                    return False
            else:
                print(f"✗ FAIL: Expected 4 entries, got {total_entries}")
                return False
    else:
        print("✗ FAIL: Log file was not created")
        return False

def verify_independence():
    """Verify that temp control logging is independent of fermentation tracking"""
    print("\n" + "="*80)
    print("Verifying Independence of Logging Mechanisms")
    print("="*80)
    
    # Reset
    app.last_temp_control_log_ts = None
    app.last_tilt_log_ts.clear()
    log_file = 'logs/temp_control_tilt.jsonl'
    if os.path.exists(log_file):
        os.remove(log_file)
    
    print("\nScenario: Temperature control should log even if fermentation tracking doesn't")
    print("-" * 80)
    
    # Simulate fermentation tracking being blocked by rate limiting
    # But temp control should still log
    app.last_tilt_log_ts['Red'] = datetime.utcnow()  # Just logged, so blocked for 15 min
    
    # Run temp control (should log at 2-min interval)
    print("\n[Minute 0] First temp control cycle (should log)...")
    app.temperature_control_logic()
    
    time.sleep(0.1)  # Brief delay
    
    # Simulate 2 minutes passing
    app.last_temp_control_log_ts = datetime.utcnow() - timedelta(minutes=2)
    
    print("[Minute 2] Second temp control cycle (should log)...")
    app.temperature_control_logic()
    
    # Verify
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            entries = len(f.readlines())
            print(f"\nResult: {entries} temp control log entries")
            if entries == 2:
                print("✓ PASS: Temperature control logging is independent")
                return True
            else:
                print(f"✗ FAIL: Expected 2 entries, got {entries}")
                return False
    else:
        print("✗ FAIL: No log file created")
        return False

def main():
    setup_test_environment()
    
    # Run tests
    test1 = test_scenario()
    test2 = verify_independence()
    
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    
    if test1 and test2:
        print("\n✓ ALL TESTS PASSED")
        print("\nThe fix correctly implements:")
        print("  1. Temperature control tilt readings log at 2-minute interval")
        print("  2. Logging is independent of fermentation tracking (15-minute interval)")
        print("  3. Both mechanisms can operate simultaneously without interference")
        print()
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        print("\nPlease review the output above for details.")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
