# Fermenter Temp Controller

This project is a Raspberry Pi-based fermentation monitor and temperature controller for homebrewing. It uses Tilt hydrometers and TP-Link Kasa smart plugs to manage and log fermentation temperature with a web dashboard.

## Features

- Reads Tilt hydrometer data via Bluetooth (BLE)
- Controls heating/cooling with Kasa smart plugs
- Web dashboard for monitoring and configuration (Flask)
- Batch history and temperature logging to JSONL/CSV
- **Email/SMS notifications for fermentation status and temperature alerts**
  - Temperature control alerts (out of range, heating/cooling events)
  - Batch alerts (signal loss, fermentation starting, daily reports)
  - Configurable notification settings per event type
  - See [NOTIFICATIONS.md](NOTIFICATIONS.md) for detailed configuration guide

## Getting Started

### Prerequisites

- Raspberry Pi (recommended)
- Python 3.7+
- Bluetooth enabled (for Tilt)
- TP-Link Kasa plugs for temperature control

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RabbitFarmer/Fermenter-Temp-Controller.git
   cd Fermenter-Temp-Controller
   ```

2. **Set up a Python virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the application:**
   ```bash
   python3 app.py
   ```
   Then visit `http://<raspberry-pi-ip>:5000` in your browser.

## Configuration

- Edit system settings via the web dashboard.
- Configure batch and temperature settings for each Tilt hydrometer color.

## File Structure

- `app.py` — Main web server and controller
- `tilt_static.py` — Tilt UUIDs and color maps
- `kasa_worker.py` — Kasa plug interface
- `logger.py` — Logging and notification system
- `fermentation_monitor.py` — Fermentation stability logic
- `batch_history.py` — Batch logging and management
- `/templates` — HTML files for web UI
- `/static` — CSS and static assets

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

MIT License

## Credits

- [Tilt Hydrometer](https://tilthydrometer.com/)
- [python-kasa](https://github.com/python-kasa/python-kasa)
- [Bleak](https://github.com/hbldh/bleak)