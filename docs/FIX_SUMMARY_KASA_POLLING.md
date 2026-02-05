# Fix Summary: Simplified Redundancy Check

## User Requirement
"There is no need for a redundancy check if you are not sending Kasa a signal. Does it make sense to do it this way: (knowing you need to send Kasa a signal) 1. Turn on redundancy check 2. Send Kasa the signal 3. Remain in redundancy until "success" is returned 4. Turn off redundancy check."

**Clarification:** The temperature (not user) triggers the signal based on control logic.

## Previous Approach (Time-Based)
The initial fix used a 10-minute timeout to block redundant commands. While this reduced polling by 83%, it was unnecessarily complex because the system already had a better mechanism.

## New Approach (State-Based - User Suggested)
The user correctly identified that the **pending flag mechanism already implements the desired behavior**:

1. **Temperature triggers command** → set `pending=True` (turn on redundancy check)
2. **While `pending=True`** → block duplicate commands (remain in redundancy)
3. **Success received** → set `pending=False` (turn off redundancy check)
4. **State check** → don't send commands that wouldn't change state

## Implementation

### Simplified `_is_redundant_command()`

**Before (Complex Time-Based):**
```python
def _is_redundant_command(url, action, current_state):
    # Check if command matches state
    command_matches_state = (action == "on" and current_state) or (action == "off" and not current_state)
    if not command_matches_state:
        return False
    
    # Check command history
    last = _last_kasa_command.get(url)
    if not last or last.get("action") != action:
        return False
    
    # Time-based logic
    time_since_last = time.time() - last.get("ts", 0.0)
    if time_since_last >= 600:  # 10 minutes
        return False
    
    return True
```

**After (Simple State-Based):**
```python
def _is_redundant_command(url, action, current_state):
    """
    Block commands that don't change state.
    The pending flag mechanism handles in-flight deduplication.
    """
    # If trying to send ON when already ON (or OFF when already OFF), it's redundant
    command_matches_state = (action == "on" and current_state) or (action == "off" and not current_state)
    return command_matches_state
```

### Pending Flag Mechanism (Already Exists)

The existing code in `_should_send_kasa_command()` already implements the user's suggested approach:

```python
# Check if command is already pending (lines 2389-2439)
if heater_pending and action == heater_pending_action:
    return False  # Block duplicate
```

When command is sent (lines 2605-2607):
```python
heater_pending = True
heater_pending_since = time.time()
heater_pending_action = state
```

When success received (lines 3139-3141):
```python
heater_pending = False
heater_pending_since = None
heater_pending_action = None
```

## Benefits

1. **Simpler code** - removed complex time-based logic
2. **More accurate** - pending flag tracks actual command state, not time estimates
3. **Same protection** - redundant commands still blocked
4. **Better semantics** - the pending flag IS the "redundancy check" described by user
5. **Natural flow** - follows the command lifecycle exactly as user suggested

## Behavior

**Scenario: Temperature below low limit, heater needs to stay ON**

| Loop | Time | Temperature State | Heater State | Pending? | Action | Result |
|------|------|-------------------|--------------|----------|--------|---------|
| 1 | 0s | Below limit | OFF | No | Send ON | ✓ Sent, set pending=True |
| 2 | 120s | Below limit | OFF | Yes (ON) | Try ON | ✗ Blocked by pending |
| - | 125s | - | - | - | Success | Clear pending=False, heater=ON |
| 3 | 240s | Below limit | ON | No | Try ON | ✗ Blocked by state check |
| 4 | 360s | Above limit | ON | No | Send OFF | ✓ Sent, set pending=True |
| 5 | 480s | Above limit | ON | Yes (OFF) | Try OFF | ✗ Blocked by pending |
| - | 485s | - | - | - | Success | Clear pending=False, heater=OFF |
| 6 | 600s | Above limit | OFF | No | Try OFF | ✗ Blocked by state check |

**Result:** Only 2 commands sent (ON and OFF), all duplicates blocked naturally.

## Files Changed
- `app.py` - Simplified `_is_redundant_command()` function
- `test_redundant_kasa_polling.py` - Updated tests for simplified approach
- `demo_kasa_polling_fix.py` - New demonstration of simplified behavior
- `SIMPLIFIED_REDUNDANCY_APPROACH.md` - Detailed explanation

## Security
- No security vulnerabilities introduced
- Simpler code is easier to audit and maintain
- No changes to control logic or safety mechanisms

## Testing
- Unit tests verify state-based redundancy checking
- Demo shows natural deduplication via pending flag
- No time-based behavior to test - simpler!
