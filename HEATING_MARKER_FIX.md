# Fix for Temperature Control Chart "Heating ON" Marker Issue

## Problem Statement
The temperature control chart was displaying multiple "HEATING ON" markers (red triangles) continuously while heating was active, instead of showing just one marker when heating transitions from OFF to ON.

![Issue Screenshot](https://github.com/user-attachments/assets/838f0f92-0d99-4350-a3f0-4960d7ebd251)

As shown in the screenshot above, the red triangular markers form a solid block instead of appearing as discrete state-change indicators.

## Root Cause Analysis

### The Bug
Runtime state variables (`heater_on`, `cooler_on`, etc.) were being reloaded from the config file every periodic interval (1-2 minutes) in the `periodic_temp_control()` function at line 3134:

```python
def periodic_temp_control():
    while True:
        try:
            file_cfg = load_json(TEMP_CFG_FILE, {})
            temp_cfg.update(file_cfg)  # ← BUG: Overwrites runtime state!
            temperature_control_logic()
```

### Why This Caused Duplicate Markers

1. **Initial State**: Heating turns ON at time T0
   - `kasa_result_listener` sets `temp_cfg["heater_on"] = True`
   - Logs "HEATING-PLUG TURNED ON" event ✓ (correct)

2. **Periodic Reload** at T0 + 2 minutes:
   - `load_json(TEMP_CFG_FILE)` loads config file
   - If file has `heater_on: false` (stale value), `temp_cfg.update()` overwrites the in-memory state
   - `temp_cfg["heater_on"]` is now False (reset!)

3. **State Change Detection Fails**:
   - Control logic sees temp still low, sends heating ON command
   - `kasa_result_listener` checks: `previous_state = False` (stale!), `new_state = True`
   - State appears to have changed, logs another "HEATING-PLUG TURNED ON" event ✗ (duplicate!)

4. **Repeat Every 2 Minutes**:
   - This pattern repeats every periodic interval
   - Result: Multiple heating ON markers on the chart

## The Fix

### Code Changes
Modified `periodic_temp_control()` to exclude runtime state variables from config file reload:

```python
def periodic_temp_control():
    while True:
        try:
            file_cfg = load_json(TEMP_CFG_FILE, {})
            if 'current_temp' in file_cfg and file_cfg['current_temp'] is None and temp_cfg.get('current_temp') is not None:
                file_cfg.pop('current_temp')
            
            # NEW: Exclude runtime state variables from file reload
            runtime_state_vars = [
                'heater_on', 'cooler_on',           # Current plug states
                'heater_pending', 'cooler_pending',  # Pending command flags
                'heater_pending_since', 'cooler_pending_since',
                'heater_pending_action', 'cooler_pending_action',
                'heating_error', 'cooling_error',
                'heating_error_msg', 'cooling_error_msg',
                'heating_error_notified', 'cooling_error_notified',
                'heating_blocked_trigger', 'heating_safety_off_trigger',
                'below_limit_logged', 'above_limit_logged',
                'below_limit_trigger_armed', 'above_limit_trigger_armed',
                'in_range_trigger_armed',
                'safety_shutdown_logged',
                'status'
            ]
            for var in runtime_state_vars:
                file_cfg.pop(var, None)
            
            temp_cfg.update(file_cfg)  # Now only updates config, preserves runtime state
```

### What This Achieves

1. **Configuration values** (limits, plug URLs, enable flags) are still loaded from file ✓
2. **Runtime state** (heater_on, cooler_on, etc.) is preserved in memory ✓
3. **State changes** are correctly detected based on actual hardware state transitions ✓
4. **Duplicate markers** are prevented ✓

## Expected Behavior After Fix

### Chart Markers (Before Fix)
```
Time:     14:00  14:02  14:04  14:06  14:08  14:10  14:12
Temp:     67°F   67°F   68°F   69°F   70°F   71°F   72°F
Heating:   ON     ON     ON     ON     ON     ON    OFF
Markers:   ▲      ▲      ▲      ▲      ▲      ▲     ▼
                 ↑ Duplicate markers (bug)
```

### Chart Markers (After Fix)
```
Time:     14:00  14:02  14:04  14:06  14:08  14:10  14:12
Temp:     67°F   67°F   68°F   69°F   70°F   71°F   72°F
Heating:   ON    (on)   (on)   (on)   (on)   (on)   OFF
Markers:   ▲      -      -      -      -      -     ▼
          ON                                       OFF
```

Only two markers appear:
- **One red triangle (▲)** when heating turns ON
- **One pink triangle (▼)** when heating turns OFF

## Testing

### Test Coverage
1. ✅ **Unit Test** (`test_heating_marker_fix.py`):
   - Demonstrates the bug in isolation
   - Verifies the fix prevents state reset
   - Confirms duplicate events are eliminated

2. ✅ **Integration Test** (`test_integration_heating_markers.py`):
   - Tests with actual app code
   - Simulates full periodic control loop
   - Verifies end-to-end behavior

3. ✅ **Regression Test** (`test_chart_periodic_readings.py`):
   - Existing chart functionality still works
   - Periodic readings are correctly logged
   - Chart data endpoint works properly

### Test Results
```
$ python3 test_heating_marker_fix.py
✓ Test PASSED: Runtime state preserved, config values updated
✓ Test PASSED: Fix prevents duplicate events (2 → 1)
ALL TESTS PASSED

$ python3 test_integration_heating_markers.py
✓ TEST PASSED: Only one heating ON event and one heating OFF event
Fix successfully prevents duplicate heating markers!

$ python3 test_chart_periodic_readings.py
✓ ALL TESTS PASSED
```

### Security Scan
```
$ codeql_checker
Analysis Result for 'python'. Found 0 alerts.
```

## Impact

### What's Fixed
- ✅ Chart no longer shows duplicate "heating ON" markers
- ✅ State-change detection works correctly
- ✅ Chart displays clean, discrete state transition markers
- ✅ Same fix applies to cooling markers

### What's Preserved
- ✅ Configuration reloading still works
- ✅ User can update settings and they'll be loaded
- ✅ Periodic temperature readings still logged correctly
- ✅ All existing functionality intact

### No Breaking Changes
- ✅ Backwards compatible with existing logs
- ✅ No changes to log format
- ✅ No changes to chart rendering
- ✅ No changes to user-facing settings

## Files Modified

1. **app.py** (lines 3128-3157)
   - Added runtime state variable exclusion in `periodic_temp_control()`
   - Added comprehensive comments explaining the fix

## Files Added

1. **test_heating_marker_issue.py**
   - Demonstrates expected state-change behavior

2. **test_heating_marker_fix.py**
   - Unit test showing bug and fix

3. **test_integration_heating_markers.py**
   - Integration test with actual app code

## Summary

This fix resolves the issue where the temperature control chart displayed multiple "heating ON" markers during a single heating cycle. The root cause was runtime state variables being overwritten by stale values from the config file during periodic reloads. By excluding these runtime state variables from the file reload process, the fix ensures that only actual hardware state transitions trigger marker events on the chart, resulting in the expected behavior of one marker per state change.
