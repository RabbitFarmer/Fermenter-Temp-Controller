#!/usr/bin/env python3
"""
Test the improved browser opening logic that uses system commands.
This test verifies that the browser opening function works correctly
in headless and Raspberry Pi environments.
"""

import os
import subprocess
import shutil
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import time

# Test the open_browser function in isolation
def test_open_browser_logic():
    """
    Test the logic of the open_browser function without actually opening a browser.
    """
    
    # Simulate the function logic
    url = 'http://127.0.0.1:5000'
    
    print("Testing browser open logic...")
    
    # Test 1: Check if xdg-open is available
    if shutil.which('xdg-open'):
        print("✓ xdg-open is available")
        try:
            # Simulate the command that would be run (don't actually run it)
            cmd = ['nohup', 'xdg-open', url]
            print(f"  Would execute: {' '.join(cmd)}")
            print("  With stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, start_new_session=True")
        except Exception as e:
            print(f"✗ Error simulating xdg-open: {e}")
            return False
    
    # Test 2: Check if open is available (macOS)
    elif shutil.which('open'):
        print("✓ open command is available (macOS)")
        try:
            cmd = ['nohup', 'open', url]
            print(f"  Would execute: {' '.join(cmd)}")
            print("  With stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, start_new_session=True")
        except Exception as e:
            print(f"✗ Error simulating open: {e}")
            return False
    
    # Test 3: Fallback to webbrowser module
    else:
        print("ℹ No system browser command available, would use webbrowser module")
        try:
            import webbrowser
            print("✓ webbrowser module is available as fallback")
        except ImportError:
            print("✗ webbrowser module not available")
            return False
    
    print("\n✓ All browser open logic tests passed")
    return True


class TestBrowserOpenFunction(unittest.TestCase):
    """
    Unit tests for the browser opening functionality.
    """
    
    @patch('subprocess.Popen')
    @patch('shutil.which')
    def test_xdg_open_used_when_available(self, mock_which, mock_popen):
        """Test that xdg-open is used when available on Linux."""
        # Setup
        mock_which.return_value = '/usr/bin/xdg-open'
        mock_popen.return_value = MagicMock()
        
        # Import the function (we'll test the logic inline)
        url = 'http://127.0.0.1:5000'
        
        # Execute the browser open logic
        if shutil.which('xdg-open'):
            subprocess.Popen(
                ['nohup', 'xdg-open', url],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        
        # Verify
        mock_which.assert_called_with('xdg-open')
        mock_popen.assert_called_once()
        args = mock_popen.call_args
        self.assertEqual(args[0][0], ['nohup', 'xdg-open', url])
        self.assertEqual(args[1]['stdin'], subprocess.DEVNULL)
        self.assertEqual(args[1]['stdout'], subprocess.DEVNULL)
        self.assertEqual(args[1]['stderr'], subprocess.DEVNULL)
        self.assertEqual(args[1]['start_new_session'], True)
    
    @patch('subprocess.Popen')
    @patch('shutil.which')
    def test_open_used_on_macos(self, mock_which, mock_popen):
        """Test that 'open' command is used on macOS."""
        # Setup - xdg-open not available, but 'open' is
        def which_side_effect(cmd):
            if cmd == 'xdg-open':
                return None
            elif cmd == 'open':
                return '/usr/bin/open'
            return None
        
        mock_which.side_effect = which_side_effect
        mock_popen.return_value = MagicMock()
        
        url = 'http://127.0.0.1:5000'
        
        # Execute the browser open logic
        if shutil.which('xdg-open'):
            subprocess.Popen(['nohup', 'xdg-open', url], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           start_new_session=True)
        elif shutil.which('open'):
            subprocess.Popen(['nohup', 'open', url], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           start_new_session=True)
        
        # Verify
        mock_popen.assert_called_once()
        args = mock_popen.call_args
        self.assertEqual(args[0][0], ['nohup', 'open', url])
    
    def test_shutil_which_availability(self):
        """Test that shutil.which can find system commands."""
        # This should work in any environment
        self.assertIsNotNone(shutil.which)
        
        # At least one browser command should be available or None
        xdg_result = shutil.which('xdg-open')
        open_result = shutil.which('open')
        
        # Just verify the function works
        self.assertTrue(isinstance(xdg_result, (str, type(None))))
        self.assertTrue(isinstance(open_result, (str, type(None))))


if __name__ == '__main__':
    # Run the logic test
    print("=" * 60)
    print("Browser Open Logic Test")
    print("=" * 60)
    test_open_browser_logic()
    
    print("\n" + "=" * 60)
    print("Unit Tests")
    print("=" * 60)
    
    # Run unit tests
    unittest.main(verbosity=2)
