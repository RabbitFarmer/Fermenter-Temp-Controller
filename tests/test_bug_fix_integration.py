#!/usr/bin/env python3
"""
Integration test to verify the bug fix in app.py works correctly.

This test imports the actual rotate_and_archive_old_history function from app.py
and verifies it correctly archives only samples belonging to the old brewid.
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Add parent directory to path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test directory setup
TEST_DIR = tempfile.mkdtemp(prefix="integration_test_")
TEMP_CONTROL_DIR = os.path.join(TEST_DIR, "temp_control")
BATCHES_DIR = os.path.join(TEST_DIR, "batches")

os.makedirs(TEMP_CONTROL_DIR, exist_ok=True)
os.makedirs(BATCHES_DIR, exist_ok=True)

# Temporarily override paths in app module
import app
original_LOG_PATH = app.LOG_PATH
original_BATCHES_DIR = app.BATCHES_DIR
app.LOG_PATH = os.path.join(TEMP_CONTROL_DIR, 'temp_control_log.jsonl')
app.BATCHES_DIR = BATCHES_DIR

print(f"Test directory: {TEST_DIR}")
print(f"Using LOG_PATH: {app.LOG_PATH}")
print(f"Using BATCHES_DIR: {app.BATCHES_DIR}")

# Mock configurations
app.tilt_cfg = {}
app.temp_cfg = {}

def generate_brewid(beer_name, batch_name, ferm_start_date):
    import hashlib
    id_str = f"{beer_name}-{batch_name}-{ferm_start_date}"
    return hashlib.sha256(id_str.encode('utf-8')).hexdigest()[:8]

def append_log_entry(entry):
    """Directly append a log entry."""
    os.makedirs(os.path.dirname(app.LOG_PATH), exist_ok=True)
    with open(app.LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + "\n")

def test_actual_fix():
    """Test that the actual app.py function now works correctly after the fix."""
    print("\n" + "="*80)
    print("TEST: Verify app.py rotate_and_archive_old_history works correctly after fix")
    print("="*80)
    
    # Setup: Two different batches
    color = "Black"
    old_brewid = generate_brewid("IPA", "Batch1", "2025-01-01")
    other_brewid = generate_brewid("Stout", "Batch2", "2025-01-15")
    
    print(f"Old brewid to archive: {old_brewid}")
    print(f"Other brewid (should stay): {other_brewid}")
    
    # Create samples for both batches
    for i in range(3):
        append_log_entry({
            "timestamp": f"2025-01-{10+i}T12:00:00Z",
            "event": "SAMPLE",
            "tilt_color": color,
            "brewid": old_brewid,
            "temp_f": 68.0 + i,
            "gravity": 1.050
        })
    
    for i in range(2):
        append_log_entry({
            "timestamp": f"2025-01-{20+i}T12:00:00Z",
            "event": "SAMPLE",
            "tilt_color": color,
            "brewid": other_brewid,
            "temp_f": 55.0 + i,
            "gravity": 1.048
        })
    
    # Add a Kasa event (should not be archived)
    append_log_entry({
        "timestamp": "2025-01-15T12:00:00Z",
        "event": "HEATING-PLUG TURNED ON",
        "tilt_color": color,
        "brewid": old_brewid,
        "temp_f": 67.0
    })
    
    print(f"Created 3 samples for old brewid")
    print(f"Created 2 samples for other brewid")
    print(f"Created 1 Kasa event")
    
    # Count total entries before archiving
    total_before = 0
    samples_before = 0
    if os.path.exists(app.LOG_PATH):
        with open(app.LOG_PATH, 'r') as f:
            for line in f:
                total_before += 1
                obj = json.loads(line)
                if obj.get('event') == 'SAMPLE':
                    samples_before += 1
    
    print(f"\nTotal entries before archiving: {total_before}")
    print(f"SAMPLE entries before archiving: {samples_before}")
    
    # Call the actual function from app.py
    old_cfg = {"beer_name": "IPA", "brewid": old_brewid}
    success = app.rotate_and_archive_old_history(color, old_brewid, old_cfg)
    
    print(f"\nArchive operation success: {success}")
    
    # Check what was archived
    archive_files = [f for f in os.listdir(BATCHES_DIR) if f.endswith('.jsonl')]
    if not archive_files:
        print("❌ FAIL: No archive file was created")
        return False
    
    archive_path = os.path.join(BATCHES_DIR, archive_files[0])
    with open(archive_path, 'r') as f:
        archived = [json.loads(line) for line in f if line.strip()]
    
    print(f"\nArchived entries: {len(archived)}")
    
    # Count by brewid
    old_count = sum(1 for e in archived if e.get('brewid') == old_brewid)
    other_count = sum(1 for e in archived if e.get('brewid') == other_brewid)
    kasa_count = sum(1 for e in archived if e.get('event') not in ['SAMPLE'])
    
    print(f"Samples from old brewid in archive: {old_count}")
    print(f"Samples from OTHER brewid in archive: {other_count}")
    print(f"Non-SAMPLE events in archive: {kasa_count}")
    
    # Check what remains in log
    remaining_total = 0
    remaining_samples = 0
    remaining_other_brewid = 0
    remaining_kasa = 0
    
    if os.path.exists(app.LOG_PATH):
        with open(app.LOG_PATH, 'r') as f:
            for line in f:
                obj = json.loads(line)
                remaining_total += 1
                if obj.get('event') == 'SAMPLE':
                    remaining_samples += 1
                    if obj.get('brewid') == other_brewid:
                        remaining_other_brewid += 1
                elif obj.get('event') not in ['SAMPLE']:
                    remaining_kasa += 1
    
    print(f"\nRemaining total entries in log: {remaining_total}")
    print(f"Remaining SAMPLE entries: {remaining_samples}")
    print(f"Remaining samples from OTHER brewid: {remaining_other_brewid}")
    print(f"Remaining Kasa/control events: {remaining_kasa}")
    
    # Verify correctness
    # Should archive: 3 samples from old brewid
    # Should NOT archive: 2 samples from other brewid, 1 Kasa event
    # Note: The function also appends a "temp_control_mode_changed" event after archiving
    
    if old_count == 3 and other_count == 0 and kasa_count == 0 and remaining_other_brewid == 2:
        print("\n✅ PASS: Bug fix verified! Only samples from old brewid were archived.")
        print("         Samples from other batches and Kasa events remained in the log.")
        return True
    else:
        print(f"\n❌ FAIL: Unexpected results")
        print(f"         Expected: 3 old in archive, 0 other in archive, 0 Kasa in archive, 2 other remaining")
        print(f"         Got: {old_count} old, {other_count} other, {kasa_count} Kasa in archive, {remaining_other_brewid} other remaining")
        return False

# Run test
def run_test():
    print("\n╔" + "="*78 + "╗")
    print("║" + " "*20 + "INTEGRATION TEST: app.py BUG FIX" + " "*25 + "║")
    print("╚" + "="*78 + "╝")
    
    result = test_actual_fix()
    
    print("\n" + "="*80)
    print("TEST RESULT")
    print("="*80)
    print("✅ PASSED" if result else "❌ FAILED")
    
    return 0 if result else 1

# Cleanup
def cleanup():
    print(f"\nCleaning up test directory: {TEST_DIR}")
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    # Restore original paths
    app.LOG_PATH = original_LOG_PATH
    app.BATCHES_DIR = original_BATCHES_DIR

if __name__ == '__main__':
    try:
        exit_code = run_test()
        cleanup()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Test execution failed with error: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)
