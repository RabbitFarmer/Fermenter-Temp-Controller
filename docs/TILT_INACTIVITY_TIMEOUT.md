# Quick Reference: Tilt Inactivity Timeout

## What Changed?
Tilts that haven't sent data for a while (default: 30 minutes) are now automatically hidden from the main display.

## Why?
Previously, if a Tilt stopped working (dead battery, out of range, etc.), it would remain on the display indefinitely showing stale data. This fix ensures only active Tilts are shown.

## Configuration

Edit `config/system_config.json` to adjust the timeout:

```json
{
  "tilt_inactivity_timeout_minutes": 30
}
```

### Recommended Values
- **15 minutes**: Quick detection (good for testing/debugging)
- **30 minutes**: Default (recommended)
- **60 minutes**: Extended detection
- **120 minutes**: Very extended (for Tilts with slow reporting)

## How It Works

1. When a Tilt broadcasts data via Bluetooth, the timestamp is recorded
2. Every time the display refreshes, it checks each Tilt's timestamp
3. Tilts with timestamps older than the timeout are hidden
4. When the Tilt starts broadcasting again, it reappears immediately

## Example Timeline

With default 30 minute timeout:

```
10:00 AM - Red Tilt broadcasts data → SHOWN on display
10:20 AM - Red Tilt stops broadcasting (battery dies)
10:40 AM - Red Tilt HIDDEN from display (30 minutes since last reading, timeout reached)
11:00 AM - Red Tilt still hidden
...
2:00 PM - Replace battery, Red Tilt starts broadcasting → SHOWN again
```

## What's Not Affected

- **Historical Data**: Charts and reports still show all historical data from when the Tilt was active
- **Notifications**: Signal loss notifications still work as configured

## Important Note

If a Tilt is inactive (not transmitting data):
- **NO new data is being logged** - there's no data to log
- **Temperature control will not work** for that Tilt - there's no current temperature reading
- The Tilt is hidden from display until it starts transmitting again

## SAFETY FEATURE: Temperature Control Shutdown

**Critical Safety Behavior:**

If the Tilt assigned to temperature control becomes inactive (exceeds timeout):
- **ALL Kasa plugs are immediately turned OFF** (both heating and cooling)
- **A safety notification is sent** (email/push) alerting you of the shutdown
- Status changes to "Control Tilt Inactive - Safety Shutdown"
- Safety shutdown event is logged to the temperature control log
- The actual plug OFF events are also logged to the chart
- Normal operation resumes automatically when the Tilt starts transmitting again

This prevents runaway heating/cooling when the monitoring Tilt fails (dead battery, out of range, etc.).

## Troubleshooting

### Tilt disappeared from display
- Check if it's been more than 30 minutes since last reading
- Battery might be dead
- Tilt might be out of Bluetooth range
- Check Bluetooth logs for errors

### Tilt reappears and disappears
- Weak signal (borderline range)
- Consider increasing timeout or moving Raspberry Pi closer

### All Tilts gone
- Check if Bluetooth scanning is working
- Check system logs for errors
- Restart the app

## Technical Details

For developers and advanced users:

- Function: `get_active_tilts()` in `app.py`
- Affects routes: `/`, `/live_snapshot`, `/batch_settings`, `/temp_config`
- Config key: `system_cfg['tilt_inactivity_timeout_minutes']`
- Default: 30 minutes
- Timestamp format: ISO 8601 UTC

See `FIX_SUMMARY_TILT_INACTIVE.md` for complete technical details.
