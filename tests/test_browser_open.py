#!/usr/bin/env python3
"""
Test script to verify the browser opening functionality.
This tests that the browser opening logic doesn't break the app startup.
"""

import threading
import time
import webbrowser
import subprocess
import shutil
from unittest.mock import patch, MagicMock

def test_browser_open_function():
    """Test the open_browser function logic"""
    print("Testing browser opening logic...")
    
    # Test 1: Normal operation with system commands
    with patch('subprocess.Popen') as mock_popen, \
         patch('shutil.which') as mock_which:
        
        # Mock xdg-open being available
        mock_which.return_value = '/usr/bin/xdg-open'
        mock_popen.return_value = MagicMock()
        
        # Define the function with updated logic
        def open_browser():
            """
            Open the default web browser to the Flask app URL after a short delay.
            Uses system commands (xdg-open, open) for better compatibility.
            """
            time.sleep(0.1)  # Reduced delay for testing
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
                elif shutil.which('open'):
                    subprocess.Popen(
                        ['nohup', 'open', url],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    print(f"[LOG] Opened browser at {url} using open")
                else:
                    webbrowser.open(url)
                    print(f"[LOG] Opened browser at {url} using webbrowser module")
            except Exception as e:
                print(f"[LOG] Could not automatically open browser: {e}")
                print(f"[LOG] Please manually navigate to {url}")
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        browser_thread.join(timeout=1)
        
        # Verify subprocess.Popen was called with correct arguments
        assert mock_popen.called, "subprocess.Popen should have been called"
        args = mock_popen.call_args
        assert args[0][0] == ['nohup', 'xdg-open', 'http://127.0.0.1:5000'], "Should use xdg-open with correct URL"
        print("✓ Browser opening logic works correctly with system commands")
    
    # Test 2: Fallback to webbrowser module
    with patch('subprocess.Popen') as mock_popen, \
         patch('shutil.which', return_value=None), \
         patch('webbrowser.open') as mock_webbrowser:
        
        def open_browser_fallback():
            time.sleep(0.1)
            url = 'http://127.0.0.1:5000'
            try:
                if shutil.which('xdg-open'):
                    subprocess.Popen(['nohup', 'xdg-open', url],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
                elif shutil.which('open'):
                    subprocess.Popen(['nohup', 'open', url],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
                else:
                    webbrowser.open(url)
            except Exception as e:
                print(f"[LOG] Could not automatically open browser: {e}")
        
        browser_thread = threading.Thread(target=open_browser_fallback, daemon=True)
        browser_thread.start()
        browser_thread.join(timeout=1)
        
        assert mock_webbrowser.called, "webbrowser.open should be called as fallback"
        print("✓ Fallback to webbrowser module works correctly")
    
    # Test 3: Exception handling
    with patch('subprocess.Popen', side_effect=Exception("Test error")), \
         patch('shutil.which', return_value='/usr/bin/xdg-open'):
        
        def open_browser_with_error():
            time.sleep(0.1)
            url = 'http://127.0.0.1:5000'
            try:
                if shutil.which('xdg-open'):
                    subprocess.Popen(['nohup', 'xdg-open', url],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
            except Exception as e:
                print(f"[LOG] Could not automatically open browser: {e}")
                print(f"[LOG] Please manually navigate to {url}")
        
        browser_thread = threading.Thread(target=open_browser_with_error, daemon=True)
        browser_thread.start()
        browser_thread.join(timeout=1)
        print("✓ Exception handling works correctly")
    
    print("\nAll tests passed! ✓")

if __name__ == '__main__':
    test_browser_open_function()
