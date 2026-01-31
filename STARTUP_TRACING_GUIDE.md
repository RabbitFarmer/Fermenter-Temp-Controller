# Startup Tracing and Diagnostics Guide

## Overview

The startup script (`start.sh`) now includes comprehensive tracing to help diagnose startup issues. All startup activity is automatically logged to `startup.log` for later review.

## Features

### 1. Automatic Startup Logging

Every time you run `./start.sh`, all output is saved to `startup.log`:

```bash
./start.sh
```

The log includes:
- Timestamped progress messages
- Process IDs and status
- Health check attempts
- Error messages and diagnostics
- Startup timing information

### 2. Debug Mode

For even more detailed tracing, enable DEBUG mode:

```bash
DEBUG=1 ./start.sh
```

Debug mode adds:
- Bash command tracing (`set -x`) - shows every command before execution
- Detailed debug messages with full timestamps
- Python version and path information
- Process status details
- curl command traces

### 3. Viewing Logs

**View the complete startup log:**
```bash
cat startup.log
```

**View the last startup:**
```bash
tail -50 startup.log
```

**Follow startup in real-time:**
```bash
tail -f startup.log
```

**View application log:**
```bash
tail -f app.log
```

## What Gets Traced

### Normal Mode Output

```
=======================================================================
Startup trace log - Sat Jan 31 19:18:15 UTC 2026
=======================================================================
[19:18:15] === Fermenter Temp Controller Startup ===
[19:18:15] Startup log will be saved to: startup.log
[19:18:15] Navigating to script directory...
[19:18:15] Checking for virtual environment...
[19:18:15] Activating virtual environment...
[19:18:15] Virtual environment activated.
[19:18:16] Installing dependencies from requirements.txt...
[19:18:25] Dependencies installed successfully.
[19:18:25] Starting the application...
[19:18:25] Launching app.py with nohup...
[19:18:25] Application started with PID 12345
[19:18:25] Waiting for application to respond on http://127.0.0.1:5000...
[19:18:26] Health check attempt 1/30...
[19:18:28] Health check attempt 2/30...
[19:18:30] Health check attempt 3/30...
[19:18:32] ✓ Application is responding! (after 7s)
[19:18:32] Opening the application in your default browser...
[19:18:32] Browser launched with xdg-open
=======================================================================
[19:18:32] ✓ Startup completed successfully!
=======================================================================
  Application PID: 12345
  Total startup time: 7 seconds
  Access dashboard: http://127.0.0.1:5000
  Startup log saved: startup.log
  Application log: app.log
=======================================================================
```

### Debug Mode Output (Additional Information)

```
[DEBUG] Debug mode enabled - all commands will be traced
+ log_step '=== Fermenter Temp Controller Startup ==='
[DEBUG 2026-01-31 19:18:15] Script: ./start.sh
[DEBUG 2026-01-31 19:18:15] Working directory: /home/user/app
[DEBUG 2026-01-31 19:18:15] Script directory: /home/user/app
[DEBUG 2026-01-31 19:18:15] Current directory: /home/user/app
[DEBUG 2026-01-31 19:18:15] Virtual environment already exists at .venv
[DEBUG 2026-01-31 19:18:15] Sourcing .venv/bin/activate
[DEBUG 2026-01-31 19:18:15] Python path: /home/user/app/.venv/bin/python3
[DEBUG 2026-01-31 19:18:15] Python version: Python 3.9.2
[DEBUG 2026-01-31 19:18:15] Pip version: pip 20.3.4
[DEBUG 2026-01-31 19:18:15] Python path for app: /home/user/app/.venv/bin/python3
[DEBUG 2026-01-31 19:18:15] Setting SKIP_BROWSER_OPEN=1
[DEBUG 2026-01-31 19:18:15] Command: nohup /home/user/app/.venv/bin/python3 app.py > app.log 2>&1 &
[DEBUG 2026-01-31 19:18:15] Process status:
  PID  PPID STAT CMD
12345  1234 S    python3 app.py
[DEBUG 2026-01-31 19:18:15] Process 12345 is running
[DEBUG 2026-01-31 19:18:26] Running: curl -s http://127.0.0.1:5000
[DEBUG 2026-01-31 19:18:26] App not ready yet, process still running. Waiting 2s...
```

## Troubleshooting Scenarios

### Scenario 1: App Dies Immediately

If the app process dies right after launch, you'll see:

```
[ERROR] Application process 12345 died immediately after launch!
[ERROR] Last 20 lines of app.log:
  Traceback (most recent call last):
    File "app.py", line 10, in <module>
      import missing_module
  ModuleNotFoundError: No module named 'missing_module'
```

**Action**: Check app.log for the error details.

### Scenario 2: App Dies During Health Checks

If the app crashes while waiting for it to respond:

```
[19:18:30] Health check attempt 3/30...
[ERROR] Application process 12345 died during startup!
[ERROR] Last 30 lines of app.log:
  [Log content showing the error]
```

**Action**: Review app.log to see what caused the crash.

### Scenario 3: App Times Out

If the app doesn't respond within 60 seconds:

```
=======================================================================
[WARNING] Application did not respond after 60 seconds (62s elapsed)
=======================================================================
The application is still starting in the background (PID 12345).

Process status:
  PID  PPID STAT  ELAPSED CMD
12345  1234 S     00:01:02 python3 app.py

Last 20 lines of app.log:
  [Recent log entries]

=======================================================================
TROUBLESHOOTING:
  - Check app.log for errors: tail -f app.log
  - Check startup log: cat startup.log
  - Test if app responds: curl http://127.0.0.1:5000
  - Check process: ps -p 12345
  - Try with debug mode: DEBUG=1 ./start.sh
  - Manually open browser: http://127.0.0.1:5000
=======================================================================
```

**Action**: 
1. Check if process is still running: `ps -p 12345`
2. Monitor app.log: `tail -f app.log`
3. Try to access manually after waiting longer
4. Run with DEBUG=1 for more details

## Common Commands

**Check if app is running:**
```bash
curl http://127.0.0.1:5000
```

**Check process status:**
```bash
ps aux | grep app.py
```

**View recent startup log:**
```bash
tail -100 startup.log
```

**View recent app log:**
```bash
tail -100 app.log
```

**Start with full debug tracing:**
```bash
DEBUG=1 ./start.sh 2>&1 | tee startup_debug.log
```

## Log Files

- **startup.log** - Complete trace of startup script execution
- **app.log** - Flask application output and errors  
- **temp_control/temp_control_log.jsonl** - Temperature control events

## Tips

1. **Always check startup.log first** when diagnosing startup issues
2. **Use DEBUG=1** if startup.log doesn't show enough detail
3. **Compare successful and failed startups** by reviewing startup.log from each
4. **Check timestamps** to identify slow steps
5. **Process verification** happens at multiple points to catch early crashes

## Example Workflow

When reporting a startup issue:

1. Run with debug mode:
   ```bash
   DEBUG=1 ./start.sh
   ```

2. Save the complete log:
   ```bash
   cp startup.log startup_issue_$(date +%Y%m%d_%H%M%S).log
   ```

3. Check app.log:
   ```bash
   tail -50 app.log
   ```

4. Share the logs:
   - startup.log (or startup_issue_*.log)
   - Relevant sections of app.log
   - Any error messages seen on screen

## Log Rotation

The startup.log file appends each run. To start fresh:

```bash
rm startup.log
./start.sh
```

Or to archive old logs:

```bash
mv startup.log startup_$(date +%Y%m%d_%H%M%S).log
./start.sh
```
