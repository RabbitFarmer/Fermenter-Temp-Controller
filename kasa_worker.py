#!/usr/bin/env python3
"""
kasa_worker.py - worker process for controlling Kasa plugs.

This worker is intended to be started as a separate Process from app.py:
    proc = Process(target=kasa_worker, args=(kasa_queue, kasa_result_queue))

Behavior:
- Monkey-patches zoneinfo.ZoneInfo to accept common timezone abbreviations
  (e.g. 'EST' -> 'America/New_York') before importing python-kasa so that
  device responses using abbreviated TZ keys don't raise ZoneInfoNotFoundError.
- Listens on cmd_queue for commands of the form:
    {'mode': 'heating'|'cooling', 'url': '<ip_or_host>', 'action': 'on'|'off'}
  Places a confirmation dict on result_queue:
    {'mode':..., 'action':..., 'success': True/False, 'url':..., 'error': '...'}
- Uses asyncio to interact with python-kasa plugs (IotPlug preferred).
"""

import os
import time
import asyncio

# Defensive TZ environment: ensure a sane TZ is available for zoneinfo fallback
os.environ.setdefault('TZ', 'UTC')
try:
    time.tzset()
except Exception:
    # tzset may not exist on some platforms (e.g., Windows), ignore
    pass

# --- Monkey-patch zoneinfo.ZoneInfo for common abbreviations ----------
try:
    import zoneinfo
    from zoneinfo import ZoneInfo as _ZoneInfo

    _ZONE_ABBREV_MAP = {
        'EST': 'America/New_York',
        'EDT': 'America/New_York',
        'CST': 'America/Chicago',
        'CDT': 'America/Chicago',
        'MST': 'America/Denver',
        'MDT': 'America/Denver',
        'PST': 'America/Los_Angeles',
        'PDT': 'America/Los_Angeles',
        'UTC': 'UTC'
    }

    class ZoneInfoAlias:
        def __new__(cls, key):
            mapped = _ZONE_ABBREV_MAP.get(key, key)
            return _ZoneInfo(mapped)

    # Apply monkeypatch so python-kasa (or other libraries) calling ZoneInfo(...)
    # get the aliasing behavior.
    zoneinfo.ZoneInfo = ZoneInfoAlias
except Exception:
    # If zoneinfo isn't available or monkeypatch fails, continue; errors will surface later.
    pass

# Now import kasa and other helpers (after zoneinfo patch)
try:
    # Prefer the new IOT API when available
    from kasa.iot import IotPlug as PlugClass  # type: ignore
    HAS_IOT = True
except Exception:
    try:
        from kasa import SmartPlug as PlugClass  # type: ignore
        HAS_IOT = False
    except Exception:
        PlugClass = None
        HAS_IOT = False

# Import application logger helper if available (non-blocking)
try:
    from logger import log_error
except Exception:
    def log_error(msg):
        # fallback logger
        try:
            print(f"[kasa_worker][ERROR] {msg}")
        except Exception:
            pass

# --- Worker implementation ---------------------------------------------
def kasa_worker(cmd_queue, result_queue):
    """
    Main loop: consume commands from cmd_queue and put confirmation dicts into result_queue.
    Each confirmation is a dict:
        {'mode': str, 'action': str, 'success': bool, 'url': str, 'error': str}
    
    Creates a persistent event loop to avoid network binding issues that occur when
    asyncio.run() creates a new event loop for each command in multiprocessing workers.
    """
    print(f"[kasa_worker] started (HAS_IOT={HAS_IOT})")
    if PlugClass is None:
        err = "kasa library not available"
        log_error(err)
        # Drain commands and return failure results so the controller doesn't hang.
        while True:
            try:
                cmd = cmd_queue.get()
                if not isinstance(cmd, dict):
                    continue
                result_queue.put({
                    'mode': cmd.get('mode', 'unknown'),
                    'action': cmd.get('action', 'off'),
                    'success': False,
                    'url': cmd.get('url', ''),
                    'error': err
                })
            except Exception:
                time.sleep(0.5)
        # unreachable

    # Create a persistent event loop for this worker process
    # This avoids network binding issues that occur when creating new loops for each command
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print(f"[kasa_worker] Created persistent event loop for worker process")

    try:
        while True:
            try:
                command = cmd_queue.get()
                if not isinstance(command, dict):
                    continue
                mode = command.get('mode', 'unknown')
                url = command.get('url', '')
                action = command.get('action', 'off')

                print(f"[kasa_worker] Received command: mode={mode}, action={action}, url={url}")
                
                if not url:
                    error = "No URL provided"
                    log_error(f"{mode.upper()} plug operation skipped: {error}")
                    result_queue.put({'mode': mode, 'action': action, 'success': False, 'url': url, 'error': error})
                    continue

                try:
                    # Use the persistent event loop instead of creating a new one with asyncio.run()
                    error = loop.run_until_complete(kasa_control(url, action, mode))
                except Exception as e:
                    error = str(e)
                    log_error(f"{mode.upper()} kasa_control run failed: {error}")

                success = (error is None)
                result = {'mode': mode, 'action': action, 'success': success, 'url': url, 'error': error}
                print(f"[kasa_worker] Sending result: mode={mode}, action={action}, success={success}, error={error}")
                result_queue.put(result)

            except Exception as e:
                # Defensive: log and sleep briefly, then continue
                try:
                    log_error(f"kasa_worker loop exception: {e}")
                except Exception:
                    print(f"[kasa_worker] loop exception (logging failed): {e}")
                time.sleep(0.5)
                continue
    finally:
        # Clean up event loop when worker exits
        try:
            loop.close()
            print(f"[kasa_worker] Event loop closed on worker shutdown")
        except Exception as e:
            print(f"[kasa_worker] Error closing event loop: {e}")

