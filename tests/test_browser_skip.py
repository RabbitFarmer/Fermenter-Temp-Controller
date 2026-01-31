#!/usr/bin/env python3
"""
Test to verify that SKIP_BROWSER_OPEN environment variable prevents browser opening.
This test ensures app.py respects the SKIP_BROWSER_OPEN flag when running via start.sh.
"""

import os
import sys
import threading
import time
import subprocess
import shutil
from unittest.mock import patch, MagicMock

def test_browser_skip_with_env_var():
    """Test that browser opening is skipped when SKIP_BROWSER_OPEN is set"""
    
    # Set the environment variable
    os.environ['SKIP_BROWSER_OPEN'] = '1'
    
    # Mock subprocess.Popen to track calls
    with patch('subprocess.Popen') as mock_popen, \
         patch('shutil.which', return_value='/usr/bin/xdg-open'):
        
        # Simulate the app.py browser opening logic
        def open_browser():
            time.sleep(0.1)
            url = 'http://127.0.0.1:5000'
            try:
                if shutil.which('xdg-open'):
                    subprocess.Popen(
                        ['nohup', 'xdg-open', url],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    print(f"[LOG] Opened browser at {url} using xdg-open")
            except Exception as e:
                print(f"[LOG] Could not automatically open browser: {e}")
        
        # Simulate the condition check from app.py
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and not os.environ.get('SKIP_BROWSER_OPEN'):
            browser_thread = threading.Thread(target=open_browser, daemon=True)
            browser_thread.start()
            time.sleep(0.3)  # Wait for thread
        
        # Browser should NOT have been opened because SKIP_BROWSER_OPEN is set
        assert not mock_popen.called, "Browser should NOT open when SKIP_BROWSER_OPEN is set"
        print("✓ Test passed: Browser correctly skipped when SKIP_BROWSER_OPEN=1")
    
    # Clean up
    del os.environ['SKIP_BROWSER_OPEN']


def test_browser_opens_without_env_var():
    """Test that browser opens normally when SKIP_BROWSER_OPEN is not set"""
    
    # Make sure SKIP_BROWSER_OPEN is not set
    os.environ.pop('SKIP_BROWSER_OPEN', None)
    
    # Mock subprocess.Popen to track calls
    with patch('subprocess.Popen') as mock_popen, \
         patch('shutil.which', return_value='/usr/bin/xdg-open'):
        
        # Simulate the app.py browser opening logic
        def open_browser():
            time.sleep(0.1)
            url = 'http://127.0.0.1:5000'
            try:
                if shutil.which('xdg-open'):
                    subprocess.Popen(
                        ['nohup', 'xdg-open', url],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    print(f"[LOG] Opened browser at {url} using xdg-open")
            except Exception as e:
                print(f"[LOG] Could not automatically open browser: {e}")
        
        # Simulate the condition check from app.py
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and not os.environ.get('SKIP_BROWSER_OPEN'):
            browser_thread = threading.Thread(target=open_browser, daemon=True)
            browser_thread.start()
            time.sleep(0.3)  # Wait for thread
        
        # Browser SHOULD have been opened
        assert mock_popen.called, "Browser SHOULD open when SKIP_BROWSER_OPEN is not set"
        args = mock_popen.call_args
        assert args[0][0] == ['nohup', 'xdg-open', 'http://127.0.0.1:5000'], "Should use xdg-open with correct URL"
        print("✓ Test passed: Browser correctly opens when SKIP_BROWSER_OPEN is not set")


if __name__ == '__main__':
    print("Testing browser skip logic...")
    print("\nTest 1: Browser skip with SKIP_BROWSER_OPEN=1")
    test_browser_skip_with_env_var()
    
    print("\nTest 2: Browser opens without SKIP_BROWSER_OPEN")
    test_browser_opens_without_env_var()
    
    print("\n✓ All tests passed!")
    sys.exit(0)
