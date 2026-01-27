# Quick Fix: PEP 668 Installation Error

If you're seeing this error:
```
error: externally-managed-environment
× This environment is externally managed
```

## Immediate Solution (2 commands)

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

That's it! You should now see `(venv)` in your terminal prompt and the installation will complete successfully.

---

## If You Get "No module named venv"

Install it first:
```bash
sudo apt update
sudo apt install python3-venv python3-full
```

Then retry the commands above.

---

## Automated Installation

Or use our automated setup script:
```bash
./setup.sh
```

---

## Starting the Application

After installation, always activate the virtual environment before starting:

```bash
# Activate virtual environment
source venv/bin/activate

# Start the app
python3 app.py
```

Or simply use the start script which handles this automatically:
```bash
./start.sh
```

---

## Why This Happens

Modern Python installations on Raspberry Pi OS (and other Debian/Ubuntu systems) are marked as "externally managed" to prevent you from accidentally breaking system packages. This is a safety feature introduced in PEP 668.

Virtual environments are the recommended solution - they isolate your project's dependencies from the system Python.

---

## More Help

For complete installation instructions and troubleshooting, see:
- [INSTALLATION.md](INSTALLATION.md) - Detailed installation guide
- [README.md](README.md) - Quick start guide

## DO NOT Use These (Not Recommended)

❌ `pip install --break-system-packages` - Can break your system Python  
❌ `sudo pip install` - Security risk and can cause conflicts  
✅ **Use virtual environment instead** - Safe, clean, recommended
