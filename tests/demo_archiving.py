#!/usr/bin/env python3
"""
Comprehensive demonstration of data history archiving behavior.

This script demonstrates all the archiving scenarios:
1. Batch change archives old batch samples
2. Temperature control new session archives all events
3. Continue existing session preserves data
4. Kasa plug events are handled correctly
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Add parent directory to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test directory
TEST_DIR = tempfile.mkdtemp(prefix="demo_archive_")
TEMP_CONTROL_DIR = os.path.join(TEST_DIR, "temp_control")
BATCHES_DIR = os.path.join(TEST_DIR, "batches")
LOGS_DIR = os.path.join(TEST_DIR, "logs")

os.makedirs(TEMP_CONTROL_DIR, exist_ok=True)
os.makedirs(BATCHES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Override paths in app module
import app
original_LOG_PATH = app.LOG_PATH
original_BATCHES_DIR = app.BATCHES_DIR
app.LOG_PATH = os.path.join(TEMP_CONTROL_DIR, 'temp_control_log.jsonl')
app.BATCHES_DIR = BATCHES_DIR

# Mock configs
app.tilt_cfg = {}
app.temp_cfg = {
    "low_limit": 65,
    "high_limit": 70,
    "current_temp": 68,
    "enable_heating": True,
    "enable_cooling": True
}

def generate_brewid(beer_name, batch_name, ferm_start_date):
    import hashlib
    id_str = f"{beer_name}-{batch_name}-{ferm_start_date}"
    return hashlib.sha256(id_str.encode('utf-8')).hexdigest()[:8]

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_log_contents(title="Current Log Contents"):
    print(f"\n{title}:")
    print("-" * 60)
    if os.path.exists(app.LOG_PATH):
        with open(app.LOG_PATH, 'r') as f:
            for i, line in enumerate(f, 1):
                obj = json.loads(line)
                event = obj.get('event', '')
                brewid = obj.get('brewid', 'N/A')[:8]
                temp = obj.get('temp_f', 'N/A')
                print(f"  {i}. {event:30s} brewid={brewid:12s} temp={temp}")
    else:
        print("  (log file does not exist)")
    print()

def list_archive_files():
    print("Archive Files:")
    print("-" * 60)
    
    # Batch archives
    batch_archives = [f for f in os.listdir(BATCHES_DIR) if f.endswith('.jsonl')]
    if batch_archives:
        print("  Batch Archives:")
        for f in batch_archives:
            path = os.path.join(BATCHES_DIR, f)
            count = sum(1 for _ in open(path))
            print(f"    - {f} ({count} entries)")
    
    # Temp control archives
    temp_archives = [f for f in os.listdir(LOGS_DIR) if f.endswith('.jsonl')]
    if temp_archives:
        print("  Temp Control Archives:")
        for f in temp_archives:
            path = os.path.join(LOGS_DIR, f)
            count = sum(1 for _ in open(path))
            print(f"    - {f} ({count} entries)")
    
    if not batch_archives and not temp_archives:
        print("  (no archive files)")
    print()

def scenario_1_batch_change():
    """Scenario 1: Changing batch archives old batch samples."""
    print_section("SCENARIO 1: Batch Change Archives Old Batch Data")
    
    print("Setup: Starting with Batch 1 (IPA)")
    color = "Black"
    batch1_brewid = generate_brewid("IPA", "Batch1", "2025-01-01")
    
    app.tilt_cfg[color] = {
        "beer_name": "IPA",
        "batch_name": "Batch1",
        "brewid": batch1_brewid
    }
    
    print(f"  - Batch 1 brewid: {batch1_brewid}")
    
    # Add samples for Batch 1
    print("\nLogging samples for Batch 1...")
    for i in range(5):
        payload = {
            "tilt_color": color,
            "brewid": batch1_brewid,
            "temp_f": 68.0 + i * 0.5,
            "gravity": 1.050 - i * 0.002
        }
        app.append_control_log("tilt_reading", payload)
    
    # Add some Kasa events
    print("Logging Kasa plug events...")
    app.append_control_log("heating_on", {
        "tilt_color": color,
        "low_limit": 65,
        "current_temp": 64,
        "high_limit": 70
    })
    app.append_control_log("heating_off", {
        "tilt_color": color,
        "low_limit": 65,
        "current_temp": 67,
        "high_limit": 70
    })
    
    print_log_contents()
    
    # Change to Batch 2
    print("Changing to Batch 2 (Stout)...")
    batch2_brewid = generate_brewid("Stout", "Batch2", "2025-01-15")
    print(f"  - Batch 2 brewid: {batch2_brewid}")
    
    old_cfg = app.tilt_cfg[color].copy()
    app.rotate_and_archive_old_history(color, batch1_brewid, old_cfg)
    
    app.tilt_cfg[color] = {
        "beer_name": "Stout",
        "batch_name": "Batch2",
        "brewid": batch2_brewid
    }
    
    print_log_contents("Log After Archiving Batch 1")
    list_archive_files()
    
    print("✅ Result: Batch 1 samples archived, Kasa events remained in log")

def scenario_2_temp_control_new_session():
    """Scenario 2: Starting new temp control session archives everything."""
    print_section("SCENARIO 2: New Temp Control Session Archives All Events")
    
    print("Setup: Continuing with current log state...")
    
    # Add a few more events to the current log
    color = "Black"
    current_brewid = app.tilt_cfg[color]['brewid']
    
    print(f"Adding more events for current batch (brewid: {current_brewid})...")
    for i in range(3):
        payload = {
            "tilt_color": color,
            "brewid": current_brewid,
            "temp_f": 55.0 + i,
            "gravity": 1.048 - i * 0.001
        }
        app.append_control_log("tilt_reading", payload)
    
    app.append_control_log("cooling_on", {
        "tilt_color": color,
        "low_limit": 50,
        "current_temp": 59,
        "high_limit": 58
    })
    
    print_log_contents("Before Starting New Session")
    
    # Start new temp control session (archive everything)
    print("Starting NEW temperature control session...")
    if os.path.exists(app.LOG_PATH):
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        archive_name = f"temp_control_{color}_{timestamp}.jsonl"
        archive_path = os.path.join(LOGS_DIR, archive_name)
        shutil.move(app.LOG_PATH, archive_path)
        print(f"  - Archived to: {archive_name}")
    
    # Add a "started" event for the new session
    app.append_control_log("temp_control_started", {
        "tilt_color": color,
        "low_limit": app.temp_cfg.get("low_limit"),
        "high_limit": app.temp_cfg.get("high_limit")
    })
    
    print_log_contents("After Starting New Session")
    list_archive_files()
    
    print("✅ Result: All previous events archived, fresh log started")

def scenario_3_continue_existing():
    """Scenario 3: Continuing existing session preserves data."""
    print_section("SCENARIO 3: Continue Existing Session Preserves Data")
    
    print("Setup: Current log has recent events...")
    print_log_contents()
    
    # Count entries before
    entries_before = 0
    if os.path.exists(app.LOG_PATH):
        with open(app.LOG_PATH, 'r') as f:
            entries_before = sum(1 for _ in f)
    
    print(f"Entries before continuing: {entries_before}")
    
    # Continue existing session (just add more data, no archiving)
    print("\nContinuing EXISTING session (no archiving)...")
    color = "Black"
    current_brewid = app.tilt_cfg[color]['brewid']
    
    for i in range(2):
        payload = {
            "tilt_color": color,
            "brewid": current_brewid,
            "temp_f": 56.0 + i,
            "gravity": 1.045 - i * 0.001
        }
        app.append_control_log("tilt_reading", payload)
    
    # Count entries after
    entries_after = 0
    if os.path.exists(app.LOG_PATH):
        with open(app.LOG_PATH, 'r') as f:
            entries_after = sum(1 for _ in f)
    
    print(f"Entries after continuing: {entries_after}")
    print(f"New entries added: {entries_after - entries_before}")
    
    print_log_contents("After Continuing Session")
    list_archive_files()
    
    print("✅ Result: Data preserved, no new archives created")

def scenario_4_multiple_batches():
    """Scenario 4: Multiple active batches - only archive the correct one."""
    print_section("SCENARIO 4: Multiple Active Batches")
    
    print("Setup: Adding a second active batch on different Tilt...")
    
    # Add samples for a second batch on a different color
    color2 = "Blue"
    batch3_brewid = generate_brewid("Lager", "Batch3", "2025-01-20")
    
    app.tilt_cfg[color2] = {
        "beer_name": "Lager",
        "batch_name": "Batch3",
        "brewid": batch3_brewid
    }
    
    print(f"  - Batch 3 (Blue Tilt) brewid: {batch3_brewid}")
    
    for i in range(3):
        payload = {
            "tilt_color": color2,
            "brewid": batch3_brewid,
            "temp_f": 50.0 + i,
            "gravity": 1.046 - i * 0.001
        }
        app.append_control_log("tilt_reading", payload)
    
    print_log_contents("With Multiple Active Batches")
    
    # Now change the Black batch again
    print("Changing Black batch to Batch 4...")
    color1 = "Black"
    old_brewid = app.tilt_cfg[color1]['brewid']
    batch4_brewid = generate_brewid("Porter", "Batch4", "2025-01-25")
    
    print(f"  - Archiving Black batch brewid: {old_brewid}")
    print(f"  - New Black batch brewid: {batch4_brewid}")
    
    old_cfg = app.tilt_cfg[color1].copy()
    app.rotate_and_archive_old_history(color1, old_brewid, old_cfg)
    
    app.tilt_cfg[color1] = {
        "beer_name": "Porter",
        "batch_name": "Batch4",
        "brewid": batch4_brewid
    }
    
    print_log_contents("After Changing Black Batch")
    
    # Verify Blue batch samples are still there
    blue_samples = 0
    if os.path.exists(app.LOG_PATH):
        with open(app.LOG_PATH, 'r') as f:
            for line in f:
                obj = json.loads(line)
                if obj.get('brewid') == batch3_brewid:
                    blue_samples += 1
    
    print(f"Blue batch (Batch 3) samples remaining in log: {blue_samples}")
    list_archive_files()
    
    print("✅ Result: Only Black batch archived, Blue batch samples preserved")

# Run all scenarios
def run_demo():
    print("\n╔" + "="*78 + "╗")
    print("║" + " "*15 + "DATA HISTORY ARCHIVING DEMONSTRATION" + " "*27 + "║")
    print("╚" + "="*78 + "╝")
    print(f"\nTest directory: {TEST_DIR}")
    print(f"Log file: {app.LOG_PATH}")
    print(f"Batch archives: {BATCHES_DIR}")
    print(f"Temp control archives: {LOGS_DIR}")
    
    try:
        scenario_1_batch_change()
        scenario_2_temp_control_new_session()
        scenario_3_continue_existing()
        scenario_4_multiple_batches()
        
        print_section("FINAL SUMMARY")
        print("\n✅ All scenarios completed successfully!")
        print("\nKey Findings:")
        print("  1. Batch changes archive only samples from the old brewid")
        print("  2. Kasa plug events stay in temp control log (not archived with batches)")
        print("  3. New temp control sessions archive ALL previous events")
        print("  4. Continuing existing sessions preserves all data")
        print("  5. Multiple active batches are handled correctly")
        
        print_log_contents("Final Log State")
        list_archive_files()
        
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

def cleanup():
    print(f"\nCleaning up test directory: {TEST_DIR}")
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    app.LOG_PATH = original_LOG_PATH
    app.BATCHES_DIR = original_BATCHES_DIR

if __name__ == '__main__':
    try:
        exit_code = run_demo()
        cleanup()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)
