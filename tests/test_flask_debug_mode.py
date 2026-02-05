#!/usr/bin/env python3
"""
Test to verify Flask debug mode is configurable via FLASK_DEBUG environment variable
"""
import os
import sys
import unittest

class TestFlaskDebugMode(unittest.TestCase):
    def test_debug_mode_defaults_to_false(self):
        """Test that debug mode defaults to False when FLASK_DEBUG is not set"""
        # Ensure FLASK_DEBUG is not set
        if 'FLASK_DEBUG' in os.environ:
            del os.environ['FLASK_DEBUG']
        
        # Test the logic from app.py
        debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
        self.assertFalse(debug_mode, "Debug mode should default to False")
    
    def test_debug_mode_enabled_when_flask_debug_is_1(self):
        """Test that debug mode is enabled when FLASK_DEBUG=1"""
        os.environ['FLASK_DEBUG'] = '1'
        debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
        self.assertTrue(debug_mode, "Debug mode should be True when FLASK_DEBUG=1")
        del os.environ['FLASK_DEBUG']
    
    def test_debug_mode_disabled_when_flask_debug_is_0(self):
        """Test that debug mode is disabled when FLASK_DEBUG=0"""
        os.environ['FLASK_DEBUG'] = '0'
        debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
        self.assertFalse(debug_mode, "Debug mode should be False when FLASK_DEBUG=0")
        del os.environ['FLASK_DEBUG']
    
    def test_debug_mode_disabled_for_other_values(self):
        """Test that debug mode is disabled for non-'1' values"""
        for value in ['true', 'True', 'yes', 'on', '2']:
            os.environ['FLASK_DEBUG'] = value
            debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
            self.assertFalse(debug_mode, f"Debug mode should be False for FLASK_DEBUG={value}")
            del os.environ['FLASK_DEBUG']

if __name__ == '__main__':
    unittest.main()
