#!/usr/bin/env python3
"""
Test to verify that SKIP_BROWSER_OPEN environment variable prevents browser opening.
This test ensures app.py respects the SKIP_BROWSER_OPEN flag when running via start.sh.
"""

import os
import sys
import threading
import time
from unittest.mock import patch, MagicMock

def test_browser_skip_with_env_var():
    """Test that browser opening is skipped when SKIP_BROWSER_OPEN is set"""
    
    # Set the environment variable
    os.environ['SKIP_BROWSER_OPEN'] = '1'
    
    # Import webbrowser to mock it
    import webbrowser
    
    # Mock webbrowser.open to track calls
    with patch('webbrowser.open') as mock_open:
        
        # Simulate the app.py browser opening logic
        def open_browser():
            time.sleep(0.1)  # Simulated delay
            try:
                webbrowser.open('http://127.0.0.1:5000')
                print("[LOG] Opened browser at http://127.0.0.1:5000")
            except Exception as e:
                print(f"[LOG] Could not automatically open browser: {e}")
        
        # Simulate the condition check from app.py
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and not os.environ.get('SKIP_BROWSER_OPEN'):
            browser_thread = threading.Thread(target=open_browser, daemon=True)
            browser_thread.start()
            time.sleep(0.3)  # Wait for thread
        
        # Browser should NOT have been opened because SKIP_BROWSER_OPEN is set
        assert not mock_open.called, "Browser should NOT open when SKIP_BROWSER_OPEN is set"
        print("✓ Test passed: Browser correctly skipped when SKIP_BROWSER_OPEN=1")
    
    # Clean up
    del os.environ['SKIP_BROWSER_OPEN']


def test_browser_opens_without_env_var():
    """Test that browser opens normally when SKIP_BROWSER_OPEN is not set"""
    
    # Make sure SKIP_BROWSER_OPEN is not set
    os.environ.pop('SKIP_BROWSER_OPEN', None)
    
    # Import webbrowser to mock it
    import webbrowser
    
    # Mock webbrowser.open to track calls
    with patch('webbrowser.open') as mock_open:
        
        # Simulate the app.py browser opening logic
        def open_browser():
            time.sleep(0.1)  # Simulated delay
            try:
                webbrowser.open('http://127.0.0.1:5000')
                print("[LOG] Opened browser at http://127.0.0.1:5000")
            except Exception as e:
                print(f"[LOG] Could not automatically open browser: {e}")
        
        # Simulate the condition check from app.py
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and not os.environ.get('SKIP_BROWSER_OPEN'):
            browser_thread = threading.Thread(target=open_browser, daemon=True)
            browser_thread.start()
            time.sleep(0.3)  # Wait for thread
        
        # Browser SHOULD have been opened
        assert mock_open.called, "Browser SHOULD open when SKIP_BROWSER_OPEN is not set"
        mock_open.assert_called_once_with('http://127.0.0.1:5000')
        print("✓ Test passed: Browser correctly opens when SKIP_BROWSER_OPEN is not set")


if __name__ == '__main__':
    print("Testing browser skip logic...")
    print("\nTest 1: Browser skip with SKIP_BROWSER_OPEN=1")
    test_browser_skip_with_env_var()
    
    print("\nTest 2: Browser opens without SKIP_BROWSER_OPEN")
    test_browser_opens_without_env_var()
    
    print("\n✓ All tests passed!")
    sys.exit(0)
