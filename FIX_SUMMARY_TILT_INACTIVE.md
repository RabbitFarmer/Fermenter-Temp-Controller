# Fix Summary: Inactive Tilt Detection

## Issue
**GitHub Issue**: "Tilt listed as active and displayed on main display"

**Problem**: Tilt was last active 2 hours ago but program continues to list it as active and continues to display it on the main display.

## Root Cause
The `live_tilts` dictionary stored all Tilt data indefinitely once a Tilt was detected via BLE. There was no mechanism to filter out inactive Tilts (those that haven't sent data recently) from the display.

## Solution Implemented

### 1. Added `get_active_tilts()` Function
Created a new filtering function in `app.py` that:
- Checks the timestamp of each Tilt in `live_tilts`
- Calculates elapsed time since last reading
- Returns only Tilts within the configured timeout threshold
- Handles edge cases (missing timestamps, parse errors)

```python
def get_active_tilts():
    """Filter live_tilts to only include tilts that have sent data recently."""
    timeout_minutes = int(system_cfg.get('tilt_inactivity_timeout_minutes', 60))
    now = datetime.utcnow()
    active_tilts = {}
    
    for color, info in live_tilts.items():
        timestamp_str = info.get('timestamp')
        if not timestamp_str:
            continue
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.rstrip('Z'))
            elapsed_minutes = (now - timestamp).total_seconds() / 60.0
            
            if elapsed_minutes < timeout_minutes:
                active_tilts[color] = info
        except Exception as e:
            print(f"[LOG] Error parsing timestamp for {color}: {e}, excluding from active tilts")
    
    return active_tilts
```

### 2. Updated Flask Routes
Modified all routes that display Tilt data to use `get_active_tilts()` instead of `live_tilts`:

- **Dashboard (`/`)**: Shows only active Tilts on main display
- **Live Snapshot API (`/live_snapshot`)**: Returns only active Tilts (used by frontend for live updates)
- **Batch Settings (`/batch_settings`)**: Shows only active Tilts in dropdown
- **Temperature Config (`/temp_config`)**: Shows only active Tilts

### 3. Configuration Option
Added `tilt_inactivity_timeout_minutes` to `system_config.json.template`:
```json
{
  "tilt_inactivity_timeout_minutes": 60
}
```

**Default**: 60 minutes (1 hour)

Users can adjust this timeout based on their needs:
- 15 minutes: Quick detection for debugging
- 30 minutes: Normal operation
- 60 minutes: Default (good balance)
- 120 minutes: Extended for slow-reporting Tilts

### 4. Documentation
Updated `config/README.md` to document the new setting:
```
- `tilt_inactivity_timeout_minutes`: Time in minutes after which a Tilt is 
  considered inactive if no data is received (default: 60). Inactive Tilts 
  are hidden from the main display.
```

## Technical Details

### Data Flow
1. BLE scanner detects Tilt broadcasts
2. `update_live_tilt()` updates `live_tilts[color]` with new data + timestamp
3. Routes call `get_active_tilts()` to get filtered view
4. Only Tilts within timeout are returned
5. Frontend displays only active Tilts

### Important Notes
- The raw `live_tilts` dictionary still contains ALL Tilt data
- This is important for temperature control and logging
- Only the **display** filters out inactive Tilts
- Logging and control continue to work even for inactive Tilts

### Timezone Handling
- Uses naive UTC datetimes consistently (matches existing codebase)
- Timestamps are stored as ISO 8601 with 'Z' suffix
- Parser strips 'Z' and creates naive datetime for comparison

### Error Handling
- Tilts without timestamps: Excluded from display (can't determine activity)
- Unparseable timestamps: Logged and excluded (indicates data corruption)
- This prevents stale/corrupted data from appearing on display

## Testing

### Unit Tests (`test_tilt_active_filter.py`)
- Tests basic filtering logic
- Tests boundary conditions (59 min vs 61 min)
- Tests custom timeout values
- Tests missing/invalid timestamps
- **Result**: All 7 tests pass ✓

### Integration Tests (`test_tilt_active_integration.py`)
- Tests with actual Flask app imports
- Tests multiple simultaneous Tilts
- Tests configuration changes
- Tests edge cases
- **Result**: All 5 tests pass ✓

### End-to-End Simulation (`test_issue_simulation.py`)
- Simulates exact issue described in GitHub issue
- Creates Tilt 2 hours old
- Verifies it's hidden from display
- Demonstrates configuration options
- **Result**: Issue is fixed ✓

### Security Scan
- CodeQL scan: 0 vulnerabilities found ✓

## Behavior Comparison

### Before Fix
```
Time: 10:00 AM - Red Tilt sends data
Time: 12:00 PM - Red Tilt stops sending data (battery dead, out of range, etc.)
Time: 2:00 PM - Red Tilt STILL SHOWS on main display (INCORRECT)
```

### After Fix
```
Time: 10:00 AM - Red Tilt sends data
Time: 12:00 PM - Red Tilt stops sending data
Time: 11:00 AM - Red Tilt STILL SHOWS (within 60 min timeout)
Time: 1:00 PM - Red Tilt HIDDEN from display (beyond 60 min timeout) ✓
```

## Files Changed

1. **app.py**
   - Added `get_active_tilts()` function
   - Updated dashboard route
   - Updated live_snapshot route
   - Updated batch_settings route
   - Updated temp_config route

2. **config/system_config.json.template**
   - Added `tilt_inactivity_timeout_minutes` setting

3. **config/README.md**
   - Documented new configuration option

4. **Tests** (new files)
   - `test_tilt_active_filter.py` - Unit tests
   - `test_tilt_active_integration.py` - Integration tests
   - `test_issue_simulation.py` - End-to-end simulation

## Backward Compatibility

✓ **Fully backward compatible**
- Existing installations get default 60 minute timeout
- If setting is missing, defaults to 60 minutes
- No database migrations required
- No breaking changes to API

## Future Enhancements (Optional)

Possible future improvements:
1. Add UI control for timeout in system settings page
2. Visual indicator on Tilt card showing time since last reading
3. Different timeouts per Tilt color
4. Notification when Tilt becomes inactive

## Summary

The issue has been completely resolved. Tilts that haven't sent data for the configured timeout period (default: 60 minutes) are now automatically hidden from the main display and API endpoints. The solution is:

- ✓ Minimal changes to codebase
- ✓ Fully tested
- ✓ Configurable
- ✓ Backward compatible
- ✓ Well documented
- ✓ No security vulnerabilities

Users experiencing the issue will now see Tilts automatically disappear from the display after they become inactive, providing a much cleaner and more accurate view of their fermentation setup.
