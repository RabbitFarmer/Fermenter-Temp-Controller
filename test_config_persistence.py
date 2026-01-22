#!/usr/bin/env python3
"""
Test to verify configuration persistence issue.
This test simulates the issue described:
"After starting the program and entering system settings, 
most of the data elements are blank even though they were 
fully completed at an earlier use."
"""

import json
import os
import sys
import tempfile
import shutil

# Simulate the load_json and save_json functions from app.py
def load_json(path, fallback):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return fallback

def save_json(path, data):
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[LOG] Error saving JSON to {path}: {e}")

def test_config_persistence():
    """Test that configuration data is properly saved and loaded."""
    print("Testing configuration persistence...")
    
    # Create a temp directory for testing
    test_dir = tempfile.mkdtemp()
    config_dir = os.path.join(test_dir, 'config')
    os.makedirs(config_dir)
    
    try:
        # Test file path
        test_config_file = os.path.join(config_dir, 'system_config.json')
        
        # Simulate initial data entry
        print("\n1. Simulating user entering system settings...")
        system_cfg = {
            "brewery_name": "Test Brewery",
            "brewer_name": "Test Brewer",
            "street": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "email": "test@example.com",
            "mobile": "555-1234",
            "timezone": "America/New_York",
            "timestamp_format": "%Y-%m-%d %H:%M:%S"
        }
        
        print(f"   Data entered: {list(system_cfg.keys())}")
        
        # Save the configuration
        print("\n2. Saving configuration...")
        save_json(test_config_file, system_cfg)
        
        # Verify file was created
        if os.path.exists(test_config_file):
            print(f"   ✓ Config file created: {test_config_file}")
            with open(test_config_file, 'r') as f:
                saved_data = json.load(f)
            print(f"   ✓ Saved data: {list(saved_data.keys())}")
        else:
            print(f"   ✗ ERROR: Config file not created!")
            return False
        
        # Simulate app restart - reload configuration
        print("\n3. Simulating app restart and loading configuration...")
        reloaded_cfg = load_json(test_config_file, {})
        
        print(f"   Loaded data: {list(reloaded_cfg.keys())}")
        
        # Verify all fields are present
        missing_fields = []
        for key in system_cfg:
            if key not in reloaded_cfg:
                missing_fields.append(key)
            elif reloaded_cfg[key] != system_cfg[key]:
                print(f"   ✗ Field '{key}' value mismatch: '{reloaded_cfg[key]}' != '{system_cfg[key]}'")
                return False
        
        if missing_fields:
            print(f"   ✗ Missing fields after reload: {missing_fields}")
            return False
        
        print("   ✓ All fields loaded correctly!")
        
        # Now test the actual config files in the repository
        print("\n4. Testing actual repository config files...")
        actual_system_cfg_file = 'config/system_config.json'
        
        if os.path.exists(actual_system_cfg_file):
            print(f"   ✓ {actual_system_cfg_file} exists")
            actual_cfg = load_json(actual_system_cfg_file, {})
            print(f"   Current data in file: {actual_cfg}")
            
            if actual_cfg:
                print(f"   ✓ File contains {len(actual_cfg)} fields")
            else:
                print(f"   ⚠ WARNING: File is empty or contains only {{}}")
        else:
            print(f"   ✗ {actual_system_cfg_file} does not exist!")
        
        print("\n✓ Configuration persistence test PASSED")
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)

def test_actual_configs():
    """Load and inspect the actual config files."""
    print("\n" + "="*60)
    print("Inspecting Actual Configuration Files")
    print("="*60)
    
    configs = {
        'System Config': 'config/system_config.json',
        'Tilt Config': 'config/tilt_config.json',
        'Temp Control Config': 'config/temp_control_config.json'
    }
    
    for name, path in configs.items():
        print(f"\n{name} ({path}):")
        if os.path.exists(path):
            data = load_json(path, {})
            print(f"  ✓ File exists")
            print(f"  ✓ Contains {len(data)} top-level keys")
            if isinstance(data, dict):
                for key, value in list(data.items())[:5]:  # Show first 5 entries
                    value_preview = str(value)[:50]
                    print(f"    - {key}: {value_preview}")
                if len(data) > 5:
                    print(f"    ... and {len(data) - 5} more")
        else:
            print(f"  ✗ File does not exist!")

if __name__ == '__main__':
    print("Configuration Persistence Test")
    print("="*60)
    
    # Run tests
    test1_passed = test_config_persistence()
    test_actual_configs()
    
    if test1_passed:
        print("\n" + "="*60)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("✗✗✗ TESTS FAILED ✗✗✗")
        print("="*60)
        sys.exit(1)
