# System Settings Interval Variables - Explained

This document explains the interval variables in System Settings and what each one controls.

## The Two Interval Variables

After reviewing the code and cleaning up unused settings, there are **TWO** interval variables that control different aspects of the system:

### 1. Update Interval (minutes)
**Default:** 2 minutes  
**Location:** System Settings → Main Settings tab  
**Controls:**
- How often the temperature control loop runs
- How often temperature readings are logged to the chart
- How often control tilt readings are logged

**Why it works this way:**
- The temperature control loop (`periodic_temp_control()`) runs every `update_interval` minutes
- Each time the loop runs, it:
  1. Reads current temperature from the assigned Tilt
  2. Runs control logic to decide whether to turn heating/cooling on or off
  3. Logs the temperature reading to the in-memory buffer
  4. Sleeps for `update_interval` minutes

**Typical usage:**
- Default: 2 minutes for responsive temperature control
- You want this fairly short so the system reacts quickly to temperature changes
- Shorter interval = more responsive control, more data points on charts
- Longer interval = less responsive control, fewer data points

---

### 2. Tilt Reading Logging Interval (minutes)
**Default:** 15 minutes  
**Location:** System Settings → Main Settings tab  
**Setting name:** `tilt_logging_interval_minutes`  
**Controls:**
- How often to log Tilt hydrometer readings for fermentation tracking
- Applies to non-control tilts (fermentation monitoring only)
- Logs gravity, temperature, and other fermentation data

**Why it works this way:**
- Fermentation tracking doesn't need frequent updates (gravity changes slowly)
- Logging every 15 minutes instead of every 2 minutes reduces data storage
- Different tilts can be used for different purposes:
  - **Control tilt:** Logs at `update_interval` (2 min) for responsive control
  - **Fermentation tilts:** Log at `tilt_logging_interval_minutes` (15 min) for history

**Typical usage:**
- Default: 15 minutes is good for fermentation tracking
- Longer interval is fine since gravity changes slowly over days/weeks
- Reduces storage and makes fermentation charts cleaner

---

## What Was Removed

### temp_logging_interval (REMOVED)
This field appeared in the UI but was **never used** in the code. It created confusion about what controlled temperature logging.

**Why it was removed:**
- It was unused - no code referenced it
- Having three intervals was unnecessarily complex
- Users assumed it controlled temperature logging, but `update_interval` actually did
- Removing it makes the system simpler and clearer

---

## Summary

| Variable | Default | Controls |
|----------|---------|----------|
| `update_interval` | 2 min | Temperature control loop frequency AND logging |
| `tilt_logging_interval_minutes` | 15 min | Fermentation tilt logging frequency |

**Key Insight:** The control loop runs frequently (2 min) for responsive heating/cooling control, while fermentation data is logged less frequently (15 min) since gravity changes slowly.

---

## Technical Details

### Temperature Control Loop Flow
```python
while True:
    # Read current temperature from control tilt
    # Run control logic (heating/cooling decisions)
    # Log temperature reading
    sleep(update_interval * 60)  # Sleep for update_interval minutes
```

### Tilt Reading Rate Limiting
```python
# Control tilt (used for temperature control)
if tilt_is_control_tilt:
    log_interval = update_interval  # 2 minutes - responsive

# Fermentation tilt (monitoring only)
else:
    log_interval = tilt_logging_interval_minutes  # 15 minutes - historical
```

This ensures control tilts log frequently for temperature control, while fermentation tilts log less frequently to reduce data volume.
