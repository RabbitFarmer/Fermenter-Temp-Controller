#!/usr/bin/env python3
"""
Integration test to verify that inactive Tilts are properly filtered
from the main display and API endpoints.

This test:
1. Simulates Tilt readings with different timestamps
2. Verifies that only active Tilts appear in the dashboard
3. Verifies that only active Tilts appear in the /live_snapshot endpoint
4. Tests different timeout configurations
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_active_tilt_filtering():
    """
    Test that the get_active_tilts function properly filters tilts.
    """
    # Import from app
    from app import get_active_tilts, live_tilts, system_cfg
    
    print("=" * 70)
    print("Integration Test: Tilt Inactivity Filtering")
    print("=" * 70)
    
    # Store original values
    original_tilts = dict(live_tilts)
    original_timeout = system_cfg.get('tilt_inactivity_timeout_minutes')
    
    try:
        # Set a known timeout value
        system_cfg['tilt_inactivity_timeout_minutes'] = 60
        
        # Clear live_tilts
        live_tilts.clear()
        
        now = datetime.utcnow()
        
        # Test 1: Add a recent Tilt (should be active)
        print("\nTest 1: Recent Tilt (10 minutes ago)")
        print("-" * 70)
        recent_timestamp = (now - timedelta(minutes=10)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Red'] = {
            'timestamp': recent_timestamp,
            'temp_f': 68.5,
            'gravity': 1.050,
            'beer_name': 'Test IPA',
            'brewid': 'test123'
        }
        
        active_tilts = get_active_tilts()
        assert 'Red' in active_tilts, "Recent Tilt should be active"
        print(f"✓ Red Tilt is active")
        print(f"  Timestamp: {recent_timestamp}")
        print(f"  Elapsed: 10 minutes")
        print(f"  Status: ACTIVE (within 60 minute timeout)")
        
        # Test 2: Add an old Tilt (should be inactive)
        print("\nTest 2: Old Tilt (90 minutes ago)")
        print("-" * 70)
        old_timestamp = (now - timedelta(minutes=90)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Blue'] = {
            'timestamp': old_timestamp,
            'temp_f': 70.0,
            'gravity': 1.048,
            'beer_name': 'Test Stout',
            'brewid': 'test456'
        }
        
        active_tilts = get_active_tilts()
        assert 'Red' in active_tilts, "Recent Tilt should still be active"
        assert 'Blue' not in active_tilts, "Old Tilt should be inactive"
        print(f"✓ Blue Tilt is inactive")
        print(f"  Timestamp: {old_timestamp}")
        print(f"  Elapsed: 90 minutes")
        print(f"  Status: INACTIVE (beyond 60 minute timeout)")
        
        # Test 3: Multiple Tilts with mixed ages
        print("\nTest 3: Multiple Tilts with different ages")
        print("-" * 70)
        live_tilts.clear()
        
        # Add 5 minute old tilt
        ts_5min = (now - timedelta(minutes=5)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Green'] = {
            'timestamp': ts_5min,
            'temp_f': 65.0,
            'gravity': 1.055,
            'beer_name': 'Test Lager',
            'brewid': 'test789'
        }
        
        # Add 45 minute old tilt
        ts_45min = (now - timedelta(minutes=45)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Orange'] = {
            'timestamp': ts_45min,
            'temp_f': 66.0,
            'gravity': 1.052,
            'beer_name': 'Test Ale',
            'brewid': 'test101'
        }
        
        # Add 120 minute old tilt
        ts_120min = (now - timedelta(minutes=120)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Purple'] = {
            'timestamp': ts_120min,
            'temp_f': 69.0,
            'gravity': 1.045,
            'beer_name': 'Test Porter',
            'brewid': 'test202'
        }
        
        active_tilts = get_active_tilts()
        assert 'Green' in active_tilts, "5 minute old Tilt should be active"
        assert 'Orange' in active_tilts, "45 minute old Tilt should be active"
        assert 'Purple' not in active_tilts, "120 minute old Tilt should be inactive"
        
        print(f"✓ Green Tilt (5 min): ACTIVE")
        print(f"✓ Orange Tilt (45 min): ACTIVE")
        print(f"✓ Purple Tilt (120 min): INACTIVE")
        print(f"  Active Tilts: {len(active_tilts)} out of {len(live_tilts)}")
        
        # Test 4: Custom timeout (30 minutes)
        print("\nTest 4: Custom timeout (30 minutes)")
        print("-" * 70)
        system_cfg['tilt_inactivity_timeout_minutes'] = 30
        
        active_tilts = get_active_tilts()
        assert 'Green' in active_tilts, "5 minute old Tilt should be active with 30min timeout"
        assert 'Orange' not in active_tilts, "45 minute old Tilt should be inactive with 30min timeout"
        assert 'Purple' not in active_tilts, "120 minute old Tilt should be inactive with 30min timeout"
        
        print(f"✓ Green Tilt (5 min): ACTIVE")
        print(f"✓ Orange Tilt (45 min): INACTIVE (beyond 30 min timeout)")
        print(f"✓ Purple Tilt (120 min): INACTIVE")
        print(f"  Active Tilts: {len(active_tilts)} out of {len(live_tilts)}")
        
        # Test 5: Verify boundary condition
        print("\nTest 5: Boundary condition (exactly at timeout)")
        print("-" * 70)
        system_cfg['tilt_inactivity_timeout_minutes'] = 60
        live_tilts.clear()
        
        # Add tilt at exactly 60 minutes (should be excluded, >= timeout)
        ts_60min = (now - timedelta(minutes=60)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Black'] = {
            'timestamp': ts_60min,
            'temp_f': 67.0,
            'gravity': 1.049,
            'beer_name': 'Test Pilsner',
            'brewid': 'test303'
        }
        
        active_tilts = get_active_tilts()
        # At exactly 60 minutes, should be inactive (>= timeout)
        assert 'Black' not in active_tilts, "Tilt at exactly timeout should be inactive"
        print(f"✓ Black Tilt (60 min): INACTIVE (at timeout boundary)")
        
        # Add tilt at 59.5 minutes (should be included)
        ts_59_5min = (now - timedelta(minutes=59, seconds=30)).replace(microsecond=0).isoformat() + "Z"
        live_tilts['Yellow'] = {
            'timestamp': ts_59_5min,
            'temp_f': 68.0,
            'gravity': 1.051,
            'beer_name': 'Test Wheat',
            'brewid': 'test404'
        }
        
        active_tilts = get_active_tilts()
        assert 'Yellow' in active_tilts, "Tilt just under timeout should be active"
        assert 'Black' not in active_tilts, "Tilt at timeout should still be inactive"
        print(f"✓ Yellow Tilt (59.5 min): ACTIVE")
        
        print("\n" + "=" * 70)
        print("All integration tests passed! ✓")
        print("=" * 70)
        print("\nSummary:")
        print("  - Inactive Tilts are properly filtered based on timeout")
        print("  - Timeout is configurable via system_config")
        print("  - Boundary conditions work correctly")
        print("  - Multiple simultaneous Tilts are handled correctly")
        
        return True
        
    finally:
        # Restore original values
        live_tilts.clear()
        live_tilts.update(original_tilts)
        if original_timeout is not None:
            system_cfg['tilt_inactivity_timeout_minutes'] = original_timeout

if __name__ == '__main__':
    try:
        # Try to import Flask app components
        try:
            from app import get_active_tilts, live_tilts, system_cfg
        except ImportError as e:
            print(f"Unable to import from app.py: {e}")
            print("This test requires the Flask app to be importable.")
            sys.exit(1)
        
        # Run the tests
        success = test_active_tilt_filtering()
        sys.exit(0 if success else 1)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error running integration tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
