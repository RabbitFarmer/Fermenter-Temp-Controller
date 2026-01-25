#!/usr/bin/env python3
"""
Test the display mode setting functionality.
"""

import json
import os
import sys

def test_display_mode_in_template():
    """Test that display_mode is in the system config template."""
    print("="*60)
    print("Testing Display Mode Setting")
    print("="*60)
    
    template_path = 'config/system_config.json.template'
    
    # Check template exists
    if not os.path.exists(template_path):
        print(f"✗ Template not found: {template_path}")
        return False
    
    # Load and check template
    with open(template_path, 'r') as f:
        template = json.load(f)
    
    print(f"\n[STEP 1] Checking template has display_mode field...")
    if 'display_mode' not in template:
        print(f"  ✗ display_mode field missing from template")
        return False
    
    print(f"  ✓ display_mode field found")
    print(f"  Default value: {template['display_mode']}")
    
    # Verify default value
    print(f"\n[STEP 2] Verifying default value...")
    if template['display_mode'] == "4":
        print(f"  ✓ Default is '4' (4-across mode)")
    else:
        print(f"  ⚠ Default is '{template['display_mode']}' (expected '4')")
    
    # Check system_config.html has the dropdown
    print(f"\n[STEP 3] Checking system_config.html template...")
    html_path = 'templates/system_config.html'
    
    if not os.path.exists(html_path):
        print(f"  ✗ Template not found: {html_path}")
        return False
    
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    required_elements = [
        ('display_mode', 'name="display_mode"'),
        ('4 Across option', '4 Across (Default)'),
        ('3 Across option', '3 Across (Large Numbers)')
    ]
    
    all_found = True
    for element_name, search_string in required_elements:
        if search_string in html_content:
            print(f"  ✓ Found {element_name}")
        else:
            print(f"  ✗ Missing {element_name}")
            all_found = False
    
    if not all_found:
        return False
    
    # Check maindisplay.html uses the setting
    print(f"\n[STEP 4] Checking maindisplay.html applies display mode...")
    display_path = 'templates/maindisplay.html'
    
    if not os.path.exists(display_path):
        print(f"  ✗ Template not found: {display_path}")
        return False
    
    with open(display_path, 'r') as f:
        display_content = f.read()
    
    if 'display-mode-' in display_content:
        print(f"  ✓ Display mode class is applied")
    else:
        print(f"  ✗ Display mode class not found")
        return False
    
    # Check CSS has the styles
    print(f"\n[STEP 5] Checking CSS has display mode styles...")
    css_path = 'static/styles.css'
    
    if not os.path.exists(css_path):
        print(f"  ✗ CSS file not found: {css_path}")
        return False
    
    with open(css_path, 'r') as f:
        css_content = f.read()
    
    required_css = [
        ('.display-mode-3', '.display-mode-3'),
        ('card width', '--card-width: 400px'),
        ('metric size', '--metric-number-size: 32px')
    ]
    
    all_found = True
    for css_name, search_string in required_css:
        if search_string in css_content:
            print(f"  ✓ Found {css_name}")
        else:
            print(f"  ✗ Missing {css_name}")
            all_found = False
    
    if not all_found:
        return False
    
    print(f"\n[STEP 6] All display mode components verified!")
    return True

if __name__ == '__main__':
    result = test_display_mode_in_template()
    
    print("\n" + "="*60)
    if result:
        print("✓ Display Mode test PASSED")
        print("\nUsers can now choose between:")
        print("  - 4 Across (Default): Standard compact layout")
        print("  - 3 Across (Large Numbers): Larger cards for distance viewing")
    else:
        print("✗ Display Mode test FAILED")
        sys.exit(1)
    print("="*60)
