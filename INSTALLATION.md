# Installation Guide

This guide provides detailed installation instructions for the Fermenter Temp Controller on Raspberry Pi.

## Table of Contents
- [Quick Start (Recommended)](#quick-start-recommended)
- [Manual Installation](#manual-installation)
- [Troubleshooting](#troubleshooting)
- [Alternative Installation Methods](#alternative-installation-methods)

---

## Quick Start (Recommended)

The easiest way to install the Fermenter Temp Controller is using the automated setup script:

```bash
# Clone the repository
git clone https://github.com/RabbitFarmer/Fermenter-Temp-Controller.git
cd Fermenter-Temp-Controller

# Run the automated setup script
./setup.sh
```

The setup script will:
1. ✓ Check Python version (requires Python 3.7+)
2. ✓ Create a virtual environment
3. ✓ Install all dependencies
4. ✓ Create necessary directories

After setup completes, start the application:

```bash
./start.sh
```

---

## Manual Installation

If you prefer to install manually or the automated script doesn't work:

### Step 1: Prerequisites

Ensure you have Python 3.7+ and venv support:

```bash
# Check Python version
python3 --version

# Install required system packages (Raspberry Pi OS / Debian / Ubuntu)
sudo apt update
sudo apt install python3-venv python3-full
```

### Step 2: Clone Repository

```bash
git clone https://github.com/RabbitFarmer/Fermenter-Temp-Controller.git
cd Fermenter-Temp-Controller
```

### Step 3: Create Virtual Environment

**Why use a virtual environment?**
- Isolates project dependencies from system Python
- Prevents conflicts with other Python projects
- Avoids PEP 668 "externally-managed-environment" errors
- Allows easy cleanup and reinstallation

```bash
# Create virtual environment (use .venv for consistency with setup.sh)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

**Note:** You can use either `.venv` or `venv` as the directory name. The `start.sh` script automatically detects both. For consistency with `setup.sh` and the systemd service, we recommend using `.venv`.

When activated, you'll see `(.venv)` or `(venv)` in your terminal prompt:
```
(.venv) user@raspberrypi:~/Fermenter-Temp-Controller$
```

### Step 4: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```

### Step 5: Run the Application

```bash
# Option A: Use the convenience script
./start.sh

# Option B: Run directly
python3 app.py
```

Then open your browser to: `http://localhost:5000`

---

## Troubleshooting

### Error: "externally-managed-environment"

**Problem:**
```
error: externally-managed-environment

× This environment is externally managed
```

**Solution:**
This error occurs when trying to install packages globally on modern Python installations. You MUST use a virtual environment:

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Now install packages
pip install -r requirements.txt
```

**Why this happens:**
- Raspberry Pi OS (and other Debian-based systems) protect the system Python installation
- PEP 668 prevents breaking system packages
- Virtual environments are the recommended solution

**DO NOT use `--break-system-packages`** - this can break your system Python and other applications!

---

### Error: "No module named 'venv'"

**Problem:**
```
/usr/bin/python3: No module named venv
```

**Solution:**
Install the venv module:

```bash
sudo apt update
sudo apt install python3-venv python3-full
```

---

### Virtual Environment Not Activating

**Problem:**
The `source .venv/bin/activate` or `source venv/bin/activate` command doesn't work or doesn't show `(.venv)` or `(venv)` in prompt.

**Solution:**

1. Make sure you're in the correct directory and check which venv exists:
```bash
cd ~/Fermenter-Temp-Controller
ls .venv/bin/activate  # Check for .venv
# OR
ls venv/bin/activate   # Check for venv
```

2. Try alternative activation (using . instead of source):
```bash
. .venv/bin/activate
# OR
. venv/bin/activate
```

3. If still not working, recreate the virtual environment:
```bash
# Remove old venv
rm -rf .venv venv

# Create new one (using .venv for consistency)
python3 -m venv .venv
source .venv/bin/activate
```

**Note:** The `start.sh` script automatically detects and uses either `.venv` or `venv`, so you don't need to worry about which one you have when using that script.

---

### Permission Denied on setup.sh

**Problem:**
```
bash: ./setup.sh: Permission denied
```

**Solution:**
Make the script executable:

```bash
chmod +x setup.sh
./setup.sh
```

---

### Bluetooth/BLE Issues

**Problem:**
Can't detect Tilt hydrometers.

**Solution:**
1. Ensure Bluetooth is enabled:
```bash
sudo systemctl status bluetooth
```

2. Install Bluetooth libraries:
```bash
sudo apt install bluetooth bluez libbluetooth-dev
```

3. Add your user to the bluetooth group:
```bash
sudo usermod -a -G bluetooth $USER
```

4. Reboot the Raspberry Pi

---

### KASA Plug Connection Issues

**Problem:**
KASA smart plugs not responding.

**Solution:**
1. Run the diagnostic tool:
```bash
python3 diagnose_kasa.py
```

2. Configure actual IP addresses in `config/temp_control_config.json`

3. Test the plugs:
```bash
python3 test_kasa_plugs.py
```

See [KASA_TESTING.md](KASA_TESTING.md) for detailed troubleshooting.

---

## Alternative Installation Methods

### Method 1: Using --break-system-packages (NOT RECOMMENDED)

⚠️ **Warning:** This can break your system Python installation!

Only use this if you fully understand the risks:

```bash
pip install -r requirements.txt --break-system-packages
```

### Method 2: System Package Manager (Limited)

Some packages may be available via apt:

```bash
sudo apt install python3-flask python3-requests
```

However, many required packages (like `python-kasa`, `bleak`) are not available via apt, so this method is incomplete.

### Method 3: User Installation (NOT RECOMMENDED)

Install to user directory (still not ideal for this project):

```bash
pip install --user -r requirements.txt
```

---

## Running on System Startup (Recommended)

You have three options for auto-starting the application at boot. Choose based on your setup:

### Method 1: Desktop Autostart (Best for setups with monitor)

**Use this if:**
- ✓ You have a Raspberry Pi with monitor, keyboard, and mouse
- ✓ You want the browser to open automatically at boot
- ✓ You prefer a simple user-friendly setup

**Installation:**
```bash
cd /path/to/Fermenter-Temp-Controller
bash install_desktop_autostart.sh
```

**What it does:**
- Installs a desktop autostart entry in `~/.config/autostart/`
- Runs `start.sh` when you log in to the desktop
- Automatically opens browser when Flask is ready
- Waits up to 3 minutes for system to be ready (handles boot delays)
- No sudo required

**After installation:**
- Reboot or log out and back in
- Application starts automatically
- Browser opens to http://127.0.0.1:5000

**To disable:**
```bash
rm ~/.config/autostart/fermenter.desktop
```

### Method 2: Systemd Service (Best for headless/server setups)

**Use this if:**
- ✓ You access the Pi via SSH (headless)
- ✓ You want the app to run without browser opening
- ✓ You want automatic restart on failure
- ✓ You need detailed logging via journalctl

**Installation:**
The easiest way to install the systemd service is using the automated installation script:

```bash
# Run the service installer with full path (required)
bash /full/path/to/Fermenter-Temp-Controller/install_service.sh

# Example:
# bash /home/pi/Fermenter-Temp-Controller/install_service.sh
```

> **Important:** The installer must be run with the full path to ensure correct service file generation.

The installer will:
1. ✓ Detect your installation directory automatically
2. ✓ Detect your username automatically
3. ✓ Find your virtual environment (.venv or venv)
4. ✓ Generate a service file with correct paths
5. ✓ Show you the service file before installing
6. ✓ Install and optionally enable/start the service

**Important Notes:**
- The service is configured with `SKIP_BROWSER_OPEN=1` to prevent browser opening attempts when running as a background service
- Access the dashboard by manually opening `http://<raspberry-pi-ip>:5000` in your browser
- The service runs in the background without requiring a desktop session

After installation, the application will start automatically on boot.

---

### Method 2: Manual systemd service Installation (Advanced)

If you prefer to install manually or need to customize the service:

1. **Edit the service file template:**

The repository includes a template service file (`fermenter.service`). You need to update it with your specific paths.

```bash
# Make a copy of the service file
cp fermenter.service fermenter.service.custom

# Edit the custom file
nano fermenter.service.custom
```

Update these values to match your installation:
- **User**: Your username (e.g., `flc3`, `pi`, etc.)
- **WorkingDirectory**: Your installation path (e.g., `/home/flc3/FermenterApp`)
- **ExecStart**: Full path to python3 in your venv and app.py

Example for user `flc3` with installation in `/home/flc3/FermenterApp`:

```ini
[Unit]
Description=Fermenter Temperature Controller
After=network.target bluetooth.service

[Service]
Type=simple
User=flc3
WorkingDirectory=/home/flc3/FermenterApp
Environment="DISPLAY=:0"
Environment="SKIP_BROWSER_OPEN=1"
ExecStart=/home/flc3/FermenterApp/.venv/bin/python3 /home/flc3/FermenterApp/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

> **Note:** Both `setup.sh` and `start.sh` now create/use `.venv` for consistency. However, `start.sh` automatically detects either `.venv` or `venv` if you created it manually. Make sure the `ExecStart` path matches your actual venv directory name.

2. **Install the customized service file:**

```bash
sudo cp fermenter.service.custom /etc/systemd/system/fermenter.service
```

3. **Enable and start the service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable fermenter
sudo systemctl start fermenter
```

4. **Verify the service is running:**

```bash
sudo systemctl status fermenter
```

You should see "active (running)" in green.

5. **View logs if needed:**

```bash
# View recent logs
sudo journalctl -u fermenter -n 50

# Follow logs in real-time
sudo journalctl -u fermenter -f
```

6. **Access the web interface:**

Once the service is running, open your browser to `http://<raspberry-pi-ip>:5000`

**Service Management Commands:**

```bash
# Stop the service
sudo systemctl stop fermenter

# Restart the service
sudo systemctl restart fermenter

# Disable autostart (but don't stop)
sudo systemctl disable fermenter

# Re-enable autostart
sudo systemctl enable fermenter
```

### Method 3: crontab @reboot (Not Recommended)

> **⚠️ Warning:** This method is NOT recommended. Use **Desktop Autostart** (Method 1) or **Systemd Service** (Method 2) instead.

If you still want to use crontab (for legacy compatibility):

```bash
crontab -e
```

Add this line:
```
@reboot cd /home/pi/Fermenter-Temp-Controller && ./start.sh
```

**Why this method is not recommended:**
- ✗ Runs very early in boot (network/desktop may not be ready)
- ✗ Timing issues can cause browser to open before Flask is ready
- ✗ Less reliable than desktop autostart or systemd
- ✗ Difficult to debug if issues occur

**However:** The enhanced `start.sh` now includes boot detection and will automatically:
- Wait up to 3 minutes for Flask to be ready (vs 1 minute in interactive mode)
- Wait for desktop environment to load before opening browser
- Show progress updates every 10 attempts

So while this method still works, **Desktop Autostart (Method 1)** is more reliable for desktop setups, and **Systemd Service (Method 2)** is better for headless setups.

**Comparison:**

| Feature | Desktop Autostart | Systemd Service | Crontab @reboot |
|---------|------------------|-----------------|-----------------|
| Browser opens automatically | ✓ Yes | ✗ No | ✓ Yes (may fail) |
| Waits for desktop ready | ✓ Yes | N/A | ⚠️ With delays |
| Reliable timing | ✓ Yes | ✓ Yes | ⚠️ Sometimes |
| Easy to debug | ✓ Yes | ✓ Yes | ✗ No |
| Requires sudo | ✗ No | ✓ Yes | ✗ No |
| Works headless | ✗ No | ✓ Yes | ⚠️ Partial |
| **Recommended** | **Desktop** | **Headless** | **Not recommended** |

---

## Verifying Installation

After installation, verify everything works:

1. **Check virtual environment:**
```bash
source .venv/bin/activate
python3 -c "import flask; import bleak; import kasa; print('All packages OK')"
```

2. **Test KASA plugs:**
```bash
python3 diagnose_kasa.py
```

3. **Start the application:**
```bash
./start.sh
```

4. **Access web interface:**
- Local: http://localhost:5000
- Network: http://<raspberry-pi-ip>:5000

---

## Updating

To update the application:

```bash
cd ~/Fermenter-Temp-Controller

# Pull latest changes
git pull

# Activate virtual environment (use whichever you have: .venv or venv)
source .venv/bin/activate
# OR: source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade
```

---

## Uninstalling

To completely remove the installation:

```bash
# Stop the service (if using systemd)
sudo systemctl stop fermenter
sudo systemctl disable fermenter
sudo rm /etc/systemd/system/fermenter.service

# Remove the application
cd ~
rm -rf Fermenter-Temp-Controller
```

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [README.md](README.md) for general information
2. Review [KASA_TESTING.md](KASA_TESTING.md) for KASA plug issues
3. Check [FIX_SUMMARY.md](FIX_SUMMARY.md) for recent fixes
4. Open an issue on GitHub with:
   - Your Raspberry Pi OS version (`cat /etc/os-release`)
   - Python version (`python3 --version`)
   - Error messages
   - Steps you've already tried
