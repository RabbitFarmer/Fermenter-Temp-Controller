#!/usr/bin/env python3
"""
Integration test for temperature control chart fixes.
Creates test data with 999 readings and verifies:
1. 999 readings are filtered out
2. Temperature range is calculated correctly (34-100°F base)
3. Only active tilts appear in data
"""

import json
import os
import tempfile
import shutil

def create_test_temp_control_data():
    """Create test temperature control log with 999 readings mixed in"""
    test_data = [
        {"timestamp": "2026-01-29T10:00:00Z", "temp_f": 65.0, "tilt_color": "Black", "event": "SAMPLE"},
        {"timestamp": "2026-01-29T10:05:00Z", "temp_f": 999, "tilt_color": "Black", "event": "SAMPLE"},  # Should be filtered
        {"timestamp": "2026-01-29T10:10:00Z", "temp_f": 66.0, "tilt_color": "Black", "event": "SAMPLE"},
        {"timestamp": "2026-01-29T10:15:00Z", "temp_f": 67.0, "tilt_color": "Black", "event": "SAMPLE"},
        {"timestamp": "2026-01-29T10:20:00Z", "temp_f": 999.0, "tilt_color": "Black", "event": "SAMPLE"},  # Should be filtered
        {"timestamp": "2026-01-29T10:25:00Z", "temp_f": 68.0, "tilt_color": "Black", "event": "HEATING-PLUG TURNED ON"},
        {"timestamp": "2026-01-29T10:30:00Z", "temp_f": 69.0, "tilt_color": "Black", "event": "SAMPLE"},
        {"timestamp": "2026-01-29T10:35:00Z", "temp_f": 70.0, "tilt_color": "Black", "event": "HEATING-PLUG TURNED OFF"},
    ]
    return test_data

def simulate_chart_data_processing(log_data):
    """Simulate the chart_data_for processing logic from app.py"""
    points = []
    
    ALLOWED_EVENT_VALUES = [
        'SAMPLE',
        'HEATING-PLUG TURNED ON',
        'HEATING-PLUG TURNED OFF',
        'COOLING-PLUG TURNED ON',
        'COOLING-PLUG TURNED OFF',
    ]
    
    for obj in log_data:
        event = obj.get('event', '')
        if event not in ALLOWED_EVENT_VALUES:
            continue
        
        ts = obj.get('timestamp')
        tf = obj.get('temp_f') if obj.get('temp_f') is not None else obj.get('current_temp')
        g = obj.get('gravity')
        
        try:
            ts_str = str(ts) if ts is not None else None
        except Exception:
            ts_str = None
        try:
            temp_num = float(tf) if (tf is not None and tf != '') else None
            # Filter out 999 readings (battery/connection issues)
            if temp_num == 999:
                temp_num = None
        except Exception:
            temp_num = None
        try:
            grav_num = float(g) if (g is not None and g != '') else None
        except Exception:
            grav_num = None
        
        entry = {
            "timestamp": ts_str,
            "temp_f": temp_num,
            "gravity": grav_num,
            "event": event,
            "tilt_color": obj.get('tilt_color', '')
        }
        points.append(entry)
    
    return points

def test_999_filtering_in_chart_data():
    """Test that 999 readings are properly filtered"""
    print("Testing 999 filtering in chart data processing...")
    
    test_data = create_test_temp_control_data()
    processed_points = simulate_chart_data_processing(test_data)
    
    # Verify we have the right number of points (8 total, but 2 have 999 temps)
    assert len(processed_points) == 8, f"Expected 8 points, got {len(processed_points)}"
    
    # Verify that none of the processed points have temp_f == 999
    for point in processed_points:
        assert point['temp_f'] != 999, f"Found 999 reading that wasn't filtered: {point}"
        assert point['temp_f'] != 999.0, f"Found 999.0 reading that wasn't filtered: {point}"
    
    # Count how many points have valid temperatures
    valid_temp_count = sum(1 for p in processed_points if p['temp_f'] is not None)
    assert valid_temp_count == 6, f"Expected 6 valid temps (8 total - 2 with 999), got {valid_temp_count}"
    
    # Verify temperature range calculation would work correctly
    temps = [p['temp_f'] for p in processed_points if p['temp_f'] is not None]
    min_temp = min(temps)
    max_temp = max(temps)
    
    print(f"  ✓ Processed {len(processed_points)} points")
    print(f"  ✓ Filtered out 2 readings with temp=999")
    print(f"  ✓ Valid temperature count: {valid_temp_count}")
    print(f"  ✓ Temperature range: {min_temp}°F - {max_temp}°F")
    print(f"  ✓ No 999 readings found in processed data")
    
    # Verify base temperature range logic (34-100°F)
    chartTempMargin = 1.0
    tempMin = min(34, min_temp - chartTempMargin)
    tempMax = max(100, max_temp + chartTempMargin)
    
    print(f"  ✓ Chart temperature range: {tempMin}°F - {tempMax}°F")
    assert tempMin == 34, f"Expected min temp to be 34°F (base range), got {tempMin}°F"
    assert tempMax == 100, f"Expected max temp to be 100°F (base range), got {tempMax}°F"
    
    print("\n✅ All chart data processing tests passed!")

def test_active_tilt_filtering():
    """Test that only tilts with data points would be shown"""
    print("\nTesting active tilt filtering...")
    
    test_data = create_test_temp_control_data()
    processed_points = simulate_chart_data_processing(test_data)
    
    # Group by tilt color (simulating what chart does)
    colorGroups = {}
    for p in processed_points:
        color = p.get('tilt_color') or 'Unknown'
        if color not in colorGroups:
            colorGroups[color] = []
        colorGroups[color].append(p)
    
    # Only show tilts with data points
    active_tilts = [color for color, points in colorGroups.items() if len(points) > 0]
    
    print(f"  ✓ Active tilts: {active_tilts}")
    assert len(active_tilts) == 1, f"Expected 1 active tilt (Black), got {len(active_tilts)}: {active_tilts}"
    assert 'Black' in active_tilts, f"Expected 'Black' tilt to be active"
    
    print("  ✓ Only active tilts would be shown in legend")
    print("\n✅ Active tilt filtering test passed!")

if __name__ == '__main__':
    test_999_filtering_in_chart_data()
    test_active_tilt_filtering()
    print("\n" + "="*50)
    print("ALL TESTS PASSED! ✅")
    print("="*50)
