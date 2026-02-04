# Temperature Control Tilt Refresh Interval Fix

## Issue Summary

**Issue #**: Referenced in problem statement (previous issue #269)
**Issue Title**: Temp control tilt at wrong refresh interval

## Problem Description

Temperature control tilt readings (SAMPLE events) were being logged to `temp_control_log.jsonl` at the fermentation tracking interval (`tilt_logging_interval_minutes`, default 15 minutes) instead of the temperature control interval (`update_interval`, default 2 minutes).

### Evidence from User Logs

```json
{"timestamp": "2026-02-04T10:30:59Z", "date": "2026-02-04", "time": "05:30:59", "tilt_color": "Black", "brewid": "9d0274c9", "low_limit": null, "current_temp": 72.0, "temp_f": 72.0, "gravity": 1.0, "high_limit": null, "event": "SAMPLE"}
{"timestamp": "2026-02-04T10:15:58Z", "date": "2026-02-04", "time": "05:15:58", "tilt_color": "Black", "brewid": "9d0274c9", "low_limit": null, "current_temp": 71.0, "temp_f": 71.0, "gravity": 1.0, "high_limit": null, "event": "SAMPLE"}
{"timestamp": "2026-02-04T10:04:29Z", "date": "2026-02-04", "time": "05:04:29", "tilt_color": "Black", "brewid": "9d0274c9", "low_limit": 74.0, "current_temp": 71.0, "temp_f": 71.0, "gravity": null, "high_limit": 75.0, "event": "HEATING-PLUG TURNED ON"}
```

**Problem**: SAMPLE events appeared at irregular intervals (15 minutes, then 11 minutes) when they should have been logged every 2 minutes for responsive temperature control.

## Root Cause

The `log_tilt_reading()` function in `app.py` (lines 779-836) was using `tilt_logging_interval_minutes` (default 15 minutes) for all tilts, regardless of whether they were assigned to temperature control or used for fermentation tracking.

### Before Fix

```python
def log_tilt_reading(color, gravity, temp_f, rssi):
    # ...
    # Rate limiting based on tilt_logging_interval_minutes
    interval_minutes = int(system_cfg.get('tilt_logging_interval_minutes', 15))
    # ...
```

This meant:
- All tilts logged at 15-minute intervals
- Temperature control tilts couldn't provide responsive readings
- Control decisions were less frequent than configured

## Solution

Modified `log_tilt_reading()` to check if a tilt is assigned to temperature control and use different rate limiting intervals:

### After Fix

```python
def log_tilt_reading(color, gravity, temp_f, rssi):
    # ...
    # Rate limiting based on tilt usage:
    # - If tilt is assigned to temperature control: use update_interval (default 2 min) for responsive control
    # - Otherwise: use tilt_logging_interval_minutes (default 15 min) for fermentation tracking
    control_tilt_color = temp_cfg.get("tilt_color")
    is_control_tilt = (color == control_tilt_color)
    
    if is_control_tilt:
        # Use update_interval for temperature control tilt
        try:
            interval_minutes = int(system_cfg.get('update_interval', 2))
        except (ValueError, TypeError):
            interval_minutes = 2
    else:
        # Use tilt_logging_interval_minutes for fermentation tracking
        try:
            interval_minutes = int(system_cfg.get('tilt_logging_interval_minutes', 15))
        except (ValueError, TypeError):
            interval_minutes = 15
    # ...
```

## Changes Made

### Files Modified

1. **app.py** (lines 799-814)
   - Added logic to detect if a tilt is assigned to temperature control
   - Use `update_interval` (2 min) for control tilts
   - Use `tilt_logging_interval_minutes` (15 min) for fermentation tilts
   - Added specific exception handling for config value conversion

### Files Created

2. **test_temp_control_refresh_interval.py**
   - Comprehensive test suite for the fix
   - Tests control tilt at 2-minute interval
   - Tests non-control tilt at 15-minute interval
   - Tests mixed scenarios with both tilt types

## Testing

### New Tests

Created `test_temp_control_refresh_interval.py` with three test cases:

1. **test_control_tilt_interval()**: Verifies control tilt logs at 2-minute interval
   - ✓ First reading logs immediately
   - ✓ Second reading at 1 minute doesn't log
   - ✓ Third reading at 2 minutes logs successfully

2. **test_non_control_tilt_interval()**: Verifies non-control tilt logs at 15-minute interval
   - ✓ First reading logs immediately
   - ✓ Second reading at 2 minutes doesn't log
   - ✓ Third reading at 15 minutes logs successfully

3. **test_mixed_tilt_intervals()**: Verifies both tilts work independently
   - ✓ Both tilts log initially
   - ✓ After 2 minutes, only control tilt logs
   - ✓ After 15 minutes, both tilts log

**All tests PASS ✓**

### Existing Tests

Verified no regressions with existing tests:
- ✓ `test_update_interval_fix.py` - PASS (temperature control chart uses update_interval)

## Code Review

Code review completed with 2 comments addressed:

1. **Removed `globals()` check**: `temp_cfg` is always available in scope, no need for fragile globals check
2. **Added specific exception handling**: Changed from catching broad `Exception` to specific `ValueError` and `TypeError` for int conversion

## Security

Security scan completed with CodeQL:
- **python**: No alerts found ✓

## Impact

### Before Fix
- Temperature control tilts logged every 15 minutes
- Irregular logging intervals (15 min, 11 min, etc.)
- Less responsive temperature control
- Control decisions based on stale data

### After Fix
- Temperature control tilts log every 2 minutes (configurable via `update_interval`)
- Consistent logging intervals
- Responsive temperature control
- Control decisions based on fresh data
- Fermentation tracking tilts still log at 15-minute intervals (unchanged)

## Verification

To verify the fix is working:

1. Assign a tilt to temperature control via the web UI
2. Enable temperature control
3. Check `temp_control_log.jsonl` for SAMPLE events
4. SAMPLE events for the control tilt should appear every 2 minutes
5. SAMPLE events for other tilts should appear every 15 minutes

### Example Expected Log (After Fix)

```json
{"timestamp": "2026-02-04T10:00:00Z", "tilt_color": "Black", "event": "SAMPLE", ...}  // Control tilt
{"timestamp": "2026-02-04T10:02:00Z", "tilt_color": "Black", "event": "SAMPLE", ...}  // 2 min later ✓
{"timestamp": "2026-02-04T10:04:00Z", "tilt_color": "Black", "event": "SAMPLE", ...}  // 2 min later ✓
{"timestamp": "2026-02-04T10:06:00Z", "tilt_color": "Black", "event": "SAMPLE", ...}  // 2 min later ✓
{"timestamp": "2026-02-04T10:15:00Z", "tilt_color": "Red", "event": "SAMPLE", ...}    // Fermentation tilt (15 min) ✓
```

## Conclusion

✅ **Fix Complete**: Temperature control tilts now log at the responsive 2-minute interval while fermentation tracking tilts continue to use the 15-minute interval.

✅ **All Tests Pass**: New and existing tests verify the fix works correctly.

✅ **No Security Issues**: CodeQL scan found no vulnerabilities.

✅ **Code Review Addressed**: All review comments have been addressed.
