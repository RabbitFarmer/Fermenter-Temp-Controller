#!/usr/bin/env python3
"""
Test to verify that Gmail authentication errors provide helpful error messages.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the system config before importing app
import unittest
from unittest.mock import Mock, patch, MagicMock

class TestGmailErrorMessages(unittest.TestCase):
    """Test that Gmail authentication errors provide helpful guidance."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.gmail_bad_credentials_error = (
            "535", 
            b"5.7.8 Username and Password not accepted. For more information, go to\n"
            b"5.7.8 https://support.google.com/mail/?p=BadCredentials 00721157ae682-793c66f326bsm83413277b3.19 - gsmtp"
        )
    
    @patch('smtplib.SMTP')
    def test_gmail_badcredentials_error_message(self, mock_smtp):
        """Test that Gmail BadCredentials error returns helpful message."""
        # Import app after patching
        import app as app_module
        
        # Set up mock system config
        app_module.system_cfg = {
            'sending_email': 'test@gmail.com',
            'email': 'recipient@example.com',
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_starttls': True,
            'smtp_password': 'wrong_password'
        }
        
        # Mock SMTP to raise authentication error
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        mock_server.login.side_effect = Exception(
            "(535, b'5.7.8 Username and Password not accepted. For more information, go to\\n"
            "5.7.8 https://support.google.com/mail/?p=BadCredentials 00721157ae682-793c66f326bsm83413277b3.19 - gsmtp')"
        )
        
        # Call _smtp_send
        success, error_msg = app_module._smtp_send(
            'recipient@example.com',
            'Test Subject',
            'Test Body'
        )
        
        # Verify the result
        self.assertFalse(success)
        self.assertIn('App Password', error_msg)
        self.assertIn('2-Factor Authentication', error_msg)
        self.assertIn('https://myaccount.google.com/apppasswords', error_msg)
        print("\n✓ Gmail BadCredentials error provides helpful App Password guidance")
    
    @patch('smtplib.SMTP')
    def test_gmail_535_error_message(self, mock_smtp):
        """Test that Gmail 535 error with gmail.com host returns helpful message."""
        # Import app after patching
        import app as app_module
        
        # Set up mock system config
        app_module.system_cfg = {
            'sending_email': 'test@gmail.com',
            'email': 'recipient@example.com',
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_starttls': True,
            'smtp_password': 'wrong_password'
        }
        
        # Mock SMTP to raise 535 error
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        mock_server.login.side_effect = Exception(
            "(535, b'Authentication failed')"
        )
        
        # Call _smtp_send
        success, error_msg = app_module._smtp_send(
            'recipient@example.com',
            'Test Subject',
            'Test Body'
        )
        
        # Verify the result
        self.assertFalse(success)
        self.assertIn('App Password', error_msg)
        self.assertIn('Gmail', error_msg)
        print("✓ Gmail 535 error provides helpful App Password guidance")
    
    @patch('smtplib.SMTP')
    def test_non_gmail_error_unchanged(self, mock_smtp):
        """Test that non-Gmail errors are returned as-is."""
        # Import app after patching
        import app as app_module
        
        # Set up mock system config for non-Gmail SMTP
        app_module.system_cfg = {
            'sending_email': 'test@example.com',
            'email': 'recipient@example.com',
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_starttls': True,
            'smtp_password': 'password'
        }
        
        # Mock SMTP to raise authentication error
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        original_error = "Authentication failed"
        mock_server.login.side_effect = Exception(original_error)
        
        # Call _smtp_send
        success, error_msg = app_module._smtp_send(
            'recipient@example.com',
            'Test Subject',
            'Test Body'
        )
        
        # Verify the result
        self.assertFalse(success)
        self.assertIn(original_error, error_msg)
        self.assertNotIn('App Password', error_msg)
        print("✓ Non-Gmail errors are returned without modification")

if __name__ == '__main__':
    print("=" * 80)
    print("Testing Gmail Error Message Improvements")
    print("=" * 80)
    unittest.main(verbosity=2)
