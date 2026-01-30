# Simple Safety Rule: No Connection = No Plugs Turn ON

## Overview

A simple, straightforward safety feature to protect your fermentation when the Tilt hydrometer loses connection or signal.

**The Rule:**
> **No connection = No plugs turn ON**

**The Trigger Pattern:**
> **Report once, flip trigger, reset when corrected**

## How It Works

### Three Simple Cases

1. **Tilt Connection Lost + Trying to Turn ON** → **BLOCKED**
   - System blocks the ON command
   - Plug stays OFF for safety
   - **First time**: Log ✓ and Notify ✓ (flip trigger)
   - **Subsequent attempts**: Skip (trigger already flipped)

2. **Tilt Connection Lost + Plug is ON** → **Turn OFF**
   - System turns the plug OFF for safety
   - **First time**: Log ✓ and Notify ✓ (flip trigger)
   - **Subsequent checks**: Skip (trigger already flipped)

3. **Tilt Connection Active** → **Normal Operation**
   - All commands work normally
   - **Trigger reset** when connection restored
   - Ready to log/notify for next incident if it happens again

### Trigger Pattern

```
Issue detected
  ↓
Check: Is trigger flipped?
  ↓
NO → Log + Notify + Flip trigger
  ↓
Issue persists (checked every 2 minutes)
  ↓
Check: Is trigger flipped?
  ↓
YES → Skip logging and notification
  ↓
Issue corrected (Tilt reconnects)
  ↓
Reset trigger
  ↓
Ready for next incident
```

**Result:** Once is enough until corrected!

## Example Scenarios

### Scenario 1: Tilt Battery Dies During Fermentation

```
10:00 AM - Tilt broadcasting, heater ON, temp 68°F
10:30 AM - Tilt battery dies (stops broadcasting)
10:34 AM - System detects: no Tilt signal for 4 minutes
         - Heater is ON → System turns heater OFF
         - Trigger: heating_safety_off_trigger flipped
         - Log entry written ✓
         - Notification sent: "SAFETY: Heating Turned OFF" ✓
10:36 AM - Temperature drops to 67°F (would normally trigger heating)
         - System tries to turn heater ON → BLOCKED
         - Trigger: heating_blocked_trigger flipped
         - Log entry written ✓
         - Notification sent: "SAFETY: Heating Blocked" ✓
10:38 AM - Temperature control runs again (2 min later)
         - System tries to turn heater ON → BLOCKED
         - Trigger already flipped → Skip log and notification
10:40 AM - Temperature control runs again (2 min later)
         - System tries to turn heater ON → BLOCKED
         - Trigger already flipped → Skip log and notification
         ... (no more spam every 2 minutes)
Later    - You replace Tilt battery
         - Tilt starts broadcasting again
         - Triggers reset: heating_blocked_trigger = False
         - Normal heating/cooling resumes automatically
         - Ready to log/notify again if issue happens in future
```

**Key Point:** Only 2 log entries and 2 notifications total (not one every 2 minutes!)

### Scenario 2: Tilt Out of Range (Setup Issue)

```
2:00 PM - You assign Red Tilt to temperature control
        - Temperature is 72°F (above high limit 70°F)
        - System wants to turn cooling ON
        - But Tilt hasn't broadcast yet (just placed in fermenter)
        - Grace period active (15 minutes) → Cooling allowed temporarily
2:10 PM - Tilt still hasn't broadcast (maybe too far from Pi?)
2:15 PM - Grace period expires
        - System wants to turn cooling ON
        - But no Tilt signal → ON command BLOCKED
        - Trigger: cooling_blocked_trigger flipped
        - Notification sent ✓
        - Log entry written ✓
2:17 PM - System tries again (2 min later)
        - Trigger already flipped → Skip notification and log
2:19 PM - System tries again (2 min later)
        - Trigger already flipped → Skip notification and log
2:20 PM - You move Pi closer to fermenter
        - Tilt starts broadcasting
        - Trigger reset: cooling_blocked_trigger = False
        - Normal cooling resumes automatically
```

**Key Point:** Only 1 notification and 1 log entry (not spam every 2 minutes!)

### Scenario 3: Normal Operation (No Issues)

```
All day - Tilt broadcasting every few seconds
        - Temperature control working normally
        - Heating/cooling as needed
        - No safety notifications (everything is fine!)
```

## Notifications

When the safety rule triggers, you receive notifications (email/push):

### Blocked ON Command

```
Subject: [Brewery Name] - SAFETY: Heating Blocked (No Tilt Connection)

SAFETY ALERT

The system attempted to turn ON the heating plug, but the Tilt assigned 
to temperature control is not transmitting data.

Safety Rule: No connection = No plugs turn ON

The heating plug will remain OFF until the Tilt connection is restored.

Action Required:
1. Check Tilt battery
2. Verify Tilt is in range
3. Ensure Tilt is in liquid
4. Check Bluetooth connectivity
```

### Safety OFF Command

```
Subject: [Brewery Name] - SAFETY: Heating Turned OFF (No Tilt Connection)

SAFETY ALERT

The Tilt assigned to temperature control is not transmitting data.
The heating plug has been automatically turned OFF for safety.

Safety Rule: No connection = Plugs turn OFF

Action Required:
1. Check Tilt battery
2. Verify Tilt is in range
3. Ensure Tilt is in liquid
4. Check Bluetooth connectivity
```

