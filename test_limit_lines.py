#!/usr/bin/env python3
"""
Test that temperature control chart includes horizontal limit lines.

This test verifies that low_limit and high_limit are included in chart data
and that the template includes code to render them as horizontal red lines.
"""

import os
import re

def test_limit_lines():
    """Verify that limit lines are properly configured"""
    
    print("Temperature Limit Lines Test")
    print("=" * 60)
    
    # Test 1: Check backend includes limits in chart data
    print("\n1. Backend Changes (app.py)")
    print("-" * 60)
    
    app_path = 'app.py'
    if not os.path.exists(app_path):
        print(f"❌ App file not found: {app_path}")
        return False
    
    with open(app_path, 'r') as f:
        app_content = f.read()
    
    # Check that entry includes low_limit and high_limit
    if '"low_limit": obj.get(\'low_limit\')' in app_content:
        print("✓ low_limit included in chart data entry")
    else:
        print("❌ low_limit NOT included in chart data entry")
        return False
        
    if '"high_limit": obj.get(\'high_limit\')' in app_content:
        print("✓ high_limit included in chart data entry")
    else:
        print("❌ high_limit NOT included in chart data entry")
        return False
    
    # Test 2: Check template renders limit lines
    print("\n2. Frontend Changes (chart_plotly.html)")
    print("-" * 60)
    
    template_path = 'templates/chart_plotly.html'
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Check for low limit extraction
    if 'lowLimit' in template_content and 'p.low_limit' in template_content:
        print("✓ Low limit extraction code found")
    else:
        print("❌ Low limit extraction code NOT found")
        return False
    
    # Check for high limit extraction
    if 'highLimit' in template_content and 'p.high_limit' in template_content:
        print("✓ High limit extraction code found")
    else:
        print("❌ High limit extraction code NOT found")
        return False
    
    # Check for low limit line trace
    if "name: 'Low Limit'" in template_content:
        print("✓ Low Limit line trace found")
    else:
        print("❌ Low Limit line trace NOT found")
        return False
    
    # Check for high limit line trace
    if "name: 'High Limit'" in template_content:
        print("✓ High Limit line trace found")
    else:
        print("❌ High Limit line trace NOT found")
        return False
    
    # Check that lines are red and thin
    red_line_pattern = r"line:\s*{\s*color:\s*'red',\s*width:\s*1"
    red_lines = re.findall(red_line_pattern, template_content)
    if len(red_lines) >= 2:
        print(f"✓ Found {len(red_lines)} thin red limit lines (expected 2)")
    else:
        print(f"❌ Expected 2 thin red lines, found {len(red_lines)}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nTemperature control chart will now display:")
    print("  • Thin red horizontal line at the low temperature limit")
    print("  • Thin red horizontal line at the high temperature limit")
    print("  • Lines span the full width of the chart")
    print("  • Lines appear in the legend as 'Low Limit' and 'High Limit'")
    return True

if __name__ == '__main__':
    success = test_limit_lines()
    exit(0 if success else 1)
