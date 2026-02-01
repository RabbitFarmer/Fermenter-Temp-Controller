#!/usr/bin/env python3
"""
Test that chart line shapes are set to 'linear' for direct point-to-point lines.

This test verifies the fix for the issue where charts displayed horizontal lines
with periodic vertical jumps instead of lines moving directly from point to point.
"""

import os
import re

def test_chart_line_shapes():
    """Verify that all line shapes in chart_plotly.html are set to 'linear'"""
    
    template_path = 'templates/chart_plotly.html'
    
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Find all line shape configurations
    shape_pattern = r"shape:\s*'(\w+)'"
    matches = re.findall(shape_pattern, content)
    
    print("Chart Line Shape Test")
    print("=" * 60)
    print(f"Template: {template_path}")
    print(f"Found {len(matches)} line shape configurations:")
    
    all_linear = True
    for i, shape in enumerate(matches, 1):
        status = "✓" if shape == "linear" else "✗"
        print(f"  {status} Shape {i}: '{shape}'")
        if shape != "linear":
            all_linear = False
    
    print()
    
    # Check for any remaining 'spline' configurations
    spline_count = content.count("shape: 'spline'")
    if spline_count > 0:
        print(f"❌ Found {spline_count} 'spline' shape configurations (should be 0)")
        all_linear = False
    
    # Verify we have the expected number of line shape configurations
    expected_count = 3  # Temperature (temp control), Temperature (regular), Gravity
    if len(matches) == expected_count:
        print(f"✓ Found expected {expected_count} line shape configurations")
    else:
        print(f"⚠ Warning: Found {len(matches)} line shapes, expected {expected_count}")
    
    print()
    
    if all_linear and len(matches) == expected_count:
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nChart will now display:")
        print("  • Lines that move directly from point to point")
        print("  • No horizontal lines with vertical jumps")
        print("  • Smooth transitions using linear interpolation")
        return True
    else:
        print("=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        return False

if __name__ == '__main__':
    success = test_chart_line_shapes()
    exit(0 if success else 1)
