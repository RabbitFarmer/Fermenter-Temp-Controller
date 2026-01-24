#!/usr/bin/env python3
"""
Integration test for system settings tab persistence and external_refresh_rate fix.
"""

import sys
import os

# Set up path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_system_config_route():
    """Test that system_config route handles tab parameter correctly"""
    print("Test 1: system_config route with tab parameter")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test default (no tab parameter)
            response = client.get('/system_config')
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert b'SYSTEM SETTINGS CONFIGURATION' in response.data, "Page title not found"
            print("  ✓ PASS: Default route loads successfully")
            
            # Test with tab parameter
            response = client.get('/system_config?tab=logging-integrations')
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert b'logging-integrations' in response.data, "Tab parameter not in response"
            print("  ✓ PASS: Route with tab parameter loads successfully")
            
            # Verify hidden field is present
            assert b'<input type="hidden" id="active_tab" name="active_tab"' in response.data, \
                "Hidden active_tab field not found in response"
            print("  ✓ PASS: Hidden active_tab field present in HTML")
            
    except ImportError as e:
        print(f"  ✗ FAIL: Could not import app: {e}")
        return False
    except AssertionError as e:
        print(f"  ✗ FAIL: {e}")
        return False
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False
    
    return True

def test_update_system_config_redirect():
    """Test that update_system_config preserves tab on redirect"""
    print("\nTest 2: update_system_config redirect behavior")
    
    try:
        from app import app, system_cfg
        
        with app.test_client() as client:
            # Prepare form data with active_tab
            form_data = {
                'active_tab': 'logging-integrations',
                'brewery_name': 'Test Brewery',
                'brewer_name': 'Test Brewer',
                'external_refresh_rate': '25',
                'warning_mode': 'NONE',
            }
            
            # Submit the form
            response = client.post('/update_system_config', 
                                 data=form_data,
                                 follow_redirects=False)
            
            # Check redirect
            assert response.status_code == 302, f"Expected redirect (302), got {response.status_code}"
            print("  ✓ PASS: Form submission returns redirect")
            
            # Verify redirect location includes tab parameter
            location = response.headers.get('Location', '')
            assert 'tab=logging-integrations' in location, \
                f"Redirect location doesn't include tab parameter: {location}"
            print(f"  ✓ PASS: Redirect includes tab parameter: {location}")
            
            # Verify external_refresh_rate was saved
            assert system_cfg.get('external_refresh_rate') == '25', \
                f"external_refresh_rate not saved correctly: {system_cfg.get('external_refresh_rate')}"
            print("  ✓ PASS: external_refresh_rate saved correctly")
            
    except ImportError as e:
        print(f"  ✗ FAIL: Could not import app: {e}")
        return False
    except AssertionError as e:
        print(f"  ✗ FAIL: {e}")
        return False
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False
    
    return True

def test_external_refresh_rate_preservation():
    """Test that external_refresh_rate is preserved when not in form data"""
    print("\nTest 3: external_refresh_rate preservation")
    
    try:
        from app import app, system_cfg
        
        # Set initial value
        system_cfg['external_refresh_rate'] = '30'
        
        with app.test_client() as client:
            # Submit form without external_refresh_rate
            form_data = {
                'active_tab': 'main-settings',
                'brewery_name': 'Test Brewery',
                'warning_mode': 'NONE',
                # Note: external_refresh_rate is NOT included
            }
            
            response = client.post('/update_system_config', 
                                 data=form_data,
                                 follow_redirects=False)
            
            assert response.status_code == 302, f"Expected redirect (302), got {response.status_code}"
            print("  ✓ PASS: Form submission successful")
            
            # Verify external_refresh_rate was preserved (not reset to default)
            saved_value = system_cfg.get('external_refresh_rate')
            assert saved_value == '30', \
                f"external_refresh_rate should be preserved as '30', got '{saved_value}'"
            print(f"  ✓ PASS: external_refresh_rate preserved: {saved_value}")
            
    except ImportError as e:
        print(f"  ✗ FAIL: Could not import app: {e}")
        return False
    except AssertionError as e:
        print(f"  ✗ FAIL: {e}")
        return False
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False
    
    return True

def test_goodbye_route():
    """Test that goodbye route passes brewery_name correctly"""
    print("\nTest 4: goodbye route with brewery_name")
    
    try:
        from app import app, system_cfg
        
        # Set brewery name
        system_cfg['brewery_name'] = 'My Test Brewery'
        
        with app.test_client() as client:
            # POST to exit_system route with confirm=yes
            response = client.post('/exit_system', 
                                 data={'confirm': 'yes'},
                                 follow_redirects=False)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            print("  ✓ PASS: Goodbye page renders")
            
            # Check that brewery name is in the response
            assert b'My Test Brewery' in response.data, \
                "Brewery name not found in goodbye page"
            print("  ✓ PASS: Brewery name displayed in goodbye page")
            
            # Verify hardcoded text is NOT present
            assert b'The Fermenter Temperature Controller is shutting down' not in response.data, \
                "Hardcoded text still present in goodbye page"
            print("  ✓ PASS: Hardcoded text removed from goodbye page")
            
    except ImportError as e:
        print(f"  ✗ FAIL: Could not import app: {e}")
        return False
    except AssertionError as e:
        print(f"  ✗ FAIL: {e}")
        return False
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False
    
    return True

def test_tab_validation():
    """Test that invalid tab values are rejected and default to main-settings"""
    print("\nTest 5: tab parameter validation")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test with invalid tab parameter (potential XSS attempt)
            response = client.get('/system_config?tab=<script>alert(1)</script>')
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            # Verify the malicious script is NOT in the response
            assert b'<script>alert(1)</script>' not in response.data, \
                "Malicious script found in response - XSS vulnerability!"
            print("  ✓ PASS: Malicious script rejected")
            
            # Test with another invalid tab value
            response = client.get('/system_config?tab=invalid-tab-name')
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            # Should default to main-settings tab being active
            assert b'class="tab-button active"' in response.data, \
                "No active tab button found"
            print("  ✓ PASS: Invalid tab value handled gracefully")
            
            # Test form submission with invalid active_tab
            form_data = {
                'active_tab': '<script>alert(2)</script>',
                'brewery_name': 'Test',
                'warning_mode': 'NONE',
            }
            
            response = client.post('/update_system_config', 
                                 data=form_data,
                                 follow_redirects=False)
            
            assert response.status_code == 302, f"Expected redirect (302), got {response.status_code}"
            location = response.headers.get('Location', '')
            
            # Should redirect to main-settings (default) since invalid tab was provided
            assert 'tab=main-settings' in location, \
                f"Expected redirect to main-settings, got: {location}"
            print("  ✓ PASS: Invalid form active_tab validated correctly")
            
    except ImportError as e:
        print(f"  ✗ FAIL: Could not import app: {e}")
        return False
    except AssertionError as e:
        print(f"  ✗ FAIL: {e}")
        return False
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False
    
    return True

def main():
    print("=" * 70)
    print("Integration Tests for System Settings Fixes")
    print("=" * 70)
    
    tests = [
        test_system_config_route,
        test_update_system_config_redirect,
        test_external_refresh_rate_preservation,
        test_goodbye_route,
        test_tab_validation,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ UNEXPECTED ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 70)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)
    
    if all(results):
        print("✓ All integration tests passed!")
        return 0
    else:
        print("✗ Some integration tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
