# Feature Implementation: On/Off Toggle for temp_control_tilt.jsonl Logging

## Summary

Added a user-configurable toggle to enable/disable logging to the `temp_control_tilt.jsonl` file. This allows users to control when they want to log the assigned Tilt's readings, addressing the requirement: "I will not always need it".

## User Request

> "Can you add an on/off switch to this one log. I will not always need it"

## Implementation

### 1. Configuration Field
**File**: `config/temp_control_config.json.template`

Added new boolean field:
```json
"log_temp_control_tilt": true
```

- **Default**: `true` (maintains existing behavior for backward compatibility)
- **Purpose**: Controls whether the assigned Tilt's readings are logged to temp_control_tilt.jsonl

### 2. User Interface
**File**: `templates/temp_control_config.html`

Added a new "Logging Options" section with a checkbox:

```html
<div class="form-row">
  <label>Logging Options:</label>
  <div>
    <label style="display:inline-block; width:auto;">
      <input type="checkbox" name="log_temp_control_tilt" 
             {% if temp_control.log_temp_control_tilt %}checked{% endif %}>
      Log Assigned Tilt to temp_control_tilt.jsonl
    </label>
  </div>
  <span class="small">
    Enable/disable logging of the assigned Tilt's readings to temp_control_tilt.jsonl file.
  </span>
</div>
```

**Location**: Temperature Control Settings page, between "Enabled Actions" and plug configuration

### 3. Backend Processing
**File**: `app.py`

#### Route Handler (`/update_temp_config`)
Added handling for the new checkbox (line 4180):
```python
temp_cfg.update({
    ...
    "log_temp_control_tilt": 'log_temp_control_tilt' in data,
    ...
})
```

#### Logging Logic (`temperature_control_logic()`)
Added check before logging (lines 2747-2763):
```python
# Log temp control tilt reading - ONLY if explicitly assigned AND logging is enabled
# Don't log fallback tilts, only log when tilt_color is explicitly set
# Check log_temp_control_tilt setting (default True for backward compatibility)
tilt_logging_enabled = temp_cfg.get("log_temp_control_tilt", True)
assigned_tilt_color = temp_cfg.get("tilt_color")
if tilt_logging_enabled and assigned_tilt_color and assigned_tilt_color in live_tilts:
    # ... perform logging
```

### 4. Testing
**File**: `test_temp_control_tilt_toggle.py`

Comprehensive test suite covering:
1. ✓ Logging works when enabled (checkbox checked)
2. ✓ Logging is blocked when disabled (checkbox unchecked)
3. ✓ Logging defaults to enabled for backward compatibility

**Helper Function**: `simulate_logging()` - Reduces code duplication in tests

## Behavior

### When Checkbox is CHECKED (Enabled)
- ✓ Assigned Tilt's readings are logged to `logs/temp_control_tilt.jsonl`
- ✓ Each log entry includes: timestamp, tilt_color, temperature, gravity, brewid, beer_name
- ✓ Only the explicitly assigned Tilt is logged (not fallback Tilts)

### When Checkbox is UNCHECKED (Disabled)
- ✗ No entries are written to `logs/temp_control_tilt.jsonl`
- ✓ Temperature control still functions normally
- ✓ Assigned Tilt is still used for temperature control
- ✓ Only logging is disabled

### Default Behavior
- **New installations**: Checkbox is checked by default (logging enabled)
- **Existing installations**: Will default to enabled if field is not present (backward compatible)
- **User choice**: Can be toggled on/off at any time via the UI

## User Workflow

1. Navigate to **Temperature Control Settings** page
2. Scroll to the **"Logging Options"** section
3. Check/uncheck the checkbox: **"Log Assigned Tilt to temp_control_tilt.jsonl"**
4. Click **"Save"** button
5. Setting is immediately applied

## Benefits

✓ **User Control**: Users decide when they need the log  
✓ **Disk Space**: Can disable logging when not needed to save disk space  
✓ **Clarity**: Clear UI label explains what the setting does  
✓ **Backward Compatible**: Existing systems continue logging by default  
✓ **No Breaking Changes**: Doesn't affect temperature control functionality  

## Technical Details

### Files Changed
1. `config/temp_control_config.json.template` - Added config field
2. `templates/temp_control_config.html` - Added UI checkbox
3. `app.py` - Added form handling and logging check
4. `test_temp_control_tilt_toggle.py` - Added comprehensive tests

### Code Quality
- ✓ All tests pass
- ✓ Code review completed - feedback addressed
- ✓ CodeQL security scan: No vulnerabilities
- ✓ Python compilation: Success
- ✓ Minimal, focused changes
- ✓ Clear variable naming (`tilt_logging_enabled`)
- ✓ DRY principle (helper function in tests)

## Integration with Previous Fix

This feature builds on the previous fix that ensured only explicitly assigned Tilts are logged:

**Previous Fix**: Only log explicitly assigned Tilts (not fallback Tilts)  
**This Feature**: Allow users to enable/disable that logging

Combined behavior:
```
IF log_temp_control_tilt == True:
    IF tilt is explicitly assigned:
        IF assigned tilt is available:
            ✓ Log to temp_control_tilt.jsonl
        ELSE:
            ✗ Don't log (tilt offline)
    ELSE:
        ✗ Don't log (no explicit assignment)
ELSE:
    ✗ Don't log (logging disabled by user)
```

## Visual Reference

```
┌────────────────────────────────────────────────────────────┐
│  Enabled Actions:   [✓] Enable Heating  [ ] Enable Cooling│
│                                                            │
│ ┌──────────────────────────────────────────────────────┐ │
│ │  Logging Options:  [✓] Log Assigned Tilt to          │ │
│ │                        temp_control_tilt.jsonl       │ │
│ │                    Enable/disable logging of the      │ │
│ │                    assigned Tilt's readings.          │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Heating Plug URL/ID: [192.168.1.100]                     │
└────────────────────────────────────────────────────────────┘
```

## Notes

- The setting persists in `temp_control_config.json`
- Changes take effect immediately after clicking "Save"
- No application restart required
- Logging state is independent of temperature control operation
- Temperature control continues to function whether logging is on or off
