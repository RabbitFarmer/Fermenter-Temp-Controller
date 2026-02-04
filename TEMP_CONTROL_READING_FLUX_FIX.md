# Fix Summary: Temperature Control Card Reading Fluctuations

## Issue
On the main display, the temp control card shows temperature readings that fluctuate (e.g., dropping from 74°F to 71°F and back to 74°F), while the corresponding Tilt card (Black Tilt) shows stable readings.

## Root Cause Analysis

### Data Flow
1. **BLE Scanner** (`ble_loop()` at line 3554):
   - Runs continuously in a separate thread
   - Updates `live_tilts[color]['temp_f']` when Tilt data arrives
   - Every 5 seconds, calls `get_current_temp_for_control_tilt()` 
   - Stores result in `temp_cfg['current_temp']` (line 3566)

2. **Temperature Control Loop** (`periodic_temp_control()` at line 3440):
   - Runs every 2 minutes (default `update_interval`)
   - Reloads configuration from disk (line 3443)
   - Updates `temp_cfg` with file values (line 3477)

3. **Configuration Persistence**:
   - When Kasa plug commands succeed, `save_json(TEMP_CFG_FILE, temp_cfg)` is called
   - This saves the entire `temp_cfg` dictionary, including `current_temp`
   - The saved value becomes stale as soon as temperature changes

### The Bug
The `runtime_state_vars` exclusion list in `periodic_temp_control()` excluded many runtime values but **did NOT exclude `current_temp` or `last_reading_time`**.

This caused:
1. BLE scanner updates `temp_cfg['current_temp']` to 74°F at time T
2. Some time later, a Kasa command executes and saves config with `current_temp: 74.0`
3. Temperature drops to 72°F, BLE scanner updates `temp_cfg['current_temp']` to 72°F
4. Another Kasa command executes and saves config with `current_temp: 72.0`
5. At T+2min, `periodic_temp_control()` reloads config from disk
6. The file still has `current_temp: 74.0` (from step 2) if no new save occurred
7. `temp_cfg['current_temp']` gets overwritten back to 74°F
8. 5 seconds later, BLE scanner updates it back to 72°F
9. This creates visible "jumping" between stale file values and live BLE values

### Why Tilt Cards Don't Have This Issue
Tilt cards display `live_tilts[color]['temp_f']` directly, which is updated immediately by the BLE scanner and never persisted to disk. Only the temp control card uses `temp_cfg['current_temp']`.

## Solution

### Code Change
**File: `app.py`, lines 3470-3472**

Added to the `runtime_state_vars` exclusion list:
```python
# Temperature reading state - updated live from BLE scanner
# Exclude to prevent overwriting live readings with stale file values
'current_temp', 'last_reading_time',
```

### How This Fixes The Issue
1. `periodic_temp_control()` still reloads config from file
2. Before applying file values, it removes `current_temp` and `last_reading_time` from `file_cfg`
3. When `temp_cfg.update(file_cfg)` executes, these fields are NOT overwritten
4. Live temperature readings from BLE scanner are preserved
5. No more fluctuations!

### What Still Works
- Other configuration values (like `tilt_color`, `enable_heating`, etc.) are still reloadable from file
- Temperature limits (`low_limit`, `high_limit`) remain excluded (existing behavior)
- All existing tests pass

## Testing

### New Test
**File: `test_current_temp_reload_fix.py`**

Simulates the exact bug scenario:
1. Sets `temp_cfg['current_temp'] = 68.5` (live value)
2. Saves file with `current_temp: 65.0` (stale value)
3. Runs the reload logic from `periodic_temp_control()`
4. Verifies `temp_cfg['current_temp']` is still 68.5 (preserved)
5. Verifies other config values can still be updated

**Result:** ✅ PASSED

### Existing Tests
- `test_temp_control_refresh_interval.py` - ✅ PASSED
- No syntax errors in `app.py` - ✅ PASSED

### Security Scan
- CodeQL analysis: ✅ No alerts

## Impact
- **User Visible:** Temperature readings on temp control card will now be stable and match Tilt card readings
- **Breaking Changes:** None
- **Data Loss Risk:** None
- **Performance:** No impact (same reload logic, just excludes 2 more fields)

## Files Modified
1. `app.py` - Added 2 fields to exclusion list
2. `test_current_temp_reload_fix.py` - New comprehensive test

## Deployment Notes
- No configuration migration needed
- No database changes
- No restart required for fix (but restart needed to apply new code)
- Compatible with all existing temp control configurations
