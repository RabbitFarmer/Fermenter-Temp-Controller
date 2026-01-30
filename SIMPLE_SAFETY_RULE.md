# Simple Safety Rule: No Connection = No Plugs Turn ON

## Overview

A simple, straightforward safety feature to protect your fermentation when the Tilt hydrometer loses connection or signal.

**The Rule:**
> **No connection = No plugs turn ON**

## How It Works

### Three Simple Cases

1. **Tilt Connection Lost + Trying to Turn ON** → **BLOCKED**
   - System blocks the ON command
   - Plug stays OFF for safety
   - You receive a notification
   - Event is logged

2. **Tilt Connection Lost + Plug is ON** → **Turn OFF**
   - System turns the plug OFF for safety
   - You receive a notification
   - Event is logged

3. **Tilt Connection Active** → **Normal Operation**
   - All commands work normally
   - No special notifications

## Example Scenarios

### Scenario 1: Tilt Battery Dies During Fermentation

```
10:00 AM - Tilt broadcasting, heater ON, temp 68°F
10:30 AM - Tilt battery dies (stops broadcasting)
10:34 AM - System detects: no Tilt signal for 4 minutes
         - Heater is ON → System turns heater OFF
         - Notification sent: "SAFETY: Heating Turned OFF (No Tilt Connection)"
         - Log entry: "SAFETY - TURNING OFF (NO TILT CONNECTION)"
10:36 AM - Temperature drops to 67°F (would normally trigger heating)
         - System tries to turn heater ON → BLOCKED
         - Notification sent: "SAFETY: Heating Blocked (No Tilt Connection)"
         - Log entry: "SAFETY - BLOCKED ON COMMAND (NO TILT CONNECTION)"
Later    - You replace Tilt battery
         - Tilt starts broadcasting again
         - Normal heating/cooling resumes automatically
         - No more safety notifications
```

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
        - Notification sent: "SAFETY: Cooling Blocked (No Tilt Connection)"
        - Plug stays OFF for safety
2:20 PM - You move Pi closer to fermenter
        - Tilt starts broadcasting
        - Normal cooling resumes automatically
```

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

All safety events are logged to `temp_control_log.jsonl`:

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
