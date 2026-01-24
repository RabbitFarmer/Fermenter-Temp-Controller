#!/usr/bin/env python3
"""
Test the temperature control fixes:
1. Verify live_snapshot includes tilt_color
2. Verify toggle_temp_control returns redirect when new_session is True
"""

import sys
import json
import os
import tempfile
import shutil

def test_live_snapshot_includes_tilt_color():
    """Test that live_snapshot includes tilt_color in temp_control"""
    print("\n" + "="*60)
    print("Test 1: live_snapshot includes tilt_color")
    print("="*60)
    
    # Create temporary config directory
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        os.makedirs('config', exist_ok=True)
        os.makedirs('temp_control', exist_ok=True)
        os.makedirs('batches', exist_ok=True)
        
        # Create minimal config files
        with open('config/system_config.json', 'w') as f:
            json.dump({}, f)
        
        with open('config/tilt_config.json', 'w') as f:
            json.dump({}, f)
        
        with open('config/temp_control_config.json', 'w') as f:
            json.dump({
                "tilt_color": "Blue",
                "low_limit": 65.0,
                "high_limit": 70.0,
                "temp_control_active": True
            }, f)
        
        # Import app after setting up the temp directory
        sys.path.insert(0, old_cwd)
        import app as test_app
        
        # Create test client
        test_app.app.config['TESTING'] = True
        client = test_app.app.test_client()
        
        # Call live_snapshot
        response = client.get('/live_snapshot')
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.get_json()
        assert 'temp_control' in data, "Response should contain temp_control"
        assert 'tilt_color' in data['temp_control'], "temp_control should contain tilt_color"
        
        # Check the value matches what we set
        assert data['temp_control']['tilt_color'] == 'Blue', \
            f"Expected tilt_color='Blue', got '{data['temp_control']['tilt_color']}'"
        
        print("✓ live_snapshot correctly includes tilt_color")
        print(f"  tilt_color value: {data['temp_control']['tilt_color']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_toggle_returns_redirect_for_new_session():
    """Test that toggle_temp_control returns redirect for new_session=True"""
    print("\n" + "="*60)
    print("Test 2: toggle_temp_control returns redirect for new session")
    print("="*60)
    
    # Create temporary config directory
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        os.makedirs('config', exist_ok=True)
        os.makedirs('temp_control', exist_ok=True)
        os.makedirs('batches', exist_ok=True)
        
        # Create minimal config files
        with open('config/system_config.json', 'w') as f:
            json.dump({}, f)
        
        with open('config/tilt_config.json', 'w') as f:
            json.dump({}, f)
        
        with open('config/temp_control_config.json', 'w') as f:
            json.dump({
                "tilt_color": "",
                "temp_control_active": False
            }, f)
        
        # Import app after setting up the temp directory
        sys.path.insert(0, old_cwd)
        # Remove previous import if it exists
        if 'app' in sys.modules:
            del sys.modules['app']
        import app as test_app
        
        # Create test client
        test_app.app.config['TESTING'] = True
        client = test_app.app.test_client()
        
        # Test 1: Toggle ON with new_session=True should return redirect
        response = client.post('/toggle_temp_control', 
                               json={'active': True, 'new_session': True})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.get_json()
        assert data['success'] is True, "Toggle should succeed"
        assert 'redirect' in data, "Response should contain redirect field"
        assert data['redirect'] == '/temp_config', \
            f"Expected redirect='/temp_config', got '{data['redirect']}'"
        
        print("✓ toggle_temp_control correctly returns redirect='/temp_config' for new_session=True")
        
        # Test 2: Toggle ON with new_session=False should NOT return redirect
        response = client.post('/toggle_temp_control', 
                               json={'active': True, 'new_session': False})
        data = response.get_json()
        assert data['success'] is True, "Toggle should succeed"
        assert data['redirect'] is None, \
            f"Expected redirect=None for existing session, got '{data['redirect']}'"
        
        print("✓ toggle_temp_control correctly returns redirect=None for new_session=False")
        
        # Test 3: Toggle OFF should NOT return redirect
        response = client.post('/toggle_temp_control', 
                               json={'active': False, 'new_session': False})
        data = response.get_json()
        assert data['success'] is True, "Toggle should succeed"
        assert data['redirect'] is None, \
            f"Expected redirect=None when turning OFF, got '{data['redirect']}'"
        
        print("✓ toggle_temp_control correctly returns redirect=None when turning OFF")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    print("Testing Temperature Control Fixes")
    print("="*60)
    
    results = []
    results.append(test_live_snapshot_includes_tilt_color())
    results.append(test_toggle_returns_redirect_for_new_session())
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
