# Kasa Command and Response Logging

**Date**: February 4, 2026  
**Feature**: Log all Kasa plug commands and responses to `kasa_error_log.jsonl`  
**Branch**: copilot/redesign-temperature-control-system

## Overview

This feature adds comprehensive logging of all Kasa smart plug commands and responses to a dedicated JSONL log file. This provides complete visibility into the communication between the temperature control system and the physical Kasa plugs.

## Problem Statement

Previously, only Kasa errors were logged to `kasa_errors.log` (a text format log). There was no systematic logging of:
- Commands being sent to plugs (heating ON/OFF, cooling ON/OFF)
- Successful responses from plugs
- The complete communication timeline

This made it difficult to:
- Debug temperature control issues
- Understand the timing of plug operations
- Verify that commands were actually being sent and received
- Audit the system's behavior over time

## Solution Implemented

### New Log File: `logs/kasa_error_log.jsonl`

All Kasa plug commands and responses are now logged to `logs/kasa_error_log.jsonl` in JSONL (JSON Lines) format.

### What Gets Logged

**1. Commands Sent** (when `control_heating()` or `control_cooling()` sends a command):
```json
{
  "timestamp": "2026-02-04T00:29:20.067974Z",
  "mode": "heating",
  "url": "192.168.1.100",
  "action": "on"
}
```

**2. Successful Responses** (when kasa_result_listener receives success):
```json
{
  "timestamp": "2026-02-04T00:29:20.068154Z",
  "mode": "heating",
  "url": "192.168.1.100",
  "action": "on",
  "success": true
}
```

**3. Failed Responses** (when kasa_result_listener receives failure):
```json
{
  "timestamp": "2026-02-04T00:29:20.068289Z",
  "mode": "cooling",
  "url": "192.168.1.101",
  "action": "off",
  "success": false,
  "error": "Connection timeout"
}
```

## Implementation Details

### New Function: `log_kasa_command()`

Added to `logger.py`:

```python
def log_kasa_command(mode, url, action, success=None, error=None):
    """
    Log Kasa plug commands and responses to kasa_error_log.jsonl.
    
    Args:
        mode: 'heating' or 'cooling'
        url: IP address or hostname of the plug
        action: 'on' or 'off'
        success: True/False/None (None = command sent, not yet responded)
        error: Error message if command failed
    """
```

### Integration Points

**1. Command Sent** - `app.py` lines ~2579, ~2668:
```python
# In control_heating() and control_cooling()
log_kasa_command('heating', url, state)  # or 'cooling'
kasa_queue.put({'mode': 'heating', 'url': url, 'action': state})
```

**2. Response Received** - `app.py` line ~3100:
```python
# In kasa_result_listener()
log_kasa_command(mode, url, action, success=success, error=error if not success else None)
```

## Log File Format

The log file uses **JSONL (JSON Lines)** format:
- One JSON object per line
- Each line is independently parsable
- Easy to process with standard tools (`jq`, Python, etc.)
- Append-only for efficient logging

### Example Log File Contents

```jsonl
{"timestamp": "2026-02-04T00:30:04.123456Z", "mode": "heating", "url": "192.168.1.100", "action": "on"}
{"timestamp": "2026-02-04T00:30:04.234567Z", "mode": "heating", "url": "192.168.1.100", "action": "on", "success": true}
{"timestamp": "2026-02-04T00:35:12.345678Z", "mode": "heating", "url": "192.168.1.100", "action": "off"}
{"timestamp": "2026-02-04T00:35:12.456789Z", "mode": "heating", "url": "192.168.1.100", "action": "off", "success": true}
{"timestamp": "2026-02-04T00:40:22.567890Z", "mode": "cooling", "url": "192.168.1.101", "action": "on"}
{"timestamp": "2026-02-04T00:40:22.678901Z", "mode": "cooling", "url": "192.168.1.101", "action": "on", "success": false, "error": "Connection timeout"}
```

## Usage Examples

### Viewing the Log

**Display all entries:**
```bash
cat logs/kasa_error_log.jsonl | jq '.'
```

**Show only failed commands:**
```bash
cat logs/kasa_error_log.jsonl | jq 'select(.success == false)'
```

