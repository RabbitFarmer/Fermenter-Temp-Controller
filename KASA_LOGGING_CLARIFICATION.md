# Kasa Logging Clarification

## Issue Resolution

**Issue**: kasa_errors.log was logging every kasaplug transaction every 3 seconds instead of only logging errors.

**Root Cause**: The `kasa_worker.py` module contained numerous `print()` statements that logged routine operations (successful commands, state verifications, etc.) along with actual errors.

**Solution**: Removed informational logging from `kasa_worker.py` so that `kasa_errors.log` only contains actual errors.

---

## Log File Purposes

### kasa_errors.log (logs/kasa_errors.log)

**Purpose**: Error-only logging for Kasa plug operations

**Contains**:
- Connection failures to Kasa plugs
- State verification failures
- Command execution errors
- Worker process exceptions
- Any other Kasa-related errors

**Does NOT contain**:
- Successful command executions
- Routine state queries
- Normal operation logs

**Example entries**:
```
2024-02-03 10:15:23 ERROR Failed to contact plug at 192.168.1.100: Connection timeout
2024-02-03 10:20:45 ERROR HEATING plug at 192.168.1.100: State mismatch after on: expected is_on=True, actual is_on=False
2024-02-03 11:30:12 ERROR WARNING: State verification update failed for heating plug at 192.168.1.100: Device unreachable
```

### temp_control_log.jsonl (temp_control/temp_control_log.jsonl)

**Purpose**: Temperature control event logging

**Contains**:
- `heating_on` - When heating plug is successfully turned on
- `heating_off` - When heating plug is successfully turned off
- `cooling_on` - When cooling plug is successfully turned on
- `cooling_off` - When cooling plug is successfully turned off
- `temp_below_low_limit` - Temperature below low limit
- `temp_above_high_limit` - Temperature above high limit
- `temp_in_range` - Temperature within range
- `temp_control_reading` - Periodic temperature readings
- `tilt_reading` - Tilt hydrometer samples

**Example entries**:
```json
{"timestamp": "2024-02-03T10:15:23Z", "event_type": "heating_on", "message": "HEATING-PLUG TURNED ON", "data": {"low_limit": 66.0, "current_temp": 65.5, "high_limit": 68.0, "tilt_color": "Blue"}}
{"timestamp": "2024-02-03T10:30:45Z", "event_type": "heating_off", "message": "HEATING-PLUG TURNED OFF", "data": {"low_limit": 66.0, "current_temp": 67.0, "high_limit": 68.0, "tilt_color": "Blue"}}
{"timestamp": "2024-02-03T10:35:12Z", "event_type": "temp_control_reading", "message": "TEMP CONTROL READING", "data": {"temp_f": 67.2, "tilt_color": "Blue"}}
```

---

## What Information Is Collected?

### Information in temp_control_log.jsonl (COMPREHENSIVE):
✅ **Plug state changes** (heating_on, heating_off, cooling_on, cooling_off)
✅ **Timestamps** for all events
✅ **Temperature readings** with context (current_temp, low_limit, high_limit)
✅ **Tilt color** identifying which fermenter
✅ **Event type** for filtering and analysis
✅ **Success confirmations** (logged only when state actually changes)

### Information in kasa_errors.log (ERROR-ONLY):
✅ **Connection failures** with error details
✅ **State verification failures** showing expected vs actual state
✅ **Command execution errors** with exception messages
✅ **Retry exhaustion** when all retry attempts fail
✅ **Worker process issues** for debugging

### Information NOT logged (to reduce noise):
❌ Successful individual plug commands (only state changes logged in temp_control_log.jsonl)
❌ Initial state before each command (not needed - actual state changes are logged)
❌ Verification success messages (silence = success; errors are logged)
❌ Routine retry attempts (only final failure logged if retries exhausted)
❌ Worker startup/shutdown (minimal diagnostic only)

---

## Benefits of This Approach

1. **Clear separation of concerns**:
   - `kasa_errors.log` = problems only
   - `temp_control_log.jsonl` = operational events and data

2. **Reduced log noise**:
   - No more logs every 3 seconds for routine operations
   - Easy to spot actual problems in kasa_errors.log
   - File size significantly reduced

3. **Complete audit trail**:
   - temp_control_log.jsonl provides full history of temperature control decisions
   - kasa_errors.log provides debugging information when things go wrong
   - Together they provide complete picture

4. **Performance improvement**:
   - Less I/O from reduced logging
   - Smaller log files easier to manage
   - Faster log analysis when troubleshooting

---

## Use Cases

### Monitoring Normal Operation
**Use**: temp_control_log.jsonl
- Check when heating/cooling turned on/off
- Review temperature trends
- Verify control decisions

### Troubleshooting Kasa Plug Issues
**Use**: kasa_errors.log
- Identify connection problems
- Debug state verification failures
- Track recurring errors

### Complete System Analysis
**Use**: Both logs together
- Correlate errors with control decisions
- Understand impact of failures on temperature control
- Verify retry logic effectiveness
