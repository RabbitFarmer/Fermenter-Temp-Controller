# Configuration Files

This directory contains the application configuration files.

## Important: Configuration File Management

**Your configuration files will NOT be overwritten** when you update the application via git pull or rsync.

- **Template files** (`.json.template`) are tracked in git and contain default values
- **Actual config files** (`.json`) are NOT tracked in git and contain YOUR settings
- On first run, the application automatically copies templates to create your config files
- Your settings persist across application updates

## Configuration Files

The application uses three configuration files that you can customize:

- `system_config.json` - General system settings (automatically created from template)
- `temp_control_config.json` - Temperature control settings (automatically created from template)
- `tilt_config.json` - Tilt hydrometer assignments and batch information (automatically created from template)

**You can edit these files directly OR use the web interface** (recommended for most users).

## Template Files

Template files provide safe defaults and are used to initialize your configuration:

- `system_config.json.template` - Template for system settings
- `temp_control_config.json.template` - Template for temperature control
- `tilt_config.json.template` - Template for Tilt configurations

**Do not edit template files directly** - they will be overwritten by git updates.

## Deployment Workflow

When updating the application:

```bash
# On your local machine
git pull origin main

# Sync to Raspberry Pi (rsync will NOT overwrite your .json files)
rsync -av --exclude='*.json' /path/to/repo/ pi@raspberrypi:/path/to/app/

# Or if you sync .json files, your settings are preserved because 
# actual config files are not in git (only templates are)
```

The application will automatically create config files from templates if they don't exist.

### tilt_config.json
Contains Tilt hydrometer assignments and batch information for each color (Red, Green, Black, Purple, Orange, Blue, Yellow, Pink).

**Fields per tilt:**
- `beer_name`: Name of the beer being fermented
- `batch_name`: Batch identifier
- `ferm_start_date`: Fermentation start date (YYYY-MM-DD)
- `recipe_og`: Recipe original gravity
- `recipe_fg`: Recipe final gravity
- `recipe_abv`: Recipe ABV percentage
- `actual_og`: Actual measured original gravity
- `og_confirmed`: Whether the original gravity has been confirmed (true/false)
- `brewid`: Auto-generated batch ID

### temp_control_config.json
Temperature control settings for the fermentation chamber.

**Fields:**
- `low_limit`: Lower temperature limit (°F)
- `high_limit`: Upper temperature limit (°F)
- `enable_heating`: Enable heating control (true/false)
- `enable_cooling`: Enable cooling control (true/false)
- `tilt_color`: Which Tilt to use for temperature monitoring
- `heating_plug`: IP address or identifier for heating Kasa plug
- `cooling_plug`: IP address or identifier for cooling Kasa plug
- `compressor_delay`: Delay in minutes before restarting compressor

### system_config.json
General system settings.

**Fields:**
- `brewery_name`: Your brewery name
- `brewer_name`: Your name
- `units`: Temperature units ("Fahrenheit" or "Celsius")
- `tilt_inactivity_timeout_minutes`: Time in minutes after which a Tilt is considered inactive if no data is received (default: 30). Inactive Tilts are hidden from the main display. **SAFETY FEATURE**: If the Tilt assigned to temperature control becomes inactive, all Kasa plugs are automatically turned OFF to prevent runaway heating/cooling.

Additional fields can be added through the web interface for notifications, logging, etc.
