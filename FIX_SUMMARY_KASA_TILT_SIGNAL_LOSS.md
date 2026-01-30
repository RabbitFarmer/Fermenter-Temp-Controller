# Fix Summary: KASA Control Error - Tilt Signal Loss Safety Shutdown

## Issue
**GitHub Issue**: "KASA Control Error"

**Problem**: The safety shutdown mechanism was not triggered when a Tilt hydrometer lost signal if the Tilt was not explicitly assigned to temperature control (fallback mode). Additionally, the timeout for temperature control safety was incorrectly using the 30-minute general monitoring timeout instead of a rapid 4-minute timeout based on 2 missed readings.

### User Report
> "The setting for the temperature controller to talk to the KASA plug is at 2 minutes. Too, there is logic in the program for emergency shut down of the kasa plugs. However, this does not currently apply to tilt loss of signal when the tilt is assigned to control the temperature."

### Clarification from User
> "Normally, a tilt used for fermentation is checked every 15 minutes. If it passes 2 readings (aka 30 minutes) then we go into notifications and other stuff. Now, when a tilt is also used for Temperature Control, the temp control setting is at 2 minutes. At 4 minutes without signal, KASA plugs should be turned off."

## Root Causes

### Issue 1: Fallback Mode Not Covered

The temperature control system has two modes for selecting which Tilt to use:

1. **Explicit Assignment**: User selects a specific Tilt color in the temperature config (e.g., `tilt_color: "Red"`)
2. **Fallback Mode**: No Tilt is explicitly assigned (`tilt_color: ""`), and the system uses the temperature from any available Tilt

The safety shutdown mechanism only checked for inactive Tilts when a Tilt was explicitly assigned:

```python
# OLD CODE (before fix)
if temp_cfg.get("tilt_color") and not is_control_tilt_active():
    # Trigger safety shutdown
```

**The bug:** When `tilt_color` was empty (fallback mode), the condition `temp_cfg.get("tilt_color")` evaluated to falsy, so the safety check never triggered.

### Issue 2: Wrong Timeout for Temperature Control

Temperature control was using the general 30-minute inactivity timeout (designed for display/notification purposes), but it should use a much shorter timeout:

- **General Monitoring**: 15-minute check interval, 30-minute timeout (2 missed readings)
- **Temperature Control**: 2-minute update interval, 4-minute timeout (2 missed readings)

Temperature control requires rapid response because continued heating/cooling with stale data can damage the fermentation batch.

## Solution Implemented

### 1. Added `get_control_tilt_color()` Function

Created a new function to identify which Tilt is actually being used for temperature control, regardless of whether it's explicitly assigned or selected via fallback:

```python
def get_control_tilt_color():
    """
    Get the color of the Tilt currently being used for temperature control.
    
    Returns:
        str: The color of the Tilt being used, or None if no Tilt is being used.
    """
    # First check if a Tilt is explicitly assigned
    color = temp_cfg.get("tilt_color")
    if color and color in live_tilts:
        return color
    
    # If no explicit assignment, check if we're using a fallback Tilt
    for tilt_color, info in live_tilts.items():
        if info.get("temp_f") is not None:
            return tilt_color
    
    return None
```

### 2. Modified `is_control_tilt_active()` for Temperature Control Timeout

Updated the function to use the correct timeout for temperature control safety:

```python
def is_control_tilt_active():
    """
    Check if the Tilt being used for temperature control is currently active.
    
    For temperature control safety, uses a shorter timeout than general Tilt monitoring:
    - Temperature control timeout: 2 × update_interval (default: 2 × 2 min = 4 minutes)
    - This ensures KASA plugs turn off quickly if Tilt signal is lost
    - Much shorter than the general 30-minute inactivity timeout used for display/notifications
    """
    # Get the color of the Tilt actually being used for control
    control_color = get_control_tilt_color()
    
    if not control_color:
        return True
    
    # For temperature control, use timeout = 2 × update_interval (2 missed readings)
    try:
        update_interval_minutes = int(system_cfg.get("update_interval", 2))
    except Exception:
        update_interval_minutes = 2
    
    temp_control_timeout_minutes = update_interval_minutes * 2
    
    # Check if the control Tilt has sent data within the temp control timeout
    if control_color not in live_tilts:
        return False
    
    tilt_info = live_tilts[control_color]
    timestamp_str = tilt_info.get('timestamp')
    if not timestamp_str:
        return False
    
    try:
        timestamp = datetime.fromisoformat(timestamp_str.rstrip('Z'))
        now = datetime.utcnow()
        elapsed_minutes = (now - timestamp).total_seconds() / 60.0
        
        # Tilt is active if it's within the temp control timeout
        return elapsed_minutes < temp_control_timeout_minutes
    except Exception:
        # If we can't determine activity, assume inactive for safety
        return False
```

