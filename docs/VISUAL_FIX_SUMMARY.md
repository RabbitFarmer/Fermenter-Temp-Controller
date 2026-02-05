# Temperature Control Bug - Visual Timeline

## User's Reported Issue

```
Timeline from user's log (Low=74°F, High=75°F):

16:11:12  Temp 71°F  │ HEATING-PLUG TURNED ON ✓
16:24:53  Temp 71°F  │ (heating...)
16:39:58  Temp 72°F  │ (heating...)
16:55:05  Temp 73°F  │ (heating...)
17:10:06  Temp 74°F  │ (heating...)
17:17:12  Temp 74°F  │ IN RANGE
17:25:10  Temp 74°F  │ (at low limit, heater still ON)
17:40:12  Temp 75°F  │ (at HIGH LIMIT - heater should turn OFF!)
17:55:12  Temp 75°F  │ ← NO OFF EVENT! BUG!
18:10:14  Temp 75°F  │ (heater still running...)
18:25:14  Temp 76°F  │ (heater still running...)
18:40:16  Temp 76°F  │ (heater still running...)
18:55:17  Temp 76°F  │ (heater still running...)
19:10:18  Temp 77°F  │ (heater still running...)
19:12:31  ---        │ SAFETY SHUTDOWN (Tilt inactive)
19:13:52  Temp 77°F  │ HEATING-PLUG TURNED ON (incorrect!)
```

**Problem**: Heater never turned off when reaching high limit at 17:40!

---

## Root Cause Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ SCENARIO: Kasa Command Response Lost                        │
└─────────────────────────────────────────────────────────────┘

Step 1: Send ON Command
┌────────────────┐
│ App            │ control_heating("on")
│ heater_on=FALSE├─────────────────┐
│ pending=TRUE   │                 │
└────────────────┘                 │
                                   ▼
                          ┌────────────────┐
                          │ Kasa Queue     │
                          │ action="on"    │
                          └────────────────┘
                                   │
                                   ▼
                          ┌────────────────┐
                          │ Network        │
                          │ (sending...)   │
                          └────────────────┘
                                   │
                                   ▼
                          ┌────────────────┐
                          │ Kasa Plug      │
                          │ Status: ON ✓   │
                          └────────────────┘
                                   │
                                   X  Response LOST!
                                   
Step 2: Timeout (30 seconds)
┌────────────────┐
│ App            │ OLD CODE (before fix):
│ heater_on=FALSE├──  pending=FALSE (cleared)
│ pending=FALSE  │    heater_on=FALSE (NOT updated!) ← BUG
└────────────────┘
     ▲
     │  State says: OFF
     │  Reality:    ON  ← OUT OF SYNC!
     
Step 3: Temp Reaches High Limit
┌────────────────┐
│ App            │ control_heating("off")
│ temp=77°F      │
│ high=75°F      │ Redundancy Check:
│ heater_on=FALSE│   action="off", heater_on=FALSE
└────────────────┘   → "Already OFF, skip command" ✗
                     → COMMAND BLOCKED!
                     
                     Physical heater stays ON indefinitely!
```

---

## The Fix - Visual Flow

```
┌─────────────────────────────────────────────────────────────┐
│ FIXED: Assume Success on Timeout                            │
└─────────────────────────────────────────────────────────────┘

Step 1: Send ON Command (same as before)
┌────────────────┐
│ App            │ control_heating("on")
│ heater_on=FALSE├──→ Kasa Queue → Network → Plug turns ON
│ pending=TRUE   │                         Response lost X
└────────────────┘
                                   
Step 2: Timeout (30 seconds) - WITH FIX
┌────────────────┐
│ App            │ NEW CODE (with fix):
│                │   pending_action="on"
│                │   ↓
│                │   if pending_action == "on":
│                │       heater_on = TRUE  ← FIX APPLIED!
│ heater_on=TRUE ├──  pending=FALSE (cleared)
│ pending=FALSE  │    
└────────────────┘
     ▲
     │  State says: ON
     │  Reality:    ON  ✓ IN SYNC!
     
Step 3: Temp Reaches High Limit
┌────────────────┐
│ App            │ control_heating("off")
│ temp=77°F      │
│ high=75°F      │ Redundancy Check:
│ heater_on=TRUE │   action="off", heater_on=TRUE
└────────────────┘   → "Need to turn OFF, send command" ✓
                     → COMMAND SENT!
                     
                     Heater turns OFF correctly! ✓
```

---

## Why The Fix Works

```
┌──────────────────────────────────────────────────────────────┐
│ Scenario 1: Plug Actually Turned ON                          │
├──────────────────────────────────────────────────────────────┤
│ Reality:   Plug is ON                                         │
│ After Fix: heater_on = TRUE                                  │
│ Result:    ✓ State matches reality                           │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Scenario 2: Plug Didn't Actually Turn ON                     │
├──────────────────────────────────────────────────────────────┤
│ Reality:   Plug is OFF                                        │
│ After Fix: heater_on = TRUE (incorrect assumption)           │
│ Next Cycle: temp_control_logic() checks temp                 │
│            temp < low_limit                                   │
│            → calls control_heating("on") again                │
│            → command sent, plug turns ON                      │
│ Result:    ✓ Self-correcting within 2 minutes                │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Risk Analysis                                                 │
├──────────────────────────────────────────────────────────────┤
│ Worst Case: Plug is OFF when we think it's ON                │
│ Impact:     Temperature not controlled for 1-2 cycles         │
│ Recovery:   Automatic within update_interval (2 min default) │
│ vs Bug:     Heater stuck ON FOREVER until manual restart     │
│ Conclusion: ✓ Fix is strictly better than bug                │
└──────────────────────────────────────────────────────────────┘
```

---

## Timestamp Fix - Before and After

```
┌────────────────────────────────────────────────────────────┐
│ BEFORE FIX - All UTC                                        │
├────────────────────────────────────────────────────────────┤
│ User timezone: PST (UTC-8)                                 │
│ Actual time:   11:13:52 AM PST                            │
│                                                            │
│ Log entry:                                                 │
│ {                                                          │
│   "timestamp": "2026-02-03T19:13:52Z",  ← UTC             │
│   "date": "2026-02-03",                  ← UTC             │
│   "time": "19:13:52",                    ← UTC (confusing!)│
│   "event": "HEATING-PLUG TURNED ON"                       │
│ }                                                          │
│                                                            │
│ User sees: "19:13:52" but clock shows "11:13:52"         │
│ Problem: 8 hour difference is confusing                    │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ AFTER FIX - Local time for date/time                       │
├────────────────────────────────────────────────────────────┤
│ User timezone: PST (UTC-8)                                 │
│ Actual time:   11:13:52 AM PST                            │
│                                                            │
│ Log entry:                                                 │
│ {                                                          │
│   "timestamp": "2026-02-03T19:13:52Z",  ← UTC (unchanged) │
│   "date": "2026-02-03",                  ← Local          │
│   "time": "11:13:52",                    ← Local (matches!)│
│   "event": "HEATING-PLUG TURNED ON"                       │
│ }                                                          │
│                                                            │
│ User sees: "11:13:52" and clock shows "11:13:52" ✓       │
│ Benefit: Times match user's wall clock                     │
└────────────────────────────────────────────────────────────┘
```
