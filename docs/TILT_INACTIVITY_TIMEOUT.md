# Quick Reference: Tilt Inactivity Timeout

## What Changed?
Tilts that haven't sent data for a while (default: 60 minutes) are now automatically hidden from the main display.

## Why?
Previously, if a Tilt stopped working (dead battery, out of range, etc.), it would remain on the display indefinitely showing stale data. This fix ensures only active Tilts are shown.

## Configuration

Edit `config/system_config.json` to adjust the timeout:

```json
{
  "tilt_inactivity_timeout_minutes": 60
}
```

### Recommended Values
- **15 minutes**: Quick detection (good for testing/debugging)
- **30 minutes**: Normal detection
- **60 minutes**: Default (recommended)
- **120 minutes**: Extended (for Tilts with slow reporting)

## How It Works

1. When a Tilt broadcasts data via Bluetooth, the timestamp is recorded
2. Every time the display refreshes, it checks each Tilt's timestamp
3. Tilts with timestamps older than the timeout are hidden
4. When the Tilt starts broadcasting again, it reappears immediately

## Example Timeline

With default 60 minute timeout:

```
10:00 AM - Red Tilt broadcasts data → SHOWN on display
10:30 AM - Red Tilt stops broadcasting (battery dies)
11:00 AM - Red Tilt still SHOWN (30 minutes since last reading)
11:30 AM - Red Tilt HIDDEN from display (60 minutes since last reading)
12:00 PM - Red Tilt still hidden
...
2:00 PM - Replace battery, Red Tilt starts broadcasting → SHOWN again
```

## What's Not Affected

- **Logging**: All data is still logged to files
- **Temperature Control**: Temperature control continues to work
- **Historical Data**: Charts and reports still show all historical data
- **Notifications**: Signal loss notifications still work

Only the **display** filters out inactive Tilts.

## Troubleshooting

### Tilt disappeared from display
- Check if it's been more than 60 minutes since last reading
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
- Default: 60 minutes
- Timestamp format: ISO 8601 UTC

See `FIX_SUMMARY_TILT_INACTIVE.md` for complete technical details.