### 3. Updated Safety Check Logic

Modified the safety check in `temperature_control_logic()` to work for both modes and include better status messages:

```python
# NEW CODE (after fix)
if not is_control_tilt_active():
    control_heating("off")
    control_cooling("off")
    
    # Get the actual Tilt color being used
    actual_tilt_color = get_control_tilt_color()
    assigned_tilt_color = temp_cfg.get("tilt_color", "")
    
    # Set status message indicating which Tilt triggered shutdown
    if assigned_tilt_color:
        temp_cfg["status"] = f"Control Tilt Inactive - Safety Shutdown ({assigned_tilt_color})"
    elif actual_tilt_color:
        temp_cfg["status"] = f"Control Tilt Inactive - Safety Shutdown (using {actual_tilt_color} as fallback)"
    else:
        temp_cfg["status"] = "Control Tilt Inactive - Safety Shutdown"
```

### 4. Enhanced Logging

Updated the safety shutdown log to include both the assigned Tilt color and the actual Tilt color being used:

```python
append_control_log("temp_control_safety_shutdown", {
    "tilt_color": tilt_color,
    "assigned_tilt": assigned_tilt_color,
    "actual_tilt": actual_tilt_color or "None",
    "reason": "Control Tilt inactive beyond timeout",
    "low_limit": low,
    "high_limit": high
})
```

## Testing

### Unit Tests

1. **`test_tilt_fallback_safety.py`** - Comprehensive test for fallback mode with correct timeout:
   - Test 1: Fallback Tilt at 1 minute - active, normal operation ✓
   - Test 2: Tilt at 3 minutes - still active (< 4 min timeout) ✓
   - Test 3: Tilt at 5 minutes - inactive, safety shutdown ✓
   - Test 4: Explicitly assigned Tilt at 2 minutes - active ✓
   - Test 5: Explicitly assigned Tilt at 5 minutes - inactive, safety shutdown ✓

2. **`test_safety_shutdown.py`** - Updated existing test for 4-minute timeout:
   - Updated timestamps to use 1 minute (active) and 5 minutes (inactive)
   - All 4 tests pass ✓

3. **`test_issue_kasa_control_error.py`** - Simulates exact issue scenario with 4-minute timeout:
   - Scenario 1: Fallback mode, shutdown at 4 minutes ✓
   - Scenario 2: Explicit mode, shutdown at 4 minutes ✓

### Test Results

```
✓ test_tilt_fallback_safety.py - ALL TESTS PASSED
✓ test_safety_shutdown.py - ALL TESTS PASSED  
✓ test_issue_kasa_control_error.py - ISSUE RESOLVED
```

## Behavior Comparison

### Before Fix

**Fallback Mode (tilt_color is empty):**
```
Time: 10:00 AM - Red Tilt broadcasts (temp 68°F), heater turns on
Time: 10:02 AM - Tilt check runs, still sees data
Time: 10:04 AM - Red Tilt stops broadcasting
Time: 10:06 AM - Tilt check runs, uses STALE data, heater STAYS ON ✗
Time: 10:30 AM - Still heating with stale temp ✗
Time: 11:00 AM - Possible batch damage ✗
```

**Explicit Mode with Wrong Timeout:**
```
Time: 10:00 AM - Red Tilt broadcasts, heater turns on
Time: 10:04 AM - Tilt stops broadcasting
Time: 10:30 AM - After 30 minutes, heater finally turns OFF
Time: 10:30 AM - 26 minutes of heating with stale data! ✗
```

### After Fix

**Both Modes with Correct 4-Minute Timeout:**
```
Time: 10:00 AM - Tilt broadcasts (temp 68°F), heater turns on
Time: 10:02 AM - Check runs (2 min elapsed), still active ✓
Time: 10:03 AM - Tilt stops broadcasting (last signal at 10:02)
Time: 10:04 AM - Check runs (2 min since last signal), still active ✓
Time: 10:06 AM - Check runs (4 min since last signal), INACTIVE → SAFETY SHUTDOWN ✓
  - All KASA plugs turned OFF immediately
  - Status: "Control Tilt Inactive - Safety Shutdown"
  - Safety event logged
  - Email/push notification sent to user
Time: 10:08 AM - Heater remains OFF, batch is safe ✓
```

**Key Improvement:** Safety shutdown now happens after just 4 minutes (2 missed readings at 2-minute intervals) instead of 30+ minutes!

## Timeout Comparison

