# Fermenter Temp Controller

This project is a Raspberry Pi-based fermentation monitor and temperature controller for homebrewing. It uses Tilt hydrometers and TP-Link Kasa smart plugs to manage and log fermentation temperature with a web dashboard.

## Features

- Reads Tilt hydrometer data via Bluetooth (BLE)
- Controls heating/cooling with Kasa smart plugs
- Web dashboard for monitoring and configuration (Flask)
- Batch history and temperature logging to JSONL/CSV
- **Email/Push notifications for fermentation status and temperature alerts**
  - Temperature control alerts (temp out of range, heating/cooling events, Kasa plug failures)
  - Batch alerts (signal loss, fermentation starting, daily reports)
  - Configurable notification settings per event type
  - See [NOTIFICATIONS.md](NOTIFICATIONS.md) for detailed configuration guide
  - See [Notification Types](#notification-types) section below for complete list of 11 notification types

## Demo Data

This repository includes demo fermentation data for the **Black tilt** to showcase the charting capabilities:

- **Beer**: 803 Blonde Ale Clone of 805
- **Duration**: 15 days of fermentation data
- **Data Points**: 30 samples showing gravity drop from 1.049 to 1.004

To set up the demo data:
```bash
./utils/setup_demo.sh
```

Then start the app and navigate to `http://localhost:5000/chart_plotly/Black` to view the demo chart.

For more information on importing custom data, see [utils/README.md](utils/README.md).

## Getting Started

### Prerequisites

- Raspberry Pi (recommended)
- Python 3.7+
- Bluetooth enabled (for Tilt)
- TP-Link Kasa plugs for temperature control

### Quick Installation

**Automated Setup (Recommended):**
```bash
git clone https://github.com/RabbitFarmer/Fermenter-Temp-Controller.git
cd Fermenter-Temp-Controller
./setup.sh
./start.sh
```

The setup script will automatically create a virtual environment and install all dependencies.

> **Important for Raspberry Pi Users:** Modern Python installations require using virtual environments. The setup script handles this automatically. See [INSTALLATION.md](INSTALLATION.md) for details.

### Manual Installation

If you prefer to install manually or encounter issues:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RabbitFarmer/Fermenter-Temp-Controller.git
   cd Fermenter-Temp-Controller
   ```

2. **Set up a Python virtual environment (REQUIRED on Raspberry Pi):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   
   > **Note:** You can use either `.venv` or `venv` as the directory name. The `start.sh` script automatically detects both. If you get "No module named venv" error, install it first:
   > ```bash
   > sudo apt install python3-venv python3-full
   > ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the application:**
   
   **Option A: Using the convenience script (automatically opens browser):**
   ```bash
   ./start.sh
   ```
   This script will start the Flask app and automatically open `http://127.0.0.1:5000` in your default browser.
   
   **Option B: Manual start:**
   ```bash
   python3 app.py
   ```
   Then visit `http://<raspberry-pi-ip>:5000` in your browser.

### Running on System Startup (Recommended)

To have the application start automatically when your Raspberry Pi boots up, use the automated service installer:

```bash
# Run the automated service installer (requires full path)
bash /full/path/to/Fermenter-Temp-Controller/install_service.sh

# Example:
# bash /home/pi/Fermenter-Temp-Controller/install_service.sh
```

> **Note:** The installer must be run with the full path to ensure correct service file generation.

The installer will:
- ✓ Automatically detect your installation directory and username
- ✓ Generate a service file with correct paths for your setup
- ✓ Install and optionally enable/start the systemd service

**Alternative - Manual Installation:**
```bash
# Edit fermenter.service with your paths, then:
sudo cp fermenter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fermenter
sudo systemctl start fermenter
```

For detailed instructions, including service management and logging, see the [Running on System Startup](INSTALLATION.md#running-on-system-startup-recommended) section in INSTALLATION.md.

### Troubleshooting Installation

If you encounter errors during installation, see [INSTALLATION.md](INSTALLATION.md) for:
- **PEP 668 "externally-managed-environment" errors**
- Bluetooth/BLE setup issues
- KASA plug configuration
- Running on system startup
- Complete troubleshooting guide

## Configuration

- Edit system settings via the web dashboard.
- Configure batch and temperature settings for each Tilt hydrometer color.

## Remote Access via VPN

Access your Fermenter Temperature Controller from anywhere using WireGuard VPN. This allows secure remote monitoring of your fermentation from your phone or computer while away from home.

### Quick Start

1. **Set up WireGuard VPN** on your Raspberry Pi and client devices:
   - See [How to Create Internet Access through VPN Tunnel.md](How%20to%20Create%20Internet%20Access%20through%20VPN%20Tunnel.md) for complete setup instructions

2. **Access the dashboard** through your VPN:
   ```
   http://<your-vpn-ip>:5000
   ```
   Example: `http://10.0.0.1:5000`

### Troubleshooting VPN Connection

If you get "connection refused" errors when accessing through VPN:

1. **Run the verification script** on your Raspberry Pi:
   ```bash
   ./verify_vpn_access.sh
   # Or use the Python version:
   python3 verify_vpn_access.py
   ```

2. **Common fixes:**
   - Ensure Flask app is running: `sudo systemctl status fermenter`
   - Add firewall rule: `sudo iptables -I INPUT -i wg0 -p tcp --dport 5000 -j ACCEPT`
   - Save firewall rule: `sudo iptables-save | sudo tee /etc/iptables/rules.v4`

3. **Detailed troubleshooting:**
   - See [VPN_TROUBLESHOOTING_GUIDE.md](VPN_TROUBLESHOOTING_GUIDE.md) for comprehensive diagnosis and solutions

The Flask application is already configured to accept connections from all interfaces (`0.0.0.0:5000`), so VPN access should work once the firewall rules are properly configured.

## File Structure

### Core Application Files
- `app.py` — Main web server and controller
- `start.sh` — Convenience script to start the app and open browser
- `tilt_static.py` — Tilt UUIDs and color maps
- `kasa_worker.py` — Kasa plug interface
- `logger.py` — Logging and notification system
- `fermentation_monitor.py` — Fermentation stability logic
- `batch_history.py` — Batch logging and management
- `archive_compact_logs.py` — Log archival and compaction utility

### Directory Structure
```
/config/              Configuration files (JSON)
  ├── system_config.json
  ├── tilt_config.json
  ├── temp_control_config.json
  ├── batch_settings.json
  └── config.json

/batches/             Per-batch data files (JSONL)
  ├── {brewname}_{YYYYmmdd}_{brewid}.jsonl
  └── batch_history_{color}.json

/temp_control/        Temperature control logs (JSONL)
  └── temp_control_log.jsonl

/logs/                General application logs
  ├── error.log
  ├── warning.log
  └── kasa_errors.log

/templates/           HTML files for web UI
/static/              CSS and static assets
/export/              Exported CSV files
```

### Configuration Files
Configuration files are stored in `/config/` directory and contain:
- `system_config.json` - System-wide settings (brewery info, SMTP, notifications, external logging)
- `tilt_config.json` - Per-tilt configuration (batch info, OG/FG targets)
- `temp_control_config.json` - Temperature control settings
- `batch_settings.json` - Batch-specific settings
- `config.json` - Additional configuration options

### External Logging Integrations

The system supports posting fermentation data to external logging services like Brewer's Friend, BrewFather, or custom endpoints.

**Configuration via Web Dashboard:**
1. Navigate to **System Settings** → **Logging Integrations** tab
2. Set the **External Post Interval** (recommended: 15 minutes)
3. For each external service (up to 3):
   - Enter a **Service Name** (e.g., "Brewer's Friend")
   - Enter the **URL** from your external service
   - Configure **HTTP Method**, **Content Type**, and **Request Timeout**
   - Select appropriate **Field Map Template** or create custom mapping

**Brewer's Friend Integration:**
- Brewer's Friend supports both `/tilt/` and `/stream/` endpoints
- The program can use **either** endpoint - both work correctly
- Recommended: Use the **Stream endpoint** (`https://log.brewersfriend.com/stream/YOUR_API_KEY`) for real-time logging
- The `/tilt/` endpoint is also supported for compatibility with Tilt-specific integrations
- Field mapping: The system automatically maps Tilt data fields to Brewer's Friend's expected format

**URL Format Examples:**
- Brewer's Friend Stream: `https://log.brewersfriend.com/stream/YOUR_API_KEY`
- Brewer's Friend Tilt: `https://log.brewersfriend.com/tilt/YOUR_API_KEY`
- BrewFather: `http://log.brewfather.net/stream?id=YOUR_STREAM_ID`
- Custom endpoint: `https://your-server.com/api/fermentation-data`

**Field Mapping:**
The system provides predefined field maps for common services and allows custom JSON mapping for other services. Available data fields include:
- `timestamp` - ISO 8601 timestamp
- `tilt_color` - Tilt hydrometer color
- `gravity` - Specific gravity reading
- `temp_f` - Temperature in Fahrenheit
- `brew_id` - Unique batch identifier
- `device` - Device identifier

**Request Timeout:**
The Request Timeout setting (default: 8 seconds) controls how long the system will wait for a response from the external service before timing out. This prevents the system from hanging if the external service is slow or unavailable.

## Notification Types

The system can send notifications via Email and/or Push (Pushover or ntfy) for various fermentation and temperature control events. All notifications (except test notifications) use a common notification system with deduplication to prevent duplicate alerts.

### Batch Notifications

Batch notifications monitor fermentation progress and tilt signal status:

1. **Loss of Signal** - Sent when no Tilt readings have been received for the configured timeout period (default: 30 minutes)
   - Subject: `{Brewery Name} - Loss of Signal`
   - Includes: Brewery name, Tilt color, Beer name, Date/Time
   - Configurable: `enable_loss_of_signal` in batch notifications settings

2. **Fermentation Started** - Sent when gravity drops 0.010+ points from original gravity across 3 consecutive readings
   - Subject: `{Brewery Name} - Fermentation Started`
   - Includes: Brewery name, Tilt color, Beer name, Starting gravity, Current gravity
   - Configurable: `enable_fermentation_starting` in batch notifications settings

3. **Fermentation Completion** - Sent when gravity has been stable (±0.002) for 24 hours
   - Subject: `{Brewery Name} - Fermentation Completion`
   - Includes: Brewery name, Tilt color, Beer name, Final gravity, Apparent attenuation
   - Configurable: `enable_fermentation_completion` in batch notifications settings

4. **Daily Report** - Sent once per day at a configured time with fermentation progress
   - Subject: `{Brewery Name} - Daily Report`
   - Includes: Starting gravity, Current gravity, Net change, Change since yesterday
   - Configurable: `enable_daily_report` and `daily_report_time` in batch notifications settings

### Temperature Control Notifications

Temperature control notifications alert when temperatures exceed limits, when heating/cooling equipment changes state, or when Kasa smart plugs fail to respond:

3. **Temperature Below Low Limit** - Sent when current temperature drops below the configured low limit
   - Subject: `{Brewery Name} - Temperature Control Alert`
   - Includes: Current temperature, Low limit setting, Tilt color
   - Configurable: `enable_temp_below_low_limit` in temperature control notifications settings

4. **Temperature Above High Limit** - Sent when current temperature rises above the configured high limit
   - Subject: `{Brewery Name} - Temperature Control Alert`
   - Includes: Current temperature, High limit setting, Tilt color
   - Configurable: `enable_temp_above_high_limit` in temperature control notifications settings

5. **Heating On** - Sent when the heating control is activated
   - Subject: `{Brewery Name} - Temperature Control Alert`
   - Includes: Current temperature, Low limit setting, Tilt color
   - Configurable: `enable_heating_on` in temperature control notifications settings (disabled by default)

6. **Heating Off** - Sent when the heating control is deactivated
   - Subject: `{Brewery Name} - Temperature Control Alert`
   - Includes: Current temperature, Tilt color
   - Configurable: `enable_heating_off` in temperature control notifications settings (disabled by default)

7. **Cooling On** - Sent when the cooling control is activated
   - Subject: `{Brewery Name} - Temperature Control Alert`
   - Includes: Current temperature, High limit setting, Tilt color
   - Configurable: `enable_cooling_on` in temperature control notifications settings (disabled by default)

8. **Cooling Off** - Sent when the cooling control is deactivated
   - Subject: `{Brewery Name} - Temperature Control Alert`
   - Includes: Current temperature, Tilt color
   - Configurable: `enable_cooling_off` in temperature control notifications settings (disabled by default)

9. **Kasa Plug Connection Failure** - Sent when a Kasa smart plug fails to respond or connection is lost
   - Subject: `{Brewery Name} - Kasa Plug Connection Failure`
   - Includes: Mode (Heating/Cooling), Plug URL, Error message, Tilt color
   - Configurable: `enable_kasa_error` in temperature control notifications settings
   - Note: Helps alert when heating/cooling equipment becomes unreachable

**Note:** Heating On/Off and Cooling On/Off notifications are disabled by default to avoid notification overload, but users can enable them if desired. These events are always logged to the temperature chart regardless of notification settings.

### Notification Delivery Methods

- **Email** - SMTP-based email notifications (supports Gmail, custom SMTP servers)
- **Push** - Mobile push notifications via:
  - **Pushover** - Paid service ($5 one-time per platform, very reliable)
  - **ntfy** - Free, open-source, self-hostable alternative
- **Both** - Send via both Email and Push simultaneously

### Notification Deduplication

All notifications use a 10-second pending queue with deduplication to prevent duplicate alerts. If the same notification is triggered multiple times within 10 seconds (e.g., from rapid BLE updates), only the first notification will be sent.

### Retry Mechanism

Failed notifications are automatically retried with exponential backoff:
- First retry: After 5 minutes
- Second retry: After 30 minutes
- Maximum retries: 2 (total of 3 attempts including initial send)

### Configuration

Notification settings can be configured via the web dashboard:
- Navigate to **System Settings** → **Push/Email** tab for delivery method settings
- Navigate to **Batch Settings** for batch notification preferences
- Navigate to **Temp Control Settings** for temperature control notification preferences

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

MIT License

## Credits

- [Tilt Hydrometer](https://tilthydrometer.com/)
- [python-kasa](https://github.com/python-kasa/python-kasa)
- [Bleak](https://github.com/hbldh/bleak)