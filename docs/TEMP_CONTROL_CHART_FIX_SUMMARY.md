# Temperature Control Chart Plotting Fix - Summary

## Issue Description
Temperature control readings frequency has its own setting in system settings (`update_interval`), but the code was ignoring that interval and defaulting to the frequency of Tilt device postings (`tilt_logging_interval_minutes`) for fermentation monitoring. These serve two different purposes.

## Problem Analysis

### Settings
- **`update_interval`**: Temperature control loop frequency (default 1-2 minutes)
  - Controls how often the temperature control logic runs
  - Should also control how often temperature readings are logged for charting
  
- **`tilt_logging_interval_minutes`**: Tilt gravity reading logging frequency (default 15 minutes)
  - Controls how often Tilt hydrometer readings are logged to batch files
  - Used for fermentation monitoring

### Root Cause
The `periodic_temp_control()` function runs every `update_interval` minutes and calls `temperature_control_logic()` to make heating/cooling decisions. However, it was NOT logging periodic temperature readings. 

Only event-based logging was happening:
- State changes (heating_on, cooling_off)
- Boundary crossings (temp_below_low_limit, temp_above_high_limit, temp_in_range)
- Safety events (temp_control_safety_shutdown)

This meant the temperature control chart had sparse data points - only when events occurred - rather than regular time-series data at the configured `update_interval`.

## Solution Implemented

### Code Changes

#### 1. Added New Event Type
**File**: `app.py` (line 242)
```python
ALLOWED_EVENTS = {
    "tilt_reading": "SAMPLE",
    "temp_control_reading": "TEMP CONTROL READING",  # NEW
    # ... existing events ...
}
```

#### 2. Created Periodic Reading Logger
**File**: `app.py` (lines 339-385)
```python
def log_periodic_temp_reading():
    """
    Log a periodic temperature control reading at the update_interval frequency.
    
    This function is called by periodic_temp_control() after each control loop
    iteration to log temperature readings for the temperature control chart.
    """
    # Only log if temp control monitoring is active
    if not temp_cfg.get("temp_control_active", False):
        return
    
    # Create payload with current temperature control state
    payload = {
        "low_limit": temp_cfg.get("low_limit"),
        "current_temp": temp_cfg.get("current_temp"),
        "high_limit": temp_cfg.get("high_limit"),
        "tilt_color": temp_cfg.get("tilt_color", "")
    }
    
    entry = _format_control_log_entry("temp_control_reading", payload)
    with open(LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + "\n")
```

**Key Features**:
- Bypasses the `enable_heating/enable_cooling` gate in `append_control_log()`
- Only logs when `temp_control_active` is True (monitoring enabled)
- Logs to same file as control events: `temp_control/temp_control_log.jsonl`
- Uses same format as other control log entries for consistency

#### 3. Modified Periodic Control Loop
**File**: `app.py` (lines 3086-3090)
```python
def periodic_temp_control():
    while True:
        try:
            # Load config and run control logic
            temperature_control_logic()
            
            # NEW: Log periodic temperature reading at update_interval frequency
            log_periodic_temp_reading()
        except Exception as e:
            # Error handling...
```

### How It Works Now

1. **Every `update_interval` minutes** (default 1-2 min):
   - `periodic_temp_control()` runs
   - Calls `temperature_control_logic()` to make heating/cooling decisions
   - Calls `log_periodic_temp_reading()` to log current temperature state
   - Events (heating_on, temp_below_low_limit, etc.) are ALSO logged when state changes

2. **Chart data endpoint** (`/chart_data/Fermenter`):
   - Returns ALL entries from `temp_control_log.jsonl` that have allowed event types
   - Now includes both:
     - Periodic readings (TEMP CONTROL READING) at `update_interval` frequency
     - Control events (HEATING-PLUG TURNED ON, etc.) when state changes

3. **Tilt readings** are UNCHANGED:
   - Still logged at `tilt_logging_interval_minutes` frequency
   - Go to batch-specific JSONL files in `batches/` directory
   - Used for fermentation monitoring, not temperature control

### Backward Compatibility

✅ **Fully backward compatible**:
- All existing event types remain unchanged
- Existing log files work without modification
- New periodic readings coexist with legacy events
- Chart data endpoint handles both old and new formats
- No breaking changes to configuration or APIs

### Example Log Entry

