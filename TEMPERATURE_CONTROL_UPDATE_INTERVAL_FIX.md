# Temperature Control Chart Update Interval Fix

## Summary

Fixed the temperature control chart to use the configured `update_interval` setting instead of the `tilt_logging_interval_minutes` for temperature data logging. This resolves the "jagged EKG pattern" issue and provides smoother temperature curves with proper data point density.

## Problem

The temperature control chart displayed a jagged "EKG" pattern because:

1. **SAMPLE events** (tilt readings) were being included in the chart data
2. SAMPLE events are logged at the **tilt_logging_interval_minutes** (default: 15 minutes)
3. This resulted in sparse temperature data points (only 3 points in 30 minutes)
4. The chart appeared jagged instead of smooth

## Root Cause

In the `chart_data` endpoint for "Fermenter" (temperature control):
- The code was including ALL events from `temp_control_log.jsonl`
- This included "SAMPLE" events (tilt readings logged every 15 minutes)
- These sparse SAMPLE events were mixed with periodic readings, but the 15-minute gaps created a jagged appearance

## Solution

### Code Changes

**File: `app.py`** (lines 4722-4725)

Added filter to exclude SAMPLE events from Fermenter chart:

```python
# Skip SAMPLE (tilt_reading) events - they're logged at tilt_logging_interval_minutes (15 min)
# We only want periodic readings from temp_reading_buffer (logged at update_interval)
if event == "SAMPLE":
    continue
```

### How It Works Now

The temperature control chart (`/chart_data/Fermenter`) now returns:

1. **Periodic temperature readings** from `temp_reading_buffer`
   - Logged at `update_interval` (default: 2 minutes)
   - Stored in-memory (not written to file)
   - Provides dense, smooth data points

2. **Control events** from `temp_control_log.jsonl`
   - HEATING-PLUG TURNED ON/OFF
   - COOLING-PLUG TURNED ON/OFF
   - Temperature limit events
   - Used for markers and annotations

3. **EXCLUDES** SAMPLE events (tilt readings)
   - These are logged separately at 15-minute intervals
   - Not needed for temperature control chart
   - Used only for fermentation monitoring charts

### Chart Styling

Temperature trace styling already matches tilt card temperature traces exactly:
- `mode: 'lines'` - Line chart (not scatter)
- `shape: 'linear'` - Linear interpolation between points
- `width: 1.5` - Consistent line width
- `connectgaps: false` - Don't connect across missing data

## Results

### Data Point Density Improvement

| Metric | Before Fix | After Fix | Improvement |
|--------|-----------|-----------|-------------|
| Interval | 15 minutes | 2 minutes | 7.5x faster |
| Points in 30 min | 3 | 16 | 433% more |
| Chart appearance | Jagged EKG | Smooth curve | ✓ Fixed |

### Test Results

Created `test_update_interval_fix.py` to validate the fix:
- ✓ SAMPLE events correctly excluded (0 found)
- ✓ Heating events correctly included (2 found)
- ✓ Periodic readings correctly included (15 found at 2-min intervals)

## Configuration Settings

### Temperature Control Update Interval
- **Setting**: `update_interval` in `system_config.json`
- **Default**: 2 minutes
- **Purpose**: How often to run temperature control loop and log periodic readings
- **Used by**: `periodic_temp_control()` function

### Tilt Logging Interval
- **Setting**: `tilt_logging_interval_minutes` in `system_config.json`
- **Default**: 15 minutes
- **Purpose**: How often to log tilt readings to batch files
- **Used by**: `log_tilt_reading()` function for fermentation monitoring

These are **separate** settings for different purposes:
- `update_interval`: Temperature control responsiveness (2 min)
- `tilt_logging_interval_minutes`: Fermentation history logging (15 min)

## Files Modified

1. **app.py** (line 4722-4724)
   - Added filter to exclude SAMPLE events from Fermenter chart data

2. **test_update_interval_fix.py** (new file)
   - Test to verify SAMPLE events are excluded
   - Validates periodic readings are included
   - Confirms data point density improvement

## No Changes Needed

The following were already correct:
- ✓ Chart styling parameters in `chart_plotly.html`
- ✓ `log_periodic_temp_reading()` function
- ✓ Call to `log_periodic_temp_reading()` in `periodic_temp_control()`
- ✓ Use of `update_interval` in temperature control loop

## Expected Behavior

### Temperature Control Chart (`/chart_data/Fermenter`)
- Shows temperature readings every `update_interval` (e.g., 2 minutes)
- Displays smooth curve, not jagged EKG pattern
- Includes heating/cooling control markers
- Shows temperature limit lines

### Tilt Charts (`/chart_data/<Color>`)
- Show tilt readings every `tilt_logging_interval_minutes` (e.g., 15 minutes)
- Include gravity and temperature data
- Used for fermentation monitoring
- Unaffected by this fix

## Testing

To test the fix:

1. **Run the test**:
   ```bash
   python3 test_update_interval_fix.py
   ```

2. **View temperature control chart**:
   - Navigate to dashboard
   - Click "Temperature Control" chart
   - Verify smooth curve with data points every 2 minutes

3. **Compare with tilt chart**:
   - Click a tilt color chart
   - Data points should be at 15-minute intervals
   - This is correct for fermentation monitoring

## Background

The system uses two different logging intervals for different purposes:

### Temperature Control (Responsive)
- **Frequency**: Every 2 minutes (default `update_interval`)
- **Purpose**: Responsive heating/cooling control
- **Storage**: In-memory buffer (1440 entries = 2 days)
- **Chart**: Temperature Control chart

### Fermentation Monitoring (Historical)
- **Frequency**: Every 15 minutes (default `tilt_logging_interval_minutes`)
- **Purpose**: Long-term fermentation history
- **Storage**: Per-batch JSONL files
- **Chart**: Individual tilt color charts

This separation allows:
- Responsive temperature control (2-min updates)
- Efficient fermentation logging (15-min samples)
- Different data retention policies
- Optimal chart displays for each purpose
