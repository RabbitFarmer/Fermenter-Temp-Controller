# Fix Summary: Reduce Kasa Plug Polling Frequency

## Issue
Kasa smart plugs were being sent redundant ON/OFF commands every temperature control loop iteration (every 2 minutes by default), even when the plug was already in the desired state. This resulted in unnecessary network traffic, excessive wear on plug relays, and noisy activity logs.

### Evidence from User's Log
```
{"timestamp": "2026-02-04T03:11:24.788340Z", "local_time": "2026-02-03 22:11:24", "mode": "heating", "url": "192.168.1.208", "action": "on", "success": true}
{"timestamp": "2026-02-04T03:11:24.081551Z", "local_time": "2026-02-03 22:11:24", "mode": "heating", "url": "192.168.1.208", "action": "on"}
{"timestamp": "2026-02-04T03:10:24.769053Z", "local_time": "2026-02-03 22:10:24", "mode": "heating", "url": "192.168.1.208", "action": "on", "success": true}
{"timestamp": "2026-02-04T03:10:24.079488Z", "local_time": "2026-02-03 22:10:24", "mode": "heating", "url": "192.168.1.208", "action": "on"}
```

The log shows "on" commands being sent every minute, even though the heater was already on.

## Root Cause
The `_is_redundant_command()` function in `app.py` had a 30-second timeout for blocking redundant commands. Since the temperature control loop runs every 120 seconds (2 minutes) by default, this timeout was always exceeded, causing redundant commands to be sent on every loop iteration.

```python
# OLD CODE (line 2372)
if time_since_last >= 30:  # 30 seconds for state recovery
    return False  # Allow redundant command
```

## Solution
Increased the redundancy check timeout from 30 seconds to 10 minutes (600 seconds). This ensures:

1. **Redundant commands are blocked** for the vast majority of control loop iterations
2. **State recovery is still possible** if the plug gets out of sync (manual intervention, power loss, etc.)
3. **The timeout is long enough** to cover various temperature control interval configurations (1-5 minutes)

```python
# NEW CODE (line 2374)
if time_since_last >= 600:  # 10 minutes for state recovery
    return False  # Allow for state verification
```

## Impact

### Before Fix
- **Control loop interval:** 2 minutes
- **Redundancy timeout:** 30 seconds
- **Result:** Commands sent on EVERY loop iteration (6 commands in 12 minutes)

### After Fix
- **Control loop interval:** 2 minutes  
- **Redundancy timeout:** 10 minutes
- **Result:** Command sent once, then blocked for ~5 loops (1 command in 12 minutes)

### Improvement
- **83% reduction** in Kasa plug polling
- Significantly reduced network traffic
- Reduced wear on smart plug relays
- Cleaner activity logs
- Maintains all safety and control functionality
- Still allows periodic state verification (every 10 minutes)

## Testing
Created comprehensive tests:

1. **test_redundant_kasa_polling.py** - Unit tests for the `_is_redundant_command()` function
   - Validates redundant commands are blocked within 10 minutes
   - Validates state-changing commands are never blocked
   - Validates state recovery after 10 minutes

2. **demo_kasa_polling_fix.py** - Integration test demonstrating before/after behavior
   - Shows 83% reduction in polling over 12-minute simulation
   - Demonstrates expected behavior in real-world usage

## Files Changed
- `app.py` - Updated `_is_redundant_command()` timeout from 30s to 600s
- `test_redundant_kasa_polling.py` - New unit tests
- `demo_kasa_polling_fix.py` - New demonstration script

## Security
- No security vulnerabilities introduced
- No changes to control logic or safety mechanisms
- State verification still occurs periodically for recovery

## Backward Compatibility
- Fully backward compatible
- No configuration changes required
- Works with all existing temperature control interval settings
