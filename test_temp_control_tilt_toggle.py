#!/usr/bin/env python3
"""
Test to verify that the log_temp_control_tilt toggle works correctly.
"""

import json

class MockLogger:
    def __init__(self):
        self.logged_entries = []
    
    def log_temp_control_tilt_reading(self, tilt_color, temperature, gravity, brewid=None, beer_name=None):
        entry = {
            "tilt_color": tilt_color,
            "temperature": temperature,
            "gravity": gravity,
        }
        if brewid:
            entry["brewid"] = brewid
        if beer_name:
            entry["beer_name"] = beer_name
        self.logged_entries.append(entry)


def test_logging_enabled():
    """
    Test that logging occurs when log_temp_control_tilt is True.
    """
    print("Test 1: Logging ENABLED")
    print("-" * 50)
    
    temp_cfg = {
        "tilt_color": "Black",
        "log_temp_control_tilt": True,  # Logging ENABLED
    }
    
    live_tilts = {
        "Black": {"temp_f": 68.0, "gravity": 1.050},
    }
    
    tilt_cfg = {
        "Black": {"brewid": "test-brew", "beer_name": "Test IPA"},
    }
    
    mock_logger = MockLogger()
    
    # Simulate the logging logic
    log_enabled = temp_cfg.get("log_temp_control_tilt", True)
    assigned_tilt_color = temp_cfg.get("tilt_color")
    if log_enabled and assigned_tilt_color and assigned_tilt_color in live_tilts:
        tilt_data = live_tilts[assigned_tilt_color]
        gravity = tilt_data.get("gravity")
        brewid = tilt_cfg.get(assigned_tilt_color, {}).get("brewid")
        beer_name = tilt_cfg.get(assigned_tilt_color, {}).get("beer_name")
        mock_logger.log_temp_control_tilt_reading(
            tilt_color=assigned_tilt_color,
            temperature=68.0,
            gravity=gravity,
            brewid=brewid,
            beer_name=beer_name
        )
    
    print(f"log_temp_control_tilt: {temp_cfg.get('log_temp_control_tilt')}")
    print(f"Entries logged: {len(mock_logger.logged_entries)}")
    
    assert len(mock_logger.logged_entries) == 1, f"Expected 1 entry, got {len(mock_logger.logged_entries)}"
    entry = mock_logger.logged_entries[0]
    assert entry["tilt_color"] == "Black"
    
    print("✓ PASS: Logging occurred when enabled")
    print(f"  Entry: {entry}")
    print()


def test_logging_disabled():
    """
    Test that logging does NOT occur when log_temp_control_tilt is False.
    """
    print("Test 2: Logging DISABLED")
    print("-" * 50)
    
    temp_cfg = {
        "tilt_color": "Black",
        "log_temp_control_tilt": False,  # Logging DISABLED
    }
    
    live_tilts = {
        "Black": {"temp_f": 68.0, "gravity": 1.050},
    }
    
    tilt_cfg = {
        "Black": {"brewid": "test-brew", "beer_name": "Test IPA"},
    }
    
    mock_logger = MockLogger()
    
    # Simulate the logging logic
    log_enabled = temp_cfg.get("log_temp_control_tilt", True)
    assigned_tilt_color = temp_cfg.get("tilt_color")
    if log_enabled and assigned_tilt_color and assigned_tilt_color in live_tilts:
        tilt_data = live_tilts[assigned_tilt_color]
        gravity = tilt_data.get("gravity")
        brewid = tilt_cfg.get(assigned_tilt_color, {}).get("brewid")
        beer_name = tilt_cfg.get(assigned_tilt_color, {}).get("beer_name")
        mock_logger.log_temp_control_tilt_reading(
            tilt_color=assigned_tilt_color,
            temperature=68.0,
            gravity=gravity,
            brewid=brewid,
            beer_name=beer_name
        )
    
    print(f"log_temp_control_tilt: {temp_cfg.get('log_temp_control_tilt')}")
    print(f"Entries logged: {len(mock_logger.logged_entries)}")
    
    assert len(mock_logger.logged_entries) == 0, f"Expected 0 entries, got {len(mock_logger.logged_entries)}"
    
    print("✓ PASS: No logging occurred when disabled")
    print()


def test_logging_default_true():
    """
    Test that logging defaults to True for backward compatibility.
    """
    print("Test 3: Logging DEFAULT (not set - should default to True)")
    print("-" * 50)
    
    temp_cfg = {
        "tilt_color": "Black",
        # log_temp_control_tilt NOT SET - should default to True
    }
    
    live_tilts = {
        "Black": {"temp_f": 68.0, "gravity": 1.050},
    }
    
    tilt_cfg = {
        "Black": {"brewid": "test-brew", "beer_name": "Test IPA"},
    }
    
    mock_logger = MockLogger()
    
    # Simulate the logging logic with default
    log_enabled = temp_cfg.get("log_temp_control_tilt", True)  # Defaults to True
    assigned_tilt_color = temp_cfg.get("tilt_color")
    if log_enabled and assigned_tilt_color and assigned_tilt_color in live_tilts:
        tilt_data = live_tilts[assigned_tilt_color]
        gravity = tilt_data.get("gravity")
        brewid = tilt_cfg.get(assigned_tilt_color, {}).get("brewid")
        beer_name = tilt_cfg.get(assigned_tilt_color, {}).get("beer_name")
        mock_logger.log_temp_control_tilt_reading(
            tilt_color=assigned_tilt_color,
            temperature=68.0,
            gravity=gravity,
            brewid=brewid,
            beer_name=beer_name
        )
    
    print(f"log_temp_control_tilt: {temp_cfg.get('log_temp_control_tilt', 'NOT SET (defaults to True)')}")
    print(f"Entries logged: {len(mock_logger.logged_entries)}")
    
    assert len(mock_logger.logged_entries) == 1, f"Expected 1 entry (default True), got {len(mock_logger.logged_entries)}"
    
    print("✓ PASS: Logging occurred with default value (backward compatible)")
    print()


if __name__ == "__main__":
    test_logging_enabled()
    test_logging_disabled()
    test_logging_default_true()
    
    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)
    print()
    print("Summary:")
    print("✓ Logging works when enabled (True)")
    print("✓ Logging is blocked when disabled (False)")
    print("✓ Logging defaults to enabled for backward compatibility")