**Before** (only events):
```json
{"timestamp": "2026-02-01T19:30:00Z", "event": "HEATING-PLUG TURNED ON", "temp_f": 64.5, ...}
{"timestamp": "2026-02-01T19:45:00Z", "event": "IN RANGE", "temp_f": 67.0, ...}
```
*Note: 15 minute gap with no data points*

**After** (events + periodic readings at 2-min intervals):
```json
{"timestamp": "2026-02-01T19:30:00Z", "event": "HEATING-PLUG TURNED ON", "temp_f": 64.5, ...}
{"timestamp": "2026-02-01T19:32:00Z", "event": "TEMP CONTROL READING", "temp_f": 65.2, ...}
{"timestamp": "2026-02-01T19:34:00Z", "event": "TEMP CONTROL READING", "temp_f": 66.1, ...}
{"timestamp": "2026-02-01T19:36:00Z", "event": "TEMP CONTROL READING", "temp_f": 66.8, ...}
{"timestamp": "2026-02-01T19:38:00Z", "event": "TEMP CONTROL READING", "temp_f": 67.0, ...}
{"timestamp": "2026-02-01T19:40:00Z", "event": "IN RANGE", "temp_f": 67.0, ...}
```
*Regular data points every 2 minutes for better charting*

## Tests Created

### 1. `test_temp_control_interval.py`
- Verifies `log_periodic_temp_reading()` function works correctly
- Tests that readings are logged when monitoring is active
- Tests that readings are NOT logged when monitoring is off
- Validates log entry format and content

### 2. `test_chart_periodic_readings.py`
- Integration test with Flask test client
- Generates test data with periodic readings at `update_interval`
- Tests `/chart_data/Fermenter` endpoint
- Verifies chart data includes both periodic readings and events
- Validates data structure and values

### 3. `test_backward_compatibility.py`
- Tests that all existing event types are still supported
- Creates legacy log file without periodic readings
- Verifies chart endpoint handles legacy logs correctly
- Tests mixed logs (legacy + new periodic readings)
- Confirms no breaking changes

### 4. Updated `test_chart_fixes.py`
- Added new event type to ALLOWED_EVENT_VALUES list
- Ensures existing test passes with new event type

### 5. `demo_fix.py`
- Demonstration script showing the fix in action
- Displays configuration differences
- Shows log entry format
- Explains impact on charting

## Impact

### User Benefits
1. **Better Temperature Visualization**: Chart updates at configured `update_interval` instead of only on events
2. **More Frequent Data**: Default 1-2 minute updates vs. sparse event-based updates
3. **Accurate Trend Analysis**: Regular time-series data shows temperature trends clearly
4. **Proper Separation**: Temperature control charting separate from fermentation monitoring

### Technical Benefits
1. **Correct Interval Usage**: Uses `update_interval` for temp control, not `tilt_logging_interval_minutes`
2. **Backward Compatible**: Existing logs and configurations work without changes
3. **Minimal Code Changes**: Small, focused changes with clear purpose
4. **Well Tested**: Comprehensive test coverage for new functionality
5. **Secure**: Passed CodeQL security analysis with no alerts

## Files Modified

### Core Application
- `app.py`: Added event type, logging function, modified control loop (89 lines added)

### Tests
- `test_temp_control_interval.py`: New test (136 lines)
- `test_chart_periodic_readings.py`: New test (208 lines)
- `test_backward_compatibility.py`: New test (219 lines)
- `test_chart_fixes.py`: Updated (1 line changed)

### Documentation
- `demo_fix.py`: Demonstration script (109 lines)
- `TEMP_CONTROL_CHART_FIX_SUMMARY.md`: This document

## Verification

All tests pass:
- ✅ `test_temp_control_interval.py` - Periodic reading logging
- ✅ `test_chart_periodic_readings.py` - Chart data integration
- ✅ `test_backward_compatibility.py` - Legacy compatibility
- ✅ `test_chart_fixes.py` - Existing test still passes
- ✅ CodeQL security scan - No alerts

## Configuration

No configuration changes required. The fix uses existing settings:
- `update_interval` from `system_config.json` (already exists)
- `temp_control_active` from `temp_control_config.json` (already exists)

## Migration

No migration needed. The fix is transparent to users:
- Existing logs continue to work
- New periodic readings start appearing automatically when monitoring is enabled
- Chart will show more data points without any user action

## Security

✅ No security vulnerabilities introduced:
- Uses existing, validated logging functions
- No new file paths or external access
- Same JSONL format as existing logs
- CodeQL scan passed with 0 alerts
