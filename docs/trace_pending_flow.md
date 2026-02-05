# Pending State Flow Analysis

## Current Flow (with time-based redundancy):

### 1. Temperature Control Loop Decides to Send "ON" Command
- `temperature_control_logic()` → `control_heating("on")`

### 2. Check if Command Should Be Sent
- `control_heating("on")` → `_should_send_kasa_command(url, "on")`

### 3. _should_send_kasa_command Checks (in order):
   a. **Pending State Check** (lines 2389-2439):
      - If `heater_pending = True` and same action → BLOCK (line 2438-2439)
      - If `heater_pending = True` but different action → ALLOW and clear pending
      - If pending timeout exceeded → clear pending and allow
   
   b. **Redundancy Check** (lines 2492-2499):
      - Call `_is_redundant_command(url, action, heater_on)`
      - Checks if command matches current state
      - Has 600-second timeout for "state recovery"
      - **THIS IS WHAT WE NEED TO CHANGE**
   
   c. **Rate Limiting** (lines 2507-2513):
      - Prevents same command within 10 seconds

### 4. If All Checks Pass, Send Command
- `kasa_queue.put(...)` (line 2600)
- Set `heater_pending = True` (line 2605)
- Set `heater_pending_since = time.time()` (line 2606)
- Set `heater_pending_action = state` (line 2607)

### 5. Kasa Worker Processes Command
- Returns success/failure result

### 6. Result Listener Clears Pending State
- `kasa_result_listener()` receives result (line 3124)
- Clears pending flags (lines 3139-3141):
  - `heater_pending = False`
  - `heater_pending_since = None`
  - `heater_pending_action = None`

## User's Suggested Simplified Flow:

The user is saying: **Steps 3a (pending check) already does what we need!**

We should:
1. Remove the time-based redundancy check (step 3b)
2. Rely solely on:
   - Pending state (blocks duplicates while command is in-flight)
   - Actual state changes (don't send "on" when already "on")

## What _is_redundant_command Should Do (Simplified):

Instead of time-based logic, just check:
- Is the command trying to set the state to what it already is?
- If yes → redundant, block
- If no → not redundant, allow

NO time-based overrides. The pending state already handles deduplication.

