# Fix Summary: Temp_Control_Tilt.jsonl Logging Issue

## Issue Description
The `temp_control_tilt.jsonl` log file was incorrectly recording readings from **all available Tilts** instead of only the Tilt that was explicitly assigned for temperature control.

### User's Problem
- User assigned **Black** tilt for temperature control
- User does NOT own a **Red** tilt
- Log file showed entries for both Red and Blue tilts:
  ```json
  {"timestamp": "2026-02-04T02:35:50.145585Z", "local_time": "2026-02-04 02:35:50", "tilt_color": "Red", "temperature": 70.2, "gravity": 1.048}
  {"timestamp": "2026-02-04T02:35:50.145455Z", "local_time": "2026-02-04 02:35:50", "tilt_color": "Blue", "temperature": 68.5, "gravity": 1.05, "brewid": "test-brew-123", "beer_name": "Test IPA"}
  ```

## Root Cause

The logging code in `app.py` (lines 2747-2760) was using `get_control_tilt_color()` to determine which tilt to log:

```python
# OLD CODE (BEFORE FIX)
control_tilt_color = get_control_tilt_color()
if control_tilt_color and control_tilt_color in live_tilts:
    # ... log the tilt reading
```

The problem is that `get_control_tilt_color()` has **fallback logic**:
- If `temp_cfg["tilt_color"]` is set, it returns that color (correct behavior)
- If `temp_cfg["tilt_color"]` is empty, it returns **any available tilt** (incorrect for logging)

This fallback behavior is intentional for temperature control (allows system to work without explicit assignment), but it's **NOT appropriate for logging** because:
1. The log file should only track the **explicitly assigned** tilt
2. Fallback tilts should not be logged as they are not officially assigned for temp control
3. Users expect to see only their assigned tilt in this log file

## The Fix

Changed the logging logic to check `temp_cfg.get("tilt_color")` **directly** instead of using `get_control_tilt_color()`:

```python
# NEW CODE (AFTER FIX)
# Log temp control tilt reading - ONLY if explicitly assigned
# Don't log fallback tilts, only log when tilt_color is explicitly set
assigned_tilt_color = temp_cfg.get("tilt_color")
if assigned_tilt_color and assigned_tilt_color in live_tilts:
    # ... log the tilt reading
```

### Key Changes
1. **Line 2749**: Changed from `control_tilt_color = get_control_tilt_color()` to `assigned_tilt_color = temp_cfg.get("tilt_color")`
2. **Added comments**: Explicitly explain that fallback tilts should not be logged
3. **Updated variable name**: Changed from `control_tilt_color` to `assigned_tilt_color` for clarity

## Behavior After Fix

### Scenario 1: No Tilt Assigned
- `temp_cfg["tilt_color"]` = `""` (empty)
- Available tilts: Red, Blue
- **Result**: Nothing logged ✓
- **Reason**: No tilt is explicitly assigned

### Scenario 2: Black Tilt Assigned and Active
- `temp_cfg["tilt_color"]` = `"Black"`
- Available tilts: Black, Red, Blue
- **Result**: Only Black is logged ✓
- **Reason**: Black is the assigned tilt and is available

### Scenario 3: Black Tilt Assigned but Offline
- `temp_cfg["tilt_color"]` = `"Black"`
- Available tilts: Red, Blue (Black is offline)
- **Result**: Nothing logged ✓
- **Reason**: Assigned tilt (Black) is not available; fallback tilts are not logged

## Files Changed

1. **app.py** (lines 2747-2761)
   - Changed logging logic to only log explicitly assigned tilts
   - Added clarifying comments

2. **logs/temp_control_tilt.jsonl**
   - Cleared incorrect log entries

## Testing

Created comprehensive tests to verify the fix:

1. **test_temp_control_tilt_log_fix.py**
   - Test 1: Only assigned tilt is logged when multiple tilts are available
   - Test 2: No logging when no tilt is assigned
   - Both tests pass ✓

2. **demonstrate_tilt_log_fix.py**
   - Demonstrates the before/after behavior
   - Shows all three scenarios
   - Educational tool for understanding the fix

## Quality Checks

- ✓ Code compiles successfully
- ✓ Code review: No issues found
- ✓ CodeQL security scan: No vulnerabilities
- ✓ Tests pass
- ✓ Minimal changes made (only affected lines)

## Impact

### Before Fix
- ❌ All available tilts were logged to temp_control_tilt.jsonl
- ❌ Users saw readings from tilts they didn't assign or even own
- ❌ Confusion about which tilt was actually being used for temperature control

### After Fix
- ✓ Only the explicitly assigned tilt is logged
- ✓ Log file accurately reflects the temperature control configuration
- ✓ Clear separation between assigned and fallback tilts
- ✓ Users see only the data they expect

## Notes

- The fallback logic in `get_control_tilt_color()` is **still intact** for temperature control purposes
- This fix only affects **logging behavior**, not temperature control behavior
- Temperature control will still use fallback tilts when no tilt is assigned (for backward compatibility)
- But those fallback tilts will NOT be logged to temp_control_tilt.jsonl
