#!/usr/bin/env python3
"""
Test to verify there's a bug in the batch archiving logic.

This test demonstrates that the current implementation archives ALL SAMPLE
entries with a tilt_color, not just the ones belonging to the old brewid.
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Test directory setup
TEST_DIR = tempfile.mkdtemp(prefix="bug_test_")
TEMP_CONTROL_DIR = os.path.join(TEST_DIR, "temp_control")
BATCHES_DIR = os.path.join(TEST_DIR, "batches")

os.makedirs(TEMP_CONTROL_DIR, exist_ok=True)
os.makedirs(BATCHES_DIR, exist_ok=True)

LOG_PATH = os.path.join(TEMP_CONTROL_DIR, 'temp_control_log.jsonl')

print(f"Test directory: {TEST_DIR}")

# Mock configurations
tilt_cfg = {}
temp_cfg = {}

def generate_brewid(beer_name, batch_name, ferm_start_date):
    import hashlib
    id_str = f"{beer_name}-{batch_name}-{ferm_start_date}"
    return hashlib.sha256(id_str.encode('utf-8')).hexdigest()[:8]

def append_log_entry(entry):
    """Directly append a log entry (bypassing append_control_log)."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + "\n")

def rotate_and_archive_old_history_BUGGY(color, old_brewid, old_cfg):
    """Current implementation from app.py (line 592-629) - has a bug!"""
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
                    payload = obj or {}
                    # BUG: This line checks old_cfg.get('brewid') == old_brewid which is always true!
                    # It should check payload.get('brewid') == old_brewid
                    if isinstance(payload, dict) and payload.get('tilt_color') and old_cfg.get('brewid') == old_brewid:
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
        
        print(f"[BUGGY] Archived {moved} SAMPLE entries")
        return True
    except Exception as e:
        print(f"[LOG] rotate_and_archive_old_history error: {e}")
        return False

def rotate_and_archive_old_history_FIXED(color, old_brewid, old_cfg):
    """Fixed implementation - checks payload.get('brewid') == old_brewid"""
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
                    payload = obj or {}
                    # FIXED: Check if the sample's brewid matches the old brewid
                    if isinstance(payload, dict) and payload.get('brewid') == old_brewid:
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
        
        print(f"[FIXED] Archived {moved} SAMPLE entries")
        return True
    except Exception as e:
        print(f"[LOG] rotate_and_archive_old_history error: {e}")
        return False

def test_bug_demonstration():
    """Demonstrate the bug: it archives samples from OTHER batches too!"""
    print("\n" + "="*80)
    print("TEST: Demonstrate the archiving bug")
    print("="*80)
    
    # Setup: Two different batches with different brewids
    color = "Black"
    old_brewid = generate_brewid("IPA", "Batch1", "2025-01-01")
    other_brewid = generate_brewid("Stout", "Batch2", "2025-01-15")
    
    # Create log entries for BOTH batches
    # 3 samples from old batch
    for i in range(3):
        append_log_entry({
            "timestamp": f"2025-01-{10+i}T12:00:00Z",
            "event": "SAMPLE",
            "tilt_color": color,
            "brewid": old_brewid,
            "temp_f": 68.0 + i,
            "gravity": 1.050
        })
    
    # 2 samples from a DIFFERENT batch (should NOT be archived!)
    for i in range(2):
        append_log_entry({
            "timestamp": f"2025-01-{20+i}T12:00:00Z",
            "event": "SAMPLE",
            "tilt_color": color,
            "brewid": other_brewid,
            "temp_f": 55.0 + i,
            "gravity": 1.048
        })
    
    print(f"Created 3 samples for old brewid: {old_brewid}")
    print(f"Created 2 samples for other brewid: {other_brewid}")
    
    # Count total samples before archiving
    total_before = 0
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f:
            for line in f:
                obj = json.loads(line)
                if obj.get('event') == 'SAMPLE':
                    total_before += 1
    
    print(f"Total SAMPLE entries before archiving: {total_before}")
    
    # Test with BUGGY version
    old_cfg = {"beer_name": "IPA", "brewid": old_brewid}
    rotate_and_archive_old_history_BUGGY(color, old_brewid, old_cfg)
    
    # Check what was archived
    archive_files = [f for f in os.listdir(BATCHES_DIR) if f.endswith('.jsonl')]
    if archive_files:
        archive_path = os.path.join(BATCHES_DIR, archive_files[0])
        with open(archive_path, 'r') as f:
            archived = [json.loads(line) for line in f if line.strip()]
        
        print(f"\nArchived entries: {len(archived)}")
        
        # Count by brewid
        old_count = sum(1 for e in archived if e.get('brewid') == old_brewid)
        other_count = sum(1 for e in archived if e.get('brewid') == other_brewid)
        
        print(f"Samples from old brewid in archive: {old_count}")
        print(f"Samples from OTHER brewid in archive: {other_count} ⚠️")
        
        if other_count > 0:
            print("\n❌ BUG CONFIRMED: The function archived samples from OTHER batches!")
            print("   This is because it checks 'old_cfg.get('brewid') == old_brewid' instead of 'payload.get('brewid') == old_brewid'")
            return False
        else:
            print("\n✅ No bug detected (unexpected)")
            return True
    else:
        print("No archive file created")
        return False

