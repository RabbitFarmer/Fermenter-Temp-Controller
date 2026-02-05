# Simplified Redundancy Check Implementation

## User Requirement
"There is no need for a redundancy check if you are not sending Kasa a signal. Does it make sense to do it this way: (knowing you need to send Kasa a signal) 1. Turn on redundancy check 2. Send Kasa the signal 3. Remain in redundancy until "success" is returned. 4) Turn off redundancy check."

## Clarification
The temperature (not user) triggers the signal based on control logic:
- Temperature below low limit → trigger heating ON
- Temperature above high limit → trigger heating OFF
- Temperature within range → maintain current state

## Implementation Approach

### OLD Approach (Time-Based)
```
Temperature triggers control logic
  ↓
Check if command is redundant (time-based: allow if >10 minutes since last)
  ↓
Check if pending (block if pending)
  ↓
Send command → set pending=True
  ↓
Wait for response
  ↓
Receive success → set pending=False
```

**Problem:** Time-based logic is complex and unnecessary since pending flag already handles deduplication.

### NEW Approach (State-Based - User Suggested)
```
Temperature triggers control logic
  ↓
Check if pending (block if pending) ← This IS the redundancy check!
  ↓
Check if command changes state (block if no change needed)
  ↓
Send command → set pending=True ← "Turn on redundancy check"
  ↓
Wait for response ← "Remain in redundancy"
  ↓
Receive success → set pending=False ← "Turn off redundancy check"
```

**Benefit:** Simpler! The pending flag mechanism IS the redundancy check.

## Code Changes

### Simplified `_is_redundant_command()`
- **Before:** Complex time-based logic with 600-second timeout
- **After:** Simple state comparison - is command trying to set state to what it already is?

```python
def _is_redundant_command(url, action, current_state):
    """Block commands that don't change state."""
    # If trying to send ON when already ON (or OFF when already OFF), it's redundant
    command_matches_state = (action == "on" and current_state) or (action == "off" and not current_state)
    return command_matches_state
```

### Pending Flag Mechanism (Already Exists)
The `heater_pending` flag already implements the user's suggested approach:
1. **Before sending:** Check if `heater_pending=True` → if yes, BLOCK (line 2435-2439)
2. **When sending:** Set `heater_pending=True` (line 2605)
3. **While waiting:** All duplicate commands are blocked by pending check
4. **On success:** Set `heater_pending=False` (line 3139)

## Result

- **Simpler code** - removed complex time-based logic
- **More accurate** - pending flag tracks actual command state, not time
- **Same behavior** - redundant commands still blocked
- **Better semantics** - "pending" flag IS the "redundancy check" the user described

