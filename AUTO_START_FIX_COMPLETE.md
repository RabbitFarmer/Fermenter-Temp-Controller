# Auto-Start Failure Fix - Complete Solution

## Problem Summary

The auto-start via systemd service was failing because the `fermenter.service` file had hard-coded paths that didn't match your actual installation:

- **Service expected:** User `pi` at `/home/pi/Fermenter-Temp-Controller`
- **Your actual setup:** User `flc3` at `/home/flc3/FermenterApp`

When the service tried to start, it couldn't find the application at the hard-coded paths.

## Solution Provided

We've created an **automated service installer** that detects your actual installation and generates a correct service file automatically.

## How to Fix Auto-Start

### Quick Fix (Recommended)

Simply run the automated installer:

```bash
cd ~/FermenterApp  # Or wherever you installed the app
./install_service.sh
```

The installer will:
1. ✓ Automatically detect your username (`flc3`)
2. ✓ Automatically detect your installation directory (`/home/flc3/FermenterApp`)
3. ✓ Find your virtual environment (`.venv` or `venv`)
4. ✓ Generate a service file with the correct paths
5. ✓ Show you the service file before installing it
6. ✓ Ask for confirmation before installing
7. ✓ Optionally enable and start the service

### What the Installer Does

The installer creates a service file like this (customized for your system):

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

Notice:
- **User** is set to `flc3` (your actual username)
- **WorkingDirectory** and **ExecStart** use `/home/flc3/FermenterApp` (your actual path)
- **SKIP_BROWSER_OPEN=1** is set to prevent browser opening attempts when running as a service

## After Installation

Once installed, the service will:
- ✓ Start automatically when your Raspberry Pi boots
- ✓ Restart automatically if it crashes
- ✓ Run in the background without opening a browser
- ✓ Log to systemd journal for easy troubleshooting

### Access the Dashboard

Since the service runs in the background with `SKIP_BROWSER_OPEN=1`, you need to manually open the dashboard:

**On the Raspberry Pi:**
- Open browser and go to: `http://localhost:5000`

**From another device on your network:**
- Open browser and go to: `http://<raspberry-pi-ip>:5000`

### Service Management Commands

```bash
# Check service status
sudo systemctl status fermenter

# Start the service
sudo systemctl start fermenter

# Stop the service
sudo systemctl stop fermenter

# Restart the service
sudo systemctl restart fermenter

# View logs
sudo journalctl -u fermenter -f
```

## Additional Improvements

We also made `start.sh` more flexible:

### Flexible Virtual Environment Detection

The `start.sh` script now automatically detects and uses either:
- `.venv` (recommended, created by `setup.sh`)
- `venv` (if you created it manually)

### Flexible Directory Names

The `start.sh` script works with any installation directory name:
- `/home/flc3/FermenterApp` ✓
- `/home/pi/Fermenter-Temp-Controller` ✓
- `/home/anyuser/anyname` ✓

No hardcoded paths - it automatically detects where it's installed!

## Verification

After running `./install_service.sh` and enabling the service:

1. **Reboot your Raspberry Pi:**
   ```bash
   sudo reboot
   ```

2. **After reboot, check if the service started:**
   ```bash
   sudo systemctl status fermenter
   ```

   You should see "active (running)" in green.

3. **Open the dashboard in your browser:**
   ```
   http://localhost:5000
   ```

   The main display page should appear!

4. **Check the logs if needed:**
   ```bash
   sudo journalctl -u fermenter -n 50
   ```

## Troubleshooting

If the service still doesn't start:

1. **Check the service status:**
   ```bash
   sudo systemctl status fermenter
   ```

2. **View detailed logs:**
   ```bash
   sudo journalctl -u fermenter -n 100
   ```

3. **Verify the service file paths:**
   ```bash
   cat /etc/systemd/system/fermenter.service
   ```

   Ensure:
   - `User=` matches your username
   - `WorkingDirectory=` matches your installation directory
   - `ExecStart=` paths are correct

4. **Test manual start:**
   ```bash
   cd ~/FermenterApp
   ./start.sh
   ```

   If manual start works but service doesn't, there's likely a path mismatch in the service file.

## Summary of Changes

### New Files
- **install_service.sh** - Automated service installer with path detection
- **test_install_service.sh** - Tests for service file generation
- **test_start_flexibility.sh** - Tests for start.sh flexibility

### Updated Files
- **start.sh** - Now detects `.venv` or `venv` automatically
- **setup.sh** - Now creates `.venv` for consistency
- **fermenter.service** - Updated template with warnings and SKIP_BROWSER_OPEN
- **README.md** - Updated installation instructions
- **INSTALLATION.md** - Comprehensive documentation with automated installer instructions

## Why This Fix Works

**Before:**
- Hard-coded paths in service file
- Needed manual editing (error-prone)
- Different venv names caused confusion
- Users had to know exact paths

**After:**
- Automatic path detection
- No manual editing required
- Works with `.venv` or `venv`
- Works with any directory name
- Clear error messages if something is wrong

## Next Steps

1. Run `./install_service.sh` to set up auto-start
2. Reboot and verify the service starts automatically
3. Enjoy automatic startup on every boot!

---

**Need Help?**

If you encounter any issues:
1. Check the logs: `sudo journalctl -u fermenter -f`
2. Try manual start: `./start.sh`
3. Open an issue on GitHub with the log output