def test_fixed_version():
    """Test the fixed version - should only archive samples from the old brewid"""
    print("\n" + "="*80)
    print("TEST: Verify the fixed version works correctly")
    print("="*80)
    
    # Clear log and archives
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    for f in os.listdir(BATCHES_DIR):
        os.remove(os.path.join(BATCHES_DIR, f))
    
    # Setup: Two different batches
    color = "Blue"
    old_brewid = generate_brewid("Lager", "Batch1", "2025-01-01")
    other_brewid = generate_brewid("Ale", "Batch2", "2025-01-15")
    
    # Create samples for both batches
    for i in range(3):
        append_log_entry({
            "timestamp": f"2025-01-{10+i}T12:00:00Z",
            "event": "SAMPLE",
            "tilt_color": color,
            "brewid": old_brewid,
            "temp_f": 50.0 + i,
            "gravity": 1.048
        })
    
    for i in range(2):
        append_log_entry({
            "timestamp": f"2025-01-{20+i}T12:00:00Z",
            "event": "SAMPLE",
            "tilt_color": color,
            "brewid": other_brewid,
            "temp_f": 68.0 + i,
            "gravity": 1.052
        })
    
    print(f"Created 3 samples for old brewid: {old_brewid}")
    print(f"Created 2 samples for other brewid: {other_brewid}")
    
    # Test with FIXED version
    old_cfg = {"beer_name": "Lager", "brewid": old_brewid}
    rotate_and_archive_old_history_FIXED(color, old_brewid, old_cfg)
    
    # Check what was archived
    archive_files = [f for f in os.listdir(BATCHES_DIR) if f.endswith('.jsonl')]
    if archive_files:
        archive_path = os.path.join(BATCHES_DIR, archive_files[0])
        with open(archive_path, 'r') as f:
            archived = [json.loads(line) for line in f if line.strip()]
        
        print(f"\nArchived entries: {len(archived)}")
        
        # Count by brewid
        old_count = sum(1 for e in archived if e.get('brewid') == old_brewid)
        other_count = sum(1 for e in archived if e.get('brewid') == other_brewid)
        
        print(f"Samples from old brewid in archive: {old_count}")
        print(f"Samples from OTHER brewid in archive: {other_count}")
        
        # Check what remains in log
        remaining_total = 0
        remaining_other = 0
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                for line in f:
                    obj = json.loads(line)
                    if obj.get('event') == 'SAMPLE':
                        remaining_total += 1
                        if obj.get('brewid') == other_brewid:
                            remaining_other += 1
        
        print(f"Remaining SAMPLE entries in log: {remaining_total}")
        print(f"Remaining samples from OTHER brewid: {remaining_other}")
        
        if old_count == 3 and other_count == 0 and remaining_other == 2:
            print("\n✅ PASS: Fixed version correctly archives only the old batch samples")
            return True
        else:
            print(f"\n❌ FAIL: Expected 3 old, 0 other in archive, 2 other remaining")
            return False
    else:
        print("No archive file created")
        return False

# Run tests
def run_all_tests():
    print("\n╔" + "="*78 + "╗")
    print("║" + " "*25 + "BATCH ARCHIVE BUG TEST" + " "*30 + "║")
    print("╚" + "="*78 + "╝")
    
    bug_result = test_bug_demonstration()
    fixed_result = test_fixed_version()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Bug demonstration: {'FAILED (bug exists)' if not bug_result else 'PASSED (no bug found)'}")
    print(f"Fixed version: {'PASSED' if fixed_result else 'FAILED'}")
    
    return 0 if fixed_result else 1

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
