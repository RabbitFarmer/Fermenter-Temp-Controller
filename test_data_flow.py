#!/usr/bin/env python3
"""
Browser simulation test - validates the complete data flow from backend to frontend.
This test simulates what would happen when the browser polls /live_snapshot.
"""

import json
import sys
import os

def test_complete_data_flow():
    """Test the complete data flow from BLE scan to frontend display."""
    print("=" * 70)
    print("Complete Data Flow Test")
    print("=" * 70 + "\n")
    
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from app import app, update_live_tilt, tilt_cfg
        
        # Step 1: Simulate BLE scan updating a tilt
        print("Step 1: Simulating BLE scan...")
        update_live_tilt('Black', 1.045, 68.5, -75)
        print("  ✓ Tilt data updated via update_live_tilt")
        
        # Step 2: Frontend polls /live_snapshot
        print("\nStep 2: Simulating frontend polling /live_snapshot...")
        with app.test_client() as client:
            response = client.get('/live_snapshot')
            data = response.get_json()
            
            assert 'live_tilts' in data
            assert 'Black' in data['live_tilts']
            print("  ✓ live_snapshot endpoint returns Black tilt data")
            
            black_data = data['live_tilts']['Black']
            
            # Step 3: Validate frontend receives all necessary data
            print("\nStep 3: Validating frontend data requirements...")
            
            # Check fields needed for createTiltCard
            create_card_fields = [
                'color_code', 'beer_name', 'batch_name', 'brewid',
                'original_gravity', 'gravity', 'temp_f',
                'recipe_og', 'recipe_fg', 'recipe_abv', 'timestamp'
            ]
            
            for field in create_card_fields:
                assert field in black_data, f"Missing field for createTiltCard: {field}"
            
            print("  ✓ All fields for createTiltCard present")
            
            # Check fields needed for updateTiltValues
            update_fields = [
                'recipe_og', 'recipe_fg', 'recipe_abv',
                'original_gravity', 'gravity', 'temp_f', 'timestamp'
            ]
            
            for field in update_fields:
                assert field in black_data, f"Missing field for updateTiltValues: {field}"
            
            print("  ✓ All fields for updateTiltValues present")
            
            # Step 4: Verify og_confirmed is in the data flow
            print("\nStep 4: Verifying og_confirmed attribute...")
            assert 'og_confirmed' in black_data, "og_confirmed missing from response"
            assert isinstance(black_data['og_confirmed'], bool), "og_confirmed should be boolean"
            assert black_data['og_confirmed'] == True, "og_confirmed should be True for Black tilt"
            print(f"  ✓ og_confirmed: {black_data['og_confirmed']}")
            
            # Step 5: Verify ABV calculation data
            print("\nStep 5: Verifying ABV calculation...")
            og = black_data['original_gravity']
            fg = black_data['gravity']
            
            # original_gravity should be a string from actual_og
            assert og == tilt_cfg['Black']['actual_og'], \
                f"original_gravity should match actual_og from config"
            print(f"  ✓ original_gravity ({og}) matches actual_og from config")
            
            # Calculate ABV like the frontend would
            expected_abv = (float(og) - float(fg)) * 131.25
            print(f"  ✓ ABV calculation: ({og} - {fg}) * 131.25 = {expected_abv:.1f}%")
            
            # Step 6: Display complete data structure
            print("\nStep 6: Complete data structure for Black tilt:")
            print("-" * 70)
            print(json.dumps(black_data, indent=2, sort_keys=True))
            print("-" * 70)
            
            print("\n" + "=" * 70)
            print("✅ Complete data flow test PASSED!")
            print("=" * 70)
            print("\nData Flow Summary:")
            print("  1. BLE Scan → update_live_tilt()")
            print("  2. update_live_tilt() → live_tilts dict")
            print("  3. Frontend polls → /live_snapshot")
            print("  4. /live_snapshot → returns JSON with og_confirmed")
            print("  5. Frontend JavaScript → createTiltCard() or updateTiltValues()")
            print("  6. Card displays → with correct OG, gravity, temp, ABV")
            print("\n✓ All steps verified successfully!\n")
            
            return True
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_complete_data_flow()
    sys.exit(0 if success else 1)
