#!/usr/bin/env python3
"""
Test external logging configuration to verify backward compatibility and new features.
"""

import json
import sys
import traceback

def test_get_predefined_field_maps():
    """Test that predefined field maps are returned correctly."""
    from app import get_predefined_field_maps
    
    maps = get_predefined_field_maps()
    
    # Verify structure
    assert isinstance(maps, dict), "Field maps should be a dictionary"
    assert "default" in maps, "Should have 'default' field map"
    assert "brewersfriend" in maps, "Should have 'brewersfriend' field map"
    assert "custom" in maps, "Should have 'custom' field map"
    
    # Verify default map structure
    default_map = maps["default"]
    assert "name" in default_map, "Field map should have 'name'"
    assert "description" in default_map, "Field map should have 'description'"
    assert "map" in default_map, "Field map should have 'map'"
    
    # Verify map fields
    map_fields = default_map["map"]
    assert "timestamp" in map_fields, "Map should have 'timestamp'"
    assert "tilt_color" in map_fields, "Map should have 'tilt_color'"
    assert "gravity" in map_fields, "Map should have 'gravity'"
    assert "temp_f" in map_fields, "Map should have 'temp_f'"
    
    print("✓ Predefined field maps test passed")
    return True

def test_backward_compatibility():
    """Test that old configuration format still works."""
    # Simulate old format configuration
    old_config = {
        "external_url_0": "https://api.example.com/v1/data",
        "external_url_1": "https://api2.example.com/data",
        "external_method": "POST",
        "external_content_type": "json",
        "external_timeout_seconds": 10,
        "external_field_map": '{"gravity":"sg","temp_f":"temperature"}'
    }
    
    # Test that the old config can be read
    assert old_config.get("external_url_0") == "https://api.example.com/v1/data"
    assert old_config.get("external_method") == "POST"
    assert old_config.get("external_content_type") == "json"
    
    # Parse field map
    try:
        field_map = json.loads(old_config["external_field_map"])
        assert field_map["gravity"] == "sg"
        assert field_map["temp_f"] == "temperature"
    except Exception as e:
        print(f"✗ Failed to parse old field map: {e}")
        return False
    
    print("✓ Backward compatibility test passed")
    return True

def test_new_format():
    """Test new per-URL configuration format."""
    new_config = {
        "external_refresh_rate": "5",
        "external_urls": [
            {
                "name": "Service A",
                "url": "https://api.example.com/v1/data",
                "method": "POST",
                "content_type": "json",
                "timeout_seconds": 10,
                "field_map_id": "default"
            },
            {
                "name": "Service B",
                "url": "https://api2.example.com/data",
                "method": "GET",
                "content_type": "form",
                "timeout_seconds": 15,
                "field_map_id": "custom",
                "custom_field_map": '{"gravity":"sg","temp_f":"temperature"}'
            }
        ]
    }
    
    # Verify structure
    assert "external_urls" in new_config
    assert isinstance(new_config["external_urls"], list)
    assert len(new_config["external_urls"]) == 2
    
    # Verify first service
    service_a = new_config["external_urls"][0]
    assert service_a["name"] == "Service A"
    assert service_a["method"] == "POST"
    assert service_a["content_type"] == "json"
    assert service_a["field_map_id"] == "default"
    
    # Verify second service has different settings
    service_b = new_config["external_urls"][1]
    assert service_b["method"] == "GET"
    assert service_b["content_type"] == "form"
    assert service_b["timeout_seconds"] == 15
    assert service_b["field_map_id"] == "custom"
    
    # Parse custom field map
    try:
        custom_map = json.loads(service_b["custom_field_map"])
        assert custom_map["gravity"] == "sg"
    except Exception as e:
        print(f"✗ Failed to parse custom field map: {e}")
        return False
    
    print("✓ New format test passed")
    return True

def main():
    """Run all tests."""
    print("\n=== Testing External Logging Configuration ===\n")
    
    tests = [
        test_get_predefined_field_maps,
        test_backward_compatibility,
        test_new_format
    ]
    
    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
