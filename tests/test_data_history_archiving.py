#!/usr/bin/env python3
"""
Test script to verify data history archiving behavior.

This test validates that:
1. When a new batch is started (brewid changes), old batch history is archived
2. When temperature control starts a new session, the old log is archived
3. Kasa plug events in archived logs are preserved
4. User can choose to continue existing session without archiving
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Test directory setup
TEST_DIR = tempfile.mkdtemp(prefix="archive_test_")
BATCHES_DIR = os.path.join(TEST_DIR, "batches")
TEMP_CONTROL_DIR = os.path.join(TEST_DIR, "temp_control")
LOGS_DIR = os.path.join(TEST_DIR, "logs")
CONFIG_DIR = os.path.join(TEST_DIR, "config")

os.makedirs(BATCHES_DIR, exist_ok=True)
os.makedirs(TEMP_CONTROL_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

LOG_PATH = os.path.join(TEMP_CONTROL_DIR, 'temp_control_log.jsonl')
TILT_CONFIG_FILE = os.path.join(CONFIG_DIR, 'tilt_config.json')
TEMP_CFG_FILE = os.path.join(CONFIG_DIR, 'temp_control_config.json')

print(f"Test directory: {TEST_DIR}")
print(f"Batches directory: {BATCHES_DIR}")
print(f"Temp control log: {LOG_PATH}")

# Mock configurations
tilt_cfg = {}
temp_cfg = {}

def generate_brewid(beer_name, batch_name, ferm_start_date):
    import hashlib
    id_str = f"{beer_name}-{batch_name}-{ferm_start_date}"
    return hashlib.sha256(id_str.encode('utf-8')).hexdigest()[:8]

def save_json(filepath, data):
    """Save JSON configuration to file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def append_control_log(event_type, payload):
    """Append event to control log (simulating app.py behavior)."""
    # Simulate the actual app.py behavior which creates a flat entry object
    # The actual app formats the entry with all fields at the top level
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event_type if event_type == "SAMPLE" else event_type,
        "tilt_color": payload.get("tilt_color", ""),
        "brewid": payload.get("brewid", ""),
        "temp_f": payload.get("temp_f"),
        "gravity": payload.get("gravity"),
        "low_limit": payload.get("low_limit"),
        "current_temp": payload.get("current_temp"),
        "high_limit": payload.get("high_limit")
    }
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + "\n")

def rotate_and_archive_old_history(color, old_brewid, old_cfg):
    """Simulate the rotate_and_archive_old_history function from app.py."""
    try:
        if not old_brewid and not color:
            return False
        os.makedirs(BATCHES_DIR, exist_ok=True)
        archive_name = f"{color}_{old_cfg.get('beer_name','unknown')}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jsonl"
        safe_archive = os.path.join(BATCHES_DIR, archive_name.replace(' ', '_'))
        moved = 0
        remaining_lines = []
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                    except Exception:
                        remaining_lines.append(line)
                        continue
                    if obj.get('event') != 'SAMPLE':
                        remaining_lines.append(line)
                        continue
                    # obj is a flat structure with all fields at the top level
                    if isinstance(obj, dict) and obj.get('brewid') == old_brewid:
                        with open(safe_archive, 'a') as af:
                            af.write(json.dumps(obj) + "\n")
                        moved += 1
                    else:
                        remaining_lines.append(line)
        try:
            with open(LOG_PATH, 'w') as f:
                f.writelines(remaining_lines)
        except Exception as e:
            print(f"[LOG] Error rewriting main log after archive: {e}")
        
        # Log the mode change only if we actually moved samples
        if moved > 0:
            append_control_log("temp_control_mode_changed", {
                "tilt_color": color,
                "low_limit": temp_cfg.get("low_limit", 0),
                "current_temp": temp_cfg.get("current_temp", 0),
                "high_limit": temp_cfg.get("high_limit", 0)
            })
        
        print(f"[LOG] Archived {moved} SAMPLE entries to {safe_archive}")
        return True
    except Exception as e:
        print(f"[LOG] rotate_and_archive_old_history error: {e}")
        return False