async def kasa_query_state(url):
    """
    Query the current state of a plug without changing it.
    Returns:
      (is_on, error) tuple where:
        - is_on is True/False if successful, None if failed
        - error is None on success, error string on failure
    """
    if PlugClass is None:
        return None, "kasa plug class not available"

    try:
        plug = PlugClass(url)
        await asyncio.wait_for(plug.update(), timeout=6)
        is_on = getattr(plug, "is_on", None)
        if is_on is None:
            return None, "Unable to determine plug state"
        print(f"[kasa_worker] queried state at {url}: {'ON' if is_on else 'OFF'}")
        return is_on, None
    except Exception as e:
        err = f"Failed to query plug at {url}: {e}"
        log_error(err)
        return None, err

async def kasa_control(url, action, mode):
    """
    Perform the plug action and verify resulting state.
    Returns:
      None on success
      error string on failure
    """
    if PlugClass is None:
        return "kasa plug class not available"

    # Log the command being sent
    print(f"[kasa_worker] Sending {action.upper()} command to {mode} plug at {url}")
    
    try:
        plug = PlugClass(url)
        # initial update may raise / timeout
        await asyncio.wait_for(plug.update(), timeout=6)
        
        # Log initial state before command
        initial_state = getattr(plug, "is_on", None)
        # Handle None case explicitly for clarity
        if initial_state is None:
            state_str = 'UNKNOWN'
        elif initial_state:
            state_str = 'ON'
        else:
            state_str = 'OFF'
        print(f"[kasa_worker] Initial state before {action}: {state_str} (is_on={initial_state})")
        
    except Exception as e:
        err = f"Failed to contact plug at {url}: {e}"
        log_error(err)
        return err

    try:
        # Send the command
        if action == 'on':
            print(f"[kasa_worker] Executing turn_on() for {mode} plug at {url}")
            await plug.turn_on()
        else:
            print(f"[kasa_worker] Executing turn_off() for {mode} plug at {url}")
            await plug.turn_off()

        # brief pause to let state change propagate
        await asyncio.sleep(0.5)

        # try to re-check state; best-effort
        verification_success = True
        try:
            await asyncio.wait_for(plug.update(), timeout=5)
        except Exception as e:
            # non-fatal: we'll still attempt to read is_on if available
            print(f"[kasa_worker] WARNING: State verification update failed: {e}")
            verification_success = False

        is_on = getattr(plug, "is_on", None)
        if is_on is None:
            err = "Unable to determine plug state after command"
            log_error(f"{mode.upper()} plug at {url}: {err}")
            return err

        # Log the verified state (defensive: handle None case even though we return above)
        if is_on is None:
            state_str = 'UNKNOWN'
        elif is_on:
            state_str = 'ON'
        else:
            state_str = 'OFF'
        print(f"[kasa_worker] Verified state after {action}: {state_str} (is_on={is_on}, verification_update={'success' if verification_success else 'failed'})")
        
        if (action == 'on' and is_on) or (action == 'off' and not is_on):
            print(f"[kasa_worker] ✓ SUCCESS: {mode} {action} confirmed at {url} - plug state matches expected")
            return None
        else:
            err = f"State mismatch after {action}: expected is_on={action == 'on'}, actual is_on={is_on}"
            log_error(f"{mode.upper()} plug at {url}: {err}")
            print(f"[kasa_worker] ✗ FAILURE: State verification failed for {mode} plug at {url}")
            return err

    except Exception as e:
        err = str(e)
        log_error(f"{mode.upper()} plug at {url} error during command execution: {err}")
        return err

