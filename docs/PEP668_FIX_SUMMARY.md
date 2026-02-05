# Installation Fix Summary

## What Was Fixed

Fixed the "externally-managed-environment" error that occurs when trying to install Python packages on Raspberry Pi.

## Error You Were Seeing

```
error: externally-managed-environment
× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.
```

## Root Cause

Modern Raspberry Pi OS (Debian/Ubuntu-based) implements PEP 668, which prevents installing packages globally to protect the system Python installation. This is a **safety feature**, not a bug.

## Solution

Use a Python virtual environment (recommended best practice).

## How to Install Now

### Option 1: Automated (Easiest)

```bash
cd ~/FermenterApp  # Or wherever you cloned the repo
./setup.sh
```

The script will:
- ✓ Check your Python version
- ✓ Verify python3-venv is installed (install instructions if not)
- ✓ Create a virtual environment
- ✓ Install all dependencies
- ✓ Set up necessary directories

### Option 2: Manual (2 Commands)

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Starting the Application

After installation, always activate the virtual environment:

```bash
# Activate virtual environment
source venv/bin/activate

# Start app
python3 app.py
```

**Or use the convenience script** (handles activation automatically):
```bash
./start.sh
```

## Files Added/Modified

### New Files
1. **setup.sh** - Automated installation script (recommended)
2. **INSTALLATION.md** - Comprehensive installation guide with troubleshooting
3. **QUICK_FIX_PEP668.md** - Quick reference for the PEP 668 error

### Modified Files
1. **README.md** - Updated with clearer installation instructions
2. **start.sh** - Enhanced to check for and activate virtual environment

## Key Changes

### README.md
- Changed virtual environment from "optional" to "REQUIRED on Raspberry Pi"
- Added quick start section using setup.sh
- Added troubleshooting section

### start.sh
- Now checks for both `venv/` and `.venv/` directories
- Displays message when activating virtual environment
- Warns if no virtual environment found

## Troubleshooting

### "No module named venv"

Install it:
```bash
sudo apt update
sudo apt install python3-venv python3-full
```

### Virtual environment not activating

Make sure you're in the correct directory:
```bash
cd ~/FermenterApp
ls venv/bin/activate  # Should exist after running setup.sh
source venv/bin/activate
```

### Still getting errors?

See [INSTALLATION.md](INSTALLATION.md) for complete troubleshooting guide.

## What NOT to Do

❌ **Don't use `--break-system-packages`** - Can break your system Python  
❌ **Don't use `sudo pip install`** - Security risk and causes conflicts  
✅ **Use virtual environment** - Safe, clean, recommended

## Why Virtual Environments?

- **Isolation**: Project dependencies don't affect system Python
- **Safety**: Can't break system packages
- **Cleanliness**: Easy to remove/recreate
- **Standard Practice**: Industry best practice for Python projects

## Running on Startup (Optional)

To run on boot, use systemd (see INSTALLATION.md section "Running on System Startup").

## Need More Help?

1. Check [INSTALLATION.md](INSTALLATION.md) for detailed guide
2. Check [QUICK_FIX_PEP668.md](QUICK_FIX_PEP668.md) for quick reference
3. Open a GitHub issue with:
   - Your Raspberry Pi OS version (`cat /etc/os-release`)
   - Python version (`python3 --version`)
   - Full error message
   - Steps already tried

## Summary

The PEP 668 error is **not a bug** - it's a safety feature. Virtual environments are the correct solution and are now fully automated with our setup script. Simply run `./setup.sh` and you're done!
