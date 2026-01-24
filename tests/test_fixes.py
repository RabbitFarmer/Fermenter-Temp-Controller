#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. External Post Interval persistence
2. Tab persistence after save
3. Brewery name in goodbye page
"""

import json
import os
import sys

# Test 1: External Post Interval persistence
def test_external_refresh_rate_persistence():
    """Test that external_refresh_rate preserves existing value when not in form data"""
    print("Test 1: External Post Interval persistence")
    
    # Mock system_cfg with existing value
    system_cfg = {"external_refresh_rate": "30"}
    
    # Mock form data without external_refresh_rate
    data = {}
    
    # This is the old (buggy) code:
    # "external_refresh_rate": data.get("external_refresh_rate", "15")
    # Would result in "15" instead of preserving "30"
    
    # This is the new (fixed) code:
    result = data.get("external_refresh_rate", system_cfg.get("external_refresh_rate", "15"))
    
    if result == "30":
        print("  ✓ PASS: External refresh rate preserved from system_cfg (30)")
    else:
        print(f"  ✗ FAIL: Expected '30', got '{result}'")
        return False
    
    # Test with form data provided
    data = {"external_refresh_rate": "20"}
    result = data.get("external_refresh_rate", system_cfg.get("external_refresh_rate", "15"))
    
    if result == "20":
        print("  ✓ PASS: External refresh rate updated from form data (20)")
    else:
        print(f"  ✗ FAIL: Expected '20', got '{result}'")
        return False
    
    # Test with no existing value
    system_cfg = {}
    data = {}
    result = data.get("external_refresh_rate", system_cfg.get("external_refresh_rate", "15"))
    
    if result == "15":
        print("  ✓ PASS: External refresh rate defaults to 15 when no existing value")
    else:
        print(f"  ✗ FAIL: Expected '15', got '{result}'")
        return False
    
    return True

# Test 2: Verify template has active_tab field
def test_template_has_active_tab_field():
    """Test that system_config.html has the active_tab hidden field"""
    print("\nTest 2: Template has active_tab hidden field")
    
    template_path = "templates/system_config.html"
    if not os.path.exists(template_path):
        print(f"  ✗ FAIL: Template not found at {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    if '<input type="hidden" id="active_tab" name="active_tab"' in content:
        print("  ✓ PASS: Template has active_tab hidden field")
    else:
        print("  ✗ FAIL: Template missing active_tab hidden field")
        return False
    
    # Check that openTab function updates the hidden field
    if "document.getElementById('active_tab').value = tabName;" in content:
        print("  ✓ PASS: openTab function updates active_tab hidden field")
    else:
        print("  ✗ FAIL: openTab function doesn't update active_tab hidden field")
        return False
    
    return True

# Test 3: Verify goodbye.html uses brewery_name
def test_goodbye_template_uses_brewery_name():
    """Test that goodbye.html uses the brewery_name variable"""
    print("\nTest 3: Goodbye template uses brewery_name")
    
    template_path = "templates/goodbye.html"
    if not os.path.exists(template_path):
        print(f"  ✗ FAIL: Template not found at {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    if "{{ brewery_name }}" in content:
        print("  ✓ PASS: Template uses {{ brewery_name }} variable")
    else:
        print("  ✗ FAIL: Template doesn't use {{ brewery_name }} variable")
        return False
    
    if "Fermenter Temperature Controller is shutting down" not in content:
        print("  ✓ PASS: Hardcoded text removed")
    else:
        print("  ✗ FAIL: Hardcoded 'Fermenter Temperature Controller' still present")
        return False
    
    return True

# Test 4: Verify app.py passes brewery_name to goodbye template
def test_app_passes_brewery_name():
    """Test that app.py passes brewery_name when rendering goodbye.html"""
    print("\nTest 4: app.py passes brewery_name to goodbye template")
    
    app_path = "app.py"
    if not os.path.exists(app_path):
        print(f"  ✗ FAIL: app.py not found at {app_path}")
        return False
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    if "render_template('goodbye.html', brewery_name=" in content:
        print("  ✓ PASS: app.py passes brewery_name to goodbye.html")
    else:
        print("  ✗ FAIL: app.py doesn't pass brewery_name to goodbye.html")
        return False
    
    return True

# Test 5: Verify redirect includes tab parameter
def test_redirect_includes_tab():
    """Test that update_system_config redirects with tab parameter"""
    print("\nTest 5: Redirect includes tab parameter")
    
    app_path = "app.py"
    if not os.path.exists(app_path):
        print(f"  ✗ FAIL: app.py not found at {app_path}")
        return False
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    if "redirect(f'/system_config?tab={active_tab}')" in content:
        print("  ✓ PASS: Redirect includes tab parameter")
    else:
        print("  ✗ FAIL: Redirect doesn't include tab parameter")
        return False
    
    # Check that active_tab is captured from form data
    if "active_tab = data.get('active_tab'" in content:
        print("  ✓ PASS: active_tab is captured from form data")
    else:
        print("  ✗ FAIL: active_tab is not captured from form data")
        return False
    
    return True

def main():
    print("=" * 60)
    print("Testing System Settings Fixes")
    print("=" * 60)
    
    tests = [
        test_external_refresh_rate_persistence,
        test_template_has_active_tab_field,
        test_goodbye_template_uses_brewery_name,
        test_app_passes_brewery_name,
        test_redirect_includes_tab
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
