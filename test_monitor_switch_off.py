#!/usr/bin/env python3
"""
Test that turning OFF the monitor switch (temp_control_active) turns off heating/cooling plugs.

This test verifies the fix for the Issue 165 follow-up where the heater stayed on
even when the monitor switch was turned off.
"""

import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, call

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_monitor_switch_off_turns_off_plugs():
    """Test that turning off monitor switch turns off heating and cooling plugs."""
    
    print("\n" + "=" * 80)
    print("TEST: Monitor Switch OFF Should Turn Off Plugs")
    print("=" * 80)
    
    # Create temporary config files
    temp_cfg_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    system_cfg_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    
    try:
        # Write initial config with monitor ON and heater ON
        temp_cfg_file.write(json.dumps({
            "temp_control_active": True,
            "heater_on": True,
            "cooler_on": False,
            "enable_heating": True,
            "enable_cooling": False,
            "heating_plug": "http://192.168.1.100/",
            "cooling_plug": "",
            "low_limit": 70,
            "high_limit": 75,
            "current_temp": 68,
            "tilt_color": "Red"
        }))
        temp_cfg_file.close()
        
        system_cfg_file.write(json.dumps({}))
        system_cfg_file.close()
        
        # Mock the app module with necessary globals
        with patch.dict('sys.modules', {
            'logger': MagicMock(),
            'kasa_worker': MagicMock(),
            'batch_history': MagicMock(),
            'batch_storage': MagicMock(),
            'fermentation_monitor': MagicMock(),
        }):
            # Import app after mocking
            import app as app_module
            
            # Override config file paths
            app_module.TEMP_CFG_FILE = temp_cfg_file.name
            app_module.SYSTEM_CFG_FILE = system_cfg_file.name
            
            # Set up temp_cfg with initial state (heater ON, monitor ON)
            app_module.temp_cfg = {
                "temp_control_active": True,
                "heater_on": True,
                "cooler_on": False,
                "enable_heating": True,
                "enable_cooling": False,
                "heating_plug": "http://192.168.1.100/",
                "cooling_plug": "",
                "low_limit": 70,
                "high_limit": 75,
                "current_temp": 68,
                "tilt_color": "Red"
            }
            
            # Mock the control functions to track calls
            control_heating_calls = []
            control_cooling_calls = []
            
            original_control_heating = app_module.control_heating
            original_control_cooling = app_module.control_cooling
            
            def mock_control_heating(state):
                control_heating_calls.append(state)
                print(f"  [MOCK] control_heating('{state}') called")
                # Update the mock state
                if state == "off":
                    app_module.temp_cfg["heater_on"] = False
            
            def mock_control_cooling(state):
                control_cooling_calls.append(state)
                print(f"  [MOCK] control_cooling('{state}') called")
                # Update the mock state
                if state == "off":
                    app_module.temp_cfg["cooler_on"] = False
            
            app_module.control_heating = mock_control_heating
            app_module.control_cooling = mock_control_cooling
            
            # Mock append_control_log
            app_module.append_control_log = MagicMock()
            
            # Mock save_json
            app_module.save_json = MagicMock()
            
            print("\n1. Initial State:")
            print(f"   temp_control_active: {app_module.temp_cfg['temp_control_active']}")
            print(f"   heater_on: {app_module.temp_cfg['heater_on']}")
            print(f"   cooler_on: {app_module.temp_cfg['cooler_on']}")
            
            # Create Flask test client
            app_module.app.config['TESTING'] = True
            client = app_module.app.test_client()
            
            print("\n2. Turning OFF monitor switch...")
            # Turn OFF the monitor switch
            response = client.post('/toggle_temp_control',
                                    json={'active': False},
                                    content_type='application/json')
            
            print(f"   Response status: {response.status_code}")
            
            # Verify the response
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            response_data = json.loads(response.data)
            print(f"   Response data: {response_data}")
            
            print("\n3. Verifying Results:")
            print(f"   temp_control_active: {app_module.temp_cfg['temp_control_active']}")
            print(f"   heater_on: {app_module.temp_cfg['heater_on']}")
            print(f"   cooler_on: {app_module.temp_cfg['cooler_on']}")
            print(f"   control_heating calls: {control_heating_calls}")
            print(f"   control_cooling calls: {control_cooling_calls}")
            
            # Verify that:
            # 1. temp_control_active is now False
            assert app_module.temp_cfg['temp_control_active'] == False, \
                "temp_control_active should be False"
            
            # 2. control_heating("off") was called
            assert "off" in control_heating_calls, \
                "control_heating('off') should have been called"
            
            # 3. control_cooling("off") was called
            assert "off" in control_cooling_calls, \
                "control_cooling('off') should have been called"
            
            # 4. Heater state is now off
            assert app_module.temp_cfg['heater_on'] == False, \
                "heater_on should be False after turning off monitor"
            
            # 5. temp_control_stopped event was logged
            app_module.append_control_log.assert_any_call("temp_control_stopped", {
                "low_limit": app_module.temp_cfg.get("low_limit"),
                "current_temp": app_module.temp_cfg.get("current_temp"),
                "high_limit": app_module.temp_cfg.get("high_limit"),
                "tilt_color": app_module.temp_cfg.get("tilt_color", "")
            })
            
            print("\n✅ SUCCESS: Monitor switch OFF correctly turns off heating and cooling plugs!")
            print("   - temp_control_active set to False")
            print("   - control_heating('off') was called")
            print("   - control_cooling('off') was called")
            print("   - heater_on is now False")
            print("   - temp_control_stopped event was logged")
            
            return True
            
    finally:
        # Clean up temp files
        try:
            os.unlink(temp_cfg_file.name)
            os.unlink(system_cfg_file.name)
        except:
            pass

