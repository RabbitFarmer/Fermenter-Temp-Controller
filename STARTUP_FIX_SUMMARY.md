# Startup Issues Fix Summary

## Problem Statement

The user reported two startup issues:

1. **Application doesn't start automatically on boot**: After power-on, the application doesn't start automatically. The user had to manually run `./start.sh` to start the application.

2. **Heating/cooling status not synchronized at startup**: When the application starts, it displays the last recorded state from the config file rather than querying the actual plug state. For example, it showed "heating is on" but the actual plug was off.

## Root Causes

### Issue 1: No Automatic Startup
The repository included instructions for setting up a systemd service in INSTALLATION.md, but:
- No systemd service file template was provided
- The instructions were buried in the "Optional" section
- Users had to manually type the service file content

### Issue 2: Stale State at Startup
The application stored `heater_on` and `cooler_on` flags in `temp_cfg` which were persisted to the config file. On startup:
- These flags were loaded from the config file
- The actual plug states were never queried
- The UI displayed the stale state until the next control loop cycle

## Solutions Implemented

### 1. Automatic Startup Solution

**Created `fermenter.service` file**:
- Systemd service template included in repository
- Uses `.venv` virtual environment (created by setup.sh)
- Includes `After=network.target bluetooth.service` to ensure dependencies are ready
- Configures automatic restart on failure (`Restart=always`)
- Adds 10-second delay between restarts (`RestartSec=10`)

**Enhanced Documentation**:
- Updated INSTALLATION.md with comprehensive systemd setup guide
- Added "Running on System Startup (Recommended)" section to README.md
- Included service management commands (start, stop, restart, enable, disable)
- Added logging instructions (journalctl commands)

### 2. Plug State Synchronization Solution

**Added `kasa_query_state()` function in `kasa_worker.py`**:
```python
async def kasa_query_state(url):
    """
    Query the current state of a plug without changing it.
    Returns: (is_on, error) tuple
    """
```
This function queries the actual plug state without turning it on or off.

**Added `sync_plug_states_at_startup()` function in `app.py`**:
- Runs before the periodic temperature control loop starts
- Queries actual state of both heating and cooling plugs
- Updates `heater_on` and `cooler_on` flags to match reality
- Falls back to OFF state if query fails (safety-first approach)
- Logs the sync event to the control log for debugging

**Execution Flow**:
1. Application starts
2. Loads config file (may contain stale heater_on/cooler_on values)
3. **NEW**: Calls `sync_plug_states_at_startup()`
   - Queries heating plug if enabled
   - Queries cooling plug if enabled
   - Updates flags to match actual state
   - Logs sync event
4. Starts periodic temperature control loop
5. UI now displays actual state instead of stale state

## Files Modified

1. **kasa_worker.py**:
   - Added `kasa_query_state()` async function to query plug state

2. **app.py**:
   - Imported `kasa_query_state` from kasa_worker
   - Added `sync_plug_states_at_startup()` function
   - Call sync function after kasa_result_listener thread starts
   - Log startup sync events to control log

3. **INSTALLATION.md**:
   - Enhanced "Running on System Startup" section
   - Changed from "Optional" to "Recommended"
   - Added comprehensive systemd setup instructions
   - Included service management and logging commands

4. **README.md**:
   - Added "Running on System Startup (Recommended)" section
   - Quick setup instructions for systemd service
   - Link to detailed INSTALLATION.md guide

## Files Created

1. **fermenter.service**:
   - Systemd service template
   - Ready to copy to `/etc/systemd/system/`
   - Configured for user `pi` and path `/home/pi/Fermenter-Temp-Controller`
   - Uses `.venv` virtual environment

2. **test_startup_sync.py**:
   - Test script to verify sync logic
   - Tests three scenarios: plugs ON, plugs OFF, query failure
   - All tests pass ✅

## Testing

**Unit Tests**:
- Created `test_startup_sync.py` to verify sync logic
- Tests three scenarios:
  1. Both plugs ON → flags should be True
  2. Both plugs OFF → flags should be False
  3. Query fails → flags should default to False (safety)
- All tests pass ✅

**Code Quality**:
- Code review: All feedback addressed ✅
- Security scan (CodeQL): No vulnerabilities found ✅
- Python syntax validation: No errors ✅

## Safety Considerations

**Fail-Safe Behavior**:
- If plug query fails, the system assumes OFF state
- This prevents the UI from showing "heating on" when state is unknown
- Temperature control logic will re-evaluate and turn on if needed

**Logging**:
- Startup sync events are logged to `temp_control_log.jsonl`
- Console output shows sync progress for debugging
- Errors are logged with details

## User Instructions

### To Enable Automatic Startup:

```bash
# Copy the service file
sudo cp fermenter.service /etc/systemd/system/

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable fermenter
sudo systemctl start fermenter

# Check status
sudo systemctl status fermenter
```

### To Verify State Synchronization:

After the application starts, check the logs:
```bash
# Look for startup sync messages
sudo journalctl -u fermenter -n 50 | grep "Syncing plug states"
```

You should see messages like:
```
[LOG] Syncing plug states at startup...
[LOG] Heating plug state synced: OFF
[LOG] Cooling plug state synced: OFF
[LOG] Plug state synchronization complete
```

## Impact

**Before**:
- User had to manually start application after every reboot
- Heating/cooling status showed stale data until first control cycle
- Potential confusion when UI showed "heating on" but plug was off

**After**:
- Application starts automatically on boot (when systemd service is enabled)
- Heating/cooling status shows actual plug state immediately on startup
- Clear logging of sync events for troubleshooting
- Easy systemd service setup with included template

## Minimal Changes

The fix adheres to the principle of minimal changes:
- Only added new functions (no existing code modified except imports)
- Sync function runs once at startup (no performance impact)
- Systemd service is optional (doesn't affect existing manual start method)
- No changes to temperature control logic
- No database schema changes
- No breaking changes to config files
