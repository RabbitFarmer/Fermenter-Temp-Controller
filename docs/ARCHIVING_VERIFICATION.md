# Data History Archiving Verification

## Issue Summary

Confirmed that when a new batch and/or new temperature control is started, previous histories (including Kasa plug events) are properly archived, with the exception of allowing the user to specifically continue with the old data or start new as already programmed.

## Bug Found and Fixed

### Description
The batch archiving function `rotate_and_archive_old_history()` contained a logic error that caused it to archive ALL sample entries with any tilt_color, instead of only archiving samples from the specific old batch being replaced.

### Root Cause
**Location:** `app.py` line 613

**Original Code:**
```python
if isinstance(payload, dict) and payload.get('tilt_color') and old_cfg.get('brewid') == old_brewid:
```

**Problem:** The condition `old_cfg.get('brewid') == old_brewid` is always `True` because both values are the same (the old brewid being archived). This meant the function would archive any sample with a tilt_color, regardless of which batch it belonged to.

**Fixed Code:**
```python
if isinstance(payload, dict) and payload.get('brewid') == old_brewid:
```

**Solution:** Check if the log entry's brewid matches the old brewid being archived.

### Impact

**Before Fix:**
- When changing batches, ALL sample entries were archived
- This incorrectly included samples from OTHER active batches on different Tilt hydrometers
- Could result in data loss for unrelated fermentation batches

**After Fix:**
- Only samples belonging to the specific old brewid are archived
- Samples from other active batches remain in the main log
- Each batch maintains its own history correctly

### Additional Improvement

**Location:** `app.py` line 625-627

Added a condition to only log "temp_control_mode_changed" events when samples were actually archived:

```python
# Only log mode change if we actually archived samples
if moved > 0:
    append_control_log("temp_control_mode_changed", {...})
```

This prevents misleading log entries when no archiving occurred.

## Archiving Behavior Verification

### Batch Changes (Brewid Changes)

✅ **Confirmed:** When a batch is changed (new brewid):
- Only SAMPLE events belonging to the old brewid are archived
- Archive file created: `batches/{color}_{beer_name}_{timestamp}.jsonl`
- Samples from OTHER active batches remain in the main log
- Kasa plug events remain in the temperature control log (not archived with batches)
- Non-SAMPLE events (heating/cooling/temp control) remain in the main log

### Temperature Control New Session

✅ **Confirmed:** When starting a NEW temperature control session:
- ALL previous events are archived (samples, Kasa events, control events)
- Archive file created: `logs/temp_control_{tilt_color}_{timestamp}.jsonl`
- A fresh log is started
- User is prompted to choose "New Session" or "Continue Existing" in the UI

### Continue Existing Session

✅ **Confirmed:** When continuing an EXISTING session:
- NO archiving occurs
- All previous data is preserved
- New events are appended to the existing log
- User chooses this option in the UI modal

### Kasa Plug Event Handling

✅ **Confirmed:** Kasa plug events (heating_on, heating_off, cooling_on, cooling_off):
- Are logged to `temp_control_log.jsonl`
- Are NOT archived when batches are changed (they stay in the temp control log)
- ARE archived when starting a new temperature control session
- Remain in log when continuing existing session

### Multiple Active Batches

✅ **Confirmed:** When multiple batches are active on different Tilt hydrometers:
- Each batch is tracked by its unique brewid
- Changing one batch does NOT affect samples from other batches
- Only samples from the specific batch being changed are archived
- Other batches' samples remain in the main log

## Test Coverage

### New Tests Created

1. **test_data_history_archiving.py**
   - Comprehensive test suite covering all archiving scenarios
   - Tests batch changes, temp control sessions, and data preservation
   - 4/4 tests passing

2. **test_batch_archive_bug.py**
   - Demonstrates the bug with the original code
   - Verifies the fix works correctly
   - Shows incorrect behavior (archives wrong samples) vs correct behavior

3. **test_bug_fix_integration.py**
   - Integration test using actual app.py functions
   - Verifies the fix works in the real application context
   - Tests with multiple batches and Kasa events

4. **demo_archiving.py**
   - Comprehensive demonstration of all archiving scenarios
   - Shows real-world usage patterns
   - Validates all edge cases

### Test Results

```
✅ All archiving tests: 4/4 PASSED
✅ Existing batch logging tests: 6/6 PASSED
✅ Integration tests: PASSED
✅ Demonstration scenarios: All successful
```

## User Experience

### Batch Settings Page
When a user changes batch information that results in a new brewid:
1. Old batch samples are automatically archived
2. Archive file is created in `batches/` directory
3. User can continue working with the new batch
4. Old batch data is preserved in the archive

### Temperature Control Page
When a user toggles temperature control ON:
1. UI modal prompts: "Start New Session" or "Continue Existing"
2. **New Session:**
   - All previous events are archived
   - Fresh log is started
   - Archive created in `logs/` directory
3. **Continue Existing:**
   - No archiving occurs
   - All previous data is preserved
   - New events append to existing log

## Files Modified

1. **app.py**
   - Line 613: Fixed brewid comparison (bug fix)
   - Lines 625-627: Only log mode change when samples archived (improvement)

2. **tests/test_data_history_archiving.py**
   - Updated to match actual app.py log structure
   - Improved test accuracy

## Files Added

1. **tests/test_batch_archive_bug.py** - Bug demonstration
2. **tests/test_bug_fix_integration.py** - Integration testing
3. **tests/demo_archiving.py** - Comprehensive demonstration
4. **ARCHIVING_VERIFICATION.md** - This documentation

## Security Analysis

✅ **CodeQL Scan:** No security issues found

## Recommendations

### For Users
1. Archive files are stored in:
   - `batches/` - Batch-specific archives (when changing batches)
   - `logs/` - Temperature control session archives (when starting new sessions)
2. Archive files use JSONL format (one JSON object per line)
3. Archive filenames include timestamp for easy identification
4. Regular backups of archive directories are recommended

### For Developers
1. When modifying batch or temperature control logic, ensure brewid comparisons use the log entry's brewid
2. Test with multiple active batches to ensure isolation
3. Verify Kasa events are not inadvertently archived with batches
4. Use the comprehensive test suite to prevent regression

## Conclusion

The data history archiving system is working correctly after the bug fix. All scenarios have been validated:

✅ Batch changes archive only the correct samples  
✅ Temperature control sessions can start fresh or continue existing  
✅ Kasa plug events are properly handled  
✅ Multiple active batches are correctly isolated  
✅ User has control over archiving behavior  
✅ No security vulnerabilities detected

The issue has been confirmed and resolved.
