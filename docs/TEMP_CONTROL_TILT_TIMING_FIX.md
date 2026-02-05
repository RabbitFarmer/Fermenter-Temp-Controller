# Temperature Control Tilt Reading Timing Fix

## Summary

Fixed an issue where temperature control tilt readings were being logged on the 15-minute fermentation tracking interval instead of the 2-minute temperature control interval as configured in system settings.

## Problem Description

The system has two separate timing intervals configured in system settings:

1. **Tilt Reading Logging Interval**: 15 minutes (for fermentation tracking)
2. **Temperature Control Logging Interval**: 2 minutes (for temperature control)

However, temperature control tilt readings were incorrectly logging on the 15-minute interval instead of the 2-minute interval.

### User-Reported Issue

From the logs provided by the user, both readings were being logged at the same timestamp:

```json
{"timestamp": "2026-02-04T02:35:50.145585Z", "local_time": "2026-02-04 02:35:50", "tilt_color": "Red", "temperature": 70.2, "gravity": 1.048}
{"timestamp": "2026-02-04T02:35:50.145455Z", "local_time": "2026-02-04 02:35:50", "tilt_color": "Blue", "temperature": 68.5, "gravity": 1.05, "brewid": "test-brew-123", "beer_name": "Test IPA"}
```

This indicated that temperature control readings were only being logged when regular tilt readings occurred (every 15 minutes).

## Root Cause

In `app.py`, the `temperature_control_logic()` function had the following code structure:

```python
temp = temp_cfg.get("current_temp")
if temp is None:
    temp_from_tilt = get_current_temp_for_control_tilt()
    if temp_from_tilt is not None:
        temp = float(temp_from_tilt)
        temp_cfg['current_temp'] = round(temp, 1)
        
        # Log temp control tilt reading
        log_temp_control_tilt_reading(...)  # <-- Only called when temp is None
```

The problem: The BLE loop (line 3546) updates `temp_cfg['current_temp']` every 5 seconds, so the condition `if temp is None` is almost never true. This meant the logging code was rarely executed.

## Solution

The fix involved three changes:

### 1. Added Rate-Limiting Timestamp Tracker

Added a global variable to track the last time a temperature control tilt reading was logged:

```python
last_temp_control_log_ts = None  # Track last temperature control tilt reading log time
```

### 2. Moved Logging Outside None Check

Moved the `log_temp_control_tilt_reading()` call outside the `if temp is None` block so it runs every time `temperature_control_logic()` is called:

```python
temp = temp_cfg.get("current_temp")
if temp is None:
    temp_from_tilt = get_current_temp_for_control_tilt()
    if temp_from_tilt is not None:
        temp = float(temp_from_tilt)
        temp_cfg['current_temp'] = round(temp, 1)
        temp_cfg['last_reading_time'] = datetime.utcnow().isoformat() + "Z"

# Log temp control tilt reading at update_interval rate (separate from fermentation tracking)
# This logs at the Temperature Control Logging Interval (default 2 min), not the Tilt Reading
# Logging Interval (default 15 min) which is used for fermentation tracking
global last_temp_control_log_ts
try:
    control_tilt_color = get_control_tilt_color()
    if control_tilt_color and control_tilt_color in live_tilts and temp is not None:
        # Rate limiting based on update_interval (temperature control interval)
        interval_minutes = int(system_cfg.get('update_interval', 2))
        now = datetime.utcnow()
        
        should_log = False
        if last_temp_control_log_ts is None:
            should_log = True
        else:
            elapsed = (now - last_temp_control_log_ts).total_seconds() / 60.0
            if elapsed >= interval_minutes:
                should_log = True
        
        if should_log:
            tilt_data = live_tilts[control_tilt_color]
            gravity = tilt_data.get("gravity")
            brewid = tilt_cfg.get(control_tilt_color, {}).get("brewid")
            beer_name = tilt_cfg.get(control_tilt_color, {}).get("beer_name")
            log_temp_control_tilt_reading(
                tilt_color=control_tilt_color,
                temperature=temp,
                gravity=gravity,
                brewid=brewid,
                beer_name=beer_name
            )
            last_temp_control_log_ts = now
except Exception as e:
    print(f"[LOG] Failed to log temp control tilt reading: {e}")
```

### 3. Added Rate-Limiting Logic

Implemented proper rate-limiting based on the `update_interval` setting (default 2 minutes):

- First call always logs (when `last_temp_control_log_ts` is None)
- Subsequent calls only log if enough time has elapsed based on `update_interval`
- This is independent of the `tilt_logging_interval_minutes` used for fermentation tracking

## Testing

Created comprehensive tests to verify the fix:

### 1. Basic Timing Test (`test_temp_control_tilt_timing.py`)

Tests that temperature control tilt readings are logged at the correct interval:

```
✓ Temperature control tilt readings are being logged
✓ Logging respects the 2-minute interval
✓ Configuration Check:
  - Tilt logging interval (fermentation): 15 min
  - Temp control interval (update_interval): 2 min
  - Logs should use: 2 min interval ✓
```

### 2. Integration Test (`test_integration_temp_control_timing.py`)

Tests that both logging mechanisms work independently:

```
✓ PASS: Correct number of entries
✓ PASS: All entries have correct format
✓ PASS: Temperature control logging is independent
```

## Files Changed

1. **app.py**
   - Added `last_temp_control_log_ts` variable
   - Refactored temperature control tilt reading logging
   - Added rate-limiting based on `update_interval`

2. **.gitignore**
   - Added `logs/temp_control_tilt.jsonl` to exclude log files from git

3. **Test files created**
   - `test_temp_control_tilt_timing.py`
   - `test_integration_temp_control_timing.py`

## Verification

- ✓ All existing tests pass
- ✓ New tests pass and validate the fix
- ✓ Code review completed
- ✓ Security scan passed (no vulnerabilities found)

## Impact

- Temperature control tilt readings now log at the correct 2-minute interval
- Logging is completely independent of fermentation tracking (15-minute interval)
- Both mechanisms can operate simultaneously without interference
- Users will now see temperature control logs appearing every 2 minutes as configured
