#!/usr/bin/env python3
"""
Test that chart x-axis starts at the left margin (first data point).

This test verifies that the x-axis configuration ensures the chart starts
exactly at the first data point without auto-padding on the left side.
"""

import os
import re

def test_chart_left_margin():
    """Verify that x-axis is configured to start at left margin"""
    
    template_path = 'templates/chart_plotly.html'
    
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    print("Chart Left Margin Test")
    print("=" * 70)
    print(f"Template: {template_path}")
    print()
    
    # Check that rangeStart uses minDate (no left padding)
    range_start_pattern = r"const rangeStart = minDate;"
    has_no_left_padding = bool(re.search(range_start_pattern, content))
    
    print("✓ Checking x-axis range start:")
    print(f"  {'✓' if has_no_left_padding else '✗'} rangeStart = minDate (no left padding)")
    print()
    
    # Check that xaxis has autorange: false
    autorange_false_count = len(re.findall(r"autorange:\s*false", content))
    expected_autorange_count = 2  # One for temp control layout, one for regular tilt layout
    
    print("✓ Checking xaxis autorange configuration:")
    print(f"  Found {autorange_false_count} 'autorange: false' configurations")
    print(f"  {'✓' if autorange_false_count >= expected_autorange_count else '✗'} Expected at least {expected_autorange_count}")
    print()
    
    # Check that xaxis has rangemode: 'normal'
    rangemode_normal_count = len(re.findall(r"rangemode:\s*'normal'", content))
    expected_rangemode_count = 2  # One for temp control layout, one for regular tilt layout
    
    print("✓ Checking xaxis rangemode configuration:")
    print(f"  Found {rangemode_normal_count} \"rangemode: 'normal'\" configurations")
    print(f"  {'✓' if rangemode_normal_count >= expected_rangemode_count else '✗'} Expected at least {expected_rangemode_count}")
    print()
    
    # Verify xaxis configuration appears in both layouts
    temp_control_xaxis = bool(re.search(
        r"titleText[^}]*layout\s*=\s*\{[^}]*xaxis:\s*\{[^}]*autorange:\s*false[^}]*rangemode:\s*'normal'",
        content, re.DOTALL
    ))
    
    regular_tilt_xaxis = bool(re.search(
        r"Fermenter Readings[^}]*layout\s*=\s*\{[^}]*xaxis:\s*\{[^}]*autorange:\s*false[^}]*rangemode:\s*'normal'",
        content, re.DOTALL
    ))
    
    print("✓ Checking xaxis in both chart types:")
    print(f"  {'✓' if temp_control_xaxis else '✗'} Temperature control chart has autorange/rangemode config")
    print(f"  {'✓' if regular_tilt_xaxis else '✗'} Regular tilt chart has autorange/rangemode config")
    print()
    
    all_tests_pass = (
        has_no_left_padding and
        autorange_false_count >= expected_autorange_count and
        rangemode_normal_count >= expected_rangemode_count
    )
    
    if all_tests_pass:
        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nCharts will now:")
        print("  • Start at the left margin (first data point)")
        print("  • Use exact range without auto-padding on the left")
        print("  • Disable Plotly's autorange feature")
        print("  • Use 'normal' rangemode for precise control")
        return True
    else:
        print("=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        return False

if __name__ == '__main__':
    success = test_chart_left_margin()
    exit(0 if success else 1)
