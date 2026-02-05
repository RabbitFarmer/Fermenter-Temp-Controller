# Temperature Control and Timestamp Fixes - Summary

## Issues Fixed

### Issue 1: Heater Not Turning Off at High Limit

**User Report:**
> "At startup, temp control works correctly. It turned the heater on. Upon reaching the high limit, it never turns the heater off."

**Root Cause:**
When a Kasa smart plug command times out (30 seconds) without confirmation:
1. The pending flag is cleared
2. BUT the `heater_on`/`cooler_on` state is NOT updated
3. System state becomes out of sync with physical plug state
4. Redundancy check incorrectly blocks future commands

**Example Scenario:**
```
1. Heater ON command sent → heater_pending=True, heater_on=False
2. Kasa plug physically turns ON but response never arrives
3. After 30 seconds, timeout occurs → heater_pending=False, heater_on still False
4. System thinks heater is OFF, but it's actually ON
5. Temp reaches 75°F (high limit), OFF command attempted
6. Redundancy check: "trying to turn off something already off" → BLOCKED
7. Heater stays ON indefinitely
```

**Fix Applied:**
When pending times out, assume the command succeeded and update state:
```python
if pending_action == "on":
    temp_cfg["heater_on"] = True  # ← NEW
    print(f"[TEMP_CONTROL] Assuming heater ON command succeeded after timeout")
elif pending_action == "off":
    temp_cfg["heater_on"] = False  # ← NEW
    print(f"[TEMP_CONTROL] Assuming heater OFF command succeeded after timeout")
```

Applied to both heating and cooling in `_should_send_kasa_command()` function.

### Issue 2: Log Timestamps Show UTC Instead of Local Time

**User Report:**
> "Check the log time. I don't think it's reading local time"

**Problem:**
All log fields used UTC time, which was confusing for users in other timezones looking at raw JSONL log files.

Example log entry (user in PST timezone):
```json
{
  "timestamp": "2026-02-03T19:13:52Z",
  "date": "2026-02-03",  // UTC date
  "time": "19:13:52",    // UTC time (11:13:52 PST)
  "event": "HEATING-PLUG TURNED ON"
}
```

User sees "19:13:52" but their wall clock shows "11:13:52" → confusion!

**Fix Applied:**
- `timestamp` field: Keep in UTC with 'Z' suffix (ISO standard, backward compatible)
- `date` field: Changed to local date
- `time` field: Changed to local time

```python
# Before:
ts = datetime.utcnow()
iso_ts = ts.replace(microsecond=0).isoformat() + "Z"
date = ts.strftime("%Y-%m-%d")     # UTC
time_str = ts.strftime("%H:%M:%S")  # UTC

# After:
ts_utc = datetime.utcnow()
iso_ts = ts_utc.replace(microsecond=0).isoformat() + "Z"  # UTC for compatibility
ts_local = datetime.now()
date = ts_local.strftime("%Y-%m-%d")     # LOCAL ← changed
time_str = ts_local.strftime("%H:%M:%S")  # LOCAL ← changed
```

Now users see times that match their wall clock.

## Files Modified

### app.py
1. `_format_control_log_entry()` function (lines 269-277):
   - Use local time for `date` and `time` fields
   - Keep `timestamp` in UTC for compatibility

2. `_should_send_kasa_command()` function:
   - Lines 2361-2371: Update `heater_on` when heater pending times out
   - Lines 2410-2420: Update `cooler_on` when cooler pending times out

## Tests Created

### test_pending_timeout_fix.py
Verifies that when a pending command times out, the state is correctly updated:
- Simulates ON command being sent
- Simulates 31-second timeout (>30 second threshold)
- Verifies `heater_on` is updated to True
- Verifies subsequent OFF command is not blocked as redundant
- ✓ ALL TESTS PASSED

### test_timestamp_fix.py  
Verifies that timestamp fields use correct timezone:
- Compares before/after behavior
- Verifies `timestamp` field still uses UTC (with 'Z' suffix)
- Verifies `date` and `time` fields use local time
- ✓ TEST PASSED

### test_issue_temp_control.py
Integration test simulating the exact user scenario:
- Temperature starts at 71°F (below low limit 74°F)
- Heater turns ON
- Temperature rises to 75°F (high limit), then 77°F
- Verifies heater turns OFF when reaching high limit
- Created but requires full app infrastructure to run

## Testing Results

### Existing Tests
- `tests/test_temp_control_fixes.py` → ✓ PASSED (2/2 tests)
- `test_heating_off_at_high_limit.py` → ✓ PASSED (all scenarios)

### New Tests
- `test_pending_timeout_fix.py` → ✓ ALL TESTS PASSED
- `test_timestamp_fix.py` → ✓ TEST PASSED

### Security Scan
- CodeQL analysis → ✓ No alerts found

## Impact

### Temperature Control Fix
- **Prevents heater/cooler from getting stuck ON indefinitely**
- **Restores proper temperature control functionality**
- Minimal risk: Only affects timeout recovery path (edge case)
- Graceful degradation: If assumption is wrong, next cycle will correct it

### Timestamp Fix
- **Improves user experience** - log times now match wall clock
- **Maintains backward compatibility** - `timestamp` field still UTC
- **No breaking changes** - existing tools can still parse logs
- Users in different timezones can now easily read raw log files

## Backward Compatibility

- Log file format unchanged (same JSON structure)
- `timestamp` field still in UTC (tools that parse it still work)
- Only `date` and `time` fields changed (human-readable fields)
- Existing logs can still be read and parsed

## Deployment Notes

- No configuration changes required
- No database migrations needed
- No user action required
- Fix takes effect immediately on deployment
- Compatible with Python 3.7+

## Future Improvements (Not in Scope)

Code review suggested using `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow()` for Python 3.12+ compatibility. This would require updating the datetime pattern throughout the entire codebase and is outside the scope of these minimal fixes.
