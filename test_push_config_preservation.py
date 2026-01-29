#!/usr/bin/env python3
"""
Test to verify that push notification configuration is preserved when saving system settings.

This test simulates the bug where pushover_user_key and other push config fields
are cleared when saving system settings if they're not provided in the form data.
"""

import sys
import json
import os
import tempfile

def test_config_preservation():
    """
    Test that push notification configuration is preserved when saving system config.
    
    This simulates the scenario where a user:
    1. Sets up push notification credentials
    2. Later edits another system setting (e.g., brewery name)
    3. The push credentials should NOT be cleared
    """
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_config_file = f.name
        
        # Initial config with push settings
        initial_config = {
            "brewery_name": "Test Brewery",
            "warning_mode": "PUSH",
            "push_provider": "pushover",
            "pushover_user_key": "test_user_key_12345678901234567890",
            "pushover_api_token": "test_api_token_12345678901234567890",
            "pushover_device": "test_device",
            "ntfy_server": "https://ntfy.sh",
            "ntfy_topic": "test_topic_123"
        }
        json.dump(initial_config, f)
    
    try:
        # Simulate the save_system_config behavior from app.py (BUGGY version)
        print("Testing BUGGY version (current code):")
        print("-" * 80)
        
        # Read existing config
        with open(temp_config_file, 'r') as f:
            system_cfg = json.load(f)
        
        print(f"Initial pushover_user_key: {system_cfg.get('pushover_user_key', 'NOT SET')}")
        print(f"Initial pushover_api_token: {system_cfg.get('pushover_api_token', 'NOT SET')}")
        print(f"Initial ntfy_topic: {system_cfg.get('ntfy_topic', 'NOT SET')}")
        print()
        
        # Simulate form data that only changes brewery_name (no push fields)
        form_data = {
            "brewery_name": "Updated Brewery Name",
            "warning_mode": "PUSH",
            "push_provider": "pushover"
            # NOTE: pushover_user_key, pushover_api_token, ntfy_topic NOT in form data
        }
        
        # Simulate the BUGGY behavior (lines 2802-2806 of app.py)
        system_cfg.update({
            "brewery_name": form_data.get("brewery_name", ""),
            "warning_mode": form_data.get("warning_mode", "NONE"),
            "push_provider": form_data.get("push_provider", "pushover"),
            "pushover_user_key": form_data.get("pushover_user_key", ""),  # BUG: overwrites with empty string
            "pushover_device": form_data.get("pushover_device", ""),  # BUG: overwrites with empty string
            "ntfy_server": form_data.get("ntfy_server", "https://ntfy.sh"),
            "ntfy_topic": form_data.get("ntfy_topic", ""),  # BUG: overwrites with empty string
        })
        
        # Handle pushover_api_token specially (lines 2744-2746)
        pushover_api_token = form_data.get("pushover_api_token", "")
        if pushover_api_token:
            system_cfg["pushover_api_token"] = pushover_api_token
        
        print(f"After BUGGY save:")
        print(f"  pushover_user_key: {system_cfg.get('pushover_user_key', 'NOT SET')}")
        print(f"  pushover_api_token: {system_cfg.get('pushover_api_token', 'NOT SET')}")
        print(f"  ntfy_topic: {system_cfg.get('ntfy_topic', 'NOT SET')}")
        print()
        
        # Check for the bug
        buggy_user_key = system_cfg.get('pushover_user_key', '')
        buggy_ntfy_topic = system_cfg.get('ntfy_topic', '')
        
        if buggy_user_key == "":
            print("❌ BUG CONFIRMED: pushover_user_key was cleared!")
        else:
            print("✅ pushover_user_key preserved")
            
        if buggy_ntfy_topic == "":
            print("❌ BUG CONFIRMED: ntfy_topic was cleared!")
        else:
            print("✅ ntfy_topic preserved")
            
        print()
        print("=" * 80)
        print()
        
        # Now test the FIXED version
        print("Testing FIXED version (corrected code):")
        print("-" * 80)
        
        # Reset to initial config
        with open(temp_config_file, 'r') as f:
            system_cfg = json.load(f)
        
        print(f"Initial pushover_user_key: {system_cfg.get('pushover_user_key', 'NOT SET')}")
        print(f"Initial pushover_api_token: {system_cfg.get('pushover_api_token', 'NOT SET')}")
        print(f"Initial ntfy_topic: {system_cfg.get('ntfy_topic', 'NOT SET')}")
        print()
        
        # Simulate the FIXED behavior (with fallback to existing values)
        system_cfg.update({
            "brewery_name": form_data.get("brewery_name", ""),
            "warning_mode": form_data.get("warning_mode", "NONE"),
            "push_provider": form_data.get("push_provider", "pushover"),
            "pushover_user_key": form_data.get("pushover_user_key", system_cfg.get("pushover_user_key", "")),  # FIX: preserve existing
            "pushover_device": form_data.get("pushover_device", system_cfg.get("pushover_device", "")),  # FIX: preserve existing
            "ntfy_server": form_data.get("ntfy_server", system_cfg.get("ntfy_server", "https://ntfy.sh")),  # FIX: preserve existing
            "ntfy_topic": form_data.get("ntfy_topic", system_cfg.get("ntfy_topic", "")),  # FIX: preserve existing
        })
        
        # Handle pushover_api_token specially (lines 2744-2746)
        pushover_api_token = form_data.get("pushover_api_token", "")
        if pushover_api_token:
            system_cfg["pushover_api_token"] = pushover_api_token
        
        print(f"After FIXED save:")
        print(f"  pushover_user_key: {system_cfg.get('pushover_user_key', 'NOT SET')}")
        print(f"  pushover_api_token: {system_cfg.get('pushover_api_token', 'NOT SET')}")
        print(f"  ntfy_topic: {system_cfg.get('ntfy_topic', 'NOT SET')}")
        print()
        
        # Verify the fix
        fixed_user_key = system_cfg.get('pushover_user_key', '')
        fixed_api_token = system_cfg.get('pushover_api_token', '')
        fixed_ntfy_topic = system_cfg.get('ntfy_topic', '')
        
        success = True
        
        if fixed_user_key == "test_user_key_12345678901234567890":
            print("✅ FIXED: pushover_user_key preserved correctly!")
        else:
            print(f"❌ FAIL: pushover_user_key = '{fixed_user_key}'")
            success = False
            
        if fixed_api_token == "test_api_token_12345678901234567890":
            print("✅ FIXED: pushover_api_token preserved correctly!")
        else:
            print(f"❌ FAIL: pushover_api_token = '{fixed_api_token}'")
            success = False
            
        if fixed_ntfy_topic == "test_topic_123":
            print("✅ FIXED: ntfy_topic preserved correctly!")
        else:
            print(f"❌ FAIL: ntfy_topic = '{fixed_ntfy_topic}'")
            success = False
        
        return success
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_config_file):
            os.unlink(temp_config_file)

if __name__ == '__main__':
    print("=" * 80)
    print("PUSH NOTIFICATION CONFIG PRESERVATION TEST")
    print("=" * 80)
    print()
    
    try:
        success = test_config_preservation()
        print()
        print("=" * 80)
        if success:
            print("✅ ALL TESTS PASSED - Fix is correct!")
        else:
            print("❌ TESTS FAILED")
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
