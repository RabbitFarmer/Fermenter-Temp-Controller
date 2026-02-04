"""
Test suite for dynamic chart Y-axis range functionality.

This test verifies that charts use automatic margin calculation
based on data range (10% or 5°F/0.002 SG minimum).
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, mock_open

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


class TestChartDynamicRanges(unittest.TestCase):
    """Test dynamic Y-axis range calculation for charts."""

    def setUp(self):
        """Set up test client."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_system_config_no_chart_margin_fields(self):
        """Test that chart margin fields have been removed from system config."""
        response = self.client.get('/system_config')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # These fields should no longer exist in the UI
        self.assertNotIn('chart_temp_margin', html)
        self.assertNotIn('Chart Temperature Margin', html)
        self.assertNotIn('chart_gravity_margin', html)
        self.assertNotIn('Chart Gravity Margin', html)

    def test_chart_uses_automatic_margin(self):
        """Test that chart uses automatic margin calculation."""
        response = self.client.get('/chart_plotly/Fermenter')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Should NOT have chartTempMargin or chartGravityMargin variables
        self.assertNotIn('chartTempMargin = ', html)
        self.assertNotIn('chartGravityMargin = ', html)
        
        # Should use automatic margin calculation (10% or 5°F minimum)
        self.assertIn('dataRange * 0.1', html)
        self.assertIn('Math.max(dataRange * 0.1, 5)', html)

    def test_chart_calculates_dynamic_temp_range(self):
        """Test that chart JavaScript includes automatic temperature range calculation."""
        response = self.client.get('/chart_plotly/Fermenter')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Check for automatic temperature range calculation logic
        # Should use: Math.max(dataRange * 0.1, 5)
        self.assertIn('const margin = Math.max(dataRange * 0.1, 5)', html)
        self.assertIn('tempMin - margin', html)
        self.assertIn('tempMax + margin', html)

    def test_chart_calculates_gravity_range(self):
        """Test that chart JavaScript includes gravity range calculation with hardcoded margin."""
        response = self.client.get('/chart_plotly/Fermenter')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Check for gravity range calculation logic with hardcoded 0.002
        self.assertIn('upperLimit += 0.002', html)
        self.assertIn('lowerLimit -= 0.002', html)

    def test_update_system_config_no_chart_margins(self):
        """Test that system config update works without chart margin fields."""
        test_data = {
            'active_tab': 'main-settings',
            'brewery_name': 'Test Brewery',
            'brewer_name': 'Test Brewer',
            'display_mode': '4',
            'update_interval': '2',  # Updated default
            'tilt_logging_interval_minutes': '15',
            'kasa_rate_limit_seconds': '10'
        }
        
        response = self.client.post('/update_system_config', data=test_data, follow_redirects=False)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)

    def test_update_interval_default_is_2_minutes(self):
        """Test that update_interval default has been corrected to 2 minutes."""
        response = self.client.get('/system_config')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Check that update_interval field exists with correct default
        self.assertIn('update_interval', html)
        # The default should be 2 when no value is set
        # This is checked by looking for the value attribute with default of '2'
        self.assertIn("get('update_interval','2')", html)


if __name__ == '__main__':
    unittest.main()
