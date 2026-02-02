# Fix Summary: Temperature Control Limits Becoming Null (Issue #244)

## Problem Statement
When temperature control started heating, the `low_limit` and `high_limit` values were being cleared from memory and becoming `null`. This prevented the heater from turning off when the high limit was reached, causing the system to stay in heating mode indefinitely.

## Root Cause
In the `periodic_temp_control()` function (app.py, line 3172), configuration is reloaded from disk every control loop iteration:

```python
file_cfg = load_json(TEMP_CFG_FILE, {})
temp_cfg.update(file_cfg)
```

If the config file contained `null` values for `low_limit` or `high_limit` (due to corruption, race condition, or incomplete save), these null values would overwrite the valid in-memory values.

## Solution
Added defensive checks to prevent null limit values from overwriting valid in-memory values, following the same pattern as the existing `current_temp` protection:

```python
# Prevent null/None values from overwriting valid limit values in memory
# This preserves limits if the file was corrupted or saved with null values
if 'low_limit' in file_cfg and file_cfg['low_limit'] is None and temp_cfg.get('low_limit') is not None:
    file_cfg.pop('low_limit')
if 'high_limit' in file_cfg and file_cfg['high_limit'] is None and temp_cfg.get('high_limit') is not None:
    file_cfg.pop('high_limit')
```

## Code Changes
**File**: `app.py`  
**Location**: Lines 3149-3154 in `periodic_temp_control()` function  
**Lines Changed**: 7 lines added (minimal surgical fix)

## How It Works
1. After loading config from disk, check if `low_limit` or `high_limit` are `null`
2. If they are `null` in the file BUT valid (not null) in memory, remove them from `file_cfg`
3. When `temp_cfg.update(file_cfg)` runs, the null values are not present, so memory values are preserved
4. Temperature control logic always has valid limits to make heating/cooling decisions

## Testing
### New Tests Created
1. **test_limit_preservation.py**
   - Memory-based limit preservation test
   - File I/O test with actual file operations
   - **Result**: ✓ PASSED

2. **test_issue_244_simulation.py**
   - Simulates exact scenario from Issue #244
   - Shows complete lifecycle: heating on → config corruption → limits preserved → heating off
   - Includes comparison of behavior with and without fix
   - **Result**: ✓ PASSED (Issue #244 RESOLVED)

### Regression Tests
- ✓ `test_heating_off_at_high_limit.py` - Still passes
- ✓ `test_cooling_off_at_low_limit.py` - Still passes
- ✓ `tests/test_both_heating_cooling.py` - Still passes

## Code Quality Verification
- ✓ **Code Review**: No issues found
- ✓ **Security Scan (CodeQL)**: 0 vulnerabilities detected
- ✓ **Follows Existing Patterns**: Matches existing `current_temp` protection pattern
- ✓ **Minimal Changes**: Only 7 lines added, no existing code modified

## Expected Behavior (After Fix)
### Before Fix (Issue #244)
```
1. Heating turns ON (temp below low limit)
2. Config file gets corrupted with null limits
3. Config reload overwrites limits with null
4. Temperature reaches high limit
5. ✗ Cannot turn heater OFF (limits are null)
6. ✗ Heater stays ON indefinitely
```

### After Fix (This PR)
```
1. Heating turns ON (temp below low limit)
2. Config file gets corrupted with null limits
3. Config reload attempts to load null limits
4. ✓ Fix detects null values and preserves memory values
5. Temperature reaches high limit
6. ✓ Heater turns OFF correctly (limits are valid)
7. ✓ System operates normally
```

## Benefits
1. **Safety**: Prevents runaway heating/cooling due to lost limits
2. **Reliability**: System recovers from config file corruption
3. **Consistency**: Uses same defensive pattern as `current_temp` protection
4. **No Breaking Changes**: Existing functionality unchanged

## Files Modified
- `app.py` - 7 lines added to `periodic_temp_control()`
- `test_limit_preservation.py` - New test file (248 lines)
- `test_issue_244_simulation.py` - New test file (338 lines)

**Total Changes**: 593 lines (7 production code, 586 test code)

## Verification Steps
To verify the fix works:

1. Run limit preservation test:
   ```bash
   python3 test_limit_preservation.py
   ```
   Expected: ✓ ALL TESTS PASSED

2. Run Issue #244 simulation:
   ```bash
   python3 test_issue_244_simulation.py
   ```
   Expected: ✓ Issue #244 is RESOLVED

3. Run existing regression tests:
   ```bash
   python3 test_heating_off_at_high_limit.py
   python3 test_cooling_off_at_low_limit.py
   python3 tests/test_both_heating_cooling.py
   ```
   Expected: All tests pass

## Security Summary
No security vulnerabilities introduced or discovered:
- CodeQL scan: 0 alerts
- No external dependencies added
- No network/file system security changes
- Defensive code addition (improves safety)

## Conclusion
This fix resolves GitHub Issue #244 by preventing temperature control limits from becoming null during config reload operations. The solution is minimal (7 lines), follows existing code patterns, is thoroughly tested, and has been verified to not introduce any security vulnerabilities or break existing functionality.