def archive_temp_control_log_for_new_session(tilt_color):
    """Simulate archiving temp control log when starting a new session."""
    try:
        if os.path.exists(LOG_PATH):
            os.makedirs(LOGS_DIR, exist_ok=True)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            archive_name = f"temp_control_{tilt_color}_{timestamp}.jsonl"
            archive_path = os.path.join(LOGS_DIR, archive_name)
            shutil.move(LOG_PATH, archive_path)
            print(f"[LOG] Archived temp control log to {archive_path}")
            return archive_path
    except Exception as e:
        print(f"[LOG] Error archiving temp control log: {e}")
        return None

# Test cases
def test_batch_change_archives_old_data():
    """Test that changing batch (new brewid) archives old batch data."""
    print("\n" + "="*80)
    print("TEST 1: Batch change archives old data")
    print("="*80)
    
    # Clear batches directory
    for f in os.listdir(BATCHES_DIR):
        if f != '.gitkeep':
            os.remove(os.path.join(BATCHES_DIR, f))
    
    # Setup: Create initial batch configuration
    color = "Black"
    old_brewid = generate_brewid("IPA", "Batch1", "2025-01-01")
    tilt_cfg[color] = {
        "beer_name": "IPA",
        "batch_name": "Batch1",
        "ferm_start_date": "2025-01-01",
        "brewid": old_brewid
    }
    
    # Clear any existing log
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    
    # Add some sample data to the log with proper structure
    for i in range(5):
        append_control_log("SAMPLE", {
            "tilt_color": color,
            "brewid": old_brewid,
            "temp_f": 68.0 + i,
            "gravity": 1.050 - (i * 0.001)
        })
    
    # Add some Kasa plug events (these should NOT be archived with batch)
    append_control_log("heating_on", {
        "tilt_color": color,
        "low_limit": 65,
        "current_temp": 64,
        "high_limit": 70
    })
    append_control_log("cooling_off", {
        "tilt_color": color,
        "low_limit": 65,
        "current_temp": 68,
        "high_limit": 70
    })
    
    # Count entries before archiving
    entries_before = 0
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f:
            entries_before = len(f.readlines())
    
    print(f"Entries before archiving: {entries_before}")
    
    # Simulate changing to a new batch
    new_brewid = generate_brewid("Stout", "Batch2", "2025-01-15")
    
    # Archive old data
    old_cfg = tilt_cfg[color].copy()
    success = rotate_and_archive_old_history(color, old_brewid, old_cfg)
    
    print(f"Archive operation success: {success}")
    
    # Check that archive file was created
    archive_files = [f for f in os.listdir(BATCHES_DIR) if f.endswith('.jsonl')]
    print(f"Archive files created: {archive_files}")
    
    # Verify archive contains the sample data
    if archive_files:
        archive_path = os.path.join(BATCHES_DIR, archive_files[0])
        with open(archive_path, 'r') as f:
            archived_entries = [json.loads(line) for line in f if line.strip()]
        
        print(f"Archived entries: {len(archived_entries)}")
        
        # Verify all sample entries were archived
        sample_entries = [e for e in archived_entries if e.get('event') == 'SAMPLE']
        print(f"Sample entries in archive: {len(sample_entries)}")
        
        # Verify Kasa events were NOT archived (they should remain in temp control log)
        kasa_entries = [e for e in archived_entries if e.get('event') in ['heating_on', 'heating_off', 'cooling_on', 'cooling_off']]
        print(f"Kasa entries in archive: {len(kasa_entries)}")
        
        # Check what remains in the log
        remaining_entries = 0
        remaining_kasa = 0
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                for line in f:
                    obj = json.loads(line)
                    remaining_entries += 1
                    if obj.get('event') in ['heating_on', 'heating_off', 'cooling_on', 'cooling_off']:
                        remaining_kasa += 1
        
        print(f"Remaining entries in log: {remaining_entries}")
        print(f"Remaining Kasa events in log: {remaining_kasa}")
        
        if len(sample_entries) == 5 and len(kasa_entries) == 0 and remaining_kasa == 2:
            print("✅ PASS: All sample entries were archived, Kasa events remained in temp log")
            return True
        else:
            print(f"❌ FAIL: Expected 5 sample entries archived, 0 Kasa in archive, 2 Kasa remaining")
            print(f"         Found {len(sample_entries)} samples, {len(kasa_entries)} Kasa in archive, {remaining_kasa} Kasa remaining")
            return False
    else:
        print("❌ FAIL: No archive file was created")
        return False

