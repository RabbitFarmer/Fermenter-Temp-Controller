# Complete Fix: All Notification Triggers Preserved

## User Feedback Addressed

**Original Comment**: "There is a stated conflict in coding in app.py file. Review and correct the conflict. Keep in mind there is more than 1 trigger at play. Previously they were conflated. For Chart Display and Notification purposes, triggers are employed so as to limit the display and/or notice to the first occurance only. The actual communication with the Kasa plugs were incorrectly included in the triggers. To get the plugs working, they were removed from these limiting triggers. So, charts and notifications should not share the same code as kasa plug management."

## The Issue

The initial fix only preserved 3 of the 7 trigger types:
- ✅ `below_limit_trigger_armed`
- ✅ `above_limit_trigger_armed`
- ✅ `in_range_trigger_armed`
- ❌ Missing: `heating_blocked_trigger`
- ❌ Missing: `cooling_blocked_trigger`
- ❌ Missing: `heating_safety_off_trigger`
- ❌ Missing: `cooling_safety_off_trigger`

## The Complete Fix

Now ALL 7 trigger types are preserved across config reloads in `app.py` lines 3135-3156:

```python
# Preserve ALL runtime trigger states - these should NOT be overwritten by config reload
# There are multiple trigger types:
# 1. Notification triggers (below/above/in_range) - limit temperature notification spam
# 2. Safety triggers (heating/cooling blocked/off) - limit Tilt safety notification spam
# All triggers track whether we've already logged/notified for the current condition
# and are reset only when the condition is resolved
preserved_triggers = {
    # Temperature limit notification triggers
    'below_limit_trigger_armed': temp_cfg.get('below_limit_trigger_armed'),
    'above_limit_trigger_armed': temp_cfg.get('above_limit_trigger_armed'),
    'in_range_trigger_armed': temp_cfg.get('in_range_trigger_armed'),
    # Safety notification triggers (Tilt connection loss)
    'heating_blocked_trigger': temp_cfg.get('heating_blocked_trigger'),
    'cooling_blocked_trigger': temp_cfg.get('cooling_blocked_trigger'),
    'heating_safety_off_trigger': temp_cfg.get('heating_safety_off_trigger'),
    'cooling_safety_off_trigger': temp_cfg.get('cooling_safety_off_trigger'),
}

temp_cfg.update(file_cfg)

# Restore the preserved trigger states after config reload
temp_cfg.update(preserved_triggers)
```

## Trigger Types Explained

### 1. Temperature Notification Triggers (3)

**Purpose**: Limit notifications when temperature crosses limits

**Behavior**:
- `below_limit_trigger_armed`: Armed initially, disarmed when temp drops below low limit, re-armed when temp reaches high limit
- `above_limit_trigger_armed`: Armed initially, disarmed when temp rises above high limit, re-armed when temp drops to low limit
- `in_range_trigger_armed`: Armed when temp is out of range, disarmed when temp enters range

**When they trigger**:
- Temperature goes below low limit → log + notify once
- Temperature goes above high limit → log + notify once
- Temperature enters range → log once
- No more logs/notifications until condition changes

### 2. Safety Notification Triggers (4)

**Purpose**: Limit notifications when Tilt connection is lost

**Behavior**:
- `heating_blocked_trigger`: Disarmed when heating ON command is blocked due to no Tilt, re-armed when Tilt reconnects
- `cooling_blocked_trigger`: Disarmed when cooling ON command is blocked due to no Tilt, re-armed when Tilt reconnects
- `heating_safety_off_trigger`: Disarmed when heating is turned OFF due to no Tilt, re-armed when Tilt reconnects
- `cooling_safety_off_trigger`: Disarmed when cooling is turned OFF due to no Tilt, re-armed when Tilt reconnects

**When they trigger**:
- Tilt loses connection and heating/cooling blocked → log + notify once
- Tilt loses connection and heating/cooling turned off for safety → log + notify once
- No more logs/notifications until Tilt reconnects

## Key Point: Triggers Do NOT Control Kasa Plugs

**Important distinction** established in previous fixes:

### What Triggers Control:
- ✅ Logging to temp_control_log.jsonl
- ✅ Notifications (email/push)
- ✅ Chart event markers
- ❌ NOT Kasa plug commands

### What Controls Kasa Plugs:
- Temperature thresholds (temp <= low, temp >= high)
- Safety checks (is_control_tilt_active)
- Enable flags (enable_heating, enable_cooling)
- Monitor state (temp_control_active)

### Code Structure:
```python
# Heating control logic (from app.py lines 2756-2768)
if enable_heat:
    if temp <= low:
        # Plug command - executes EVERY iteration
        control_heating("on")
        
        # Notification/logging - executes ONCE per condition
        if temp_cfg.get("below_limit_trigger_armed") and is_monitoring_active:
            append_control_log("temp_below_low_limit", ...)
            send_temp_control_notification("temp_below_low_limit", ...)
            temp_cfg["below_limit_trigger_armed"] = False
```

**Key observation**: `control_heating("on")` is OUTSIDE the trigger check, so plugs work every iteration. Only logging and notifications are inside the trigger check.

## Testing

Updated test verifies ALL 7 triggers:

```bash
$ python3 test_notification_trigger_fix.py

================================================================================
TEST: ALL Notification Trigger Preservation Across Config Reload
================================================================================

5. Verification of ALL trigger states:
   below_limit_trigger_armed: ✅ PRESERVED
   above_limit_trigger_armed: ✅ PRESERVED
   in_range_trigger_armed: ✅ PRESERVED
   heating_blocked_trigger: ✅ PRESERVED
   cooling_blocked_trigger: ✅ PRESERVED
   heating_safety_off_trigger: ✅ PRESERVED
   cooling_safety_off_trigger: ✅ PRESERVED

✅ ALL TESTS PASSED - All trigger types preserved correctly!
```

## Impact

### Before Fix
- Temperature notifications: ❌ Sent every 5 minutes (buggy)
- Safety notifications: ❌ Sent every 2 minutes (buggy)
- Kasa plugs: ✅ Working (already fixed in previous PR)

### After Fix
- Temperature notifications: ✅ Sent once per condition
- Safety notifications: ✅ Sent once per condition
- Kasa plugs: ✅ Still working (unaffected by this fix)

## Files Changed

- `app.py` (lines 3135-3156): Preserve all 7 trigger types
- `test_notification_trigger_fix.py`: Test all 7 trigger types

## Commit

**Commit**: 77fc935
**Message**: Fix: Preserve ALL trigger types (temperature and safety)
**Files**: app.py, test_notification_trigger_fix.py
**Changes**: +78 lines, -27 lines

## Summary

✅ All 7 trigger types now preserved across config reloads
✅ Notifications limited to once per condition
✅ Kasa plug control unaffected (works every iteration)
✅ Separation between triggers and plug control maintained
✅ Test coverage for all trigger types
✅ Ready for merge
