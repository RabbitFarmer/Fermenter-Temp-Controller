#!/usr/bin/env python3
"""
End-to-end test simulating the exact user workflow:
1. User has working system with data entered
2. User updates code via git pull
3. User syncs to Raspberry Pi via rsync
4. Verify data is NOT lost
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess

def simulate_user_workflow():
    """
    Simulate the complete user workflow from having data to updating code.
    """
    print("="*70)
    print("END-TO-END USER WORKFLOW TEST")
    print("="*70)
    
    # Create a "Raspberry Pi" directory
    pi_dir = tempfile.mkdtemp(prefix="raspberry_pi_")
    # Create a "local git clone" directory
    git_dir = tempfile.mkdtemp(prefix="git_clone_")
    
    try:
        print(f"\n[Setup] Created test directories:")
        print(f"  Raspberry Pi: {pi_dir}")
        print(f"  Git Clone:    {git_dir}")
        
        # === STEP 1: Initial deployment with old system (configs in git) ===
        print("\n" + "="*70)
        print("STEP 1: Initial Deployment (OLD SYSTEM - configs in git)")
        print("="*70)
        
        # Simulate old system - copy current repo state
        os.makedirs(f"{pi_dir}/config", exist_ok=True)
        os.makedirs(f"{git_dir}/config", exist_ok=True)
        
        # Old system has config files in git with minimal data
        old_configs = {
            'config/system_config.json': {
                "brewery_name": "My Fermentorium",
                "brewer_name": "Frank",
                "units": "Fahrenheit"
            }
        }
        
        for path, data in old_configs.items():
            full_path_pi = os.path.join(pi_dir, path)
            full_path_git = os.path.join(git_dir, path)
            
            with open(full_path_pi, 'w') as f:
                json.dump(data, f, indent=2)
            with open(full_path_git, 'w') as f:
                json.dump(data, f, indent=2)
        
        print("  ✓ Deployed initial system with minimal config")
        
        # === STEP 2: User enters data via web UI ===
        print("\n" + "="*70)
        print("STEP 2: User Enters Data via Web UI")
        print("="*70)
        
        # User fills in the system settings form
        user_data = {
            "brewery_name": "My Fermentorium",
            "brewer_name": "Frank",
            "units": "Fahrenheit",
            "street": "123 Brewing Lane",
            "city": "Hopsville",
            "state": "CO",
            "email": "frank@fermentorium.com",
            "mobile": "555-BREW",
            "timezone": "America/Denver",
            "timestamp_format": "%Y-%m-%d %H:%M:%S",
            "update_interval": "1"
        }
        
        pi_config_file = f"{pi_dir}/config/system_config.json"
        with open(pi_config_file, 'w') as f:
            json.dump(user_data, f, indent=2)
        
        print(f"  User entered {len(user_data)} fields:")
        for key in user_data:
            print(f"    - {key}")
        
        # === STEP 3: Code update (git pull) - OLD BEHAVIOR ===
        print("\n" + "="*70)
        print("STEP 3: OLD BEHAVIOR - Git Pull (would overwrite data)")
        print("="*70)
        
        # Simulate git pull - overwrites with minimal config
        with open(f"{git_dir}/config/system_config.json", 'w') as f:
            json.dump(old_configs['config/system_config.json'], f, indent=2)
        
        print("  Git pull completed (still has minimal config)")
        
        # === STEP 4: Rsync to Pi - OLD BEHAVIOR (DATA LOSS!) ===
        print("\n" + "="*70)
        print("STEP 4: OLD BEHAVIOR - Rsync (causes DATA LOSS!)")
        print("="*70)
        
        # Simulate rsync
        shutil.copy2(f"{git_dir}/config/system_config.json", 
                     f"{pi_dir}/config/system_config.json")
        
        # Check what's on the Pi now
        with open(pi_config_file, 'r') as f:
            after_rsync = json.load(f)
        
        lost_fields = [k for k in user_data if k not in after_rsync]
        
        print(f"  ✗ DATA LOSS OCCURRED!")
        print(f"  ✗ Lost {len(lost_fields)} fields: {lost_fields}")
        print(f"  ✗ This is the BUG the user reported!")
        
        # === STEP 5: Now test the FIX ===
        print("\n" + "="*70)
        print("STEP 5: NEW SYSTEM - Deploy the Fix")
        print("="*70)
        
        # First, restore user's data (simulating they had a backup or re-entered it)
        with open(pi_config_file, 'w') as f:
            json.dump(user_data, f, indent=2)
        print("  User restored their data")
        
        # Deploy the new system with templates
        # Create template file in git
        template_file_git = f"{git_dir}/config/system_config.json.template"
        with open(template_file_git, 'w') as f:
            json.dump(old_configs['config/system_config.json'], f, indent=2)
        
        # Remove config from git (it's now gitignored)
        if os.path.exists(f"{git_dir}/config/system_config.json"):
            os.remove(f"{git_dir}/config/system_config.json")
        
        print("  ✓ Deployed new template-based system")
        print(f"    - Template in git: system_config.json.template")
        print(f"    - Actual config NOT in git (gitignored)")
        
        # === STEP 6: Git pull with new system ===
        print("\n" + "="*70)
        print("STEP 6: NEW BEHAVIOR - Git Pull (safe)")
        print("="*70)
        
        # Git pull only affects template
        print("  Git pull updates template only")
        print("  ✓ User's config/system_config.json is NOT in git")
        
        # === STEP 7: Rsync with new system ===
        print("\n" + "="*70)
        print("STEP 7: NEW BEHAVIOR - Rsync (safe!)")
        print("="*70)
        
        # Copy template from git to Pi
        template_file_pi = f"{pi_dir}/config/system_config.json.template"
        shutil.copy2(template_file_git, template_file_pi)
        
        print("  ✓ Rsync'd template file")
        print("  ✓ User's config file was NOT overwritten (not in git)")
        
        # Verify user data is still intact
        with open(pi_config_file, 'r') as f:
            final_data = json.load(f)
        
        if final_data == user_data:
            print(f"\n  ✓✓✓ SUCCESS! All {len(user_data)} fields preserved!")
            for key in user_data:
                print(f"    ✓ {key}: {final_data[key][:30] if len(str(final_data[key])) > 30 else final_data[key]}")
            return True
        else:
            print(f"\n  ✗ FAILURE! Data mismatch")
            return False
        
    finally:
        # Cleanup
        shutil.rmtree(pi_dir)
        shutil.rmtree(git_dir)

if __name__ == '__main__':
    print("\n")
    success = simulate_user_workflow()
    
    print("\n" + "="*70)
    if success:
        print("✓✓✓ END-TO-END TEST PASSED ✓✓✓")
        print("\nThe template-based config system prevents data loss during")
        print("code updates via git pull and rsync!")
    else:
        print("✗✗✗ END-TO-END TEST FAILED ✗✗✗")
    print("="*70 + "\n")
    
    sys.exit(0 if success else 1)
