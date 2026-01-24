# Configuration File Migration Guide

## Problem Fixed

**Issue:** User configuration data was being overwritten during code updates via git pull / rsync.

**Root Cause:** Configuration files (`.json`) were tracked in git with default values. When syncing code updates to your Raspberry Pi, rsync would overwrite your working config files with the defaults from git, losing all your entered data.

## Solution

Configuration files are now separated into:
- **Template files** (`.json.template`) - Tracked in git, contain safe defaults
- **Actual config files** (`.json`) - NOT tracked in git, contain YOUR settings

Your settings will now persist across code updates!

## Migration Steps

### For Existing Users

If you're upgrading from an older version and have already entered configuration data:

#### Option 1: Automatic (Recommended)

1. **Before updating**, back up your current config files:
   ```bash
   cd /path/to/Fermenter-Temp-Controller
   cp config/system_config.json config/system_config.json.backup
   cp config/temp_control_config.json config/temp_control_config.json.backup
   cp config/tilt_config.json config/tilt_config.json.backup
   ```

2. **Pull the update**:
   ```bash
   git pull origin main
   ```

3. **Restore your backed-up configs**:
   ```bash
   mv config/system_config.json.backup config/system_config.json
   mv config/temp_control_config.json.backup config/temp_control_config.json
   mv config/tilt_config.json.backup config/tilt_config.json
   ```

4. **Done!** Your settings are now protected. Future updates won't overwrite them.

#### Option 2: Fresh Start

If you don't have important data or want to start fresh:

1. **Pull the update**:
   ```bash
   git pull origin main
   ```

2. **Start the application**:
   ```bash
   python3 app.py
   ```

3. **The application will automatically create config files from templates**

4. **Re-enter your settings via the web interface**

### For New Users

No migration needed! Just:

1. Clone the repository
2. Start the application with `python3 app.py`
3. Config files will be created automatically from templates
4. Enter your settings via the web interface

## Deployment Workflow (Updated)

### Updating Code on Raspberry Pi

**Method 1: Git Pull Directly on Pi**
```bash
# SSH into your Raspberry Pi
ssh pi@raspberrypi

# Navigate to app directory
cd /path/to/Fermenter-Temp-Controller

# Pull updates (your .json configs won't be touched)
git pull origin main

# Restart the application
# (your config files remain unchanged)
```

**Method 2: Local Git + Rsync**
```bash
# On your local machine
cd /path/to/local/Fermenter-Temp-Controller
git pull origin main

# Sync to Pi (configs are now safe!)
rsync -av --exclude='*.pyc' --exclude='__pycache__' \
  /path/to/local/Fermenter-Temp-Controller/ \
  pi@raspberrypi:/path/to/Fermenter-Temp-Controller/

# Your .json config files on the Pi are preserved because:
# 1. They're in .gitignore, so not in your local repo
# 2. Even if rsync'd, the Pi's files take precedence
```

**Method 3: Rsync with Explicit Config Exclusion** (Most Conservative)
```bash
rsync -av \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='config/*.json' \
  /path/to/local/Fermenter-Temp-Controller/ \
  pi@raspberrypi:/path/to/Fermenter-Temp-Controller/
```

## File Structure

```
config/
├── README.md                           # Documentation
├── system_config.json.template         # In git (default values)
├── temp_control_config.json.template   # In git (default values)
├── tilt_config.json.template           # In git (default values)
├── system_config.json                  # NOT in git (your settings)
├── temp_control_config.json            # NOT in git (your settings)
└── tilt_config.json                    # NOT in git (your settings)
```

## What Changed

### Before (Problematic)
- Config files with user data were tracked in git
- `rsync` or `git pull` would overwrite user settings
- Data loss on every update

### After (Fixed)
- Templates are tracked in git
- Actual configs are gitignored
- User data persists across updates
- Application auto-creates configs from templates on first run

## Troubleshooting

### "My settings disappeared after updating!"

If this happened before you applied this fix:

1. Check if you have a backup (system backup, restore feature, etc.)
2. If no backup, you'll need to re-enter your settings
3. After re-entering, this fix ensures it won't happen again

### "Config files missing after update"

The application automatically creates them from templates on startup. Just run:
```bash
python3 app.py
```

### "I want to reset to defaults"

```bash
cd config/
rm system_config.json temp_control_config.json tilt_config.json
# Restart app - configs will be recreated from templates
python3 ../app.py
```

## Benefits

✅ **No more data loss** during code updates  
✅ **Automatic initialization** from templates  
✅ **Backward compatible** with existing workflows  
✅ **Git-friendly** - no merge conflicts in config files  
✅ **Deployment-friendly** - rsync won't clobber your data  

## Questions?

If you encounter issues with the migration, please open a GitHub issue with:
- Your update method (git pull, rsync, etc.)
- Any error messages
- Whether you're upgrading or installing fresh