def test_temp_control_new_session_archives_log():
    """Test that starting a new temperature control session archives the log."""
    print("\n" + "="*80)
    print("TEST 2: New temp control session archives log")
    print("="*80)
    
    # Setup: Create temp control log with various events
    color = "Blue"
    
    # Clear any existing log
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    
    # Add various events including Kasa plug events
    events = [
        ("temp_control_started", {"tilt_color": color, "low_limit": 65, "high_limit": 70}),
        ("tilt_reading", {"tilt_color": color, "temp_f": 68.0, "gravity": 1.050}),
        ("heating_on", {"tilt_color": color, "low_limit": 65, "current_temp": 64, "high_limit": 70}),
        ("heating_off", {"tilt_color": color, "low_limit": 65, "current_temp": 66, "high_limit": 70}),
        ("cooling_on", {"tilt_color": color, "low_limit": 65, "current_temp": 71, "high_limit": 70}),
        ("cooling_off", {"tilt_color": color, "low_limit": 65, "current_temp": 69, "high_limit": 70}),
        ("temp_in_range", {"tilt_color": color, "low_limit": 65, "current_temp": 68, "high_limit": 70}),
    ]
    
    for event_type, payload in events:
        append_control_log(event_type, payload)
    
    # Count entries before archiving
    entries_before = 0
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f:
            entries_before = len(f.readlines())
    
    print(f"Entries before archiving: {entries_before}")
    
    # Archive the log (simulating new session start)
    archive_path = archive_temp_control_log_for_new_session(color)
    
    if archive_path and os.path.exists(archive_path):
        # Verify all entries were archived
        with open(archive_path, 'r') as f:
            archived_entries = [json.loads(line) for line in f if line.strip()]
        
        print(f"Archived entries: {len(archived_entries)}")
        
        # Verify Kasa plug events were included
        kasa_events = [e for e in archived_entries if e.get('event') in ['heating_on', 'heating_off', 'cooling_on', 'cooling_off']]
        print(f"Kasa plug events in archive: {len(kasa_events)}")
        
        # Verify original log is now empty or doesn't exist
        log_exists_after = os.path.exists(LOG_PATH)
        print(f"Original log exists after archiving: {log_exists_after}")
        
        if len(archived_entries) == entries_before and len(kasa_events) == 4:
            print("✅ PASS: All entries including Kasa plug events were archived")
            return True
        else:
            print(f"❌ FAIL: Expected {entries_before} total entries and 4 Kasa events")
            print(f"         Found {len(archived_entries)} total and {len(kasa_events)} Kasa events")
            return False
    else:
        print("❌ FAIL: Archive file was not created")
        return False

def test_continue_existing_preserves_data():
    """Test that choosing to continue existing session preserves data."""
    print("\n" + "="*80)
    print("TEST 3: Continue existing session preserves data")
    print("="*80)
    
    # Setup: Create temp control log
    color = "Green"
    
    # Clear any existing log
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    
    # Clear logs directory
    for f in os.listdir(LOGS_DIR):
        os.remove(os.path.join(LOGS_DIR, f))
    
    # Add some events
    for i in range(3):
        append_control_log("tilt_reading", {
            "tilt_color": color,
            "temp_f": 68.0 + i,
            "gravity": 1.050 - (i * 0.001)
        })
    
    # Count entries before "continuing"
    entries_before = 0
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f:
            entries_before = len(f.readlines())
    
    print(f"Entries before continuing: {entries_before}")
    
    # Simulate continuing existing session (no archiving)
    # Just add more data without archiving
    append_control_log("temp_control_started", {
        "tilt_color": color,
        "low_limit": 65,
        "high_limit": 70
    })
    
    # Count entries after continuing
    entries_after = 0
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f:
            entries_after = len(f.readlines())
    
    print(f"Entries after continuing: {entries_after}")
    
    # Check that no archive files were created
    archive_files = [f for f in os.listdir(LOGS_DIR) if f.startswith("temp_control_")]
    print(f"Archive files created: {len(archive_files)}")
    
    if entries_after == entries_before + 1 and len(archive_files) == 0:
        print("✅ PASS: Data was preserved, no archiving occurred")
        return True
    else:
        print(f"❌ FAIL: Expected {entries_before + 1} entries and 0 archives")
        print(f"         Found {entries_after} entries and {len(archive_files)} archives")
        return False

