# Temperature Control Log Management

This document describes how the temperature control logging system works and how to manage the logs.

## Log Files

### Main Log File
- **Location**: `temp_control/temp_control_log.jsonl`
- **Format**: JSON Lines (one JSON object per line)
- **Contains**: All temperature control events including:
  - Temperature readings
  - Heating/Cooling plug on/off events
  - Mode changes
  - Temperature limit violations
  - Control start/stop events

### Log Entry Format
Each entry in `temp_control_log.jsonl` contains:
```json
{
  "timestamp": "2026-01-20T10:30:45Z",
  "date": "2026-01-20",
  "time": "10:30:45",
  "tilt_color": "Black",
  "brewid": "BREW123",
  "low_limit": 64.0,
  "current_temp": 68.0,
  "temp_f": 68.0,
  "gravity": 1.052,
  "high_limit": 66.0,
  "event": "HEATING-PLUG TURNED ON"
}
```

## Log Management Options

### 1. Archive and Start New Session (Recommended)
When you turn ON the temperature control monitor, you'll be prompted to choose:
- **New Session**: Archives the current log to `/logs` directory and starts fresh
  - Archived filename format: `temp_control_{tilt_color}_{timestamp}.jsonl`
  - Example: `temp_control_Black_20260120_103045.jsonl`
  - Use this when starting a new fermentation batch

### 2. Continue Existing Session
- **Existing**: Continues appending to the current log
- Use this when resuming monitoring of the same batch after a brief pause

### 3. Manual Reset/Clear
The existing `/reset_logs` endpoint can be used to manually clear the log:
- **Endpoint**: POST to `/reset_logs`
- **Action**: 
  1. Backs up current `temp_control_log.jsonl` to `temp_control_log.jsonl.{timestamp}.bak`
  2. Creates a new empty log file
- **When to use**: When you want to manually clear the log without starting monitoring

## Export Functionality

### CSV Export
You can export the temperature control log to CSV format:
- **From UI**: Click the "Export CSV" button on the Fermenter chart page
- **Export Location**: Files are saved to `/export` directory
- **Filename format**: `temp_control_{timestamp}.csv`
- **Contains**: All logged events with columns for timestamp, date, time, tilt_color, brewid, temperatures, limits, and event types

## Viewing the Data

### Chart View
- Navigate to the Fermenter chart from the main dashboard
- The chart displays:
  - Temperature line graph (blue)
  - Heating ON markers (red triangles pointing up)
  - Heating OFF markers (pink triangles pointing down)
  - Cooling ON markers (blue squares)
  - Cooling OFF markers (light blue squares)
- No gravity axis is shown (temperature control doesn't monitor gravity)

### Raw Log Access
The JSONL file can be viewed directly:
```bash
cat temp_control/temp_control_log.jsonl
tail -f temp_control/temp_control_log.jsonl  # Live monitoring
```

## Archive Location
All archived logs are stored in:
- **Directory**: `/logs`
- **Purpose**: Historical record of previous monitoring sessions
- **Retention**: Not automatically deleted; manage manually as needed

## Best Practices

1. **Start New Session** when beginning a new fermentation batch
2. **Use Existing** when temporarily pausing and resuming the same batch
3. **Export regularly** to CSV for backup and analysis in spreadsheet software
4. **Archive old logs** periodically to keep the `/logs` directory manageable
5. **Check brewid** in log entries to verify which batch is being monitored

## Troubleshooting

### Log file not found
- The log file is created automatically when temperature control is enabled
- Check that `/temp_control` directory exists and is writable

### Archive failed
- Verify `/logs` directory exists and is writable
- Check disk space availability

### Export failed  
- Verify `/export` directory exists and is writable
- Check that temp_control_log.jsonl is readable
