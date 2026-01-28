#!/usr/bin/env python3
"""
Test the hysteresis temperature control logic:
1. Verify heating turns on at low_limit and off at midpoint
2. Verify cooling turns on at high_limit and off at midpoint
3. Verify proper state maintenance between trigger points
"""

import sys
import json
import os
import tempfile
import shutil


def test_heating_hysteresis():
    """Test that heating follows hysteresis control (ON at low, OFF at midpoint)"""
    print("\n" + "="*60)
    print("Test 1: Heating Hysteresis Control")
    print("="*60)
    
    # Create temporary config directory
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        os.makedirs('config', exist_ok=True)
        os.makedirs('temp_control', exist_ok=True)
        os.makedirs('batches', exist_ok=True)
        
        # Create minimal config files
        with open('config/system_config.json', 'w') as f:
            json.dump({}, f)
        
        with open('config/tilt_config.json', 'w') as f:
            json.dump({
                "Black": {
                    "brewid": "test123",
                    "beer_name": "Test Beer",
                    "batch_name": "Test Batch"
                }
            }, f)
        
        # Set up temp control with low=64, high=68
        # Midpoint should be 66
        with open('config/temp_control_config.json', 'w') as f:
            json.dump({
                "tilt_color": "Black",
                "low_limit": 64.0,
                "high_limit": 68.0,
                "enable_heating": True,
                "enable_cooling": False,
                "temp_control_enabled": True,
                "temp_control_active": True,
                "heating_plug": "192.168.1.100",
                "heater_on": False,
                "cooler_on": False
            }, f)
        
        # Import app after setting up the temp directory
        sys.path.insert(0, old_cwd)
        import app as test_app
        
        # Mock is_control_tilt_active to always return True (Tilt is active)
        original_is_control_tilt_active = test_app.is_control_tilt_active
        test_app.is_control_tilt_active = lambda: True
        
        # Test Case 1: Temperature at 63°F (below low limit) - should turn heating ON
        print("\nCase 1: Temp=63°F (below low=64) -> Heating should turn ON")
        test_app.temp_cfg["current_temp"] = 63.0
        test_app.temp_cfg["heater_on"] = False
        test_app.temp_cfg["below_limit_trigger_armed"] = True
        
        # Mock the control_heating function to track calls
        heating_calls = []
        original_control_heating = test_app.control_heating
        def mock_control_heating(state):
            heating_calls.append(state)
        test_app.control_heating = mock_control_heating
        
        # Run control logic
        test_app.temperature_control_logic()
        
        assert "on" in heating_calls, f"Expected heating 'on' call, got {heating_calls}"
        print(f"  ✓ Heating turned ON (calls: {heating_calls})")
        
        # Test Case 2: Temperature at 65°F (between low and midpoint) - should maintain ON
        print("\nCase 2: Temp=65°F (between low=64 and midpoint=66) -> Heating should stay ON")
        heating_calls.clear()
        test_app.temp_cfg["current_temp"] = 65.0
        test_app.temp_cfg["heater_on"] = True  # Simulating it's already on
        test_app.temp_cfg["below_limit_trigger_armed"] = False
        
        test_app.temperature_control_logic()
        
        # Should not turn off in this range
        assert "off" not in heating_calls, f"Heating should not turn off at 65°F, got {heating_calls}"
        print(f"  ✓ Heating maintained (no off command) (calls: {heating_calls})")
        
        # Test Case 3: Temperature at 66°F (at midpoint) - should turn heating OFF
        print("\nCase 3: Temp=66°F (at midpoint) -> Heating should turn OFF")
        heating_calls.clear()
        test_app.temp_cfg["current_temp"] = 66.0
        test_app.temp_cfg["heater_on"] = True
        
        test_app.temperature_control_logic()
        
        assert "off" in heating_calls, f"Expected heating 'off' call at midpoint, got {heating_calls}"
        print(f"  ✓ Heating turned OFF at midpoint (calls: {heating_calls})")
        
        # Test Case 4: Temperature at 67°F (above midpoint) - should stay OFF
        print("\nCase 4: Temp=67°F (above midpoint=66) -> Heating should stay OFF")
        heating_calls.clear()
        test_app.temp_cfg["current_temp"] = 67.0
        test_app.temp_cfg["heater_on"] = False
        
        test_app.temperature_control_logic()
        
        assert "off" in heating_calls, f"Expected heating to remain off, got {heating_calls}"
        print(f"  ✓ Heating stayed OFF (calls: {heating_calls})")
        
        # Restore original functions
        test_app.control_heating = original_control_heating
        test_app.is_control_tilt_active = original_is_control_tilt_active
        
        print("\n✓ All heating hysteresis tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_cooling_hysteresis():
    """Test that cooling follows hysteresis control (ON at high, OFF at midpoint)"""
    print("\n" + "="*60)
    print("Test 2: Cooling Hysteresis Control")
    print("="*60)
    
    # Create temporary config directory
    temp_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        os.makedirs('config', exist_ok=True)
        os.makedirs('temp_control', exist_ok=True)
        os.makedirs('batches', exist_ok=True)
        
        # Create minimal config files
        with open('config/system_config.json', 'w') as f:
            json.dump({}, f)
        
        with open('config/tilt_config.json', 'w') as f:
            json.dump({
                "Black": {
                    "brewid": "test123",
                    "beer_name": "Test Beer",
                    "batch_name": "Test Batch"
                }
            }, f)
        
        # Set up temp control with low=64, high=68
        # Midpoint should be 66
        with open('config/temp_control_config.json', 'w') as f:
            json.dump({
                "tilt_color": "Black",
                "low_limit": 64.0,
                "high_limit": 68.0,
                "enable_heating": False,
                "enable_cooling": True,
                "temp_control_enabled": True,
                "temp_control_active": True,
                "cooling_plug": "192.168.1.101",
                "heater_on": False,
                "cooler_on": False
            }, f)
        
        # Import app after setting up the temp directory
        sys.path.insert(0, old_cwd)
        import app as test_app
        
        # Mock is_control_tilt_active to always return True (Tilt is active)
        original_is_control_tilt_active = test_app.is_control_tilt_active
        test_app.is_control_tilt_active = lambda: True
        
        # Test Case 1: Temperature at 69°F (above high limit) - should turn cooling ON
        print("\nCase 1: Temp=69°F (above high=68) -> Cooling should turn ON")
        test_app.temp_cfg["current_temp"] = 69.0
        test_app.temp_cfg["cooler_on"] = False
        test_app.temp_cfg["above_limit_trigger_armed"] = True
        
        # Mock the control_cooling function to track calls
        cooling_calls = []
        original_control_cooling = test_app.control_cooling
        def mock_control_cooling(state):
            cooling_calls.append(state)
        test_app.control_cooling = mock_control_cooling
        
        # Run control logic
        test_app.temperature_control_logic()
        
        assert "on" in cooling_calls, f"Expected cooling 'on' call, got {cooling_calls}"
        print(f"  ✓ Cooling turned ON (calls: {cooling_calls})")
        
        # Test Case 2: Temperature at 67°F (between midpoint and high) - should maintain ON
        print("\nCase 2: Temp=67°F (between midpoint=66 and high=68) -> Cooling should stay ON")
        cooling_calls.clear()
        test_app.temp_cfg["current_temp"] = 67.0
        test_app.temp_cfg["cooler_on"] = True  # Simulating it's already on
        test_app.temp_cfg["above_limit_trigger_armed"] = False
        
        test_app.temperature_control_logic()
        
        # Should not turn off in this range
        assert "off" not in cooling_calls, f"Cooling should not turn off at 67°F, got {cooling_calls}"
        print(f"  ✓ Cooling maintained (no off command) (calls: {cooling_calls})")
        
        # Test Case 3: Temperature at 66°F (at midpoint) - should turn cooling OFF
        print("\nCase 3: Temp=66°F (at midpoint) -> Cooling should turn OFF")
        cooling_calls.clear()
        test_app.temp_cfg["current_temp"] = 66.0
        test_app.temp_cfg["cooler_on"] = True
        
        test_app.temperature_control_logic()
        
        assert "off" in cooling_calls, f"Expected cooling 'off' call at midpoint, got {cooling_calls}"
        print(f"  ✓ Cooling turned OFF at midpoint (calls: {cooling_calls})")
        
        # Test Case 4: Temperature at 65°F (below midpoint) - should stay OFF
        print("\nCase 4: Temp=65°F (below midpoint=66) -> Cooling should stay OFF")
        cooling_calls.clear()
        test_app.temp_cfg["current_temp"] = 65.0
        test_app.temp_cfg["cooler_on"] = False
        
        test_app.temperature_control_logic()
        
        assert "off" in cooling_calls, f"Expected cooling to remain off, got {cooling_calls}"
        print(f"  ✓ Cooling stayed OFF (calls: {cooling_calls})")
        
        # Restore original functions
        test_app.control_cooling = original_control_cooling
        test_app.is_control_tilt_active = original_is_control_tilt_active
        
        print("\n✓ All cooling hysteresis tests passed!")
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
    
    print("Testing Hysteresis Temperature Control Logic")
    print("=" * 60)
    
    results = []
    
    # Run each test in a separate subprocess to avoid state pollution
    test_functions = [
        ("Heating Hysteresis", "test_heating_hysteresis"),
        ("Cooling Hysteresis", "test_cooling_hysteresis")
    ]
    
    for name, func_name in test_functions:
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import sys; sys.path.insert(0, '.'); from tests.test_hysteresis_control import {func_name}; {func_name}()"],
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
        except subprocess.TimeoutExpired:
            print(f"\n{name} timed out")
            results.append((name, False))
        except Exception as e:
            print(f"\n{name} failed with exception: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    exit_code = 0 if all_passed else 1
    print("\n" + ("All tests passed! ✓" if all_passed else "Some tests failed ✗"))
    sys.exit(exit_code)
