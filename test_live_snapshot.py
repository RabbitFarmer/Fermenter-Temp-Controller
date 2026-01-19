#!/usr/bin/env python3
"""
End-to-end test for the live_snapshot endpoint.
This starts a Flask test client and validates the endpoint response.
"""

import json
import sys
import os

def test_live_snapshot_endpoint():
    """Test the /live_snapshot endpoint returns correct data."""
    print("=" * 60)
    print("Testing /live_snapshot endpoint")
    print("=" * 60 + "\n")
    
    try:
        # Import app
        sys.path.insert(0, os.path.dirname(__file__))
        from app import app, update_live_tilt
        
        # Create a test client
        with app.test_client() as client:
            # Simulate some tilt data
            update_live_tilt('Black', 1.045, 68.5, -75)
            update_live_tilt('Red', 1.058, 70.2, -72)
            
            # Call the endpoint
            response = client.get('/live_snapshot')
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            print("✓ Endpoint returns 200 OK")
            
            data = response.get_json()
            assert data is not None, "Response should be JSON"
            print("✓ Response is valid JSON")
            
            # Check structure
            assert 'live_tilts' in data, "Missing live_tilts"
            assert 'temp_control' in data, "Missing temp_control"
            print("✓ Response has required top-level keys")
            
            # Check Black tilt data
            if 'Black' in data['live_tilts']:
                black = data['live_tilts']['Black']
                
                # Check all required fields
                required_fields = [
                    'gravity', 'temp_f', 'timestamp', 'beer_name', 'batch_name',
                    'brewid', 'recipe_og', 'recipe_fg', 'recipe_abv',
                    'actual_og', 'og_confirmed', 'original_gravity', 'color_code'
                ]
                
                for field in required_fields:
                    assert field in black, f"Missing field: {field}"
                
                print("✓ Black tilt has all required fields")
                
                # Validate og_confirmed is present and correct type
                assert isinstance(black['og_confirmed'], bool), \
                    f"og_confirmed should be bool, got {type(black['og_confirmed'])}"
                print(f"✓ og_confirmed is boolean: {black['og_confirmed']}")
                
                # Validate original_gravity matches actual_og from config
                assert black['original_gravity'] == black['actual_og'], \
                    "original_gravity should match actual_og"
                print(f"✓ original_gravity ({black['original_gravity']}) matches actual_og ({black['actual_og']})")
                
                # Check other values
                assert black['gravity'] == 1.045, f"Expected gravity 1.045, got {black['gravity']}"
                assert black['temp_f'] == 68.5, f"Expected temp_f 68.5, got {black['temp_f']}"
                print("✓ Gravity and temperature values are correct")
                
                # Pretty print the Black tilt data
                print("\nBlack Tilt Data:")
                print(json.dumps(black, indent=2))
            
            print("\n" + "=" * 60)
            print("All endpoint tests PASSED! ✓")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_live_snapshot_endpoint()
    sys.exit(0 if success else 1)