def test_kasa_events_in_batch_archive():
    """Test that Kasa events are NOT moved to batch archives (they stay in temp control log)."""
    print("\n" + "="*80)
    print("TEST 4: Kasa events remain in temp control log during batch archiving")
    print("="*80)
    
    # Clear batches directory
    for f in os.listdir(BATCHES_DIR):
        if f != '.gitkeep':
            os.remove(os.path.join(BATCHES_DIR, f))
    
    # Setup: Create initial batch with both sample and Kasa events
    color = "Orange"
    brewid = generate_brewid("Lager", "Batch1", "2025-01-01")
    tilt_cfg[color] = {
        "beer_name": "Lager",
        "batch_name": "Batch1",
        "ferm_start_date": "2025-01-01",
        "brewid": brewid
    }
    
    # Clear any existing log
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    
    # Add sample data
    for i in range(3):
        append_control_log("SAMPLE", {
            "tilt_color": color,
            "brewid": brewid,
            "temp_f": 55.0 + i,
            "gravity": 1.048 - (i * 0.001)
        })
    
    # Add Kasa plug events (these should NOT be archived with batch)
    append_control_log("heating_on", {
        "tilt_color": color,
        "low_limit": 50,
        "current_temp": 49,
        "high_limit": 58
    })
    append_control_log("heating_off", {
        "tilt_color": color,
        "low_limit": 50,
        "current_temp": 56,
        "high_limit": 58
    })
    
    # Count Kasa events before archiving
    kasa_events_before = 0
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f:
            for line in f:
                obj = json.loads(line)
                if obj.get('event') in ['heating_on', 'heating_off', 'cooling_on', 'cooling_off']:
                    kasa_events_before += 1
    
    print(f"Kasa events before archiving: {kasa_events_before}")
    
    # Archive old batch data
    old_cfg = tilt_cfg[color].copy()
    rotate_and_archive_old_history(color, brewid, old_cfg)
    
    # Check batch archive
    archive_files = [f for f in os.listdir(BATCHES_DIR) if f.endswith('.jsonl')]
    
    if archive_files:
        archive_path = os.path.join(BATCHES_DIR, archive_files[-1])  # Get latest
        with open(archive_path, 'r') as f:
            archived_entries = [json.loads(line) for line in f if line.strip()]
        
        # Count Kasa events in batch archive (should be 0)
        kasa_in_archive = sum(1 for e in archived_entries 
                             if e.get('event') in ['heating_on', 'heating_off', 'cooling_on', 'cooling_off'])
        
        print(f"Kasa events in batch archive: {kasa_in_archive}")
        
        # Count Kasa events remaining in temp control log
        kasa_remaining = 0
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                for line in f:
                    obj = json.loads(line)
                    if obj.get('event') in ['heating_on', 'heating_off', 'cooling_on', 'cooling_off']:
                        kasa_remaining += 1
        
        print(f"Kasa events remaining in temp control log: {kasa_remaining}")
        
        if kasa_in_archive == 0 and kasa_remaining == kasa_events_before:
            print("✅ PASS: Kasa events stayed in temp control log, not moved to batch archive")
            return True
        else:
            print("❌ FAIL: Kasa events were incorrectly handled")
            return False
    else:
        print("❌ FAIL: No batch archive was created")
        return False

# Run all tests
def run_all_tests():
    print("\n╔" + "="*78 + "╗")
    print("║" + " "*20 + "DATA HISTORY ARCHIVING TESTS" + " "*29 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        test_batch_change_archives_old_data,
        test_temp_control_new_session_archives_log,
        test_continue_existing_preserves_data,
        test_kasa_events_in_batch_archive
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) FAILED")
        return 1

# Cleanup
def cleanup():
    print(f"\nCleaning up test directory: {TEST_DIR}")
    shutil.rmtree(TEST_DIR, ignore_errors=True)

if __name__ == '__main__':
    try:
        exit_code = run_all_tests()
        cleanup()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Test execution failed with error: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)
