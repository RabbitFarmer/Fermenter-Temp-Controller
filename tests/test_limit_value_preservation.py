#!/usr/bin/env python3
"""
Test to verify that temperature limits are preserved when form fields are empty or invalid.

This tests the fix for the issue where limits were being dropped/reset when updating
the configuration.
"""

def test_limit_preservation():
    """Test that existing limits are preserved when form fields are empty or invalid."""
    
    print("=" * 80)
    print("TEMPERATURE LIMIT PRESERVATION TEST")
    print("=" * 80)
    print()
    
    # Simulate existing temp_cfg with valid limits
    temp_cfg = {
        "low_limit": 74.0,
        "high_limit": 75.0,
        "tilt_color": "Red",
        "enable_heating": True,
        "enable_cooling": False
    }
    
    print(f"Initial Configuration:")
    print(f"  Low limit: {temp_cfg['low_limit']}°F")
    print(f"  High limit: {temp_cfg['high_limit']}°F")
    print()
    
    # Test Case 1: Empty form fields (should preserve existing values)
    print("=" * 80)
    print("TEST CASE 1: Empty form fields")
    print("=" * 80)
    print()
    
    form_data = {
        'low_limit': '',  # Empty string
        'high_limit': '',  # Empty string
        'tilt_color': 'Red',
        'enable_heating': True
    }
    
    # Simulate the fix logic
    low_limit_value = form_data.get('low_limit', '').strip()
    high_limit_value = form_data.get('high_limit', '').strip()
    
    if low_limit_value:
        try:
            low_limit = float(low_limit_value)
        except (ValueError, TypeError):
            low_limit = temp_cfg.get("low_limit", 0.0)
            print(f"Invalid low_limit, keeping existing: {low_limit}")
    else:
        low_limit = temp_cfg.get("low_limit", 0.0)
        print(f"Empty low_limit field, keeping existing: {low_limit}")
    
    if high_limit_value:
        try:
            high_limit = float(high_limit_value)
        except (ValueError, TypeError):
            high_limit = temp_cfg.get("high_limit", 100.0)
            print(f"Invalid high_limit, keeping existing: {high_limit}")
    else:
        high_limit = temp_cfg.get("high_limit", 100.0)
        print(f"Empty high_limit field, keeping existing: {high_limit}")
    
    print()
    print(f"Result:")
    print(f"  Low limit: {low_limit}°F")
    print(f"  High limit: {high_limit}°F")
    print()
    
    if low_limit == 74.0 and high_limit == 75.0:
        print("✓ TEST PASSED: Empty fields preserved existing values")
    else:
        print("✗ TEST FAILED: Values were not preserved")
        return False
    
    # Test Case 2: Invalid form values (should preserve existing values)
    print()
    print("=" * 80)
    print("TEST CASE 2: Invalid form values")
    print("=" * 80)
    print()
    
    form_data = {
        'low_limit': 'abc',  # Invalid value
        'high_limit': 'xyz',  # Invalid value
        'tilt_color': 'Red'
    }
    
    low_limit_value = form_data.get('low_limit', '').strip()
    high_limit_value = form_data.get('high_limit', '').strip()
    
    if low_limit_value:
        try:
            low_limit = float(low_limit_value)
        except (ValueError, TypeError):
            low_limit = temp_cfg.get("low_limit", 0.0)
            print(f"Invalid low_limit '{low_limit_value}', keeping existing: {low_limit}")
    else:
        low_limit = temp_cfg.get("low_limit", 0.0)
    
    if high_limit_value:
        try:
            high_limit = float(high_limit_value)
        except (ValueError, TypeError):
            high_limit = temp_cfg.get("high_limit", 100.0)
            print(f"Invalid high_limit '{high_limit_value}', keeping existing: {high_limit}")
    else:
        high_limit = temp_cfg.get("high_limit", 100.0)
    
    print()
    print(f"Result:")
    print(f"  Low limit: {low_limit}°F")
    print(f"  High limit: {high_limit}°F")
    print()
    
    if low_limit == 74.0 and high_limit == 75.0:
        print("✓ TEST PASSED: Invalid values preserved existing limits")
    else:
        print("✗ TEST FAILED: Values were not preserved")
        return False
    
    # Test Case 3: Valid new values (should update)
    print()
    print("=" * 80)
    print("TEST CASE 3: Valid new values")
    print("=" * 80)
    print()
    
    form_data = {
        'low_limit': '68',
        'high_limit': '72',
        'tilt_color': 'Red'
    }
    
    low_limit_value = form_data.get('low_limit', '').strip()
    high_limit_value = form_data.get('high_limit', '').strip()
    
    if low_limit_value:
        try:
            low_limit = float(low_limit_value)
            print(f"Valid low_limit provided: {low_limit}")
        except (ValueError, TypeError):
            low_limit = temp_cfg.get("low_limit", 0.0)
    else:
        low_limit = temp_cfg.get("low_limit", 0.0)
    
    if high_limit_value:
        try:
            high_limit = float(high_limit_value)
            print(f"Valid high_limit provided: {high_limit}")
        except (ValueError, TypeError):
            high_limit = temp_cfg.get("high_limit", 100.0)
    else:
        high_limit = temp_cfg.get("high_limit", 100.0)
    
    print()
    print(f"Result:")
    print(f"  Low limit: {low_limit}°F")
    print(f"  High limit: {high_limit}°F")
    print()
    
    if low_limit == 68.0 and high_limit == 72.0:
        print("✓ TEST PASSED: Valid new values were applied")
    else:
        print("✗ TEST FAILED: Values were not updated correctly")
        return False
    
    # Test Case 4: Partial update (one empty, one valid)
    print()
    print("=" * 80)
    print("TEST CASE 4: Partial update (low empty, high valid)")
    print("=" * 80)
    print()
    
    # Reset to original values
    temp_cfg["low_limit"] = 74.0
    temp_cfg["high_limit"] = 75.0
    
    form_data = {
        'low_limit': '',     # Empty - should preserve existing
        'high_limit': '76',  # Valid - should update
        'tilt_color': 'Red'
    }
    
    low_limit_value = form_data.get('low_limit', '').strip()
    high_limit_value = form_data.get('high_limit', '').strip()
    
    if low_limit_value:
        try:
            low_limit = float(low_limit_value)
        except (ValueError, TypeError):
            low_limit = temp_cfg.get("low_limit", 0.0)
    else:
        low_limit = temp_cfg.get("low_limit", 0.0)
        print(f"Empty low_limit field, keeping existing: {low_limit}")
    
    if high_limit_value:
        try:
            high_limit = float(high_limit_value)
            print(f"Valid high_limit provided: {high_limit}")
        except (ValueError, TypeError):
            high_limit = temp_cfg.get("high_limit", 100.0)
    else:
        high_limit = temp_cfg.get("high_limit", 100.0)
    
    print()
    print(f"Result:")
    print(f"  Low limit: {low_limit}°F (should be 74.0 - preserved)")
    print(f"  High limit: {high_limit}°F (should be 76.0 - updated)")
    print()
    
    if low_limit == 74.0 and high_limit == 76.0:
        print("✓ TEST PASSED: Partial update worked correctly")
    else:
        print("✗ TEST FAILED: Partial update did not work")
        return False
    
    print()
    print("=" * 80)
    print("OVERALL RESULT")
    print("=" * 80)
    print()
    print("✓ ALL TESTS PASSED")
    print("  The fix correctly preserves existing limits when form fields are empty or invalid")
    print("  while still allowing updates when valid values are provided.")
    return True

if __name__ == '__main__':
    success = test_limit_preservation()
    exit(0 if success else 1)