## Logging

All safety events are logged to `temp_control_log.jsonl` **once per incident**:

### Blocked ON Event
```json
{
  "timestamp": "2026-01-30T14:30:00Z",
  "event": "SAFETY - BLOCKED ON COMMAND (NO TILT CONNECTION)",
  "mode": "heating",
  "tilt_color": "Red",
  "reason": "Tilt connection lost - cannot turn heating ON",
  "low_limit": 65.0,
  "high_limit": 70.0
}
```

**Frequency:** Once when issue first detected, then skipped until corrected and happens again.

### Safety OFF Event
```json
{
  "timestamp": "2026-01-30T14:34:00Z",
  "event": "SAFETY - TURNING OFF (NO TILT CONNECTION)",
  "mode": "heating",
  "tilt_color": "Red",
  "reason": "Tilt connection lost - turning heating OFF for safety",
  "low_limit": 65.0,
  "high_limit": 70.0
}
```

**Frequency:** Once when issue first detected, then skipped until corrected and happens again.

## Technical Implementation

### Triggers Used

Four triggers control logging and notifications:

1. `heating_blocked_trigger` - Blocks heating ON when Tilt inactive
2. `heating_safety_off_trigger` - Turns heating OFF when Tilt inactive
3. `cooling_blocked_trigger` - Blocks cooling ON when Tilt inactive
4. `cooling_safety_off_trigger` - Turns cooling OFF when Tilt inactive

### Trigger Logic

```python
# When issue detected
if state == "on" and not is_control_tilt_active():
    # Check trigger
    if not temp_cfg.get("heating_blocked_trigger"):
        # First time - log and notify
        append_control_log("temp_control_blocked_on", {...})
        send_plug_blocked_notification("heating", tilt_color)
        # Flip trigger
        temp_cfg["heating_blocked_trigger"] = True
    return  # Block the ON command

# When issue corrected
if is_control_tilt_active():
    # Reset trigger
    if temp_cfg.get("heating_blocked_trigger"):
        temp_cfg["heating_blocked_trigger"] = False
```

This pattern ensures **once is enough until corrected**.

## Interaction with Other Features

### Grace Period (15 Minutes)

When you first assign a Tilt, there's a **15-minute grace period**:
- During grace period: Plugs can turn ON even without Tilt signal
- This gives you time to set up the batch
- After grace period: Simple safety rule applies

**Timeline:**
```
T+0:     Assign Tilt → grace period starts
T+0-15:  Plugs can turn ON (setup time)
T+15+:   Simple safety rule enforces (no connection = no ON)
```

### Existing Safety Shutdown

This simple rule **supplements** the existing safety shutdown:

**Existing safety shutdown (still active):**
- Detects when assigned Tilt goes offline
- Turns OFF all plugs immediately
- Prevents heating/cooling with stale temperature data

**New simple rule (added):**
- **Blocks** any attempt to turn plugs ON when Tilt is offline
- Ensures plugs **stay** OFF until connection restored
- Provides clear notifications about what's happening

**Together they provide:**
1. Rapid shutdown when connection lost (existing)
2. Prevention of turning ON without connection (new)
3. Clear notifications about both actions (new)

## Configuration

The safety rule uses existing settings:

```json
{
  "update_interval": 2,  // Check every 2 minutes
  "temp_control_notifications": {
    "enable_safety_shutdown": true  // Enable safety notifications (default)
  }
}
```

**Timeout for "no connection":**
- Temperature control timeout: 2 × update_interval
- Default: 2 × 2 minutes = 4 minutes
- If Tilt hasn't broadcast in 4 minutes, it's considered "no connection"

## Benefits

✅ **Simple** - Easy to understand: No connection = No ON  
✅ **Safe** - Prevents runaway heating/cooling  
✅ **Informative** - Notifications tell you exactly what happened  
✅ **Automatic** - Resumes normal operation when Tilt reconnects  
✅ **Non-intrusive** - Only activates when there's actually a problem  

## Comparison: Before vs After

### Before This Feature

```
Tilt goes offline
  ↓
Safety shutdown turns plugs OFF ✓
  ↓
Temperature drifts out of range
  ↓
System tries to turn heating ON
  ↓
ON command succeeds (using stale temp) ✗
  ↓
Heating turns on with no temperature feedback ✗
  ↓
Potential batch damage ✗
```

### After This Feature

```
Tilt goes offline
  ↓
Safety shutdown turns plugs OFF ✓
  ↓
Temperature drifts out of range
  ↓
System tries to turn heating ON
  ↓
ON command BLOCKED (no Tilt connection) ✓
  ↓
Notification sent ✓
  ↓
Plugs stay OFF for safety ✓
  ↓
Batch is protected ✓
```

## Summary

This simple safety rule ensures that KASA plugs **cannot** turn ON when the Tilt hydrometer is not transmitting data. It's a straightforward, easy-to-understand safety feature that protects your fermentation batches.

**The Rule:**
> **No connection = No plugs turn ON**

Simple, safe, effective.
