#!/usr/bin/env python3
"""
Manual demonstration of the temperature control reading fix.
Shows the difference between update_interval and tilt_logging_interval_minutes.
"""

import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

def demonstrate_fix():
    print("\n" + "="*70)
    print("DEMONSTRATION: Temperature Control Reading Interval Fix")
    print("="*70)
    
    from app import system_cfg, temp_cfg, log_periodic_temp_reading, LOG_PATH
    
    print("\n1. Current Configuration")
    print("-" * 70)
    update_interval = system_cfg.get('update_interval', 1)
    tilt_interval = system_cfg.get('tilt_logging_interval_minutes', 15)
    
    print(f"   update_interval (Temperature Control):  {update_interval} minutes")
    print(f"   tilt_logging_interval_minutes (Tilts):  {tilt_interval} minutes")
    print()
    print("   ISSUE: Temperature control chart was using tilt_logging_interval")
    print("   FIX:   Temperature control chart now uses update_interval")
    
    print("\n2. How It Works Now")
    print("-" * 70)
    print("   • periodic_temp_control() runs every update_interval minutes")
    print("   • Calls temperature_control_logic() for heating/cooling decisions")
    print("   • NOW ALSO calls log_periodic_temp_reading() to log a reading")
    print("   • Chart displays these periodic readings + control events")
    
    print("\n3. Demonstrating Periodic Reading Logging")
    print("-" * 70)
    
    # Enable monitoring and set test values
    temp_cfg['temp_control_active'] = True
    temp_cfg['low_limit'] = 65.0
    temp_cfg['high_limit'] = 70.0
    temp_cfg['current_temp'] = 67.5
    temp_cfg['tilt_color'] = 'Demo'
    
    print(f"   Enabled:      {temp_cfg['temp_control_active']}")
    print(f"   Temperature:  {temp_cfg['current_temp']}°F")
    print(f"   Low Limit:    {temp_cfg['low_limit']}°F")
    print(f"   High Limit:   {temp_cfg['high_limit']}°F")
    
    # Backup existing log
    backup_path = None
    if os.path.exists(LOG_PATH):
        backup_path = f"{LOG_PATH}.demo_backup"
        os.rename(LOG_PATH, backup_path)
    
    # Log a reading
    print("\n4. Logging Periodic Reading")
    print("-" * 70)
    print(f"   Calling log_periodic_temp_reading()...")
    
    log_periodic_temp_reading()
    
    # Read and display the log entry
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f:
            entry = json.loads(f.readline())
        
        print(f"   ✓ Reading logged successfully!")
        print()
        print("   Log Entry:")
        print("   " + "-" * 66)
        for key, value in entry.items():
            print(f"   {key:20s}: {value}")
        print("   " + "-" * 66)
    
    print("\n5. Key Differences")
    print("-" * 70)
    print("   BEFORE THE FIX:")
    print("   • Chart only showed Tilt readings (every 15 minutes)")
    print("   • Chart only showed temp control events (state changes)")
    print("   • No regular temperature readings at update_interval")
    print()
    print("   AFTER THE FIX:")
    print(f"   • Chart shows periodic readings (every {update_interval} minute(s))")
    print("   • Chart ALSO shows temp control events (state changes)")
    print("   • Tilt readings still logged separately at their own interval")
    print("   • Temperature control has proper time-series data")
    
    print("\n6. Chart Impact")
    print("-" * 70)
    print("   • Temperature control chart now updates more frequently")
    print(f"   • Data points every {update_interval} minute(s) instead of only on events")
    print("   • Better visualization of temperature trends")
    print("   • Separate from fermentation monitoring (Tilt) frequency")
    
    # Restore backup
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    if backup_path and os.path.exists(backup_path):
        os.rename(backup_path, LOG_PATH)
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print()

if __name__ == "__main__":
    demonstrate_fix()
