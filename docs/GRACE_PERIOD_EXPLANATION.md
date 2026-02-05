# Answer: Grace Period for New Batch Setup

## Your Question
> "What happens when I start up a new batch and set the temperature control for it? Does this mean I have 4 minutes to set it up starting when the tilt has been assigned before the system shuts down?"

## Answer: NO - You Have 15 Minutes!

**Good news!** When you assign a Tilt to temperature control for a new batch, you have a **15-minute grace period** before the system enforces the 4-minute safety timeout.

## How It Works

### Timeline When Starting a New Batch

```
T+0 min:  You assign Red Tilt to temperature control
          ↓
          15-minute grace period begins
          ↓
T+0-15:   You can:
          • Place Tilt in fermenter
          • Set temperature limits
          • Configure heating/cooling plugs
          • Wait for Tilt to start broadcasting
          • Complete batch setup
          ↓
          Grace period active - NO safety shutdown even if Tilt not broadcasting
          ↓
T+15 min: Grace period expires
          ↓
          Normal 4-minute safety timeout now applies
          ↓
          System checks: Has Tilt broadcast in last 4 minutes?
          • YES → Temperature control continues normally ✓
          • NO → Safety shutdown triggered (plugs turn OFF)
```

### Example Scenario

**Scenario 1: Tilt Starts Broadcasting Quickly**
```
10:00 AM - Assign Red Tilt to temp control
10:02 AM - Place Tilt in fermenter
10:05 AM - Tilt starts broadcasting (temp 68°F)
10:07 AM - Temperature control working normally ✓
           (After 15 min grace expires, Tilt is broadcasting regularly)
```

**Scenario 2: Tilt Takes Longer to Start**
```
10:00 AM - Assign Red Tilt to temp control
10:05 AM - Still setting up... (no broadcasts yet)
10:10 AM - Still setting up... (no broadcasts yet)
10:12 AM - Place Tilt in fermenter
10:14 AM - Still in grace period (14/15 minutes)
10:15 AM - Tilt starts broadcasting ✓
           Grace period expires but Tilt is now broadcasting
           Temperature control continues normally ✓
```

**Scenario 3: Tilt Never Broadcasts (Problem)**
```
10:00 AM - Assign Red Tilt to temp control
...      - Set up batch, but Tilt never broadcasts
           (Battery dead? Out of range? Not in liquid?)
10:15 AM - Grace period expires
10:16 AM - Safety shutdown triggered (no broadcasts in 4+ minutes)
           KASA plugs turn OFF ✗
           You receive notification about safety shutdown
           Fix the Tilt issue and it will resume automatically
```

## Why This Design?

### Grace Period (15 minutes)
- **Purpose**: Give you time to set up a new batch without pressure
- **Allows**: Physical setup, configuration, waiting for Tilt to initialize
- **Safety**: After grace period, normal timeout ensures rapid response to problems

### Normal Timeout (4 minutes after grace)
- **Purpose**: Rapid safety response if Tilt fails during fermentation
- **Calculation**: 2 × update_interval (default 2 min = 4 min timeout)
- **Safety**: Prevents runaway heating/cooling with stale temperature data

## Configuration

The grace period and timeout are controlled by:

```json
{
  "update_interval": 2,  // Minutes between temp control checks
                        // Timeout = 2 × this value (default: 4 minutes)
}
```

**Grace period**: Fixed at 15 minutes (not configurable)
**Normal timeout**: 2 × update_interval (configurable via update_interval)

## Key Points

✅ **15-minute grace period** when you first assign a Tilt  
✅ **No pressure** - plenty of time to set up your batch  
✅ **Automatic** - grace period starts when you assign the Tilt  
✅ **Safe** - after grace period, rapid 4-minute timeout protects your batch  
✅ **Seamless** - if Tilt is broadcasting, transition from grace to normal is invisible  

❌ **NOT** only 4 minutes - that would be too short for setup!  
❌ **NOT** permanent - grace period expires after 15 minutes  
❌ **NOT** dangerous - safety timeout still applies after grace period  

## What If You Need More Time?

If 15 minutes isn't enough for your setup:

1. **Option 1**: Assign the Tilt AFTER you've completed physical setup
   - Place Tilt in fermenter first
   - Wait for it to start broadcasting
   - Then assign it to temperature control
   - Grace period starts when you assign it

2. **Option 2**: Re-assign the Tilt to restart grace period
   - If grace period expires before Tilt broadcasts
   - Un-assign the Tilt
   - Re-assign it
   - This starts a fresh 15-minute grace period

3. **Option 3**: Use fallback mode during setup
   - Leave tilt_color empty (no assignment)
   - System uses any broadcasting Tilt
   - Once Tilt is broadcasting reliably, assign it explicitly

## Technical Details

The grace period is tracked via `tilt_assignment_time` in the temperature control config:

```python
# When you assign a Tilt:
temp_cfg["tilt_assignment_time"] = datetime.utcnow().isoformat()

# System checks:
if minutes_since_assignment < 15:
    # Grace period active - allow control even if Tilt inactive
    return True
else:
    # Grace period expired - enforce normal 4-minute timeout
    # Check if Tilt has broadcast in last 4 minutes
```

## Summary

**You have 15 minutes, not 4 minutes!**

This gives you plenty of time to:
- Set up your fermentation vessel
- Place the Tilt in the liquid
- Configure temperature control settings
- Wait for the Tilt to initialize and start broadcasting
- Complete any other batch setup tasks

After 15 minutes, the system switches to the rapid 4-minute safety timeout to protect your batch during fermentation.

This is the best of both worlds: **generous setup time** + **rapid safety response**.
