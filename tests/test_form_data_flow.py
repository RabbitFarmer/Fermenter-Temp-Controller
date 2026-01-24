#!/usr/bin/env python3
"""
Test to simulate the exact data flow when a user:
1. Starts the app (loads configs)
2. Navigates to system settings (displays form)
3. Fills in and saves the form
4. Navigates away and back to system settings (reloads form)
"""

import json
import os
import tempfile
import shutil

def load_json(path, fallback):
    """Exact copy of load_json from app.py"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return fallback

def save_json(path, data):
    """Exact copy of save_json from app.py"""
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[LOG] Error saving JSON to {path}: {e}")

def simulate_update_system_config(system_cfg, form_data, SYSTEM_CFG_FILE):
    """Simulates the update_system_config route from app.py (simplified)"""
    
    # Handle password field - only update if provided
    sending_email_password = form_data.get("sending_email_password", "")
    if sending_email_password:
        system_cfg["smtp_password"] = sending_email_password
    
    system_cfg.update({
        "brewery_name": form_data.get("brewery_name", ""),
        "brewer_name": form_data.get("brewer_name", ""),
        "street": form_data.get("street", ""),
        "city": form_data.get("city", ""),
        "state": form_data.get("state", ""),
        "email": form_data.get("email", ""),
        "mobile": form_data.get("mobile", ""),
        "timezone": form_data.get("timezone", ""),
        "timestamp_format": form_data.get("timestamp_format", ""),
        "update_interval": form_data.get("update_interval", "1"),
    })
    
    save_json(SYSTEM_CFG_FILE, system_cfg)
    return system_cfg

def test_complete_workflow():
    """Test the complete workflow from user perspective"""
    
    print("="*60)
    print("SIMULATING COMPLETE USER WORKFLOW")
    print("="*60)
    
    # Create a temp directory for testing
    test_dir = tempfile.mkdtemp()
    config_dir = os.path.join(test_dir, 'config')
    os.makedirs(config_dir)
    SYSTEM_CFG_FILE = os.path.join(config_dir, 'system_config.json')
    
    try:
        # Step 1: Initial app start with minimal config (like the actual repo)
        print("\n[STEP 1] App starts with minimal config file")
        initial_config = {
            "brewery_name": "My Fermentorium",
            "brewer_name": "Frank",
            "units": "Fahrenheit"
        }
        save_json(SYSTEM_CFG_FILE, initial_config)
        print(f"  Initial config: {list(initial_config.keys())}")
        
        # Step 2: Load config (module level in app.py)
        print("\n[STEP 2] Loading configuration at module level...")
        system_cfg = load_json(SYSTEM_CFG_FILE, {})
        print(f"  Loaded system_cfg: {system_cfg}")
        
        # Step 3: User navigates to /system_config
        print("\n[STEP 3] User navigates to /system_config page")
        print(f"  Template receives system_settings={system_cfg}")
        print(f"  Form fields populated:")
        for field in ['brewery_name', 'brewer_name', 'street', 'city', 'state']:
            value = system_cfg.get(field, '')
            print(f"    {field}: '{value}' (blank={not value})")
        
        # Step 4: User fills in the form
        print("\n[STEP 4] User fills in form and submits")
        form_data = {
            "brewery_name": "My Fermentorium",  # Keep existing
            "brewer_name": "Frank",  # Keep existing
            "street": "123 Brewing Lane",  # NEW
            "city": "Hopsville",  # NEW
            "state": "CO",  # NEW
            "email": "frank@fermentorium.com",  # NEW
            "mobile": "555-BREW",  # NEW
            "timezone": "America/Denver",  # NEW
            "timestamp_format": "%Y-%m-%d %H:%M:%S",  # NEW
            "update_interval": "1"
        }
        print(f"  Form data submitted: {list(form_data.keys())}")
        
        # Step 5: update_system_config processes the form
        print("\n[STEP 5] Processing form data in update_system_config")
        system_cfg = simulate_update_system_config(system_cfg, form_data, SYSTEM_CFG_FILE)
        print(f"  Updated system_cfg keys: {list(system_cfg.keys())}")
        print(f"  Updated system_cfg: {system_cfg}")
        
        # Step 6: Verify file was updated
        print("\n[STEP 6] Verifying config file was saved")
        saved_data = load_json(SYSTEM_CFG_FILE, {})
        print(f"  File contains: {list(saved_data.keys())}")
        
        # Check if all submitted fields are in the file
        missing_in_file = []
        for key in form_data.keys():
            if key not in saved_data:
                missing_in_file.append(key)
        
        if missing_in_file:
            print(f"  ✗ ERROR: Missing in file: {missing_in_file}")
            return False
        
        print(f"  ✓ All {len(form_data)} fields saved successfully")
        
        # Step 7: Simulate app restart (like user would experience)
        print("\n[STEP 7] Simulating app restart...")
        del system_cfg  # Forget the in-memory config
        
        # App reloads config from file
        system_cfg = load_json(SYSTEM_CFG_FILE, {})
        print(f"  Loaded system_cfg after restart: {list(system_cfg.keys())}")
        
        # Step 8: User navigates to /system_config again
        print("\n[STEP 8] User navigates to /system_config page again")
        print(f"  Template receives system_settings={system_cfg}")
        print(f"  Form fields populated:")
        
        blank_fields = []
        for field in ['brewery_name', 'brewer_name', 'street', 'city', 'state', 'email', 'mobile', 'timezone']:
            value = system_cfg.get(field, '')
            is_blank = (value == '' or value is None)
            print(f"    {field}: '{value}' {'[BLANK]' if is_blank else '[OK]'}")
            if is_blank:
                blank_fields.append(field)
        
        if blank_fields:
            print(f"\n  ✗ ERROR: These fields are blank: {blank_fields}")
            print(f"  This is the ISSUE described in the bug report!")
            return False
        else:
            print(f"\n  ✓ All fields retained their values!")
            return True
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)

def test_actual_repo_scenario():
    """Test with the actual repository files"""
    print("\n" + "="*60)
    print("TESTING ACTUAL REPOSITORY SCENARIO")
    print("="*60)
    
    SYSTEM_CFG_FILE = 'config/system_config.json'
    
    if not os.path.exists(SYSTEM_CFG_FILE):
        print(f"✗ {SYSTEM_CFG_FILE} does not exist!")
        return
    
    print(f"\n[Current State] Reading {SYSTEM_CFG_FILE}")
    system_cfg = load_json(SYSTEM_CFG_FILE, {})
    print(f"  File contains: {system_cfg}")
    print(f"  Number of fields: {len(system_cfg)}")
    
    # Check which expected fields are missing
    expected_fields = [
        'brewery_name', 'brewer_name', 'street', 'city', 'state',
        'email', 'mobile', 'timezone', 'timestamp_format', 'update_interval'
    ]
    
    missing_fields = [f for f in expected_fields if f not in system_cfg]
    present_fields = [f for f in expected_fields if f in system_cfg]
    
    print(f"\n  Present fields ({len(present_fields)}): {present_fields}")
    print(f"  Missing fields ({len(missing_fields)}): {missing_fields}")
    
    if missing_fields:
        print(f"\n  ⚠ If a user fills in these {len(missing_fields)} fields, they should persist!")

if __name__ == '__main__':
    result = test_complete_workflow()
    test_actual_repo_scenario()
    
    print("\n" + "="*60)
    if result:
        print("✓ Workflow test PASSED - No bug detected in save/load logic")
    else:
        print("✗ Workflow test FAILED - Bug reproduced!")
    print("="*60)
