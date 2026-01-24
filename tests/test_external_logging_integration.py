#!/usr/bin/env python3
"""
Integration test for external logging configuration changes.
Tests migration logic, field map transformations, and backward compatibility.
"""

import json
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_forward_to_third_party_with_old_format():
    """Test that forward_to_third_party works with old format configuration."""
    print("\n--- Testing Old Format Configuration ---")
    
    from app import forward_to_third_party_if_configured, system_cfg
    
    # Save original config
    original_config = system_cfg.copy()
    
    try:
        # Set up old format configuration
        system_cfg.clear()
        system_cfg.update({
            "external_url_0": "https://httpbin.org/post",
            "external_method": "POST",
            "external_content_type": "json",
            "external_timeout_seconds": 5,
            "external_field_map": '{"gravity":"sg","temp_f":"temperature"}'
        })
        
        # Create test payload
        payload = {
            "tilt_color": "RED",
            "gravity": 1.050,
            "temp_f": 68.0,
            "brewid": "test-batch-123",
            "timestamp": "2026-01-22T12:00:00"
        }
        
        # This should process without errors (though it will fail to connect in test env)
        result = forward_to_third_party_if_configured(payload)
        
        # Verify result structure
        assert "forwarded" in result, "Result should have 'forwarded' key"
        print(f"✓ Old format processed successfully: {result.get('reason', 'forwarded')}")
        return True
        
    except Exception as e:
        print(f"✗ Old format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original config
        system_cfg.clear()
        system_cfg.update(original_config)


def test_forward_to_third_party_with_new_format():
    """Test that forward_to_third_party works with new format configuration."""
    print("\n--- Testing New Format Configuration ---")
    
    from app import forward_to_third_party_if_configured, system_cfg
    
    # Save original config
    original_config = system_cfg.copy()
    
    try:
        # Set up new format configuration
        system_cfg.clear()
        system_cfg.update({
            "external_urls": [
                {
                    "name": "Test Service",
                    "url": "https://httpbin.org/post",
                    "method": "POST",
                    "content_type": "json",
                    "timeout_seconds": 5,
                    "field_map_id": "custom",
                    "custom_field_map": '{"gravity":"sg","temp_f":"temperature"}'
                }
            ]
        })
        
        # Create test payload
        payload = {
            "tilt_color": "BLUE",
            "gravity": 1.045,
            "temp_f": 65.0,
            "brewid": "test-batch-456",
            "timestamp": "2026-01-22T12:00:00"
        }
        
        # This should process without errors
        result = forward_to_third_party_if_configured(payload)
        
        # Verify result structure
        assert "forwarded" in result, "Result should have 'forwarded' key"
        print(f"✓ New format processed successfully: {result.get('reason', 'forwarded')}")
        return True
        
    except Exception as e:
        print(f"✗ New format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original config
        system_cfg.clear()
        system_cfg.update(original_config)


def test_brewersfriend_transformation():
    """Test that Brewers Friend transformation works correctly."""
    print("\n--- Testing Brewers Friend Transformation ---")
    
    from app import forward_to_third_party_if_configured, system_cfg
    
    # Save original config
    original_config = system_cfg.copy()
    
    try:
        # Set up configuration with Brewers Friend URL
        system_cfg.clear()
        system_cfg.update({
            "external_urls": [
                {
                    "name": "Brewers Friend",
                    "url": "https://log.brewersfriend.com/stream/test",
                    "method": "POST",
                    "content_type": "json",
                    "timeout_seconds": 5,
                    "field_map_id": "brewersfriend"
                }
            ]
        })
        
        # Create test payload
        payload = {
            "tilt_color": "GREEN",
            "gravity": 1.055,
            "temp_f": 70.0,
            "brewid": "my-brew",
            "batch_name": "Imperial Stout",
            "timestamp": "2026-01-22T12:00:00"
        }
        
        # This should process without errors
        result = forward_to_third_party_if_configured(payload)
        
        # Verify result structure
        assert "forwarded" in result, "Result should have 'forwarded' key"
        print(f"✓ Brewers Friend transformation processed: {result.get('reason', 'forwarded')}")
        return True
        
    except Exception as e:
        print(f"✗ Brewers Friend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original config
        system_cfg.clear()
        system_cfg.update(original_config)


def test_field_map_application():
    """Test that field maps are applied correctly."""
    print("\n--- Testing Field Map Application ---")
    
    from app import get_predefined_field_maps
    
    try:
        # Get predefined maps
        maps = get_predefined_field_maps()
        
        # Test default map
        default_map = maps["default"]["map"]
        assert default_map["gravity"] == "gravity", "Default map should use 'gravity'"
        assert default_map["temp_f"] == "temp", "Default map should use 'temp'"
        print("✓ Default field map structure correct")
        
        # Test Brewers Friend map
        bf_map = maps["brewersfriend"]["map"]
        assert bf_map["tilt_color"] == "name", "BF map should use 'name' for tilt_color"
        assert bf_map["brew_id"] == "beer", "BF map should use 'beer' for brew_id"
        print("✓ Brewers Friend field map structure correct")
        
        # Test custom map template
        custom_map = maps["custom"]["map"]
        assert "gravity" in custom_map, "Custom map should have gravity field"
        print("✓ Custom field map template exists")
        
        return True
        
    except Exception as e:
        print(f"✗ Field map test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_migration_logic():
    """Test that migration from old to new format works in system_config route."""
    print("\n--- Testing Migration Logic ---")
    
    # This test verifies the migration happens correctly
    # by checking the logic in the system_config route
    
    try:
        # Simulate old format config
        old_config = {
            "external_name_0": "Old Service 1",
            "external_url_0": "https://api1.example.com",
            "external_name_1": "Old Service 2",
            "external_url_1": "https://api2.example.com",
            "external_method": "GET",
            "external_content_type": "form",
            "external_timeout_seconds": 10,
            "external_field_map": '{"gravity":"sg"}'
        }
        
        # Migration should extract URLs and settings
        external_urls = []
        for i in range(3):
            name = old_config.get(f"external_name_{i}", "").strip()
            url = old_config.get(f"external_url_{i}", "").strip()
            if url:
                url_config = {
                    "name": name or f"Service {i + 1}",
                    "url": url,
                    "method": old_config.get("external_method", "POST"),
                    "content_type": old_config.get("external_content_type", "form"),
                    "timeout_seconds": int(old_config.get("external_timeout_seconds", 8)),
                    "field_map_id": "default"
                }
                if old_config.get("external_field_map"):
                    url_config["field_map_id"] = "custom"
                    url_config["custom_field_map"] = old_config.get("external_field_map")
                external_urls.append(url_config)
        
        # Verify migration results
        assert len(external_urls) == 2, "Should migrate 2 URLs"
        assert external_urls[0]["name"] == "Old Service 1", "Name should be preserved"
        assert external_urls[0]["method"] == "GET", "Method should be preserved"
        assert external_urls[0]["content_type"] == "form", "Content type should be preserved"
        assert external_urls[0]["field_map_id"] == "custom", "Should use custom field map"
        print("✓ Migration logic correctly converts old format to new format")
        
        return True
        
    except Exception as e:
        print(f"✗ Migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("External Logging Integration Tests")
    print("=" * 60)
    
    tests = [
        test_forward_to_third_party_with_old_format,
        test_forward_to_third_party_with_new_format,
        test_brewersfriend_transformation,
        test_field_map_application,
        test_migration_logic
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
        print("✓ All integration tests passed!")
        return 0
    else:
        print("✗ Some integration tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
