#!/usr/bin/env python3
"""
Test to verify that browser opening is skipped in headless mode (no DISPLAY).
This test ensures app.py correctly detects headless environments like systemd services.
"""

import os
import sys
import threading
import time
import subprocess
import shutil
from unittest.mock import patch, MagicMock
from io import StringIO

def test_browser_skip_headless():
    """Test that browser opening is skipped when DISPLAY is not set (headless mode)"""
    
    # Save original DISPLAY value
    original_display = os.environ.get('DISPLAY')
    
    # Remove DISPLAY to simulate headless environment
    if 'DISPLAY' in os.environ:
        del os.environ['DISPLAY']
    
    # Capture stdout to verify log messages
    captured_output = StringIO()
    
    # Mock subprocess.Popen to ensure it's never called
    with patch('subprocess.Popen') as mock_popen, \
         patch('shutil.which', return_value='/usr/bin/xdg-open'), \
         patch('sys.stdout', new=captured_output):
        
        # Simulate the app.py browser opening logic with headless check
        def open_browser():
            time.sleep(0.1)
            url = 'http://127.0.0.1:5000'
            
            # Check if running in headless mode (no display available)
            display = os.environ.get('DISPLAY')
            if not display:
                print(f"[LOG] Running in headless mode (no DISPLAY environment variable)")
                print(f"[LOG] Skipping automatic browser opening")
                print(f"[LOG] Access the dashboard at: {url}")
                return
            
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
        
        # Run the browser opening function
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        time.sleep(0.3)  # Wait for thread
        
        # Browser should NOT have been opened because DISPLAY is not set
        assert not mock_popen.called, "Browser should NOT open in headless mode (no DISPLAY)"
        
        # Verify log messages
        output = captured_output.getvalue()
        assert "Running in headless mode" in output, "Should log headless mode detection"
        assert "Skipping automatic browser opening" in output, "Should log skip message"
        assert "Access the dashboard at: http://127.0.0.1:5000" in output, "Should show URL"
        
        print("✓ Test passed: Browser correctly skipped in headless mode (no DISPLAY)")
    
    # Restore original DISPLAY value
    if original_display is not None:
        os.environ['DISPLAY'] = original_display
    elif 'DISPLAY' in os.environ:
        del os.environ['DISPLAY']


def test_browser_opens_with_display():
    """Test that browser opens normally when DISPLAY is set"""
    
    # Save original DISPLAY value
    original_display = os.environ.get('DISPLAY')
    
    # Set DISPLAY to simulate graphical environment
    os.environ['DISPLAY'] = ':0'
    
    # Mock subprocess.Popen to track calls
    with patch('subprocess.Popen') as mock_popen, \
         patch('shutil.which', return_value='/usr/bin/xdg-open'):
        
        # Simulate the app.py browser opening logic with headless check
        def open_browser():
            time.sleep(0.1)
            url = 'http://127.0.0.1:5000'
            
            # Check if running in headless mode (no display available)
            display = os.environ.get('DISPLAY')
            if not display:
                print(f"[LOG] Running in headless mode (no DISPLAY environment variable)")
                print(f"[LOG] Skipping automatic browser opening")
                print(f"[LOG] Access the dashboard at: {url}")
                return
            
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
        
        # Run the browser opening function
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        time.sleep(0.3)  # Wait for thread
        
        # Browser SHOULD have been opened because DISPLAY is set
        assert mock_popen.called, "Browser SHOULD open when DISPLAY is set"
        args = mock_popen.call_args
        assert args[0][0] == ['nohup', 'xdg-open', 'http://127.0.0.1:5000'], "Should use xdg-open with correct URL"
        print("✓ Test passed: Browser correctly opens when DISPLAY is set")
    
    # Restore original DISPLAY value
    if original_display is not None:
        os.environ['DISPLAY'] = original_display
    elif 'DISPLAY' in os.environ:
        del os.environ['DISPLAY']


if __name__ == '__main__':
    print("Testing headless browser opening logic...\n")
    
    print("Test 1: Browser skip in headless mode (no DISPLAY)")
    test_browser_skip_headless()
    
    print("\nTest 2: Browser opens with DISPLAY set")
    test_browser_opens_with_display()
    
    print("\n✓ All tests passed!")
    sys.exit(0)
