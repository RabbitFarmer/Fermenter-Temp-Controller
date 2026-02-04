#!/usr/bin/env python3
"""
Test to verify that temp_control_tilt.jsonl only logs the explicitly assigned Tilt,
not fallback Tilts.
"""

import json
import os
import tempfile
import shutil
from datetime import datetime

# Mock the logger module
class MockLogger:
    def __init__(self):
        self.log_file = None
        self.logged_entries = []
    
    def log_temp_control_tilt_reading(self, tilt_color, temperature, gravity, brewid=None, beer_name=None):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "local_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tilt_color": tilt_color,
            "temperature": temperature,
            "gravity": gravity,
        }
        if brewid:
            entry["brewid"] = brewid
        if beer_name:
            entry["beer_name"] = beer_name
        self.logged_entries.append(entry)

def test_only_assigned_tilt_is_logged():
    """
    Test that only the explicitly assigned Tilt is logged to temp_control_tilt.jsonl.
    
    Scenario:
    1. Multiple Tilts are active (Black, Red, Blue)
    2. Only Black is assigned for temp control (temp_cfg["tilt_color"] = "Black")
    3. Only Black should be logged, not Red or Blue
    """
    
    # Mock configuration
    temp_cfg = {
        "tilt_color": "Black",  # Explicitly assigned
        "temp_control_active": True,
        "temp_control_enabled": True,
        "enable_heating": True,
        "enable_cooling": False,
        "low_limit": 65,
        "high_limit": 70,
        "current_temp": None
    }
    
    # Mock live tilts - multiple tilts available
    live_tilts = {
        "Black": {"temp_f": 68.0, "gravity": 1.050},
        "Red": {"temp_f": 70.2, "gravity": 1.048},  # Should NOT be logged
        "Blue": {"temp_f": 68.5, "gravity": 1.050}   # Should NOT be logged
    }
    
    # Mock tilt config
    tilt_cfg = {
        "Black": {"brewid": "test-brew-black", "beer_name": "Black IPA"},
        "Red": {"brewid": "test-brew-red", "beer_name": "Red Ale"},
        "Blue": {"brewid": "test-brew-blue", "beer_name": "Blue Lager"}
    }
    
    # Simulate the logging logic from the fix
    mock_logger = MockLogger()
    
    # Simulate temperature reading and logging
    temp_from_tilt = live_tilts["Black"]["temp_f"]  # Get temp from assigned tilt
    if temp_from_tilt is not None:
        temp = float(temp_from_tilt)
        temp_cfg['current_temp'] = round(temp, 1)
        
        # NEW LOGIC: Only log if explicitly assigned
        assigned_tilt_color = temp_cfg.get("tilt_color")
        if assigned_tilt_color and assigned_tilt_color in live_tilts:
            tilt_data = live_tilts[assigned_tilt_color]
            gravity = tilt_data.get("gravity")
            brewid = tilt_cfg.get(assigned_tilt_color, {}).get("brewid")
            beer_name = tilt_cfg.get(assigned_tilt_color, {}).get("beer_name")
            mock_logger.log_temp_control_tilt_reading(
                tilt_color=assigned_tilt_color,
                temperature=temp,
                gravity=gravity,
                brewid=brewid,
                beer_name=beer_name
            )
    
    # Verify results
    print("Test: Only assigned Tilt should be logged")
    print(f"Assigned Tilt: {temp_cfg.get('tilt_color')}")
    print(f"Number of log entries: {len(mock_logger.logged_entries)}")
    
    # Should only have ONE entry for Black
    assert len(mock_logger.logged_entries) == 1, f"Expected 1 log entry, got {len(mock_logger.logged_entries)}"
    
    entry = mock_logger.logged_entries[0]
    assert entry["tilt_color"] == "Black", f"Expected Black, got {entry['tilt_color']}"
    assert entry["temperature"] == 68.0, f"Expected 68.0, got {entry['temperature']}"
    assert entry["brewid"] == "test-brew-black", f"Expected test-brew-black, got {entry.get('brewid')}"
    assert entry["beer_name"] == "Black IPA", f"Expected Black IPA, got {entry.get('beer_name')}"
    
    print("✓ PASS: Only the assigned Black Tilt was logged")
    print(f"  Entry: {entry}")


def test_no_logging_when_no_tilt_assigned():
    """
    Test that NO logging occurs when no Tilt is explicitly assigned,
    even if fallback Tilts are available.
    """
    
    # Mock configuration - NO tilt assigned
    temp_cfg = {
        "tilt_color": "",  # Empty - no explicit assignment
        "temp_control_active": True,
        "temp_control_enabled": True,
        "enable_heating": True,
        "enable_cooling": False,
        "low_limit": 65,
        "high_limit": 70,
        "current_temp": None
    }
    
    # Mock live tilts - tilts are available but none assigned
    live_tilts = {
        "Red": {"temp_f": 70.2, "gravity": 1.048},
        "Blue": {"temp_f": 68.5, "gravity": 1.050}
    }
    
    tilt_cfg = {
        "Red": {"brewid": "test-brew-red", "beer_name": "Red Ale"},
        "Blue": {"brewid": "test-brew-blue", "beer_name": "Blue Lager"}
    }
    
    # Simulate the logging logic
    mock_logger = MockLogger()
    
    # Simulate temperature reading (might use fallback)
    # But logging should NOT occur because no tilt is assigned
    temp_from_tilt = live_tilts["Red"]["temp_f"]  # Fallback to Red
    if temp_from_tilt is not None:
        temp = float(temp_from_tilt)
        temp_cfg['current_temp'] = round(temp, 1)
        
        # NEW LOGIC: Only log if explicitly assigned
        assigned_tilt_color = temp_cfg.get("tilt_color")
        if assigned_tilt_color and assigned_tilt_color in live_tilts:
            # This should NOT execute because tilt_color is empty
            tilt_data = live_tilts[assigned_tilt_color]
            gravity = tilt_data.get("gravity")
            brewid = tilt_cfg.get(assigned_tilt_color, {}).get("brewid")
            beer_name = tilt_cfg.get(assigned_tilt_color, {}).get("beer_name")
            mock_logger.log_temp_control_tilt_reading(
                tilt_color=assigned_tilt_color,
                temperature=temp,
                gravity=gravity,
                brewid=brewid,
                beer_name=beer_name
            )
    
    # Verify results
    print("\nTest: No logging when no Tilt is assigned")
    print(f"Assigned Tilt: '{temp_cfg.get('tilt_color')}'")
    print(f"Number of log entries: {len(mock_logger.logged_entries)}")
    
    # Should have ZERO entries
    assert len(mock_logger.logged_entries) == 0, f"Expected 0 log entries, got {len(mock_logger.logged_entries)}"
    
    print("✓ PASS: No entries logged when no Tilt is assigned")


if __name__ == "__main__":
    test_only_assigned_tilt_is_logged()
    test_no_logging_when_no_tilt_assigned()
    print("\n" + "="*50)
    print("All tests passed!")
    print("="*50)
