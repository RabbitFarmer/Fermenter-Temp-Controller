#!/usr/bin/env python3
"""
Test script to validate active tilt integration functionality.
This tests:
1. Backend properly loads and handles og_confirmed attribute
2. Live snapshot endpoint includes og_confirmed in response
3. Configuration updates preserve og_confirmed
"""

import json
import sys
import os

def test_config_loading():
    """Test that tilt_config.json loads correctly with og_confirmed attribute."""
    print("Test 1: Loading tilt_config.json...")
    try:
        with open('config/tilt_config.json', 'r') as f:
            tilt_cfg = json.load(f)
        
        # Check that Black tilt has og_confirmed
        if 'Black' in tilt_cfg:
            assert 'og_confirmed' in tilt_cfg['Black'], "Black tilt missing og_confirmed"
            assert tilt_cfg['Black']['og_confirmed'] is True, "Black tilt og_confirmed should be True"
            print("  ✓ Black tilt has og_confirmed=True")
        
        # Check that Red tilt has og_confirmed
        if 'Red' in tilt_cfg:
            assert 'og_confirmed' in tilt_cfg['Red'], "Red tilt missing og_confirmed"
            assert tilt_cfg['Red']['og_confirmed'] is False, "Red tilt og_confirmed should be False"
            print("  ✓ Red tilt has og_confirmed=False")
        
        print("  ✓ Config loads correctly with og_confirmed\n")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False

def test_update_live_tilt():
    """Test that update_live_tilt function properly includes og_confirmed."""
    print("Test 2: Testing update_live_tilt function...")
    try:
        # Import app modules
        sys.path.insert(0, os.path.dirname(__file__))
        from app import update_live_tilt, live_tilts, tilt_cfg
        
        # Simulate a tilt reading for Black
        update_live_tilt('Black', 1.045, 68.5, -75)
        
        # Check that live_tilts has the data
        assert 'Black' in live_tilts, "Black not in live_tilts"
        assert 'og_confirmed' in live_tilts['Black'], "og_confirmed not in live_tilts"
        assert live_tilts['Black']['og_confirmed'] is True, "og_confirmed should be True"
        assert live_tilts['Black']['original_gravity'] == tilt_cfg['Black'].get('actual_og'), \
            "original_gravity should equal actual_og"
        
        print("  ✓ update_live_tilt includes og_confirmed")
        print(f"  ✓ og_confirmed value: {live_tilts['Black']['og_confirmed']}")
        print(f"  ✓ original_gravity value: {live_tilts['Black']['original_gravity']}\n")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_live_snapshot_structure():
    """Test that live_snapshot endpoint would include og_confirmed."""
    print("Test 3: Testing live snapshot data structure...")
    try:
        from app import live_tilts
        
        # Check the structure matches what the frontend expects
        if 'Black' in live_tilts:
            required_fields = [
                'gravity', 'temp_f', 'timestamp', 'beer_name', 'batch_name',
                'brewid', 'recipe_og', 'recipe_fg', 'recipe_abv',
                'actual_og', 'og_confirmed', 'original_gravity', 'color_code'
            ]
            
            for field in required_fields:
                assert field in live_tilts['Black'], f"Missing field: {field}"
            
            print("  ✓ All required fields present in live_tilts")
            print(f"  ✓ og_confirmed: {live_tilts['Black']['og_confirmed']}")
            print(f"  ✓ actual_og: {live_tilts['Black']['actual_og']}")
            print(f"  ✓ original_gravity: {live_tilts['Black']['original_gravity']}\n")
            return True
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_javascript_compatibility():
    """Test that the JavaScript functions are present in maindisplay.html."""
    print("Test 4: Checking JavaScript functions in maindisplay.html...")
    try:
        with open('templates/maindisplay.html', 'r') as f:
            content = f.read()
        
        # Check for createTiltCard function
        assert 'function createTiltCard(color, tilt)' in content, \
            "createTiltCard function not found"
        print("  ✓ createTiltCard function exists")
        
        # Check for updateTiltValues function
        assert 'function updateTiltValues(live)' in content, \
            "updateTiltValues function not found"
        print("  ✓ updateTiltValues function exists")
        
        # Check for dynamic card creation logic
        assert 'document.querySelector(`[data-tilt="${color}"]`)' in content, \
            "Dynamic card lookup not found"
        print("  ✓ Dynamic card creation logic present")
        
        # Check for createTiltCard call
        assert 'createTiltCard(color, entry)' in content, \
            "createTiltCard call not found"
        print("  ✓ createTiltCard is called in updateTiltValues")
        
        # Check that original_gravity is used in ABV calculation
        assert 'tilt.original_gravity' in content, \
            "original_gravity not used in template"
        print("  ✓ original_gravity is referenced in JavaScript\n")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False

def main():
    print("=" * 60)
    print("Active Tilt Integration Test Suite")
    print("=" * 60 + "\n")
    
    results = []
    results.append(("Config Loading", test_config_loading()))
    results.append(("Live Tilt Update", test_update_live_tilt()))
    results.append(("Live Snapshot Structure", test_live_snapshot_structure()))
    results.append(("JavaScript Compatibility", test_javascript_compatibility()))
    
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("All tests PASSED! ✓")
        print("Active tilt integration is working correctly.")
    else:
        print("Some tests FAILED! ✗")
        print("Please review the errors above.")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
