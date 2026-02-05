# Auto-Start Fix - Multiprocessing Initialization Issue

## Problem Statement

After implementing Kasa plug reliability improvements (specifically adding `multiprocessing.set_start_method('fork')` for better network access), the auto-start functionality was broken. The application would fail to start properly at boot time.

## Root Cause

The issue occurred because:

1. **Module-level initialization**: `multiprocessing.set_start_method('fork')` was being called at module import time (outside `if __name__ == '__main__'`)
2. **Werkzeug reloader conflict**: When Flask runs (especially in debug mode), werkzeug's reloader imports the module multiple times
3. **RuntimeError**: `multiprocessing.set_start_method()` can only be called once per process - the second call raises `RuntimeError: context has already been set`
4. **Thread race conditions**: Background threads (kasa_result_listener, periodic_temp_control, etc.) were starting before `kasa_queue` and `kasa_result_queue` were initialized, causing `NoneType` errors

## The Fix

### 1. Move Multiprocessing Initialization to Main Block

**Before:**
```python
# At module level (lines 526-547)
try:
    available_methods = multiprocessing.get_all_start_methods()
    if 'fork' in available_methods:
        if multiprocessing.get_start_method(allow_none=True) is None:
            multiprocessing.set_start_method('fork')
    # ...
except RuntimeError as e:
    print(f"[LOG] Could not set multiprocessing start method: {e}")

kasa_queue = Queue()
kasa_result_queue = Queue()
# ... start kasa worker ...
```

**After:**
```python
# At module level (lines 530-532) - just declare as None
kasa_queue = None
kasa_result_queue = None
kasa_proc = None

# In if __name__ == '__main__' block (lines 5674-5702)
if __name__ == '__main__':
    # Set multiprocessing start method FIRST
    try:
        available_methods = multiprocessing.get_all_start_methods()
        if 'fork' in available_methods:
            if multiprocessing.get_start_method(allow_none=True) is None:
                multiprocessing.set_start_method('fork')
        # ...
    except RuntimeError as e:
        print(f"[LOG] Could not set multiprocessing start method: {e}")
    
    # Then initialize queues
    kasa_queue = Queue()
    kasa_result_queue = Queue()
    # ... then start worker and threads ...
```

### 2. Move All Thread Starts to Main Block

All background threads that were starting at module level were moved into `if __name__ == '__main__'`:

- `kasa_result_listener` - Processes results from kasa worker
- `periodic_temp_control` - Manages temperature control loop
- `periodic_batch_monitoring` - Monitors batches for issues
- `ble_loop` - Scans for Tilt hydrometers
- `_background_startup_sync` - Syncs plug states at startup

**Critical:** These threads must start AFTER `kasa_queue` and `kasa_result_queue` are initialized, or they will crash with `NoneType` errors.

### 3. Correct Initialization Order in Main Block

```python
if __name__ == '__main__':
    # 1. Set multiprocessing start method
    multiprocessing.set_start_method('fork')
    
    # 2. Create queues
    kasa_queue = Queue()
    kasa_result_queue = Queue()
    
    # 3. Start kasa_result_listener (consumes from kasa_result_queue)
    threading.Thread(target=kasa_result_listener, daemon=True).start()
    
    # 4. Start kasa_worker process (produces to kasa_result_queue)
    kasa_proc = Process(target=kasa_worker, args=(kasa_queue, kasa_result_queue))
    kasa_proc.start()
    
    # 5. Start other threads (may use kasa_queue)
    threading.Thread(target=periodic_temp_control, daemon=True).start()
    threading.Thread(target=periodic_batch_monitoring, daemon=True).start()
    threading.Thread(target=ble_loop, daemon=True).start()
    threading.Thread(target=_background_startup_sync, daemon=True).start()
    
    # 6. Start Flask
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
```

## Why This Works

### Understanding `if __name__ == '__main__'`

This is a module-level if statement, NOT a function. Therefore:

- Assignments inside this block **directly modify module-level variables**
- **NO `global` keyword is needed or allowed**
- Variables assigned here are accessible to all module-level functions

### Python Scoping Test

```python
x = None  # module level

if __name__ == '__main__':
    x = "modified"  # Modifies module-level x directly

print(x)  # Prints "modified"
```

This is different from inside a function, where you WOULD need `global`:

```python
x = None  # module level

def modify_x():
    global x  # Required in a function
    x = "modified"
```

### Why Werkzeug Reloader No Longer Breaks

- **Before**: Module import time initialization meant werkzeug's reload triggered the code again → RuntimeError
- **After**: Initialization only happens in `if __name__ == '__main__'` → Only runs in the main process, not during module imports

## Testing Results

### 1. Normal Startup (SKIP_BROWSER_OPEN=1)
```
[LOG] Set multiprocessing start method to 'fork' for network access
[LOG] Started kasa_result_listener thread
[LOG] Started kasa_worker process
[LOG] kasa_worker process is running and ready
[LOG] Started periodic_temp_control thread
[LOG] Started periodic_batch_monitoring thread
[LOG] Started ble_loop thread
[LOG] Started background_startup_sync thread
* Serving Flask app 'app'
* Debug mode: off
```
✅ No NoneType errors
✅ All threads start in correct order

### 2. Debug Mode (FLASK_DEBUG=1)
```
[LOG] Set multiprocessing start method to 'fork' for network access
[LOG] Started kasa_result_listener thread
...
* Debug mode: on
```
✅ No multiprocessing RuntimeError
✅ Werkzeug reloader works correctly

### 3. start.sh Script
```
=== Fermenter Temp Controller Startup ===
Checking for virtual environment...
...
Application started with PID 4225
Waiting for application to respond on http://127.0.0.1:5000...
✓ Application is responding!
```
✅ Auto-start works correctly

## Impact on Kasa Functionality

**NONE** - All Kasa plug functionality is preserved:

- `multiprocessing.set_start_method('fork')` still happens (just in correct context)
- Kasa worker process still starts with fork method
- Network access in worker is maintained
- All retry logic and reliability improvements remain intact

The fix only changes WHEN and WHERE initialization happens, not WHAT gets initialized.

## Files Modified

- `app.py`: 
  - Lines 530-532: Initialize kasa variables as None at module level
  - Lines 5668-5739: Move all initialization into `if __name__ == '__main__'` block
  - Lines 2908, 3008, 3136, 3187, 3210: Removed thread starts from module level

## Related Issues

This fix addresses the auto-start regression introduced when fixing Kasa plug reliability issues. The Kasa fixes remain fully functional while auto-start is restored.

## Key Takeaways

1. **Module-level code runs on every import** - Use `if __name__ == '__main__'` for initialization
2. **multiprocessing.set_start_method() must be in main** - Can only be called once
3. **Initialize dependencies before starting threads** - Avoid race conditions
4. **`if __name__ == '__main__'` is not a function** - No `global` keyword needed
5. **Test with werkzeug reloader** - Use FLASK_DEBUG=1 to catch import issues
