#!/usr/bin/env python3
"""
Test Flask routes for external logging configuration.
"""

import json
import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_system_config_route():
    """Test that system_config route works with migration."""
    print("\n--- Testing system_config Route ---")
    
    from app import app, system_cfg
    
    # Save original config
    original_config = system_cfg.copy()
    
    try:
        with app.test_client() as client:
            # Test with old format config
            system_cfg.clear()
            system_cfg.update({
                "external_name_0": "Test Service",
                "external_url_0": "https://example.com/api",
                "external_method": "POST",
                "external_content_type": "json",
                "external_timeout_seconds": 8
            })
            
            response = client.get('/system_config')
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            # Check that the template rendered
            html = response.data.decode('utf-8')
            assert 'External Service 1' in html, "Should have External Service 1 heading"
            assert 'Field Map Template' in html, "Should have Field Map Template dropdown"
            print("✓ system_config route renders correctly with old format")
            
            # Test with new format config
            system_cfg.clear()
            system_cfg.update({
                "external_urls": [
                    {
                        "name": "New Service",
                        "url": "https://example.com/api",
                        "method": "POST",
                        "content_type": "json",
                        "timeout_seconds": 10,
                        "field_map_id": "default"
                    }
                ]
            })
            
            response = client.get('/system_config')
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            html = response.data.decode('utf-8')
            assert 'External Service 1' in html, "Should have External Service 1 heading"
            print("✓ system_config route renders correctly with new format")
            
            return True
            
    except Exception as e:
        print(f"✗ system_config route test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original config
        system_cfg.clear()
        system_cfg.update(original_config)


def test_update_system_config_route():
    """Test that update_system_config route processes new format."""
    print("\n--- Testing update_system_config Route ---")
    
    from app import app, system_cfg, SYSTEM_CFG_FILE
    import os
    
    # Save original config
    original_config = system_cfg.copy()
    
    try:
        with app.test_client() as client:
            # Prepare form data for new format
            form_data = {
                "external_refresh_rate": "5",
                "external_name_0": "Service A",
                "external_url_0": "https://api1.example.com",
                "external_method_0": "POST",
                "external_content_type_0": "json",
                "external_timeout_seconds_0": "10",
                "external_field_map_id_0": "default",
                "external_name_1": "Service B",
                "external_url_1": "https://api2.example.com",
                "external_method_1": "GET",
                "external_content_type_1": "form",
                "external_timeout_seconds_1": "15",
                "external_field_map_id_1": "custom",
                "external_custom_field_map_1": '{"gravity":"sg"}',
                "brewery_name": "Test Brewery",
                "brewer_name": "Test Brewer",
                "update_interval": "1",
                "temp_logging_interval": "10",
                "warning_mode": "NONE",
                "kasa_rate_limit_seconds": "10",
                "tilt_logging_interval_minutes": "15"
            }
            
            response = client.post('/update_system_config', data=form_data, follow_redirects=False)
            
            # Should redirect to /system_config
            assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
            assert response.location.endswith('/system_config'), "Should redirect to /system_config"
            
            # Verify the config was updated
            assert "external_urls" in system_cfg, "Should have external_urls key"
            assert len(system_cfg["external_urls"]) == 2, "Should have 2 URLs"
            
            # Verify first service
            service_a = system_cfg["external_urls"][0]
            assert service_a["name"] == "Service A", "Service A name should match"
            assert service_a["url"] == "https://api1.example.com", "Service A URL should match"
            assert service_a["method"] == "POST", "Service A method should be POST"
            assert service_a["field_map_id"] == "default", "Service A should use default field map"
            
            # Verify second service
            service_b = system_cfg["external_urls"][1]
            assert service_b["name"] == "Service B", "Service B name should match"
            assert service_b["method"] == "GET", "Service B method should be GET"
            assert service_b["field_map_id"] == "custom", "Service B should use custom field map"
            assert service_b["custom_field_map"] == '{"gravity":"sg"}', "Custom field map should match"
            
            print("✓ update_system_config route processes new format correctly")
            return True
            
    except Exception as e:
        print(f"✗ update_system_config route test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original config
        system_cfg.clear()
        system_cfg.update(original_config)


def main():
    """Run all Flask route tests."""
    print("\n" + "=" * 60)
    print("Flask Route Tests for External Logging")
    print("=" * 60)
    
    tests = [
        test_system_config_route,
        test_update_system_config_route
    ]
    
    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All Flask route tests passed!")
        return 0
    else:
        print("✗ Some Flask route tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
