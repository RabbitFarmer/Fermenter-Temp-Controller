# Batch History Duplication Fix - Summary

## Problem Description

The batch history page was showing duplicate entries for the same batch, making it appear as if multiple tilts of the same color were active when only one was actually in use. Additionally, the "Close" button for batches was not working properly.

### Specific Issues Reported
1. **Duplicate Batches**: 1 Black tilt in operation appeared aggregated with 6 Blue tilts
2. **Close Button Failure**: Clicking the "Close" button on dead tilts did nothing

## Root Causes

### 1. Duplicate Batch Entries
**Location**: `app.py` line 4111 (batch_settings POST handler)

**Problem**: Every time a batch was edited or saved, the code **appended** a new entry to the `batch_history_{color}.json` file instead of updating the existing entry.

```python
# OLD CODE (created duplicates):
batches.append(batch_entry)  # Always added a new entry
```

**Impact**: Editing a batch 6 times resulted in 6 duplicate entries in the history file, all with the same `brewid`, which were then displayed as 6 separate batches on the batch history page.

### 2. Close Button Not Working
**Location**: `app.py` line 5702 (close_batch route)

**Problem**: The code had a `break` statement that exited the loop after closing only the first matching batch entry.

```python
# OLD CODE (only closed first match):
for batch in batches:
    if batch.get('brewid') == brewid:
        batch['is_active'] = False
        break  # ⚠️ Exits after first match!
```

**Impact**: When there were 6 duplicate entries for a batch, only the first one was marked as closed. The other 5 remained active and continued to appear on the page, making it seem like the close button didn't work.

## Solutions Implemented

### 1. UPSERT Logic for Batch Edits
**File**: `app.py` lines 4106-4125

Changed the batch save logic to **update** existing entries instead of always appending:

```python
# NEW CODE (prevents duplicates):
batch_found = False
for i, batch in enumerate(batches):
    if batch.get('brewid') == brew_id:
        # Update existing batch entry instead of creating duplicate
        batches[i] = batch_entry
        batch_found = True
        break

if not batch_found:
    # New batch - append it
    batches.append(batch_entry)
```

**Benefit**: Editing a batch now updates the existing entry in place, preventing duplicates from being created.

### 2. Close All Duplicate Entries
**File**: `app.py` lines 5695-5703

Removed the `break` statement to ensure all matching entries are closed:

```python
# NEW CODE (closes all matches):
for batch in batches:
    if batch.get('brewid') == brewid:
        batch['is_active'] = False
        batch['closed_date'] = datetime.utcnow().strftime('%Y-%m-%d')
        batch_found = True
        # Continue to close ALL matching batches (don't break)
```

**Benefit**: The close button now works properly, even for batches that have existing duplicate entries.

### 3. Cleanup Utility for Existing Duplicates
**File**: `app.py` lines 5815-5865, `templates/batch_history_select.html`

Added a new route and UI button to clean up duplicate entries that were created before the fix:

- **Route**: `/cleanup_batch_duplicates` (POST)
- **UI**: "🧹 Cleanup Duplicates" button on the Batch History page
- **Function**: Removes duplicate entries, keeping only the most recent version of each batch

**How to Use**:
1. Go to the Batch History page
2. Click the "🧹 Cleanup Duplicates" button
3. Confirm when prompted
4. The page will refresh showing deduplicated batches

## Testing

Created comprehensive test suite in `tests/test_batch_duplication_fix.py`:

1. ✅ **test_batch_upsert_prevents_duplicates**: Verifies that editing a batch updates the existing entry instead of creating duplicates
2. ✅ **test_close_batch_handles_duplicates**: Verifies that close_batch closes all duplicate entries
3. ✅ **test_cleanup_duplicates**: Verifies the cleanup utility removes duplicates correctly

All tests pass successfully.

## Migration Guide

### For New Installations
No action needed. The fix prevents duplicates from being created.

### For Existing Installations with Duplicates

If you're seeing duplicate batches in your history:

1. **Update to this version** - The new code prevents future duplicates
2. **Clean up existing duplicates** - Use the "Cleanup Duplicates" button:
   - Navigate to Batch History page
   - Click "🧹 Cleanup Duplicates" button
   - Confirm the operation
   - The page will reload showing deduplicated batches

The cleanup utility:
- Keeps the **most recent** version of each batch (last occurrence in the file)
- Preserves all unique batches (different brewids)
- Is safe to run multiple times (idempotent)
- Shows a message with the number of duplicates removed

## Technical Details

### Data Structure
Batch history is stored in JSON files: `batches/batch_history_{color}.json`

Each file contains an array of batch objects:
```json
[
  {
    "brewid": "abc123",
    "beer_name": "My IPA",
    "batch_name": "Batch 1",
    "is_active": true,
    "closed_date": null,
    ...
  }
]
```

### Key Fields
- `brewid`: Unique identifier for each batch (hash of beer_name, batch_name, and start date)
- `is_active`: Boolean flag - true for active batches, false for closed batches
- `closed_date`: ISO date string when batch was closed (null if active)

### Backwards Compatibility
- The fix handles both old and new data formats
- Existing duplicate entries are automatically handled by the close/reopen functions
- The migration flag `is_active` defaults to `true` for old batches without this field

## Security

No security vulnerabilities introduced. CodeQL scan passed with 0 alerts.

## Files Modified

1. `app.py` - Core application logic
   - batch_settings route (upsert logic)
   - close_batch route (close all duplicates)
   - reopen_batch route (reopen all duplicates)
   - New cleanup_batch_duplicates route

2. `templates/batch_history_select.html` - UI updates
   - Added cleanup button with proper accessibility
   - Added JavaScript function for cleanup operation

3. `tests/test_batch_duplication_fix.py` - Test suite
   - Comprehensive tests for all fix components

## Future Enhancements

Potential improvements for consideration:
- Add batch edit history/audit log
- Add batch merge functionality for intentional duplicates
- Add batch validation to prevent creation of true duplicates
- Add visual indicator when duplicates are detected
