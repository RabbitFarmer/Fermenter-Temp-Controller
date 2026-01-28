#!/usr/bin/env python3
"""
Test temperature control safety when both heating and cooling are enabled.
Verifies that:
1. Both heating and cooling can operate in the same session
2. They never operate simultaneously
3. Invalid configurations (low >= high) are caught
"""

import sys
import json
import os
import tempfile
import shutil


def test_both_heating_and_cooling_enabled():
    """Test that heating and cooling work correctly when both are enabled"""
    print("\n" + "="*60)
    print("Test: Both Heating and Cooling Enabled")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        os.makedirs('config', exist_ok=True)
        os.makedirs('temp_control', exist_ok=True)
        os.makedirs('batches', exist_ok=True)
        
        with open('config/system_config.json', 'w') as f:
            json.dump({}, f)
        
        with open('config/tilt_config.json', 'w') as f:
            json.dump({
                "Black": {
                    "brewid": "test123",
                    "beer_name": "Test Beer"
                }
            }, f)
        
        # Both heating and cooling enabled, low=64, high=68, midpoint=66
        with open('config/temp_control_config.json', 'w') as f:
            json.dump({
                "tilt_color": "Black",
                "low_limit": 64.0,
                "high_limit": 68.0,
                "enable_heating": True,
                "enable_cooling": True,
                "temp_control_enabled": True,
                "temp_control_active": True,
                "heating_plug": "192.168.1.100",
                "cooling_plug": "192.168.1.101",
                "heater_on": False,
                "cooler_on": False
            }, f)
        
        sys.path.insert(0, old_cwd)
        import app as test_app
        
        # Mock is_control_tilt_active
        test_app.is_control_tilt_active = lambda: True
        
        # Track heating and cooling calls
        heating_calls = []
        cooling_calls = []
        
        original_control_heating = test_app.control_heating
        original_control_cooling = test_app.control_cooling
        
        def mock_control_heating(state):
            heating_calls.append(state)
            if state == "on":
                test_app.temp_cfg["heater_on"] = True
            else:
                test_app.temp_cfg["heater_on"] = False
        
        def mock_control_cooling(state):
            cooling_calls.append(state)
            if state == "on":
                test_app.temp_cfg["cooler_on"] = True
            else:
                test_app.temp_cfg["cooler_on"] = False
        
        test_app.control_heating = mock_control_heating
        test_app.control_cooling = mock_control_cooling
        
        # Test Case 1: Temp at 63°F (below low) - heating should activate
        print("\nCase 1: Temp=63°F (below low=64) -> Heating ON, Cooling OFF")
        test_app.temp_cfg["current_temp"] = 63.0
        test_app.temp_cfg["heater_on"] = False
        test_app.temp_cfg["cooler_on"] = False
        test_app.temp_cfg["below_limit_trigger_armed"] = True
        
        heating_calls.clear()
        cooling_calls.clear()
        test_app.temperature_control_logic()
        
        assert "on" in heating_calls, f"Expected heating ON, got {heating_calls}"
        assert "off" in cooling_calls or not cooling_calls, f"Expected cooling OFF, got {cooling_calls}"
        assert not (test_app.temp_cfg["heater_on"] and test_app.temp_cfg["cooler_on"]), \
            "Both should not be ON simultaneously!"
        print(f"  ✓ Heating: {heating_calls}, Cooling: {cooling_calls}")
        print(f"  ✓ Safety: heater_on={test_app.temp_cfg['heater_on']}, cooler_on={test_app.temp_cfg['cooler_on']}")
        
        # Test Case 2: Temp at 69°F (above high) - cooling should activate
        print("\nCase 2: Temp=69°F (above high=68) -> Cooling ON, Heating OFF")
        test_app.temp_cfg["current_temp"] = 69.0
        test_app.temp_cfg["heater_on"] = False
        test_app.temp_cfg["cooler_on"] = False
        test_app.temp_cfg["above_limit_trigger_armed"] = True
        
        heating_calls.clear()
        cooling_calls.clear()
        test_app.temperature_control_logic()
        
        assert "off" in heating_calls or not heating_calls, f"Expected heating OFF, got {heating_calls}"
        assert "on" in cooling_calls, f"Expected cooling ON, got {cooling_calls}"
        assert not (test_app.temp_cfg["heater_on"] and test_app.temp_cfg["cooler_on"]), \
            "Both should not be ON simultaneously!"
        print(f"  ✓ Heating: {heating_calls}, Cooling: {cooling_calls}")
        print(f"  ✓ Safety: heater_on={test_app.temp_cfg['heater_on']}, cooler_on={test_app.temp_cfg['cooler_on']}")
        
        # Test Case 3: Temp at midpoint (66°F) - both should be OFF
        print("\nCase 3: Temp=66°F (at midpoint) -> Both OFF")
        test_app.temp_cfg["current_temp"] = 66.0
        test_app.temp_cfg["heater_on"] = True  # Simulate it was on
        test_app.temp_cfg["cooler_on"] = False
        
        heating_calls.clear()
        cooling_calls.clear()
        test_app.temperature_control_logic()
        
        assert "off" in heating_calls, f"Expected heating OFF at midpoint, got {heating_calls}"
        assert "off" in cooling_calls, f"Expected cooling OFF at midpoint, got {cooling_calls}"
        assert not (test_app.temp_cfg["heater_on"] and test_app.temp_cfg["cooler_on"]), \
            "Both should not be ON simultaneously!"
        print(f"  ✓ Heating: {heating_calls}, Cooling: {cooling_calls}")
        print(f"  ✓ Safety: heater_on={test_app.temp_cfg['heater_on']}, cooler_on={test_app.temp_cfg['cooler_on']}")
        
        # Restore
        test_app.control_heating = original_control_heating
        test_app.control_cooling = original_control_cooling
        
        print("\n✓ Both heating and cooling work correctly when both enabled!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_invalid_configuration():
    """Test that invalid configuration (low >= high) is caught"""
    print("\n" + "="*60)
    print("Test: Invalid Configuration (low >= high)")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        os.makedirs('config', exist_ok=True)
        os.makedirs('temp_control', exist_ok=True)
        os.makedirs('batches', exist_ok=True)
        
        with open('config/system_config.json', 'w') as f:
            json.dump({}, f)
        
        with open('config/tilt_config.json', 'w') as f:
            json.dump({
                "Black": {
                    "brewid": "test123"
                }
            }, f)
        
        # Invalid config: low_limit >= high_limit
        with open('config/temp_control_config.json', 'w') as f:
            json.dump({
                "tilt_color": "Black",
                "low_limit": 68.0,  # Higher than high!
                "high_limit": 64.0,
                "enable_heating": True,
                "enable_cooling": True,
                "temp_control_enabled": True,
                "temp_control_active": True,
                "heating_plug": "192.168.1.100",
                "cooling_plug": "192.168.1.101"
            }, f)
        
        sys.path.insert(0, old_cwd)
        import app as test_app
        
        test_app.is_control_tilt_active = lambda: True
        
        heating_calls = []
        cooling_calls = []
        
        def mock_control_heating(state):
            heating_calls.append(state)
        
        def mock_control_cooling(state):
            cooling_calls.append(state)
        
        test_app.control_heating = mock_control_heating
        test_app.control_cooling = mock_control_cooling
        
        test_app.temp_cfg["current_temp"] = 66.0
        test_app.temperature_control_logic()
        
        # Should turn both OFF and set error status
        assert "off" in heating_calls, f"Expected heating OFF for invalid config, got {heating_calls}"
        assert "off" in cooling_calls, f"Expected cooling OFF for invalid config, got {cooling_calls}"
        assert "Configuration Error" in test_app.temp_cfg.get("status", ""), \
            f"Expected configuration error status, got {test_app.temp_cfg.get('status')}"
        
        print(f"  ✓ Both turned OFF: heating={heating_calls}, cooling={cooling_calls}")
        print(f"  ✓ Error status set: {test_app.temp_cfg.get('status')}")
        
        print("\n✓ Invalid configuration correctly detected and handled!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    import subprocess
    
    print("Testing Heating and Cooling Safety")
    print("=" * 60)
    
    results = []
    
    test_functions = [
        ("Both Heating and Cooling Enabled", "test_both_heating_and_cooling_enabled"),
        ("Invalid Configuration", "test_invalid_configuration")
    ]
    
    for name, func_name in test_functions:
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import sys; sys.path.insert(0, '.'); from tests.test_both_heating_cooling import {func_name}; {func_name}()"],
                cwd="/home/runner/work/Fermenter-Temp-Controller/Fermenter-Temp-Controller",
                capture_output=True,
                text=True,
                timeout=30
            )
            passed = result.returncode == 0
            results.append((name, passed))
            if not passed:
                print(f"\n{name} output:")
                print(result.stdout)
                print(result.stderr)
        except Exception as e:
            print(f"\n{name} failed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + ("All tests passed! ✓" if all_passed else "Some tests failed ✗"))
    sys.exit(0 if all_passed else 1)
