# Temperature Control Chart Fix - Final Implementation

## Summary

Fixed temperature control chart plotting to use `update_interval` instead of `tilt_logging_interval_minutes`, with readings stored in memory to avoid excessive log file growth.

## Problem Statement

1. **Original Issue**: Temperature control readings were not being logged at the configured `update_interval` frequency. The chart only showed:
   - Tilt device readings (every 15 minutes at `tilt_logging_interval_minutes`)
   - Temperature control events (only when state changes occurred)

2. **Requirement Update**: Logging readings every 2 minutes would create 720+ entries per day in the JSONL file, which is too cumbersome. Solution needed to:
   - Keep readings for chart display
   - NOT log to file
   - Allow CSV export if needed

## Solution

### In-Memory Storage Approach

Implemented an in-memory buffer (`temp_reading_buffer`) that:
- Stores temperature readings at `update_interval` frequency (default 1-2 minutes)
- Limited to 1440 entries (2 days at 2-minute intervals)
- Automatically drops oldest entries when full (deque with maxlen)
- Persists only in RAM, not written to disk

### Code Changes

#### 1. Added In-Memory Buffer (app.py, line 99-104)
```python
# In-memory buffer for temperature control readings
# Max 1440 entries = 2 days at 2-minute intervals
TEMP_READING_BUFFER_SIZE = 1440
temp_reading_buffer = deque(maxlen=TEMP_READING_BUFFER_SIZE)
```

#### 2. Modified Recording Function (app.py, lines 345-403)
```python
def log_periodic_temp_reading():
    """Record periodic temperature control reading in memory."""
    if not temp_cfg.get("temp_control_active", False):
        return
    
    # Create entry with timestamp and temperature data
    entry = {
        "timestamp": iso_ts,
        "current_temp": temp_cfg.get("current_temp"),
        "low_limit": temp_cfg.get("low_limit"),
        "high_limit": temp_cfg.get("high_limit"),
        "event": "TEMP CONTROL READING"
    }
    
    # Add to in-memory buffer (not file)
    temp_reading_buffer.append(entry)
```

#### 3. Updated Chart Data Endpoint (app.py, lines 4617-4705)
```python
# Merge file-based events + in-memory readings
all_points = []

# Read events from file (heating_on, cooling_off, etc.)
# Skip old TEMP CONTROL READING entries from file
for line in LOG_PATH:
    event = obj.get('event')
    if event == "TEMP CONTROL READING":
        continue  # Use memory instead
    all_points.append(entry)

# Add in-memory periodic readings
for reading in temp_reading_buffer:
    all_points.append(reading)

# Sort by timestamp and apply limit
all_points.sort(key=lambda x: x.get('timestamp', ''))
```

### How It Works

1. **Every `update_interval` minutes**:
   - `periodic_temp_control()` runs
   - Calls `temperature_control_logic()` for heating/cooling
   - Calls `log_periodic_temp_reading()` to store reading in memory
   
2. **Chart Data (/chart_data/Fermenter)**:
   - Reads control events from file (permanent record)
   - Merges with in-memory periodic readings (recent 2 days)
   - Sorts by timestamp
   - Returns combined data for visualization

3. **File Logging**:
   - Only events are logged to file:
     - heating_on, cooling_off
     - temp_below_low_limit, temp_above_high_limit
     - temp_control_mode_changed
     - Safety events
   - Periodic readings stay in memory only

## Benefits

### Memory Efficiency
- **Buffer Size**: Limited to 1440 entries
- **Memory Usage**: ~150KB (each entry ~100 bytes)
- **Auto-cleanup**: Oldest entries automatically dropped when full

### File Efficiency  
- **Before**: 720+ periodic reading entries/day in JSONL file
- **After**: 0 periodic reading entries/day in JSONL file
- **Events Still Logged**: Important state changes permanently recorded

### User Experience
- **Chart**: Shows data at `update_interval` frequency (1-2 min)
- **Granularity**: Much better than event-only sparse data
- **CSV Export**: Can export readings from memory buffer
- **Main Display**: Shows current_temp as before

## Testing

All tests updated and passing:

### test_temp_control_interval.py
- ✅ Verifies readings stored in memory
- ✅ Tests buffer size limit
- ✅ Validates entry format
- ✅ Confirms no file logging

### test_chart_periodic_readings.py
- ✅ Chart endpoint merges file + memory data
- ✅ Readings sorted correctly
- ✅ Both events and readings appear
- ✅ Temperature progression validated

### test_backward_compatibility.py
- ✅ Existing logs still work
- ✅ Old TEMP CONTROL READING entries skipped
- ✅ No breaking changes

### Security
- ✅ CodeQL scan: 0 alerts
- ✅ No new file I/O vulnerabilities
- ✅ Memory buffer bounded (no memory leak risk)

## Configuration

No configuration changes needed:
- Uses existing `update_interval` setting (1-2 minutes)
- Uses existing `temp_control_active` flag
- No new settings required

## Migration

Transparent to users:
- No data migration needed
- No configuration changes required
- Works with existing log files
- In-memory buffer starts fresh on app restart (expected behavior)

## Performance

- **Memory**: Negligible (~150KB for full buffer)
- **CPU**: No change (same number of readings, just stored differently)
- **Disk I/O**: Reduced (no periodic reading writes)
- **Chart Response**: Fast (memory + file read, sorted once)

## Limitations

- **Restart**: In-memory readings lost on app restart (by design)
- **Export**: Can only export last 2 days of readings (buffer limit)
- **Historical**: For long-term analysis, rely on event-based log entries

These limitations are acceptable tradeoffs for avoiding 700+ log entries/day.

## Files Modified

- `app.py`: Core changes (buffer, recording, chart endpoint)
- `test_temp_control_interval.py`: Updated for memory storage
- `test_chart_periodic_readings.py`: Updated for memory approach
- `TEMP_CONTROL_CHART_FIX_SUMMARY.md`: Documentation

## Verification Checklist

- [x] Temperature readings recorded at `update_interval` frequency
- [x] Readings stored in memory, not file
- [x] Chart displays merged file events + memory readings
- [x] Buffer limited to prevent memory bloat
- [x] No excessive log file growth
- [x] All tests passing
- [x] Security scan passed (0 alerts)
- [x] Backward compatible
- [x] No configuration changes needed

## Next Steps

For production deployment:
1. Test with real hardware and temperature readings
2. Verify chart displays correctly in browser
3. Test CSV export functionality
4. Monitor memory usage over time
5. Confirm acceptable after app restart (empty buffer initially)
