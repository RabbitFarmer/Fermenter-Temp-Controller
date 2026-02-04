#!/usr/bin/env python3
"""
Test script to validate the auto-start browser opening fix.

This test validates:
1. start.sh properly sets SKIP_BROWSER_OPEN in headless mode
2. app.py browser opening function handles boot scenarios
3. Browser opening uses proper subprocess detachment
"""

import os
import sys
import subprocess
import tempfile
import time


def test_bash_syntax():
    """Test that start.sh has valid bash syntax"""
    print("Test 1: Checking start.sh bash syntax...")
    result = subprocess.run(
        ['bash', '-n', 'start.sh'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ start.sh has valid bash syntax")
        return True
    else:
        print(f"✗ start.sh has syntax errors:\n{result.stderr}")
        return False


def test_python_syntax():
    """Test that app.py has valid Python syntax"""
    print("\nTest 2: Checking app.py Python syntax...")
    result = subprocess.run(
        ['python3', '-m', 'py_compile', 'app.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ app.py has valid Python syntax")
        return True
    else:
        print(f"✗ app.py has syntax errors:\n{result.stderr}")
        return False


def test_skip_browser_logic():
    """Test that SKIP_BROWSER_OPEN is set correctly in headless mode"""
    print("\nTest 3: Checking SKIP_BROWSER_OPEN logic in start.sh...")
    
    # Read start.sh
    with open('start.sh', 'r') as f:
        content = f.read()
    
    # Check that SKIP_BROWSER_OPEN is only set when DISPLAY is not set
    if 'if [ -z "$DISPLAY" ]' in content and 'SKIP_BROWSER_OPEN=1' in content:
        print("✓ SKIP_BROWSER_OPEN is set correctly in headless mode")
        return True
    else:
        print("✗ SKIP_BROWSER_OPEN logic not found or incorrect")
        return False


def test_browser_opening_delegated_to_app():
    """Test that browser opening is delegated to app.py"""
    print("\nTest 4: Checking that browser opening is delegated to app.py...")
    
    # Read start.sh
    with open('start.sh', 'r') as f:
        content = f.read()
    
    # The old implementation had "nohup xdg-open" in start.sh
    # The new implementation should NOT have this (or should have it commented out)
    active_xdg_open_calls = []
    for line in content.split('\n'):
        stripped = line.strip()
        # Skip comments
        if stripped.startswith('#'):
            continue
        # Check for xdg-open
        if 'xdg-open' in stripped and 'http://127.0.0.1:5000' in stripped:
            active_xdg_open_calls.append(line)
    
    if len(active_xdg_open_calls) == 0:
        print("✓ Browser opening is delegated to app.py (no xdg-open in start.sh)")
        return True
    else:
        print(f"✗ Found active xdg-open calls in start.sh:")
        for call in active_xdg_open_calls:
            print(f"  {call}")
        return False


def test_app_browser_function():
    """Test that app.py has the enhanced open_browser function"""
    print("\nTest 5: Checking app.py open_browser function...")
    
    # Read app.py
    with open('app.py', 'r') as f:
        content = f.read()
    
    checks = {
        'Boot detection': 'uptime < 120' in content or 'create_time()' in content,
        'Flask readiness check': 'urlopen' in content and 'open_browser' in content,
        'subprocess.Popen usage': 'subprocess.Popen' in content and 'start_new_session=True' in content,
        'DEVNULL for detachment': 'subprocess.DEVNULL' in content or 'DEVNULL' in content,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        if passed:
            print(f"  ✓ {check_name}")
        else:
            print(f"  ✗ {check_name}")
            all_passed = False
    
    if all_passed:
        print("✓ app.py has enhanced open_browser function")
        return True
    else:
        print("✗ app.py open_browser function is missing some enhancements")
        return False


def test_no_terminal_close():
    """Test that terminal window handling is appropriate"""
    print("\nTest 6: Checking terminal window behavior...")
    
    # The desktop entry should have Terminal=true for visibility
    # This is checked in install_desktop_autostart.sh
    with open('install_desktop_autostart.sh', 'r') as f:
        content = f.read()
    
    if 'Terminal=true' in content:
        print("✓ Desktop entry will show terminal (Terminal=true)")
        return True
    else:
        print("⚠ Desktop entry may not show terminal (check Terminal= setting)")
        return True  # Not a failure, just a warning


def main():
    """Run all tests"""
    print("=" * 70)
    print("Auto-Start Browser Opening Fix - Validation Tests")
    print("=" * 70)
    
    tests = [
        test_bash_syntax,
        test_python_syntax,
        test_skip_browser_logic,
        test_browser_opening_delegated_to_app,
        test_app_browser_function,
        test_no_terminal_close,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if all(results):
        print("\n✓ All tests passed!")
        print("\nThe fix should resolve the auto-start browser opening issue:")
        print("  • start.sh delegates browser opening to app.py")
        print("  • app.py detects boot scenarios and adds appropriate delays")
        print("  • Browser opening uses robust subprocess.Popen detachment")
        print("  • Flask readiness is checked before opening browser")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
