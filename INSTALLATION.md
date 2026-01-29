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
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

When activated, you'll see `(venv)` in your terminal prompt:
```
(venv) user@raspberrypi:~/Fermenter-Temp-Controller$
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
python3 -m venv venv
source venv/bin/activate

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
The `source venv/bin/activate` command doesn't work or doesn't show `(venv)` in prompt.

**Solution:**

1. Make sure you're in the correct directory:
```bash
cd ~/Fermenter-Temp-Controller
ls venv/bin/activate  # Should exist
```

2. Try alternative activation:
```bash
. venv/bin/activate
```

3. If still not working, recreate the virtual environment:
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

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

To ensure the application starts automatically when your Raspberry Pi boots up, set up a systemd service. This is the recommended approach as it provides automatic restart on failure and better logging.

### Method 1: systemd service (Recommended)

A systemd service file template (`fermenter.service`) is included in the repository. Follow these steps to set it up:

1. **Copy the service file to the system directory:**

```bash
sudo cp fermenter.service /etc/systemd/system/fermenter.service
```

2. **Edit the service file if your paths are different:**

If you installed to a different location or use a different username, edit the service file:

```bash
sudo nano /etc/systemd/system/fermenter.service
```

The default service file assumes:
- User: `pi`
- Install path: `/home/pi/Fermenter-Temp-Controller`
- Virtual environment: `.venv` (created by setup.sh)

Update these if needed:

```ini
[Unit]
Description=Fermenter Temperature Controller
After=network.target bluetooth.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Fermenter-Temp-Controller
ExecStart=/home/pi/Fermenter-Temp-Controller/.venv/bin/python3 /home/pi/Fermenter-Temp-Controller/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

> **Note:** The service file uses `.venv` (created by setup.sh) not `venv`. If you created your virtual environment manually as `venv`, update the `ExecStart` path accordingly.

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

### Method 2: crontab (Alternative)

If you prefer not to use systemd, you can use crontab to start the application on boot:

```bash
crontab -e
```

Add this line:
```
@reboot cd /home/pi/Fermenter-Temp-Controller && ./start.sh
```

**Note:** This method uses start.sh which will attempt to open a browser. On a headless Raspberry Pi, this may produce harmless error messages. The systemd method is more robust for headless operation.

---

## Verifying Installation

After installation, verify everything works:

1. **Check virtual environment:**
```bash
source venv/bin/activate
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

# Activate virtual environment
source venv/bin/activate

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
