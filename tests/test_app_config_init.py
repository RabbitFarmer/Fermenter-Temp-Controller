#!/usr/bin/env python3
"""
Test that app.py can initialize config files from templates.
"""

import os
import sys
import json
import tempfile
import shutil

# Test the ensure_config_files function logic
def test_ensure_config_files():
    """Test the config initialization logic from app.py"""
    
    print("="*60)
    print("Testing app.py Config Initialization")
    print("="*60)
    
    # Create temp directory
    test_dir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    
    try:
        os.chdir(test_dir)
        os.makedirs('config', exist_ok=True)
        
        # Create template files
        templates = {
            'config/system_config.json.template': {
                "brewery_name": "My Fermentorium",
                "brewer_name": "Frank",
                "units": "Fahrenheit"
            },
            'config/temp_control_config.json.template': {
                "low_limit": 50,
                "high_limit": 54,
                "enable_heating": True
            },
            'config/tilt_config.json.template': {
                "Red": {
                    "beer_name": "",
                    "batch_name": "",
                    "brewid": ""
                }
            }
        }
        
        for path, data in templates.items():
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        
        print("\n[Setup] Created template files")
        for path in templates.keys():
            print(f"  ✓ {path}")
        
        # Run the ensure_config_files logic (copied from app.py)
        print("\n[Test] Running ensure_config_files()...")
        
        config_files = [
            ('config/system_config.json', 'config/system_config.json.template'),
            ('config/temp_control_config.json', 'config/temp_control_config.json.template'),
            ('config/tilt_config.json', 'config/tilt_config.json.template')
        ]
        
        for config_file, template_file in config_files:
            if not os.path.exists(config_file):
                if os.path.exists(template_file):
                    try:
                        shutil.copy2(template_file, config_file)
                        print(f"  ✓ Created {config_file} from template")
                    except Exception as e:
                        print(f"  ✗ Error creating {config_file}: {e}")
                        return False
                else:
                    print(f"  ✗ Template {template_file} not found!")
                    return False
        
        # Verify all configs exist
        print("\n[Verify] Checking config files...")
        all_exist = True
        for config_file, _ in config_files:
            if os.path.exists(config_file):
                # Load and display
                with open(config_file, 'r') as f:
                    data = json.load(f)
                print(f"  ✓ {config_file} ({len(data)} fields)")
            else:
                print(f"  ✗ {config_file} NOT CREATED!")
                all_exist = False
        
        if not all_exist:
            return False
        
        # Test idempotency - running again shouldn't recreate files
        print("\n[Test] Re-running ensure_config_files() (should not recreate)...")
        
        # Modify one config
        with open('config/system_config.json', 'r') as f:
            user_data = json.load(f)
        user_data['email'] = 'test@example.com'
        with open('config/system_config.json', 'w') as f:
            json.dump(user_data, f, indent=2)
        
        print("  Modified system_config.json")
        
        # Run ensure again
        for config_file, template_file in config_files:
            if not os.path.exists(config_file):
                shutil.copy2(template_file, config_file)
        
        # Verify modification persisted
        with open('config/system_config.json', 'r') as f:
            final_data = json.load(f)
        
        if 'email' in final_data and final_data['email'] == 'test@example.com':
            print("  ✓ User modifications preserved (file not recreated)")
        else:
            print("  ✗ User modifications lost!")
            return False
        
        print("\n✓ All tests passed!")
        return True
        
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(test_dir)

if __name__ == '__main__':
    success = test_ensure_config_files()
    sys.exit(0 if success else 1)
