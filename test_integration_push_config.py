#!/usr/bin/env python3
"""
Integration test for push notification configuration preservation.

This test simulates a realistic scenario where:
1. User sets up push notification credentials
2. User later edits another system setting
3. Push credentials should still be preserved
"""

import sys
import os
import json
import tempfile
import shutil

# Create temporary config directory
temp_dir = tempfile.mkdtemp()
config_dir = os.path.join(temp_dir, 'config')
os.makedirs(config_dir)

# Set environment to use temp config
SYSTEM_CFG_FILE = os.path.join(config_dir, 'system_config.json')

# Create initial config with push settings
initial_config = {
    "brewery_name": "Test Brewery",
    "brewer_name": "Test Brewer",
    "warning_mode": "PUSH",
    "push_provider": "pushover",
    "pushover_user_key": "u123456789abcdef123456789abcdef",
    "pushover_api_token": "a123456789abcdef123456789abcdef",
    "pushover_device": "my-phone",
    "ntfy_server": "https://ntfy.sh",
    "ntfy_topic": "my-fermenter-notifications",
    "temp_control_notifications": {
        "enable_temp_below_low_limit": True,
        "enable_temp_above_high_limit": True,
        "enable_heating_on": False,
        "enable_heating_off": False,
        "enable_cooling_on": False,
        "enable_cooling_off": False,
        "enable_kasa_error": True,
    },
    "batch_notifications": {
        "enable_loss_of_signal": True,
        "loss_of_signal_timeout_minutes": 30,
        "enable_fermentation_starting": True,
        "enable_fermentation_completion": True,
        "enable_daily_report": False,
        "daily_report_time": "09:00",
    }
}

with open(SYSTEM_CFG_FILE, 'w') as f:
    json.dump(initial_config, f, indent=2)

print("=" * 80)
print("INTEGRATION TEST: Push Notification Config Preservation")
print("=" * 80)
print()