| Purpose | Check Interval | Timeout (2 Readings) | Use Case |
|---------|---------------|----------------------|----------|
| **General Monitoring** | 15 minutes | 30 minutes | Display, notifications, batch tracking |
| **Temperature Control** | 2 minutes | **4 minutes** | **Safety shutdown of KASA plugs** |

The temperature control timeout is **7.5× faster** than general monitoring, ensuring rapid response to prevent batch damage.

## Files Changed

1. **app.py**
   - Added `get_control_tilt_color()` function (lines 574-593)
   - Modified `is_control_tilt_active()` to use temp control timeout (lines 603-655)
   - Updated safety check in `temperature_control_logic()` (lines 2203-2241)
   - Enhanced status messages to indicate which Tilt triggered shutdown
   - Improved logging to include both assigned and actual Tilt colors

2. **test_safety_shutdown.py**
   - Updated test timestamps for 4-minute timeout
   - Updated assertions and documentation

3. **test_tilt_fallback_safety.py**
   - Completely rewritten for 4-minute timeout testing
   - Tests at 1, 3, and 5 minutes to verify timeout boundary
   - Documents the difference between temp control and general monitoring

4. **test_issue_kasa_control_error.py**
   - Updated to simulate 4-minute timeout scenario
   - Tests both fallback and explicit modes
   - Documents the requirement clearly

5. **FIX_SUMMARY_KASA_TILT_SIGNAL_LOSS.md** (THIS FILE)
   - Complete documentation of the fix

## Safety Features

The temperature control system now has complete safety coverage with correct timeouts:

1. ✓ **Inactive Tilt (Explicit)**: Plugs turn off 4 minutes after last signal
2. ✓ **Inactive Tilt (Fallback)**: Plugs turn off 4 minutes after last signal
3. ✓ **No Temperature Available**: Plugs turn off when temp is None
4. ✓ **Configuration Error**: Plugs turn off if low_limit >= high_limit
5. ✓ **Both Plugs On**: Plugs turn off if both heating and cooling activate
6. ✓ **Control Disabled**: Plugs turn off when temperature control is disabled

## User Impact

### Positive Impact
- **Rapid safety response**: Heating/cooling stops after just 4 minutes (2 missed readings) when Tilt signal is lost
- **Works in both modes**: Safety applies whether Tilt is explicitly assigned or used as fallback
- **Better notifications**: Status messages clearly indicate which Tilt caused the shutdown
- **More detailed logging**: Logs include both assigned and actual Tilt colors for troubleshooting
- **Prevents batch damage**: Much faster response than the previous 30-minute timeout

### No Breaking Changes
- ✓ Backward compatible with existing configurations
- ✓ Existing functionality preserved for all modes
- ✓ No changes to user interface or configuration files
- ✓ No database migrations required
- ✓ Timeout automatically adapts to `update_interval` setting

## Configuration

The timeout is automatically calculated:

```
temp_control_timeout = 2 × update_interval
```

Examples:
- `update_interval: 1` minute → timeout: 2 minutes
- `update_interval: 2` minutes (default) → timeout: 4 minutes
- `update_interval: 5` minutes → timeout: 10 minutes

This ensures the system always waits for exactly 2 missed readings before triggering safety shutdown, regardless of the update interval configuration.

## Recommendations for Users

1. **Keep Default Update Interval**: The 2-minute default provides good balance (4-minute timeout)

2. **Monitor Notifications**: Enable email/push notifications to be alerted immediately when safety shutdown occurs

3. **Check Tilt Batteries**: If safety shutdowns occur frequently, check Tilt battery levels and replace as needed

4. **Verify Tilt Range**: Ensure Tilt hydrometers are within Bluetooth range of the controller

5. **Test Safety System**: Periodically test by removing Tilt batteries to verify shutdown occurs within 4 minutes

## Summary

The issue has been completely resolved. Both explicit and fallback mode temperature control now:

- ✓ Trigger safety shutdown after 2 missed readings (4 minutes with 2-minute updates)
- ✓ Use correct temperature control timeout (not the 30-minute general timeout)
- ✓ Minimal changes to codebase
- ✓ Fully tested with comprehensive test coverage
- ✓ Backward compatible
- ✓ Well documented
- ✓ No security vulnerabilities

Users will no longer experience prolonged runaway heating/cooling when their Tilt hydrometer goes offline. The system now responds within 4 minutes (with default 2-minute update interval), preventing potential batch damage and ensuring safe fermentation monitoring.

**Key Achievement:** Reduced safety shutdown response time from 30+ minutes to just 4 minutes - a **7.5× improvement** in safety response speed!
