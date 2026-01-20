# Configuration Files

This directory contains the application configuration files.

## Configuration Files

The repository includes default configuration files that you should customize for your setup:

- `tilt_config.json` - Tilt hydrometer assignments and batch information
- `temp_control_config.json` - Temperature control settings
- `system_config.json` - General system settings

Simply edit these files directly with your specific settings before running the application.

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

Additional fields can be added through the web interface for notifications, logging, etc.
