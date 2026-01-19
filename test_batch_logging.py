#!/usr/bin/env python3
"""
Test script for batch logging adjustments.
Verifies that the batch_jsonl_filename function correctly finds existing files
by brewid instead of creating multiple files for the same batch.
"""

import os
import tempfile
import shutil
import sys

# Create a temporary test environment
TEST_DIR = tempfile.mkdtemp(prefix="batch_test_")
BATCHES_DIR = os.path.join(TEST_DIR, "batches")
os.makedirs(BATCHES_DIR, exist_ok=True)

print(f"Test directory: {TEST_DIR}")
print(f"Batches directory: {BATCHES_DIR}")

# Mock tilt_cfg for testing
tilt_cfg = {}

def normalize_to_yyyymmdd(date_str):
    """Mock function for testing"""
    from datetime import datetime
    if not date_str:
        return datetime.utcnow().strftime("%Y%m%d")
    return date_str.replace('-', '').replace('/', '')

def sanitize_filename(name):
    """Mock function for testing"""
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\r', '\t']
    result = name
    for char in invalid_chars:
        result = result.replace(char, '_')
    result = result.replace(' ', '_')
    return result[:50]

def ensure_batches_dir():
    """Mock function for testing"""
    os.makedirs(BATCHES_DIR, exist_ok=True)

# Include the modified batch_jsonl_filename function
def batch_jsonl_filename(color, brewid, created_date_mmddyyyy=None, beer_name=None, batch_name=None):
    """Generate batch JSONL filename in format: brewname_YYYYmmdd_brewid.jsonl
    
    First searches for an existing file containing the brewid.
    If found, returns that file to prevent multiple files for the same batch.
    If not found, generates a new filename.
    """
    ensure_batches_dir()
    bid = (brewid or "unknown")
    
    # First, search for any existing file that contains this brewid
    # Match brewid as complete token: either whole filename or preceded by underscore
    try:
        for fn in os.listdir(BATCHES_DIR):
            if not fn.endswith('.jsonl'):
                continue
            # Remove .jsonl extension for matching
            name_without_ext = fn.removesuffix('.jsonl')
            # Match if brewid is the entire name, or ends with _brewid
            # This ensures exact token matching: "abc" matches "abc.jsonl" or "name_abc.jsonl"
            # but NOT "xyzabc.jsonl" (no underscore separator before brewid)
            if name_without_ext == bid or name_without_ext.endswith(f"_{bid}"):
                # Found an existing file with this brewid
                existing_path = os.path.join(BATCHES_DIR, fn)
                print(f"[BATCH] Found existing batch file for brewid {bid}: {fn}")
                return existing_path
    except Exception as e:
        print(f"[BATCH] Error searching for existing batch file: {e}")
    
    # No existing file found, generate a new filename
    # Get beer_name from tilt config if not provided
    if beer_name is None:
        cfg = tilt_cfg.get(color, {})
        beer_name = cfg.get("beer_name", "")
    
    # Create filename with brew name, date, and brewid
    if beer_name:
        safe_beer_name = sanitize_filename(beer_name)
    else:
        safe_beer_name = "Batch"
    
    # Convert date to YYYYmmdd format
    if created_date_mmddyyyy:
        date_yyyymmdd = normalize_to_yyyymmdd(created_date_mmddyyyy)
    else:
        from datetime import datetime
        date_yyyymmdd = datetime.utcnow().strftime("%Y%m%d")
    
    fname = f"{safe_beer_name}_{date_yyyymmdd}_{bid}.jsonl"
    print(f"[BATCH] Creating new batch file for brewid {bid}: {fname}")
    return os.path.join(BATCHES_DIR, fname)

# Test cases
def test_new_batch_file():
    """Test creating a new batch file when none exists"""
    print("\n" + "="*80)
    print("TEST 1: Create new batch file (no existing file)")
    print("="*80)
    
    brewid = "abc12345"
    result = batch_jsonl_filename("Black", brewid, created_date_mmddyyyy="20250115", beer_name="Test IPA")
    
    expected_filename = f"Test_IPA_20250115_{brewid}.jsonl"
    expected_path = os.path.join(BATCHES_DIR, expected_filename)
    
    print(f"Expected: {expected_path}")
    print(f"Got:      {result}")
    
    if result == expected_path:
        print("✅ PASS: Correct filename generated for new batch")
        return True
    else:
        print("❌ FAIL: Incorrect filename")
        return False

def test_existing_batch_file():
    """Test finding an existing batch file with the same brewid"""
    print("\n" + "="*80)
    print("TEST 2: Find existing batch file with same brewid")
    print("="*80)
    
    brewid = "def67890"
    
    # Create an existing file
    existing_file = os.path.join(BATCHES_DIR, f"Old_Beer_20250110_{brewid}.jsonl")
    with open(existing_file, "w") as f:
        f.write('{"test": "data"}\n')
    print(f"Created existing file: {existing_file}")
    
    # Try to get filename with different date and beer name
    result = batch_jsonl_filename("Blue", brewid, created_date_mmddyyyy="20250120", beer_name="New Beer")
    
    print(f"Expected: {existing_file}")
    print(f"Got:      {result}")
    
    if result == existing_file:
        print("✅ PASS: Found and returned existing file instead of creating new one")
        return True
    else:
        print("❌ FAIL: Did not find existing file")
        return False

