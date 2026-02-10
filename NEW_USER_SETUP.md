# New User Setup Guide

This repository has been prepared for sharing with new users. Your personal data is protected and will not be shared when others clone the repository.

## What Was Changed

### 1. Personal Data Removed from Git Tracking

The following personal data files have been removed from git version control:
- `batches/cf38d0a8.jsonl.backup` - Your batch data backup
- `logs/error.log` - Your error logs
- `logs/kasa_activity_monitoring.jsonl` - Your Kasa plug activity logs
- `logs/notifications_log.jsonl` - Your notification history
- `logs/warning.log` - Your warning logs

These files still exist on your local system but are no longer tracked by git.

### 2. Enhanced .gitignore

Updated `.gitignore` to ensure all user data remains private:
- All log files (`logs/*.log`, `logs/*.jsonl`)
- All batch data (`batches/*.jsonl`, `batches/*.json`, `batches/*.backup`)
- All export files (`export/*.csv`)
- All user configuration files (`config/*.json`)

### 3. Template Files

Configuration template files are provided for new users:
- `config/system_config.json.template` - Generic brewery/brewer names
- `config/temp_control_config.json.template` - Safe placeholder values
- `config/tilt_config.json.template` - Empty batch information

### 4. Automatic Configuration

The application automatically creates configuration files from templates on first run:
- New users get fresh config files from templates
- Your existing config files are preserved (not in git)
- Updates via `git pull` won't overwrite your settings

## For New Users

When someone clones this repository, they will:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RabbitFarmer/Fermenter-Temp-Controller.git
   cd Fermenter-Temp-Controller
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

3. **Start the application:**
   ```bash
   ./start.sh
   ```

4. **Configure via web interface:**
   - The app automatically creates config files from templates
   - Users enter their own brewery name, Kasa plug IPs, etc.
   - Their data remains private on their system

## Privacy Guarantees

✅ **No personal data in the repository:**
- No batch data or fermentation logs
- No Kasa plug activity logs
- No personal configuration files
- Only template files with placeholder values

✅ **User data stays private:**
- Configuration files created locally
- Data files created locally
- Git ignores all user data files
- Updates don't overwrite user settings

✅ **Clean clone experience:**
- New users start with empty data directories
- Templates provide safe starting values
- Web interface for easy configuration

## Updating Your Installation

When you pull updates from the repository:

```bash
git pull origin main
```

Your personal files are safe because:
1. They're not tracked by git
2. They're in `.gitignore`
3. Git won't touch them during pull/merge

## Deployment to Raspberry Pi

If you sync to a Raspberry Pi, your settings are preserved:

```bash
# Option 1: Exclude .json files (safest)
rsync -av --exclude='*.json' /path/to/repo/ pi@raspberrypi:/path/to/app/

# Option 2: Sync everything (safe because .json files aren't in git)
rsync -av /path/to/repo/ pi@raspberrypi:/path/to/app/
```

## Documentation

For more information, see:
- [README.md](README.md) - Quick start guide
- [config/README.md](config/README.md) - Configuration file details
- [docs/INSTALLATION.md](docs/INSTALLATION.md) - Detailed installation guide

---

**Summary:** This repository is now safe to share publicly. New users will get a clean installation with template files, and your personal data will remain private on your local system.
