# Quick Start Guide: temp_control_tilt.jsonl Logging Toggle

## What Was Added

A simple on/off switch for the `temp_control_tilt.jsonl` logging feature, per your request: "Can you add an on/off switch to this one log. I will not always need it"

## How to Use It

### Step 1: Navigate to Temperature Control Settings
1. Open your web browser and go to the Fermenter App dashboard
2. Click on **"Temperature Control Settings"** (or navigate to `/temp_config`)

### Step 2: Find the Logging Options
Scroll down to the new **"Logging Options"** section. It's located:
- Below the "Enabled Actions" (Enable Heating/Cooling checkboxes)
- Above the "Heating Plug URL/ID" field

### Step 3: Toggle the Checkbox
You'll see:
```
Logging Options:
  [✓] Log Assigned Tilt to temp_control_tilt.jsonl
```

- **Check the box** = Logging is ON (your assigned Tilt's readings will be logged)
- **Uncheck the box** = Logging is OFF (no entries will be written to the log file)

### Step 4: Save Your Changes
Click the **"Save"** button at the bottom of the page.

That's it! The setting takes effect immediately.

---

## What It Does

### When ENABLED (Checkbox Checked) ✓
- The system logs your assigned Tilt's readings to `logs/temp_control_tilt.jsonl`
- Each entry includes:
  - Timestamp
  - Tilt color
  - Temperature
  - Gravity
  - Brew ID (if configured)
  - Beer name (if configured)
- Only your **explicitly assigned** Tilt is logged (not fallback Tilts)

### When DISABLED (Checkbox Unchecked)
- No entries are written to `logs/temp_control_tilt.jsonl`
- Temperature control **still works normally**
- Your assigned Tilt is **still used** for temperature control
- Only the logging is disabled

---

## Default Behavior

- **First time users**: The checkbox is **checked** by default (logging enabled)
- **Existing users**: Will default to **checked** (maintains current behavior)
- **Your choice**: You can change it anytime via the UI

---

## Important Notes

✓ Temperature control continues to function whether logging is on or off  
✓ The setting persists in your configuration (saved permanently)  
✓ Changes take effect immediately - no need to restart the application  
✓ You can toggle it on and off as many times as you want  
✓ When disabled, you'll save disk space (no log entries written)  

---

## Troubleshooting

**Q: I don't see the "Logging Options" section**  
A: Make sure you've pulled the latest changes and restarted the app. Clear your browser cache (Ctrl+F5) to ensure the latest UI is loaded.

**Q: I unchecked the box but the log file still exists**  
A: That's normal. The existing log file remains, but no NEW entries will be added. You can delete the old file if you want.

**Q: Does this affect my batch logs or other logs?**  
A: No. This only affects `temp_control_tilt.jsonl`. All other logging (batch logs, error logs, etc.) continues normally.

**Q: Will temperature control stop working if I disable logging?**  
A: No. Temperature control is completely independent of this logging. Your heater/cooler will still be controlled normally based on the assigned Tilt's temperature.

---

## Examples

### Example 1: Enable Logging During Fermentation
1. Start a new batch
2. Assign your Tilt to temperature control
3. **Check** the "Log Assigned Tilt" box
4. Save
5. Monitor fermentation with detailed logs

### Example 2: Disable Logging for Testing
1. You're just testing the system
2. Don't need log files filling up disk space
3. **Uncheck** the "Log Assigned Tilt" box
4. Save
5. Test temperature control without creating logs

### Example 3: Toggle Mid-Fermentation
1. Started fermentation with logging enabled
2. Decide you don't need more logs
3. Go to Temperature Control Settings
4. **Uncheck** the box
5. Save
6. Logging stops immediately (but fermentation continues)

---

## Questions?

The feature is designed to be simple and intuitive. If you have any questions or issues, please create a GitHub issue.

**Enjoy your new control over logging! 🍺**
