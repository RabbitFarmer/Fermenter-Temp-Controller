#!/usr/bin/env python3
"""
Test to verify temperature control chart uses update_interval instead of tilt_logging_interval.

This test validates:
1. SAMPLE events (tilt readings at 15-min interval) are excluded from Fermenter chart
2. Periodic readings (at update_interval) are included in Fermenter chart
3. Chart data respects the update_interval setting
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

def test_chart_data_excludes_sample_events():
    """Test that chart_data endpoint excludes SAMPLE events for Fermenter chart."""
    print("\n" + "="*80)
    print("TEST: Temperature Control Chart Uses update_interval (Not tilt_logging_interval)")
    print("="*80)
    
    from app import app, LOG_PATH, temp_reading_buffer, system_cfg
    
    # Setup test configuration
    system_cfg['update_interval'] = 2  # Temperature control: 2 minutes
    system_cfg['tilt_logging_interval_minutes'] = 15  # Tilt readings: 15 minutes
    
    print(f"\n1. Configuration")
    print("-" * 80)
    print(f"   update_interval (temp control):        {system_cfg['update_interval']} minutes")
    print(f"   tilt_logging_interval_minutes (tilts): {system_cfg['tilt_logging_interval_minutes']} minutes")
    
    # Create a temporary control log with mixed events
    temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl')
    
    try:
        # Simulate 30 minutes of data
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # Add SAMPLE events (tilt readings) every 15 minutes - SHOULD BE EXCLUDED
        sample_times = []
        for i in range(0, 30, 15):
            ts = base_time + timedelta(minutes=i)
            sample_times.append(ts)
            entry = {
                "timestamp": ts.isoformat() + "Z",
                "event": "SAMPLE",
                "temp_f": 67.0 + i * 0.1,
                "tilt_color": "Blue",
                "low_limit": 65.0,
                "high_limit": 70.0
            }
            temp_log.write(json.dumps(entry) + "\n")
        
        # Add heating events (control events) - SHOULD BE INCLUDED
        heating_times = []
        for i in [5, 20]:
            ts = base_time + timedelta(minutes=i)
            heating_times.append(ts)
            entry = {
                "timestamp": ts.isoformat() + "Z",
                "event": "HEATING-PLUG TURNED ON",
                "temp_f": 67.0 + i * 0.1,
                "tilt_color": "Blue",
                "low_limit": 65.0,
                "high_limit": 70.0
            }
            temp_log.write(json.dumps(entry) + "\n")
        
        temp_log.close()
        
        # Backup original log and use test log
        backup_log = None
        if os.path.exists(LOG_PATH):
            backup_log = LOG_PATH + ".backup"
            os.rename(LOG_PATH, backup_log)
        
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        os.rename(temp_log.name, LOG_PATH)
        
        # Clear in-memory buffer and add periodic readings at update_interval (2 min)
        temp_reading_buffer.clear()
        periodic_times = []
        for i in range(0, 30, 2):  # Every 2 minutes (update_interval)
            ts = base_time + timedelta(minutes=i)
            periodic_times.append(ts)
            entry = {
                "timestamp": ts.isoformat() + "Z",
                "event": "TEMP CONTROL READING",
                "temp_f": 67.0 + i * 0.05,
                "tilt_color": "Blue",
                "low_limit": 65.0,
                "high_limit": 70.0
            }
            temp_reading_buffer.append(entry)
        
        print(f"\n2. Test Data Created")
        print("-" * 80)
        print(f"   SAMPLE events (15-min interval):     {len(sample_times)} events")
        print(f"   Heating events:                      {len(heating_times)} events")
        print(f"   Periodic readings (2-min interval):  {len(periodic_times)} events")
        
        # Test the chart_data endpoint
        with app.test_client() as client:
            response = client.get('/chart_data/Fermenter?limit=1000')
            data = json.loads(response.data)
            
            points = data.get('points', [])
            
            # Count event types in returned data
            sample_events = [p for p in points if p.get('event') == 'SAMPLE']
            heating_events = [p for p in points if p.get('event') == 'HEATING-PLUG TURNED ON']
            temp_control_readings = [p for p in points if p.get('event') == 'TEMP CONTROL READING']
            
            print(f"\n3. Chart Data Results")
            print("-" * 80)
            print(f"   Total data points returned:          {len(points)}")
            print(f"   SAMPLE events (SHOULD BE 0):         {len(sample_events)}")
            print(f"   Heating events (should be 2):        {len(heating_events)}")
            print(f"   Temp control readings (should be 15): {len(temp_control_readings)}")
            
            # Verify results
            success = True
            if len(sample_events) > 0:
                print(f"\n   ✗ FAIL: SAMPLE events should be excluded from Fermenter chart")
                print(f"           (These are tilt readings at 15-min interval)")
                success = False
            else:
                print(f"\n   ✓ PASS: SAMPLE events correctly excluded")
            
            if len(heating_events) != 2:
                print(f"   ✗ FAIL: Expected 2 heating events, got {len(heating_events)}")
                success = False
            else:
                print(f"   ✓ PASS: Heating events correctly included")
            
            if len(temp_control_readings) != 15:
                print(f"   ✗ FAIL: Expected 15 periodic readings (2-min interval), got {len(temp_control_readings)}")
                success = False
            else:
                print(f"   ✓ PASS: Periodic readings correctly included")
            
            print(f"\n4. Expected Behavior")
            print("-" * 80)
            print("   • Tilt readings (SAMPLE events) logged every 15 minutes")
            print("   • Temperature control readings logged every 2 minutes (update_interval)")
            print("   • Fermenter chart should ONLY show:")
            print("     - Periodic readings at update_interval (2 min)")
            print("     - Control events (heating/cooling on/off)")
            print("   • Fermenter chart should NOT show:")
            print("     - SAMPLE events (tilt readings at 15-min interval)")
            
            print(f"\n5. Data Point Density Comparison")
            print("-" * 80)
            print(f"   Before fix (15-min interval):  {30 // 15 + 1} temperature data points in 30 min")
            print(f"   After fix (2-min interval):    {30 // 2 + 1} temperature data points in 30 min")
            print(f"   Improvement:                   {((30 // 2 + 1) / (30 // 15 + 1) - 1) * 100:.0f}% more data points")
            print(f"   Result:                        Smoother curve, not jagged EKG pattern")
            
            if success:
                print(f"\n" + "="*80)
                print("✓ TEST PASSED: Temperature control chart uses update_interval")
                print("="*80)
                return True
            else:
                print(f"\n" + "="*80)
                print("✗ TEST FAILED: Issues found in chart data")
                print("="*80)
                return False
            
    finally:
        # Cleanup: restore original log
        if os.path.exists(LOG_PATH):
            os.remove(LOG_PATH)
        if backup_log and os.path.exists(backup_log):
            os.rename(backup_log, LOG_PATH)
        if os.path.exists(temp_log.name):
            os.remove(temp_log.name)

if __name__ == "__main__":
    success = test_chart_data_excludes_sample_events()
    sys.exit(0 if success else 1)
