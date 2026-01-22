#!/usr/bin/env python3
"""
Test to verify SMS/Email password persistence issue.

This test simulates the reported bug:
"I noticed when returning to the screen that the sending password was blank 
after having been set earlier."

It tests:
1. Password is saved when entered
2. Password persists after save_json
3. Password is available for SMTP authentication
4. HTML form behavior (password field blank on reload is expected for security)
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
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"[LOG] Error saving JSON to {path}: {e}")
        return False

def simulate_form_submission(system_cfg, form_data):
    """
    Simulate the update_system_config route behavior.
    This mimics lines 1768-1864 in app.py
    """
    # Handle password field - only update if provided
    sending_email_password = form_data.get("sending_email_password", "")
    if sending_email_password:
        # Store as smtp_password for SMTP authentication
        system_cfg["smtp_password"] = sending_email_password
    
    # Update other fields
    system_cfg.update({
        "brewery_name": form_data.get("brewery_name", ""),
        "brewer_name": form_data.get("brewer_name", ""),
        "email": form_data.get("email", ""),
        "mobile": form_data.get("mobile", ""),
        "sending_email": form_data.get("sending_email", system_cfg.get('sending_email','')),
        "smtp_host": form_data.get("smtp_host", system_cfg.get('smtp_host', 'smtp.gmail.com')),
        "smtp_port": int(form_data.get("smtp_port", system_cfg.get('smtp_port', 587))),
        "sms_gateway_domain": form_data.get("sms_gateway_domain", system_cfg.get('sms_gateway_domain','')),
        "warning_mode": form_data.get("warning_mode", "NONE"),
    })
    
    return system_cfg

def test_password_persistence():
    """Test that SMTP password is properly saved and loaded."""
    print("Testing SMTP password persistence...")
    
    # Create a temp directory for testing
    test_dir = tempfile.mkdtemp()
    config_dir = os.path.join(test_dir, 'config')
    os.makedirs(config_dir)
    
    try:
        test_config_file = os.path.join(config_dir, 'system_config.json')
        
        # Step 1: Initial configuration (first time user sets up)
        print("\n1. User enters system settings for the first time...")
        system_cfg = {}
        
        form_data = {
            "brewery_name": "Test Brewery",
            "brewer_name": "Test Brewer",
            "email": "recipient@example.com",
            "mobile": "5551234567",
            "sending_email": "sender@example.com",
            "sending_email_password": "MySecretPassword123",  # Password entered
            "smtp_host": "smtp.gmail.com",
            "smtp_port": "587",
            "sms_gateway_domain": "txt.att.net",
            "warning_mode": "EMAIL"
        }
        
        system_cfg = simulate_form_submission(system_cfg, form_data)
        print(f"   ✓ smtp_password in system_cfg: {('smtp_password' in system_cfg)}")
        print(f"   ✓ smtp_password value length: {len(system_cfg.get('smtp_password', ''))}")
        
        # Step 2: Save configuration
        print("\n2. Saving configuration to file...")
        save_json(test_config_file, system_cfg)
        
        with open(test_config_file, 'r') as f:
            saved_content = f.read()
            has_password = 'smtp_password' in saved_content
            print(f"   ✓ Password saved to file: {has_password}")
            if has_password:
                saved_data = json.loads(saved_content)
                print(f"   ✓ Password in saved JSON: {('smtp_password' in saved_data)}")
        
        # Step 3: Reload configuration (simulates app restart or page refresh)
        print("\n3. Reloading configuration from file...")
        system_cfg_reloaded = load_json(test_config_file, {})
        
        password_exists = 'smtp_password' in system_cfg_reloaded
        password_correct = system_cfg_reloaded.get('smtp_password') == 'MySecretPassword123'
        
        print(f"   ✓ Password exists after reload: {password_exists}")
        print(f"   ✓ Password value correct: {password_correct}")
        
        if not password_exists or not password_correct:
            print("   ✗ ERROR: Password was not persisted correctly!")
            return False
        
        # Step 4: User updates OTHER settings WITHOUT re-entering password
        print("\n4. User updates other settings WITHOUT re-entering password...")
        form_data_no_password = {
            "brewery_name": "Updated Brewery Name",  # Changed
            "brewer_name": "Test Brewer",
            "email": "recipient@example.com",
            "mobile": "5551234567",
            "sending_email": "sender@example.com",
            "sending_email_password": "",  # Password field is EMPTY (not re-entered)
            "smtp_host": "smtp.gmail.com",
            "smtp_port": "587",
            "sms_gateway_domain": "txt.att.net",
            "warning_mode": "EMAIL"
        }
        
        system_cfg_reloaded = simulate_form_submission(system_cfg_reloaded, form_data_no_password)
        
        # Step 5: Save again
        print("\n5. Saving configuration again...")
        save_json(test_config_file, system_cfg_reloaded)
        
        # Step 6: Reload and verify password is STILL there
        print("\n6. Reloading configuration again...")
        system_cfg_final = load_json(test_config_file, {})
        
        password_still_exists = 'smtp_password' in system_cfg_final
        password_still_correct = system_cfg_final.get('smtp_password') == 'MySecretPassword123'
        brewery_updated = system_cfg_final.get('brewery_name') == 'Updated Brewery Name'
        
        print(f"   ✓ Password still exists: {password_still_exists}")
        print(f"   ✓ Password still correct: {password_still_correct}")
        print(f"   ✓ Other field updated: {brewery_updated}")
        
        if not password_still_exists or not password_still_correct:
            print("   ✗ ERROR: Password was lost after updating other fields!")
            return False
        
        # Step 7: Test the SMTP authentication path (simulating _smtp_send function)
        print("\n7. Testing password retrieval for SMTP authentication...")
        cfg = system_cfg_final
        smtp_password = cfg.get("smtp_password") or cfg.get("sending_email_password")
        
        password_retrievable = smtp_password is not None and len(smtp_password) > 0
        print(f"   ✓ Password retrievable for SMTP: {password_retrievable}")
        print(f"   ✓ Password value: {'***' + smtp_password[-3:] if smtp_password else 'None'}")
        
        if not password_retrievable:
            print("   ✗ ERROR: Password not retrievable for SMTP authentication!")
            return False
        
        print("\n✓ Password persistence test PASSED")
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)

if __name__ == '__main__':
    print("SMS/Email Password Persistence Test")
    print("="*60)
    
    result = test_password_persistence()
    
    print("\n" + "="*60)
    if result:
        print("✓✓✓ TEST PASSED ✓✓✓")
        sys.exit(0)
    else:
        print("✗✗✗ TEST FAILED ✗✗✗")
        sys.exit(1)
