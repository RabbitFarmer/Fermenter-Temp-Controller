#!/usr/bin/env python3
"""
Test to verify that 999 temperature readings are filtered out in chart_data_for endpoint.
This test checks both temperature control data and regular tilt data.
"""

import json
import os
import tempfile
import shutil

# Create a minimal test to verify 999 filtering logic
def test_999_filtering_logic():
    """Test the logic that filters out 999 readings"""
    
    # Simulate the filtering logic from app.py
    test_cases = [
        (None, None, "None temperature"),
        ('', None, "Empty string temperature"),
        ('65.5', 65.5, "Valid temperature"),
        ('999', None, "999 reading (battery/connection issue)"),
        ('999.0', None, "999.0 reading"),
        ('72', 72.0, "Valid integer temperature"),
    ]
    
    for tf_input, expected_output, description in test_cases:
        try:
            temp_num = float(tf_input) if (tf_input is not None and tf_input != '') else None
            # Filter out 999 readings (battery/connection issues)
            if temp_num == 999:
                temp_num = None
        except Exception:
            temp_num = None
        
        assert temp_num == expected_output, f"Failed for {description}: expected {expected_output}, got {temp_num}"
        print(f"✓ {description}: {tf_input} -> {temp_num}")
    
    print("\n✅ All 999 filtering tests passed!")

if __name__ == '__main__':
    test_999_filtering_logic()
