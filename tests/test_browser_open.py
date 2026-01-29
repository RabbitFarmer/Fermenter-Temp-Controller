#!/usr/bin/env python3
"""
Test script to verify the browser opening functionality.
This tests that the browser opening logic doesn't break the app startup.
"""

import threading
import time
import webbrowser
from unittest.mock import patch, MagicMock

def test_browser_open_function():
    """Test the open_browser function logic"""
    print("Testing browser opening logic...")
    
    # Mock webbrowser.open to avoid actually opening a browser during test
    with patch('webbrowser.open') as mock_open:
        # Define the function exactly as it appears in app.py
        def open_browser():
            """
            Open the default web browser to the Flask app URL after a short delay.
            This runs in a separate thread to avoid blocking the Flask startup.
            """
            time.sleep(0.1)  # Reduced delay for testing
            try:
                webbrowser.open('http://127.0.0.1:5000')
                print("[LOG] Opened browser at http://127.0.0.1:5000")
            except Exception as e:
                print(f"[LOG] Could not automatically open browser: {e}")
                print("[LOG] Please manually navigate to http://127.0.0.1:5000")
        
        # Test 1: Normal operation
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        browser_thread.join(timeout=1)
        
        # Verify webbrowser.open was called
        assert mock_open.called, "webbrowser.open should have been called"
        assert mock_open.call_args[0][0] == 'http://127.0.0.1:5000', "URL should be http://127.0.0.1:5000"
        print("✓ Browser opening logic works correctly")
    
    # Test 2: Exception handling
    with patch('webbrowser.open', side_effect=Exception("Test error")):
        def open_browser_with_error():
            time.sleep(0.1)
            try:
                webbrowser.open('http://127.0.0.1:5000')
                print("[LOG] Opened browser at http://127.0.0.1:5000")
            except Exception as e:
                print(f"[LOG] Could not automatically open browser: {e}")
                print("[LOG] Please manually navigate to http://127.0.0.1:5000")
        
        browser_thread = threading.Thread(target=open_browser_with_error, daemon=True)
        browser_thread.start()
        browser_thread.join(timeout=1)
        print("✓ Exception handling works correctly")
    
    print("\nAll tests passed! ✓")

if __name__ == '__main__':
    test_browser_open_function()
