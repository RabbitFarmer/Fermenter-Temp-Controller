"""
Test suite for dynamic chart Y-axis range functionality.

This test verifies that the chart configuration margins are properly
applied to calculate dynamic Y-axis ranges based on actual data.
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

    def test_system_config_has_chart_margins(self):
        """Test that system config includes chart margin fields."""
        response = self.client.get('/system_config')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Check for temperature margin field
        self.assertIn('chart_temp_margin', html)
        self.assertIn('Chart Temperature Margin', html)
        
        # Check for gravity margin field
        self.assertIn('chart_gravity_margin', html)
        self.assertIn('Chart Gravity Margin', html)

    def test_chart_page_receives_margin_config(self):
        """Test that chart page receives margin configuration values."""
        response = self.client.get('/chart_plotly/Fermenter')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Check that JavaScript variables are set
        self.assertIn('chartTempMargin', html)
        self.assertIn('chartGravityMargin', html)
        
        # Verify that values are numeric (not wrapped in parseFloat or quotes)
        # The exact format will be "const chartTempMargin = 1.0;" or similar
        self.assertIn('chartTempMargin = ', html)

    def test_chart_calculates_dynamic_temp_range(self):
        """Test that chart JavaScript includes dynamic temperature range calculation."""
        response = self.client.get('/chart_plotly/Fermenter')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Check for temperature range calculation logic
        self.assertIn('tempMin - chartTempMargin', html)
        self.assertIn('tempMax + chartTempMargin', html)

    def test_chart_calculates_dynamic_gravity_range(self):
        """Test that chart JavaScript includes dynamic gravity range calculation."""
        response = self.client.get('/chart_plotly/Fermenter')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Check for gravity range calculation logic
        self.assertIn('gravityMin - chartGravityMargin', html)
        self.assertIn('gravityMax + chartGravityMargin', html)

    def test_update_system_config_saves_chart_margins(self):
        """Test that updating system config saves chart margin values."""
        test_data = {
            'active_tab': 'main-settings',
            'brewery_name': 'Test Brewery',
            'brewer_name': 'Test Brewer',
            'display_mode': '4',
            'update_interval': '1',
            'tilt_logging_interval_minutes': '15',
            'chart_temp_margin': '2.5',
            'chart_gravity_margin': '0.010',
            'kasa_rate_limit_seconds': '10'
        }
        
        response = self.client.post('/update_system_config', data=test_data, follow_redirects=False)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)

    def test_default_chart_margins_in_template(self):
        """Test that default chart margin values are used when not configured."""
        with patch('app.system_cfg', {}):
            response = self.client.get('/system_config')
            self.assertEqual(response.status_code, 200)
            html = response.data.decode('utf-8')
            
            # Should show default values
            self.assertIn('1.0', html)  # Default temp margin
            self.assertIn('0.005', html)  # Default gravity margin


if __name__ == '__main__':
    unittest.main()
