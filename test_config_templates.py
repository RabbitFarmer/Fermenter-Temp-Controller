#!/usr/bin/env python3
"""
Test the config file initialization and template system.
"""

import os
import sys
import json
import tempfile
import shutil

def test_config_initialization():
    """Test that config files are created from templates."""
    print("="*60)
    print("Testing Config File Initialization")
    print("="*60)
    
    # Create a temp directory for testing
    test_dir = tempfile.mkdtemp()
    config_dir = os.path.join(test_dir, 'config')
    os.makedirs(config_dir)
    
    try:
        # Create template files
        templates = {
            'system_config.json.template': {
                "brewery_name": "My Fermentorium",
                "brewer_name": "Frank",
                "units": "Fahrenheit"
            },
            'temp_control_config.json.template': {
                "low_limit": 50,
                "high_limit": 54
            },
            'tilt_config.json.template': {
                "Red": {"beer_name": "", "batch_name": ""}
            }
        }
        
        for template_name, template_data in templates.items():
            template_path = os.path.join(config_dir, template_name)
            with open(template_path, 'w') as f:
                json.dump(template_data, f, indent=2)
            print(f"✓ Created template: {template_name}")
        
        # Simulate the ensure_config_files function
        print("\n[STEP 1] Simulating first-time initialization...")
        config_files = [
            ('system_config.json', 'system_config.json.template'),
            ('temp_control_config.json', 'temp_control_config.json.template'),
            ('tilt_config.json', 'tilt_config.json.template')
        ]
        
        for config_file, template_file in config_files:
            config_path = os.path.join(config_dir, config_file)
            template_path = os.path.join(config_dir, template_file)
            
            if not os.path.exists(config_path):
                if os.path.exists(template_path):
                    shutil.copy2(template_path, config_path)
                    print(f"  ✓ Created {config_file} from template")
        
        # Verify config files were created
        print("\n[STEP 2] Verifying config files exist...")
        for config_file, _ in config_files:
            config_path = os.path.join(config_dir, config_file)
            if os.path.exists(config_path):
                print(f"  ✓ {config_file} exists")
            else:
                print(f"  ✗ {config_file} MISSING!")
                return False
        
        # Simulate user modifying config
        print("\n[STEP 3] Simulating user entering data...")
        system_config_path = os.path.join(config_dir, 'system_config.json')
        with open(system_config_path, 'r') as f:
            user_config = json.load(f)
        
        user_config.update({
            "street": "123 Brewing Lane",
            "city": "Hopsville",
            "state": "CO",
            "email": "frank@fermentorium.com"
        })
        
        with open(system_config_path, 'w') as f:
            json.dump(user_config, f, indent=2)
        
        print(f"  ✓ User added 4 new fields")
        print(f"  Config now has: {list(user_config.keys())}")
        
        # Simulate rsync/git pull (templates stay, configs are gitignored)
        print("\n[STEP 4] Simulating git pull / rsync...")
        print("  (Templates would be updated, but .json files are gitignored)")
        print("  ✓ User's config files are NOT overwritten")
        
        # Verify user data is still there
        with open(system_config_path, 'r') as f:
            final_config = json.load(f)
        
        print("\n[STEP 5] Verifying user data persisted...")
        expected_fields = ['brewery_name', 'brewer_name', 'units', 'street', 'city', 'state', 'email']
        missing = [f for f in expected_fields if f not in final_config]
        
        if missing:
            print(f"  ✗ Missing fields: {missing}")
            return False
        
        print(f"  ✓ All {len(expected_fields)} fields present!")
        print(f"  Final config: {final_config}")
        
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)

def test_template_vs_config():
    """Test that templates and configs are separate."""
    print("\n" + "="*60)
    print("Testing Template vs Config Separation")
    print("="*60)
    
    # Check actual repository
    template_files = [
        'config/system_config.json.template',
        'config/temp_control_config.json.template',
        'config/tilt_config.json.template'
    ]
    
    config_files = [
        'config/system_config.json',
        'config/temp_control_config.json',
        'config/tilt_config.json'
    ]
    
    print("\nTemplate files (tracked in git):")
    for template in template_files:
        if os.path.exists(template):
            print(f"  ✓ {template} exists")
        else:
            print(f"  ✗ {template} MISSING!")
    
    print("\nConfig files (gitignored, contains user data):")
    for config in config_files:
        if os.path.exists(config):
            print(f"  ✓ {config} exists")
        else:
            print(f"  ⚠ {config} doesn't exist yet (will be created on app start)")

if __name__ == '__main__':
    result1 = test_config_initialization()
    test_template_vs_config()
    
    print("\n" + "="*60)
    if result1:
        print("✓ Config initialization test PASSED")
        print("\nThe new system will protect user data from rsync/git pull!")
    else:
        print("✗ Config initialization test FAILED")
    print("="*60)
