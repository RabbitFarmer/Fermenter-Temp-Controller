# Notification Threshold Fix - Strict Comparison

## User Feedback

**Comment**: "The above limit and below limit notifications are just that. Notifications are going out when the current EQUALS a high or low limit. That is incorrect. The 'above high limit' Notice goes out if and only if the high limit is EXCEEDED. The 'Below Low Limit' notification goes out if and only if the current temperature IS BELOW the low limit."

## The Problem

Notifications were being sent when temperature EQUALS the limits, not just when exceeded:

**Before the fix:**
```python
# Heating control (line 2756)
if temp <= low:
    control_heating("on")
    if temp_cfg.get("below_limit_trigger_armed"):
        # Notification sent when temp <= low (including when equal!)
        send_temp_control_notification("temp_below_low_limit", ...)

# Cooling control (line 2783)
if temp >= high:
    control_cooling("on")
    if temp_cfg.get("above_limit_trigger_armed"):
        # Notification sent when temp >= high (including when equal!)
        send_temp_control_notification("temp_above_high_limit", ...)
```

**Issue**: Using `<=` and `>=` meant notifications were sent even when temperature was EXACTLY at the limit, not just when exceeded.

## The Solution

Changed notification triggers to use STRICT comparison (`<` and `>`) while keeping plug control using inclusive comparison (`<=` and `>=`):

**After the fix:**
```python
# Heating control (line 2756-2769)
if temp <= low:
    # Plug control - inclusive comparison for hysteresis
    control_heating("on")
    # Notification - strict comparison, only when EXCEEDED
    if temp < low and temp_cfg.get("below_limit_trigger_armed"):
        send_temp_control_notification("temp_below_low_limit", ...)

# Cooling control (line 2783-2797)
if temp >= high:
    # Plug control - inclusive comparison for hysteresis
    control_cooling("on")
    # Notification - strict comparison, only when EXCEEDED
    if temp > high and temp_cfg.get("above_limit_trigger_armed"):
        send_temp_control_notification("temp_above_high_limit", ...)
```

## Key Changes

### Code Changes (app.py)

**Line 2762** (heating notification):
- **Before**: `if temp_cfg.get("below_limit_trigger_armed") and is_monitoring_active:`
- **After**: `if temp < low and temp_cfg.get("below_limit_trigger_armed") and is_monitoring_active:`

**Line 2790** (cooling notification):
- **Before**: `if temp_cfg.get("above_limit_trigger_armed") and is_monitoring_active:`
- **After**: `if temp > high and temp_cfg.get("above_limit_trigger_armed") and is_monitoring_active:`

## Behavior Comparison

### Scenario 1: Temperature Below Low Limit

| Temperature | Low Limit | Heating Plug | Notification |
|-------------|-----------|--------------|--------------|
| 67.0°F | 68.0°F | ✅ ON (67 <= 68) | ✅ SENT (67 < 68) |
| **68.0°F** | **68.0°F** | ✅ **ON (68 <= 68)** | ❌ **NOT SENT (68 is NOT < 68)** |
| 69.0°F | 68.0°F | ❌ OFF | ❌ NOT SENT |

### Scenario 2: Temperature Above High Limit

| Temperature | High Limit | Cooling Plug | Notification |
|-------------|------------|--------------|--------------|
| 71.0°F | 72.0°F | ❌ OFF | ❌ NOT SENT |
| **72.0°F** | **72.0°F** | ✅ **ON (72 >= 72)** | ❌ **NOT SENT (72 is NOT > 72)** |
| 73.0°F | 72.0°F | ✅ ON (73 >= 72) | ✅ SENT (73 > 72) |

### Key Observations

**Bold rows** show the critical difference:
- When temperature EQUALS the limit, plug turns on (for hysteresis) but NO notification is sent
- This is the correct behavior requested by the user

## Why This Separation Is Important

### Plug Control (Inclusive Comparison)

**Uses `<=` and `>=` for hysteresis:**
- Heating turns ON when `temp <= low_limit`
- Cooling turns ON when `temp >= high_limit`
- This prevents rapid on/off cycling (hysteresis)

**Example**: If low limit is 68°F and temp is exactly 68°F, heating should stay ON to prevent the temperature from dropping further. Without inclusive comparison, the system would oscillate.

### Notifications (Strict Comparison)

**Uses `<` and `>` to only alert when exceeded:**
- Notification sent only when `temp < low_limit` (truly below)
- Notification sent only when `temp > high_limit` (truly above)
- This prevents false alarms when temp is at the boundary

**Example**: If low limit is 68°F and temp is exactly 68°F, the system is working correctly (maintaining the limit). No alert needed. User only wants alert when it's actually cold (below 68°F).

## Testing

Created comprehensive test in `test_notification_threshold_logic.py`:

```bash
$ python3 test_notification_threshold_logic.py

TEST: Notification Threshold Logic (Strict Comparison)

Test Cases:
✅ PASS: Below low limit (67.0°F < 68.0°F) - notification sent
✅ PASS: Equal to low limit (68.0°F == 68.0°F) - NO notification
✅ PASS: Within range (70.0°F) - NO notification
✅ PASS: Equal to high limit (72.0°F == 72.0°F) - NO notification
✅ PASS: Above high limit (73.0°F > 72.0°F) - notification sent

✅ ALL TESTS PASSED
```

## Impact

### Before Fix
- ❌ Notification sent when temp = 68.0°F and low limit = 68.0°F
- ❌ Notification sent when temp = 72.0°F and high limit = 72.0°F
- ❌ False alarms when system is working correctly at boundary

### After Fix
- ✅ NO notification when temp = 68.0°F and low limit = 68.0°F
- ✅ NO notification when temp = 72.0°F and high limit = 72.0°F
- ✅ Notifications ONLY when limits are truly exceeded
- ✅ Plug control unaffected (still uses hysteresis correctly)

## Files Changed

- **app.py** (lines 2762, 2790): Added strict comparison for notification triggers
- **test_notification_threshold_logic.py**: New test to verify strict comparison logic

## Commit

**Commit**: 8e9ad81
**Message**: Fix: Use strict comparison for notifications (< and > instead of <= and >=)
**Changes**: Added `temp < low` and `temp > high` conditions to notification triggers

## Summary

✅ Notifications now sent ONLY when limits are exceeded (< or >)
✅ Notifications NOT sent when temperature equals limits
✅ Plug control still uses hysteresis (<= and >=) for proper operation
✅ Separation between plug control and notifications maintained
✅ Test coverage added
✅ User feedback fully addressed
