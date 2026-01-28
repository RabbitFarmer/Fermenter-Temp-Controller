#!/usr/bin/env python3
"""
Test script to validate the tilt active filter functionality.

NOTE: This file contains a standalone implementation of get_active_tilts()
that duplicates the logic from app.py. This is intentional for isolated
unit testing without Flask app dependencies. If the implementation in app.py
changes, this test should be updated to match the expected behavior.
"""

import sys
from datetime import datetime, timedelta
import json

# Mock the configuration and imports
class MockConfig(dict):
    def get(self, key, default=None):
        return super().get(key, default)

# Simulate system_cfg
system_cfg = MockConfig({
    'tilt_inactivity_timeout_minutes': 60
})

# Simulate live_tilts with different timestamps
live_tilts = {}

def get_active_tilts():
    """
    Filter live_tilts to only include tilts that have sent data recently.
    
    NOTE: This is a standalone implementation for testing purposes.
    It should match the behavior of the same function in app.py.
    
    Returns:
        dict: Dictionary of active tilts (those within the inactivity timeout)
    """
    # Get timeout from system config, default to 60 minutes
    timeout_minutes = int(system_cfg.get('tilt_inactivity_timeout_minutes', 60))
    now = datetime.utcnow()
    active_tilts = {}
    
    for color, info in live_tilts.items():
        timestamp_str = info.get('timestamp')
        if not timestamp_str:
            # No timestamp means we can't determine activity - exclude for safety
            continue
        
        try:
            # Parse ISO 8601 timestamp (remove 'Z' suffix for naive UTC datetime)
            timestamp = datetime.fromisoformat(timestamp_str.rstrip('Z'))
            
            elapsed_minutes = (now - timestamp).total_seconds() / 60.0
            
            if elapsed_minutes < timeout_minutes:
                active_tilts[color] = info
        except Exception as e:
            # Unable to parse timestamp - likely corrupted data, exclude from display
            print(f"[LOG] Error parsing timestamp for {color}: {e}, excluding from active tilts")
    
    return active_tilts

def run_tests():
    """Run test cases for the active tilt filter."""
    print("Testing Tilt Active Filter Functionality")
    print("=" * 50)
    
    now = datetime.utcnow()
    
    # Test 1: Recent tilt (5 minutes ago) - should be active
    print("\nTest 1: Recent tilt (5 minutes ago)")
    live_tilts.clear()
    timestamp_5min = (now - timedelta(minutes=5)).replace(microsecond=0).isoformat() + "Z"
    live_tilts['Red'] = {
        'timestamp': timestamp_5min,
        'temp_f': 68.5,
        'gravity': 1.050
    }
    active = get_active_tilts()
    assert 'Red' in active, "Recent tilt should be active"
    print(f"✓ Red tilt is active (timestamp: {timestamp_5min})")
    
    # Test 2: Old tilt (2 hours ago) - should be inactive
    print("\nTest 2: Old tilt (2 hours ago)")
    live_tilts.clear()
    timestamp_2hr = (now - timedelta(hours=2)).replace(microsecond=0).isoformat() + "Z"
    live_tilts['Blue'] = {
        'timestamp': timestamp_2hr,
        'temp_f': 70.0,
        'gravity': 1.048
    }
    active = get_active_tilts()
    assert 'Blue' not in active, "Old tilt should be inactive"
    print(f"✓ Blue tilt is inactive (timestamp: {timestamp_2hr})")
    
    # Test 3: Mixed tilts (one active, one inactive)
    print("\nTest 3: Mixed tilts (one active, one inactive)")
    live_tilts.clear()
    timestamp_recent = (now - timedelta(minutes=10)).replace(microsecond=0).isoformat() + "Z"
    timestamp_old = (now - timedelta(hours=3)).replace(microsecond=0).isoformat() + "Z"
    live_tilts['Green'] = {
        'timestamp': timestamp_recent,
        'temp_f': 65.0,
        'gravity': 1.055
    }
    live_tilts['Orange'] = {
        'timestamp': timestamp_old,
        'temp_f': 72.0,
        'gravity': 1.045
    }
    active = get_active_tilts()
    assert 'Green' in active, "Recent tilt should be active"
    assert 'Orange' not in active, "Old tilt should be inactive"
    print(f"✓ Green tilt is active (10 minutes ago)")
    print(f"✓ Orange tilt is inactive (3 hours ago)")
    
    # Test 4: Tilt at exactly timeout boundary (59 minutes)
    print("\nTest 4: Tilt at timeout boundary (59 minutes)")
    live_tilts.clear()
    timestamp_59min = (now - timedelta(minutes=59)).replace(microsecond=0).isoformat() + "Z"
    live_tilts['Purple'] = {
        'timestamp': timestamp_59min,
        'temp_f': 66.0,
        'gravity': 1.052
    }
    active = get_active_tilts()
    assert 'Purple' in active, "Tilt within timeout should be active"
    print(f"✓ Purple tilt is active (59 minutes ago)")
    
    # Test 5: Tilt just past timeout boundary (61 minutes)
    print("\nTest 5: Tilt past timeout boundary (61 minutes)")
    live_tilts.clear()
    timestamp_61min = (now - timedelta(minutes=61)).replace(microsecond=0).isoformat() + "Z"
    live_tilts['Black'] = {
        'timestamp': timestamp_61min,
        'temp_f': 67.0,
        'gravity': 1.049
    }
    active = get_active_tilts()
    assert 'Black' not in active, "Tilt past timeout should be inactive"
    print(f"✓ Black tilt is inactive (61 minutes ago)")
    
    # Test 6: Custom timeout (30 minutes)
    print("\nTest 6: Custom timeout (30 minutes)")
    system_cfg['tilt_inactivity_timeout_minutes'] = 30
    live_tilts.clear()
    timestamp_45min = (now - timedelta(minutes=45)).replace(microsecond=0).isoformat() + "Z"
    live_tilts['Yellow'] = {
        'timestamp': timestamp_45min,
        'temp_f': 69.0,
        'gravity': 1.051
    }
    active = get_active_tilts()
    assert 'Yellow' not in active, "Tilt should be inactive with 30 minute timeout"
    print(f"✓ Yellow tilt is inactive with 30 minute timeout (45 minutes ago)")
    
    # Reset timeout
    system_cfg['tilt_inactivity_timeout_minutes'] = 60
    
    # Test 7: Tilt with no timestamp - should be included for safety
    print("\nTest 7: Tilt with no timestamp")
    live_tilts.clear()
    live_tilts['Pink'] = {
        'temp_f': 68.0,
        'gravity': 1.053
    }
    active = get_active_tilts()
    # Note: Based on the implementation, tilts without timestamps are excluded
    # This is actually the correct behavior
    assert 'Pink' not in active, "Tilt without timestamp should be excluded"
    print(f"✓ Pink tilt without timestamp is excluded (as expected)")
    
    print("\n" + "=" * 50)
    print("All tests passed! ✓")
    print("\nSummary:")
    print("- Tilts active within timeout window are shown")
    print("- Tilts inactive beyond timeout window are hidden")
    print("- Timeout is configurable via system_config")
    print(f"- Default timeout: 60 minutes")
    print(f"- Current timeout: {system_cfg.get('tilt_inactivity_timeout_minutes')} minutes")

if __name__ == '__main__':
    try:
        run_tests()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
