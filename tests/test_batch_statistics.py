#!/usr/bin/env python3
"""
Test script for calculate_batch_statistics function.
Verifies that the function correctly handles actual_og as both string and numeric types.
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import calculate_batch_statistics


def test_actual_og_as_string():
    """Test that actual_og as a string is correctly converted to float for ABV calculation."""
    batch_info = {
        'actual_og': '1.050',  # String value
        'brewid': 'test_batch_001'
    }
    
    batch_data = [
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.050,
                'temp_f': 68.0,
                'timestamp': '2024-01-01T12:00:00Z'
            }
        },
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.010,
                'temp_f': 67.5,
                'timestamp': '2024-01-08T12:00:00Z'
            }
        }
    ]
    
    stats = calculate_batch_statistics(batch_data, batch_info)
    
    # ABV = (OG - FG) * 131.25 = (1.050 - 1.010) * 131.25 = 5.25
    expected_abv = round((1.050 - 1.010) * 131.25, 2)
    
    assert stats['estimated_abv'] is not None, "ABV should be calculated"
    assert stats['estimated_abv'] == expected_abv, f"Expected ABV {expected_abv}, got {stats['estimated_abv']}"
    print(f"✓ Test passed: actual_og as string '1.050' correctly calculated ABV = {stats['estimated_abv']}")


def test_actual_og_as_float():
    """Test that actual_og as a float also works correctly."""
    batch_info = {
        'actual_og': 1.050,  # Float value
        'brewid': 'test_batch_002'
    }
    
    batch_data = [
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.050,
                'temp_f': 68.0,
                'timestamp': '2024-01-01T12:00:00Z'
            }
        },
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.010,
                'temp_f': 67.5,
                'timestamp': '2024-01-08T12:00:00Z'
            }
        }
    ]
    
    stats = calculate_batch_statistics(batch_data, batch_info)
    
    expected_abv = round((1.050 - 1.010) * 131.25, 2)
    
    assert stats['estimated_abv'] is not None, "ABV should be calculated"
    assert stats['estimated_abv'] == expected_abv, f"Expected ABV {expected_abv}, got {stats['estimated_abv']}"
    print(f"✓ Test passed: actual_og as float 1.050 correctly calculated ABV = {stats['estimated_abv']}")


def test_actual_og_invalid():
    """Test that invalid actual_og values are handled gracefully."""
    batch_info = {
        'actual_og': 'invalid_value',  # Invalid string
        'brewid': 'test_batch_003'
    }
    
    batch_data = [
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.050,
                'temp_f': 68.0,
                'timestamp': '2024-01-01T12:00:00Z'
            }
        },
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.010,
                'temp_f': 67.5,
                'timestamp': '2024-01-08T12:00:00Z'
            }
        }
    ]
    
    stats = calculate_batch_statistics(batch_data, batch_info)
    
    assert stats['estimated_abv'] is None, "ABV should be None for invalid actual_og"
    print("✓ Test passed: invalid actual_og handled gracefully, ABV = None")


def test_actual_og_empty():
    """Test that empty actual_og is handled gracefully."""
    batch_info = {
        'actual_og': '',  # Empty string
        'brewid': 'test_batch_004'
    }
    
    batch_data = [
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.050,
                'temp_f': 68.0,
                'timestamp': '2024-01-01T12:00:00Z'
            }
        },
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.010,
                'temp_f': 67.5,
                'timestamp': '2024-01-08T12:00:00Z'
            }
        }
    ]
    
    stats = calculate_batch_statistics(batch_data, batch_info)
    
    assert stats['estimated_abv'] is None, "ABV should be None for empty actual_og"
    print("✓ Test passed: empty actual_og handled gracefully, ABV = None")


def test_actual_og_none():
    """Test that None actual_og is handled gracefully."""
    batch_info = {
        'actual_og': None,  # None value
        'brewid': 'test_batch_005'
    }
    
    batch_data = [
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.050,
                'temp_f': 68.0,
                'timestamp': '2024-01-01T12:00:00Z'
            }
        },
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.010,
                'temp_f': 67.5,
                'timestamp': '2024-01-08T12:00:00Z'
            }
        }
    ]
    
    stats = calculate_batch_statistics(batch_data, batch_info)
    
    assert stats['estimated_abv'] is None, "ABV should be None when actual_og is None"
    print("✓ Test passed: None actual_og handled gracefully, ABV = None")


def test_other_stats():
    """Test that other statistics are calculated correctly regardless of actual_og."""
    batch_info = {
        'actual_og': '1.050',
        'brewid': 'test_batch_006'
    }
    
    batch_data = [
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.050,
                'temp_f': 68.0,
                'timestamp': '2024-01-01T12:00:00Z'
            }
        },
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.030,
                'temp_f': 70.0,
                'timestamp': '2024-01-05T12:00:00Z'
            }
        },
        {
            'event': 'sample',
            'payload': {
                'gravity': 1.010,
                'temp_f': 67.5,
                'timestamp': '2024-01-08T12:00:00Z'
            }
        }
    ]
    
    stats = calculate_batch_statistics(batch_data, batch_info)
    
    assert stats['total_readings'] == 3, "Total readings should be 3"
    assert stats['start_gravity'] == 1.050, "Start gravity should be 1.050"
    assert stats['end_gravity'] == 1.010, "End gravity should be 1.010"
    assert stats['gravity_change'] == round(1.050 - 1.010, 3), "Gravity change should be calculated"
    assert stats['start_temp'] == 68.0, "Start temp should be 68.0"
    assert stats['end_temp'] == 67.5, "End temp should be 67.5"
    assert stats['avg_temp'] == round((68.0 + 70.0 + 67.5) / 3, 1), "Avg temp should be calculated"
    assert stats['min_temp'] == 67.5, "Min temp should be 67.5"
    assert stats['max_temp'] == 70.0, "Max temp should be 70.0"
    print("✓ Test passed: all other statistics calculated correctly")


if __name__ == '__main__':
    print("Running calculate_batch_statistics tests...")
    print()
    
    try:
        test_actual_og_as_string()
        test_actual_og_as_float()
        test_actual_og_invalid()
        test_actual_og_empty()
        test_actual_og_none()
        test_other_stats()
        
        print()
        print("=" * 50)
        print("All tests passed! ✓")
        print("=" * 50)
    except AssertionError as e:
        print()
        print("=" * 50)
        print(f"Test failed: {e}")
        print("=" * 50)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 50)
        print(f"Error running tests: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        sys.exit(1)