def test_multiple_calls_same_brewid():
    """Test multiple calls with same brewid but different parameters"""
    print("\n" + "="*80)
    print("TEST 3: Multiple calls with same brewid, different dates")
    print("="*80)
    
    brewid = "xyz99999"
    
    # First call - should create new file
    result1 = batch_jsonl_filename("Green", brewid, created_date_mmddyyyy="20250101", beer_name="Stout")
    print(f"First call result:  {result1}")
    
    # Create the file
    with open(result1, "w") as f:
        f.write('{"test": "data"}\n')
    
    # Second call - should find existing file even with different date
    result2 = batch_jsonl_filename("Green", brewid, created_date_mmddyyyy="20250115", beer_name="Stout")
    print(f"Second call result: {result2}")
    
    # Third call - should still find the same file
    result3 = batch_jsonl_filename("Green", brewid, created_date_mmddyyyy="20250120", beer_name="Different Beer")
    print(f"Third call result:  {result3}")
    
    if result1 == result2 == result3:
        print("✅ PASS: All calls returned the same file path")
        return True
    else:
        print("❌ FAIL: Calls returned different file paths")
        return False

def test_different_brewids():
    """Test that different brewids create different files"""
    print("\n" + "="*80)
    print("TEST 4: Different brewids create different files")
    print("="*80)
    
    brewid1 = "aaa11111"
    brewid2 = "bbb22222"
    
    result1 = batch_jsonl_filename("Red", brewid1, created_date_mmddyyyy="20250115", beer_name="Beer A")
    result2 = batch_jsonl_filename("Red", brewid2, created_date_mmddyyyy="20250115", beer_name="Beer B")
    
    print(f"brewid1 file: {result1}")
    print(f"brewid2 file: {result2}")
    
    if result1 != result2 and brewid1 in result1 and brewid2 in result2:
        print("✅ PASS: Different brewids created different files")
        return True
    else:
        print("❌ FAIL: Different brewids did not create different files")
        return False

def test_brewid_substring_match():
    """Test that brewid matching doesn't accidentally match substrings"""
    print("\n" + "="*80)
    print("TEST 5: Brewid substring matching - should NOT match partial brewids")
    print("="*80)
    
    brewid_short = "abc12345"
    brewid_long = "abc123456789"  # Contains the short brewid as substring
    
    # Create file for short brewid
    file_short = os.path.join(BATCHES_DIR, f"Beer_20250115_{brewid_short}.jsonl")
    with open(file_short, "w") as f:
        f.write('{"test": "data"}\n')
    print(f"Created file for short brewid: {file_short}")
    
    # Try to get file for long brewid - should create new file, not match short one
    result_long = batch_jsonl_filename("Orange", brewid_long, created_date_mmddyyyy="20250115", beer_name="Beer")
    print(f"Long brewid result: {result_long}")
    
    # The long brewid should get its own file (not the short one)
    if brewid_long in result_long and result_long != file_short:
        print("✅ PASS: Long brewid got its own file (not substring matched to short brewid)")
        
        # Also verify that calling with short brewid still finds the original file
        result_short = batch_jsonl_filename("Orange", brewid_short, created_date_mmddyyyy="20250120", beer_name="Different Beer")
        print(f"Short brewid result: {result_short}")
        if result_short == file_short:
            print("✅ PASS: Short brewid still finds its own file correctly")
            return True
        else:
            print(f"❌ FAIL: Short brewid didn't find its file. Expected {file_short}, got {result_short}")
            return False
    else:
        print("❌ FAIL: Brewid matching is incorrect")
        return False

def test_legacy_format():
    """Test that legacy format (just brewid.jsonl) is found correctly"""
    print("\n" + "="*80)
    print("TEST 6: Legacy format (brewid.jsonl) should be found")
    print("="*80)
    
    brewid = "legacy123"
    
    # Create a legacy format file
    legacy_file = os.path.join(BATCHES_DIR, f"{brewid}.jsonl")
    with open(legacy_file, "w") as f:
        f.write('{"test": "legacy data"}\n')
    print(f"Created legacy file: {legacy_file}")
    
    # Try to get filename - should find the legacy file
    result = batch_jsonl_filename("Purple", brewid, created_date_mmddyyyy="20250115", beer_name="Some Beer")
    print(f"Result: {result}")
    
    if result == legacy_file:
        print("✅ PASS: Found legacy format file correctly")
        return True
    else:
        print(f"❌ FAIL: Did not find legacy file. Expected {legacy_file}, got {result}")
        return False

# Run all tests
def run_all_tests():
    print("\n╔" + "="*78 + "╗")
    print("║" + " "*25 + "BATCH LOGGING TESTS" + " "*34 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        test_new_batch_file,
        test_existing_batch_file,
        test_multiple_calls_same_brewid,
        test_different_brewids,
        test_brewid_substring_match,
        test_legacy_format
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
