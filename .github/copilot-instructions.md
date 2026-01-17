# Copilot Instructions for Fermenter-Temp-Controller

This repository is a Raspberry Pi-based fermentation monitor and temperature controller for homebrewing. It uses Tilt hydrometers (Bluetooth BLE), TP-Link Kasa smart plugs, and a Flask web dashboard.

## Project Overview

- **Primary Language**: Python 3.7+
- **Framework**: Flask web application
- **Hardware Integration**: Bluetooth Low Energy (BLE) for Tilt hydrometers, Kasa smart plugs for temperature control
- **Data Storage**: JSONL files for logging and batch history
- **Platform**: Designed for Raspberry Pi

## Code Style and Conventions

### Python Code

- Follow PEP 8 style guidelines for Python code
- Use descriptive variable names that reflect the homebrewing/fermentation domain (e.g., `brew_id`, `tilt_color`, `temp_control`)
- Maintain compatibility with Python 3.7+
- Use type hints where appropriate to improve code clarity
- Include docstrings for modules, classes, and functions explaining their purpose

### Error Handling

- Use try-except blocks for hardware interactions (BLE scanning, Kasa plug communication)
- Provide fallback behavior when optional dependencies are unavailable (see imports in `app.py`)
- Log errors appropriately using the logging system
- Gracefully handle missing or corrupted configuration files

### Configuration Files

- Use JSON format for configuration files (`config.json`, `system_config.json`, `batch_settings.json`, `tilt_config.json`, `temp_control_config.json`)
- Always validate configuration data before using it
- Provide sensible defaults when configuration values are missing
- Don't hardcode paths - use relative paths or make them configurable

### Data Logging

- Use JSONL (JSON Lines) format for batch history and temperature control logs
- Each log entry should be a single valid JSON object on its own line
- Include timestamps in ISO 8601 format for all log entries
- Store batch-specific data in `batches/{brewid}.jsonl` files
- Keep the restricted control log in `temp_control_log.jsonl`

### Flask Application Structure

- Keep route handlers focused and delegate complex logic to separate modules
- Use Flask's `jsonify()` for JSON responses
- Render templates from the `/templates` directory
- Serve static files (CSS, JS, favicon) from `/static` directory
- Follow RESTful conventions for API endpoints where applicable

### Hardware Integration

- **Bluetooth/BLE**: Use `bleak` library for Tilt hydrometer scanning
- **Kasa Plugs**: Use the `kasa_worker` module for smart plug control
- Always check for hardware availability before attempting operations
- Implement timeouts for hardware communication to prevent hanging
- Handle connection failures gracefully with appropriate user feedback

### Async/Threading

- Use `asyncio` for BLE operations with BleakScanner
- Use threading or multiprocessing where needed for concurrent operations
- Be mindful of thread safety when accessing shared data structures
- Properly manage process lifecycles (clean startup and shutdown)

### Dependencies

- Core dependencies are listed in `requirements.txt`
- Keep dependencies minimal and well-justified
- Use optional imports with try-except for non-critical features
- Test that the application degrades gracefully when optional dependencies are missing

## Testing and Quality

### Running the Application

- Start the application with: `python3 app.py`
- The Flask server runs on `0.0.0.0:5000` by default
- Test on a Raspberry Pi when making hardware-related changes
- Verify web UI functionality in a browser at `http://<raspberry-pi-ip>:5000`

### Manual Testing

- Test BLE scanning functionality with actual Tilt hydrometers when possible
- Verify Kasa plug control operations
- Check JSONL file format after making logging changes
- Validate JSON configuration files are properly formatted
- Test all web UI routes and forms

### Code Quality

- Avoid breaking existing functionality
- Keep changes focused and minimal
- Don't remove working code unless absolutely necessary
- Ensure configuration files remain backwards-compatible when possible
- Review JSONL log files to ensure they're still valid JSON Lines format

## File Structure Guidelines

### Core Application Files

- `app.py` - Main Flask application and web server
- `tilt_static.py` - Tilt UUID mappings and color definitions
- `kasa_worker.py` - Kasa smart plug interface and worker
- `logger.py` - Logging and notification system
- `fermentation_monitor.py` - Fermentation stability detection logic
- `batch_history.py` - Batch logging and management
- `batch_storage.py` - Batch data storage utilities

### Configuration and Data Files

- `*.json` - Configuration files (don't commit with sensitive data)
- `*.jsonl` - Log files in JSON Lines format (git-ignored)
- `batches/` - Per-batch JSONL data files
- `export/` - Exported CSV files
- `logs/` - Application log files

### Web UI Files

- `templates/*.html` - Jinja2 templates for web pages
- `static/styles.css` - Stylesheet
- `static/js/` - JavaScript files
- `static/favicon.ico` - Site favicon

## Security Considerations

- Never commit sensitive data (SMTP passwords, API keys, personal data) to the repository
- Sanitize user input from web forms before using it
- Use parameterized queries if database support is added in the future
- Validate file paths to prevent directory traversal attacks
- Be cautious with `eval()` or `exec()` - avoid if possible

## Domain-Specific Guidelines

### Homebrewing/Fermentation Context

- Understand that this controls real fermentation batches with temperature-sensitive processes
- Temperature changes should be gradual and controlled
- Maintain data integrity in batch logs - they represent real fermentation history
- Tilt colors (Black, Blue, Green, Orange, Pink, Purple, Red, Yellow) identify different fermenters
- Respect hydrometer readings and don't introduce artificial data

### Temperature Control Logic

- Heating and cooling are controlled via Kasa smart plugs
- Temperature control loops should prevent rapid on/off cycling
- Safety margins are important for temperature setpoints
- Monitor fermentation stability to detect completion

## Common Tasks

### Adding a New Configuration Option

1. Add the field to the appropriate JSON config file
2. Update the corresponding HTML form in `/templates`
3. Add form handling in the Flask route
4. Provide a sensible default value
5. Update any validation logic

### Adding a New Web Route

1. Define the route handler in `app.py`
2. Create or update the HTML template in `/templates`
3. Add any necessary static assets to `/static`
4. Update navigation if needed
5. Test the route in a browser

### Modifying Log Format

1. Ensure JSONL format is maintained (one JSON object per line)
2. Update both writing and reading functions
3. Consider backwards compatibility with existing log files
4. Test log rotation and archiving if applicable
5. Update export functionality if the change affects CSV exports

## Documentation

- Update `README.md` if adding significant new features
- Keep inline comments focused on "why" rather than "what"
- Document any new configuration options
- Maintain clear commit messages that explain the purpose of changes

## Best Practices

- **Start small**: Make minimal, focused changes
- **Test locally**: Always test on actual hardware when possible
- **Preserve data**: Be extra careful with changes affecting log files or batch data
- **Be defensive**: Code should handle missing hardware gracefully
- **Stay focused**: This is a Raspberry Pi homebrewing controller - keep it simple and reliable
