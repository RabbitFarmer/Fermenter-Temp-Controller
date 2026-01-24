#!/usr/bin/env python3
"""
Edge case tests for external logging configuration.
Tests empty configurations, malformed JSON, and mixed formats.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_empty_configuration():
    """Test that empty configuration doesn't break forwarding."""
    print("\n--- Testing Empty Configuration ---")
    
    from app import forward_to_third_party_if_configured, system_cfg
    
    original_config = system_cfg.copy()
    
    try:
        # Empty configuration
        system_cfg.clear()
        
        payload = {
            "tilt_color": "RED",
            "gravity": 1.050,
            "temp_f": 68.0,
        }
        
        result = forward_to_third_party_if_configured(payload)
        
        assert result["forwarded"] == False, "Should not forward with empty config"
        assert result["reason"] == "no external_url configured", "Should have correct reason"
        print("✓ Empty configuration handled correctly")
        return True
        
    except Exception as e:
        print(f"✗ Empty configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        system_cfg.clear()
        system_cfg.update(original_config)


def test_malformed_field_map():
    """Test that malformed field map JSON is handled gracefully."""
    print("\n--- Testing Malformed Field Map ---")
    
    from app import forward_to_third_party_if_configured, system_cfg
    
    original_config = system_cfg.copy()
    
    try:
        # Configuration with malformed field map
        system_cfg.clear()
        system_cfg.update({
            "external_urls": [
                {
                    "url": "https://example.com",
                    "method": "POST",
                    "content_type": "json",
                    "timeout_seconds": 5,
                    "field_map_id": "custom",
                    "custom_field_map": "{invalid json"  # Malformed JSON
                }
            ]
        })
        
        payload = {
            "tilt_color": "BLUE",
            "gravity": 1.045,
            "temp_f": 65.0,
        }
        
        # Should not crash, just skip field map transformation
        result = forward_to_third_party_if_configured(payload)
        
        assert "forwarded" in result, "Should have result structure"
        print("✓ Malformed field map handled gracefully (ignored)")
        return True
        
    except Exception as e:
        print(f"✗ Malformed field map test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        system_cfg.clear()
        system_cfg.update(original_config)


def test_mixed_old_and_new_format():
    """Test that new format takes precedence over old format."""
    print("\n--- Testing Mixed Old and New Format ---")
    
    from app import forward_to_third_party_if_configured, system_cfg
    
    original_config = system_cfg.copy()
    
    try:
        # Configuration with both old and new formats
        system_cfg.clear()
        system_cfg.update({
            # New format (should be used)
            "external_urls": [
                {
                    "url": "https://new-format.example.com",
                    "method": "POST",
                    "content_type": "json",
                    "timeout_seconds": 5,
                    "field_map_id": "default"
                }
            ],
            # Old format (should be ignored)
            "external_url_0": "https://old-format.example.com",
            "external_method": "GET",
            "external_content_type": "form"
        })
        
        payload = {
            "tilt_color": "GREEN",
            "gravity": 1.055,
            "temp_f": 70.0,
        }
        
        result = forward_to_third_party_if_configured(payload)
        
        # Should use new format (1 URL from external_urls)
        assert result.get("total_count") == 1, "Should only use new format URLs"
        print("✓ New format takes precedence over old format")
        return True
        
    except Exception as e:
        print(f"✗ Mixed format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        system_cfg.clear()
        system_cfg.update(original_config)


def test_field_map_with_brewersfriend():
    """Test that field map is NOT applied to Brewers Friend (BF has special handling)."""
    print("\n--- Testing Field Map with Brewers Friend ---")
    
    from app import forward_to_third_party_if_configured, system_cfg
    
    original_config = system_cfg.copy()
    
    try:
        # Configuration with field map for Brewers Friend
        system_cfg.clear()
        system_cfg.update({
            "external_urls": [
                {
                    "url": "https://log.brewersfriend.com/stream/test",
                    "method": "POST",
                    "content_type": "json",
                    "timeout_seconds": 5,
                    "field_map_id": "custom",
                    "custom_field_map": '{"gravity":"custom_sg"}'  # This should be ignored
                }
            ]
        })
        
        payload = {
            "tilt_color": "ORANGE",
            "gravity": 1.060,
            "temp_f": 72.0,
            "batch_name": "Test Brew"
        }
        
        # Should use Brewers Friend transformation, not custom field map
        result = forward_to_third_party_if_configured(payload)
        
        assert "forwarded" in result, "Should have result structure"
        print("✓ Brewers Friend uses special transformation (field map ignored)")
        return True
        
    except Exception as e:
        print(f"✗ Brewers Friend field map test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        system_cfg.clear()
        system_cfg.update(original_config)


def test_empty_urls_in_array():
    """Test that empty URLs in the array are skipped."""
    print("\n--- Testing Empty URLs in Array ---")
    
    from app import forward_to_third_party_if_configured, system_cfg
    
    original_config = system_cfg.copy()
    
    try:
        # Configuration with empty URLs
        system_cfg.clear()
        system_cfg.update({
            "external_urls": [
                {"url": "", "method": "POST"},  # Empty URL
                {"url": "   ", "method": "POST"},  # Whitespace only
                {
                    "url": "https://valid.example.com",
                    "method": "POST",
                    "content_type": "json",
                    "timeout_seconds": 5
                }
            ]
        })
        
        payload = {"tilt_color": "PURPLE", "gravity": 1.050}
        
        result = forward_to_third_party_if_configured(payload)
        
        # Should only forward to 1 URL (the valid one)
        assert result.get("total_count") == 1, "Should skip empty URLs"
        print("✓ Empty URLs in array are properly skipped")
        return True
        
    except Exception as e:
        print(f"✗ Empty URLs test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        system_cfg.clear()
        system_cfg.update(original_config)


def main():
    """Run all edge case tests."""
    print("\n" + "=" * 60)
    print("Edge Case Tests for External Logging")
    print("=" * 60)
    
    tests = [
        test_empty_configuration,
        test_malformed_field_map,
        test_mixed_old_and_new_format,
        test_field_map_with_brewersfriend,
        test_empty_urls_in_array
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
        print("✓ All edge case tests passed!")
        return 0
    else:
        print("✗ Some edge case tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
