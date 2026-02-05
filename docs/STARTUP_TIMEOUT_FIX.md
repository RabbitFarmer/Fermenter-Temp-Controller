# Fix for Application Not Surviving Startup Timeout

## Problem Description

**Before retry counter was added:**
- Application started in background successfully
- Browser auto-open failed
- User could manually navigate to 127.0.0.1:5000 and app was working
- App continued running even though startup script had issues

**After retry counter was added (20, 40, 60 attempts):**
- Script would timeout waiting for app to respond
- Script would exit with `exit 1` on timeout
- The backgrounded app process would be **killed** when script exited
- App no longer running in background - manual browser access failed
- System completely non-operational

## Root Cause

The issue was in `/start.sh`:

1. **Line 33** (before fix): App was started in background with simple `&`
   ```bash
   if ! (SKIP_BROWSER_OPEN=1 python3 app.py > app.log 2>&1 &); then
   ```

2. **Line 51** (before fix): Script would hard-fail on timeout
   ```bash
   if ! curl -s http://127.0.0.1:5000 > /dev/null; then
       echo "Error: The application never responded after $((RETRIES * 2)) seconds."
       exit 1  # This kills the shell, which kills the backgrounded app!
   fi
   ```

When the script exited with `exit 1`, the backgrounded Python process was not properly detached and received a SIGHUP (hangup signal) from the terminating shell, causing it to die.

## Solution

Made two key changes to `/start.sh`:

### 1. Proper Process Detachment (Lines 30-41)

```bash
# Get the full path to python3 in the venv
PYTHON_PATH="$(which python3)"
export SKIP_BROWSER_OPEN=1

# Use nohup to make process immune to SIGHUP
nohup "$PYTHON_PATH" app.py > app.log 2>&1 &
APP_PID=$!

# Use disown to fully detach from shell job control
disown $APP_PID 2>/dev/null || true
echo "Application started with PID $APP_PID"
```

**Why this works:**
- `nohup`: Makes the process immune to SIGHUP signals
- `disown`: Removes the process from shell's job table
- Full Python path: Ensures venv Python works even after script exits
- Together: Process survives regardless of what happens to parent script

### 2. Non-Fatal Timeout (Lines 54-62)

```bash
if ! curl -s http://127.0.0.1:5000 > /dev/null; then
    echo "Warning: The application did not respond after $((RETRIES * 2)) seconds."
    echo "The application is still starting in the background (PID $APP_PID)."
    echo "You can check app.log for startup progress."
    echo "Please manually open http://127.0.0.1:5000 in your browser once it's ready."
    echo ""
    echo "To check if the app is running: curl http://127.0.0.1:5000"
    echo "To view logs: tail -f app.log"
    exit 0  # Exit successfully, don't kill the shell!
fi
```

**Why this works:**
- `exit 0` instead of `exit 1`: Script exits successfully
- App continues running in background (thanks to nohup + disown)
- User gets helpful instructions for manual access
- Restores original behavior where app runs even if browser open fails

## Result

This fix restores the original behavior where:

1. ✅ App always starts and continues running in background
2. ✅ If app responds quickly: Browser auto-opens
3. ✅ If app is slow to start: User gets helpful message, can access manually once ready
4. ✅ App never dies due to script timeout
5. ✅ User can verify app is running via PID and logs

## Testing

Verified that:
- Process with `nohup` + `disown` survives parent script exit ✓
- App continues running even when retry timeout occurs ✓
- User can manually access app after timeout ✓
- Browser auto-open works when app responds within timeout ✓

## Files Changed

- `/start.sh`: Lines 30-62
  - Added proper process detachment with nohup + disown
  - Changed timeout from fatal error to helpful warning
  - Added PID tracking and user guidance