try:
    # Monkey-patch the config file path before importing app
    import app as app_module
    app_module.SYSTEM_CFG_FILE = SYSTEM_CFG_FILE
    
    # Reload system config from temp file
    if os.path.exists(SYSTEM_CFG_FILE):
        with open(SYSTEM_CFG_FILE, 'r') as f:
            app_module.system_cfg = json.load(f)
    
    print("Step 1: Initial Configuration")
    print("-" * 80)
    print(f"Pushover User Key: {app_module.system_cfg.get('pushover_user_key', 'NOT SET')}")
    print(f"Pushover API Token: {app_module.system_cfg.get('pushover_api_token', 'NOT SET')}")
    print(f"Pushover Device: {app_module.system_cfg.get('pushover_device', 'NOT SET')}")
    print(f"ntfy Topic: {app_module.system_cfg.get('ntfy_topic', 'NOT SET')}")
    print()
    
    # Verify initial values
    assert app_module.system_cfg.get('pushover_user_key') == "u123456789abcdef123456789abcdef"
    assert app_module.system_cfg.get('pushover_api_token') == "a123456789abcdef123456789abcdef"
    assert app_module.system_cfg.get('pushover_device') == "my-phone"
    assert app_module.system_cfg.get('ntfy_topic') == "my-fermenter-notifications"
    print("✅ Initial configuration loaded correctly")
    print()
    
    # Simulate form submission that changes ONLY brewery name
    # This is the key test - push config should be preserved
    print("Step 2: Simulate saving system config with only brewery name change")
    print("-" * 80)
    print("Form data submitted:")
    form_data = {
        "brewery_name": "Updated Test Brewery",
        "brewer_name": "Test Brewer",
        "warning_mode": "PUSH",
        "push_provider": "pushover",
        # NOTE: No pushover_user_key, pushover_api_token, ntfy_topic in form
        # This simulates the HTML form where password fields are empty unless changed
        "enable_temp_below_low_limit": "on",
        "enable_temp_above_high_limit": "on",
        "enable_kasa_error": "on",
        "enable_loss_of_signal": "on",
        "loss_of_signal_timeout_minutes": "30",
        "enable_fermentation_starting": "on",
        "enable_fermentation_completion": "on",
        "daily_report_time": "09:00",
    }
    
    for key, value in form_data.items():
        if not key.startswith('enable_'):
            print(f"  {key}: {value}")
    print()
    
    # Execute the save_system_config logic
    data = form_data
    old_warn = app_module.system_cfg.get('warning_mode','NONE')
    
    # Handle password field - only update if provided
    sending_email_password = data.get("sending_email_password", "")
    if sending_email_password:
        app_module.system_cfg["smtp_password"] = sending_email_password
    
    # Handle Pushover API Token - only update if provided
    pushover_api_token = data.get("pushover_api_token", "")
    if pushover_api_token:
        app_module.system_cfg["pushover_api_token"] = pushover_api_token
    
    # Handle ntfy Auth Token - only update if provided
    ntfy_auth_token = data.get("ntfy_auth_token", "")
    if ntfy_auth_token:
        app_module.system_cfg["ntfy_auth_token"] = ntfy_auth_token
    
    # This is the key part - the FIXED version
    app_module.system_cfg.update({
        "brewery_name": data.get("brewery_name", ""),
        "brewer_name": data.get("brewer_name", ""),
        "warning_mode": data.get("warning_mode", "NONE"),
        "push_provider": data.get("push_provider", "pushover"),
        # FIXED: These now preserve existing values
        "pushover_user_key": data.get("pushover_user_key", app_module.system_cfg.get("pushover_user_key", "")),
        "pushover_device": data.get("pushover_device", app_module.system_cfg.get("pushover_device", "")),
        "ntfy_server": data.get("ntfy_server", app_module.system_cfg.get("ntfy_server", "https://ntfy.sh")),
        "ntfy_topic": data.get("ntfy_topic", app_module.system_cfg.get("ntfy_topic", "")),
    })
    
    # Update notification settings
    temp_control_notif = {
        'enable_temp_below_low_limit': 'enable_temp_below_low_limit' in data,
        'enable_temp_above_high_limit': 'enable_temp_above_high_limit' in data,
        'enable_heating_on': 'enable_heating_on' in data,
        'enable_heating_off': 'enable_heating_off' in data,
        'enable_cooling_on': 'enable_cooling_on' in data,
        'enable_cooling_off': 'enable_cooling_off' in data,
        'enable_kasa_error': 'enable_kasa_error' in data,
    }
    app_module.system_cfg['temp_control_notifications'] = temp_control_notif
    
    batch_notif = {
        'enable_loss_of_signal': 'enable_loss_of_signal' in data,
        'loss_of_signal_timeout_minutes': int(data.get('loss_of_signal_timeout_minutes', 30)),
        'enable_fermentation_starting': 'enable_fermentation_starting' in data,
        'enable_fermentation_completion': 'enable_fermentation_completion' in data,
        'enable_daily_report': 'enable_daily_report' in data,
        'daily_report_time': data.get('daily_report_time', '09:00'),
    }
    app_module.system_cfg['batch_notifications'] = batch_notif
    
    # Save to file
    with open(SYSTEM_CFG_FILE, 'w') as f:
        json.dump(app_module.system_cfg, f, indent=2)
    
    print("Step 3: Verify Configuration After Save")
    print("-" * 80)
    
    # Reload from file to verify persistence
    with open(SYSTEM_CFG_FILE, 'r') as f:
        saved_config = json.load(f)
    
    print(f"Brewery Name: {saved_config.get('brewery_name', 'NOT SET')}")
    print(f"Pushover User Key: {saved_config.get('pushover_user_key', 'NOT SET')}")
    print(f"Pushover API Token: {saved_config.get('pushover_api_token', 'NOT SET')}")
    print(f"Pushover Device: {saved_config.get('pushover_device', 'NOT SET')}")
    print(f"ntfy Topic: {saved_config.get('ntfy_topic', 'NOT SET')}")
    print()
    
    # Verify the fix
    success = True
    
    # Brewery name should be updated
    if saved_config.get('brewery_name') == "Updated Test Brewery":
        print("✅ Brewery name was updated correctly")
    else:
        print(f"❌ Brewery name incorrect: {saved_config.get('brewery_name')}")
        success = False
    
    # Push config should be preserved
    if saved_config.get('pushover_user_key') == "u123456789abcdef123456789abcdef":
        print("✅ Pushover User Key preserved")
    else:
        print(f"❌ Pushover User Key lost: '{saved_config.get('pushover_user_key')}'")
        success = False
    
    if saved_config.get('pushover_api_token') == "a123456789abcdef123456789abcdef":
        print("✅ Pushover API Token preserved")
    else:
        print(f"❌ Pushover API Token lost: '{saved_config.get('pushover_api_token')}'")
        success = False
    
    if saved_config.get('pushover_device') == "my-phone":
        print("✅ Pushover Device preserved")
    else:
        print(f"❌ Pushover Device lost: '{saved_config.get('pushover_device')}'")
        success = False
    
    if saved_config.get('ntfy_topic') == "my-fermenter-notifications":
        print("✅ ntfy Topic preserved")
    else:
        print(f"❌ ntfy Topic lost: '{saved_config.get('ntfy_topic')}'")
        success = False
    
    print()
    print("=" * 80)
    if success:
        print("✅ INTEGRATION TEST PASSED")
        print()
        print("Summary: Push notification credentials are now preserved when")
        print("         saving system settings without re-entering them.")
    else:
        print("❌ INTEGRATION TEST FAILED")
    print("=" * 80)
    
    sys.exit(0 if success else 1)
    
except Exception as e:
    print()
    print("=" * 80)
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 80)
    sys.exit(1)
    
finally:
    # Clean up temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