**Count commands by mode:**
```bash
cat logs/kasa_error_log.jsonl | jq -r '.mode' | sort | uniq -c
```

**Show timeline of heating commands:**
```bash
cat logs/kasa_error_log.jsonl | jq 'select(.mode == "heating") | {timestamp, action, success}'
```

### Analyzing Patterns

**Find all timeouts:**
```bash
grep "timeout" logs/kasa_error_log.jsonl | jq '.'
```

**Calculate command success rate:**
```python
import json

with open('logs/kasa_error_log.jsonl') as f:
    entries = [json.loads(line) for line in f if 'success' in json.loads(line)]
    
successes = sum(1 for e in entries if e['success'])
failures = len(entries) - successes
print(f"Success rate: {successes}/{len(entries)} = {successes/len(entries)*100:.1f}%")
```

## Benefits

### 1. Complete Audit Trail
- Every command sent is logged
- Every response received is logged
- Timestamps allow correlation with temperature changes

### 2. Debugging Aid
- Identify communication failures
- Track retry patterns
- Verify timing of plug operations

### 3. System Monitoring
- Calculate plug reliability metrics
- Detect network issues
- Track response times

### 4. Compliance & Diagnostics
- Complete history of all plug operations
- Machine-readable format for automated analysis
- Timestamps in ISO 8601 format (UTC)

## Testing

Two comprehensive test suites validate the feature:

### Unit Test: `test_kasa_command_logging.py`
- Tests the `log_kasa_command()` function directly
- Verifies JSONL format
- Validates all field types
- Tests success and failure cases

**Run:** `python3 test_kasa_command_logging.py`

### Integration Test: `test_integration_kasa_logging.py`
- Simulates complete temperature control cycles
- Tests command/response pairs
- Validates retry scenarios
- Verifies log accumulation

**Run:** `python3 test_integration_kasa_logging.py`

**Both tests:** ✓ ALL TESTS PASSED

## Files Changed

### Modified Files

1. **logger.py**
   - Added `log_kasa_command()` function
   - Implements JSONL logging to `logs/kasa_error_log.jsonl`

2. **app.py**
   - Imported `log_kasa_command` function
   - Added logging in `control_heating()` (line ~2579)
   - Added logging in `control_cooling()` (line ~2668)
   - Added logging in `kasa_result_listener()` (line ~3100)

### New Files

1. **test_kasa_command_logging.py**
   - Unit tests for logging function
   - Validates JSONL format and content

2. **test_integration_kasa_logging.py**
   - Integration tests for end-to-end logging
   - Simulates realistic temperature control scenarios

3. **KASA_COMMAND_LOGGING.md**
   - This documentation file

## Log File Location

```
Fermenter-Temp-Controller/
├── logs/
│   ├── kasa_error_log.jsonl    ← NEW: Commands and responses
│   ├── kasa_errors.log         ← OLD: Legacy error-only log
│   ├── error.log
│   └── warning.log
```

**Note:** The old `kasa_errors.log` file is still maintained for backward compatibility. It receives only error messages via the `log_error()` function, while `kasa_error_log.jsonl` receives all commands and responses.

## Backward Compatibility

✓ **Fully backward compatible**
- Existing `kasa_errors.log` continues to work
- No breaking changes to existing code
- New logging is additive only
- Falls back gracefully if logger not available

## Future Enhancements

Potential improvements for future versions:

1. **Log Rotation**: Implement automatic rotation of `kasa_error_log.jsonl` when it reaches a certain size
2. **Web UI Viewer**: Add a web page to view/filter Kasa command logs
3. **Metrics Dashboard**: Calculate and display plug reliability metrics
4. **Alerting**: Send notifications when error rate exceeds threshold
5. **Compression**: Compress old log files to save disk space

## Summary

The Kasa command and response logging feature provides:
- ✓ Complete visibility into plug communication
- ✓ Machine-readable JSONL format
- ✓ Timestamps for every operation
- ✓ Success and failure tracking
- ✓ Easy integration with analysis tools
- ✓ Comprehensive test coverage
- ✓ Backward compatibility

This feature significantly improves the system's observability and debuggability without affecting existing functionality.