def test_monitor_switch_on_arms_triggers():
    """Test that turning on monitor switch arms triggers."""
    
    print("\n" + "=" * 80)
    print("TEST: Monitor Switch ON Should Arm Triggers")
    print("=" * 80)
    
    # Create temporary config files
    temp_cfg_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    system_cfg_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    
    try:
        # Write initial config with monitor OFF
        temp_cfg_file.write(json.dumps({
            "temp_control_active": False,
            "in_range_trigger_armed": False,
            "above_limit_trigger_armed": False,
            "below_limit_trigger_armed": False,
            "low_limit": 70,
            "high_limit": 75,
            "current_temp": 72,
            "tilt_color": "Blue"
        }))
        temp_cfg_file.close()
        
        system_cfg_file.write(json.dumps({}))
        system_cfg_file.close()
        
        # Mock the app module
        with patch.dict('sys.modules', {
            'logger': MagicMock(),
            'kasa_worker': MagicMock(),
            'batch_history': MagicMock(),
            'batch_storage': MagicMock(),
            'fermentation_monitor': MagicMock(),
        }):
            import app as app_module
            
            app_module.TEMP_CFG_FILE = temp_cfg_file.name
            app_module.SYSTEM_CFG_FILE = system_cfg_file.name
            
            app_module.temp_cfg = {
                "temp_control_active": False,
                "in_range_trigger_armed": False,
                "above_limit_trigger_armed": False,
                "below_limit_trigger_armed": False,
                "low_limit": 70,
                "high_limit": 75,
                "current_temp": 72,
                "tilt_color": "Blue"
            }
            
            app_module.append_control_log = MagicMock()
            app_module.save_json = MagicMock()
            
            print("\n1. Initial State:")
            print(f"   temp_control_active: {app_module.temp_cfg['temp_control_active']}")
            print(f"   in_range_trigger_armed: {app_module.temp_cfg['in_range_trigger_armed']}")
            print(f"   above_limit_trigger_armed: {app_module.temp_cfg['above_limit_trigger_armed']}")
            print(f"   below_limit_trigger_armed: {app_module.temp_cfg['below_limit_trigger_armed']}")
            
            app_module.app.config['TESTING'] = True
            client = app_module.app.test_client()
            
            print("\n2. Turning ON monitor switch...")
            response = client.post('/toggle_temp_control',
                                    json={'active': True},
                                    content_type='application/json')
            
            print(f"   Response status: {response.status_code}")
            assert response.status_code == 200
            
            print("\n3. Verifying Results:")
            print(f"   temp_control_active: {app_module.temp_cfg['temp_control_active']}")
            print(f"   in_range_trigger_armed: {app_module.temp_cfg['in_range_trigger_armed']}")
            print(f"   above_limit_trigger_armed: {app_module.temp_cfg['above_limit_trigger_armed']}")
            print(f"   below_limit_trigger_armed: {app_module.temp_cfg['below_limit_trigger_armed']}")
            
            assert app_module.temp_cfg['temp_control_active'] == True
            assert app_module.temp_cfg['in_range_trigger_armed'] == True
            assert app_module.temp_cfg['above_limit_trigger_armed'] == True
            assert app_module.temp_cfg['below_limit_trigger_armed'] == True
            
            # Verify temp_control_started event was logged
            app_module.append_control_log.assert_any_call("temp_control_started", {
                "low_limit": app_module.temp_cfg.get("low_limit"),
                "current_temp": app_module.temp_cfg.get("current_temp"),
                "high_limit": app_module.temp_cfg.get("high_limit"),
                "tilt_color": app_module.temp_cfg.get("tilt_color", "")
            })
            
            print("\n✅ SUCCESS: Monitor switch ON correctly arms all triggers!")
            print("   - temp_control_active set to True")
            print("   - All triggers armed")
            print("   - temp_control_started event was logged")
            
            return True
            
    finally:
        try:
            os.unlink(temp_cfg_file.name)
            os.unlink(system_cfg_file.name)
        except:
            pass

if __name__ == '__main__':
    try:
        print("Testing monitor switch OFF behavior (Issue 165 follow-up fix)...")
        test_monitor_switch_off_turns_off_plugs()
        
        print("\n")
        test_monitor_switch_on_arms_triggers()
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✅")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
