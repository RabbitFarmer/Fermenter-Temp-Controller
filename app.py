#!/usr/bin/env python3
"""
app.py - FermenterApp main Flask application.

This file provides the full Flask app used in the conversation:
- BLE scanning (BleakScanner) if available
- Per-brew JSONL files under batches/{brewid}.jsonl (migrates legacy batch_{COLOR}_{BREWID}_{MMDDYYYY}.jsonl)
- Restricted control log in temp_control_log.jsonl
- Kasa worker integration (if kasa_worker available)
- Per-batch append_sample_to_batch_jsonl and forward_to_third_party_if_configured
- Chart Plotly page and /chart_data/<identifier> endpoint
- UI routes: dashboard, tilt_config, batch_settings, temp_config, update_temp_config, temp_report,
  export_temp_csv, scan_kasa_plugs, live_snapshot, reset_logs, exit_system, system_config
- Program entry runs Flask on 0.0.0.0:5000 in debug mode (when run directly)
"""

import asyncio
import hashlib
import json
import os
import shutil
import smtplib
import threading
import time
from collections import deque, defaultdict
from datetime import datetime
from math import ceil
from multiprocessing import Process, Queue
import subprocess
import signal

from email.mime.text import MIMEText
from flask import (Flask, abort, jsonify, redirect, render_template, request,
                   url_for, make_response)

# Optional imports
try:
    from bleak import BleakScanner
except Exception:
    BleakScanner = None

try:
    from tilt_static import TILT_UUIDS, COLOR_MAP
except Exception:
    TILT_UUIDS = {}
    COLOR_MAP = {}

try:
    from kasa_worker import kasa_worker
except Exception:
    kasa_worker = None

try:
    import requests
except Exception:
    requests = None

# Optional psutil for process management
try:
    import psutil
except Exception:
    psutil = None

app = Flask(__name__)

# --- Files and global constants ---------------------------------------------
LOG_PATH = 'temp_control/temp_control_log.jsonl'        # control events only
BATCHES_DIR = 'batches'                    # per-batch jsonl files live here
PER_PAGE = 30

# Config files
TILT_CONFIG_FILE = 'config/tilt_config.json'
TEMP_CFG_FILE = 'config/temp_control_config.json'
SYSTEM_CFG_FILE = 'config/system_config.json'

# Chart caps
DEFAULT_CHART_LIMIT = 500
MAX_CHART_LIMIT = 2000
MAX_ALL_LIMIT = 10000
MAX_FILENAME_LENGTH = 50

# --- Initialize config files from templates if they don't exist -------------
def ensure_config_files():
    """
    Ensure config files exist by copying from templates if needed.
    This prevents rsync/git pull from overwriting user's configuration data.
    """
    config_files = [
        ('config/system_config.json', 'config/system_config.json.template'),
        ('config/temp_control_config.json', 'config/temp_control_config.json.template'),
        ('config/tilt_config.json', 'config/tilt_config.json.template')
    ]
    
    for config_file, template_file in config_files:
        if not os.path.exists(config_file):
            if os.path.exists(template_file):
                try:
                    shutil.copy2(template_file, config_file)
                    print(f"[INIT] Created {config_file} from template")
                except Exception as e:
                    print(f"[INIT] Error creating {config_file} from template: {e}")
            else:
                print(f"[INIT] Warning: Neither {config_file} nor {template_file} exists")

ensure_config_files()

# --- Stop other app.py processes on startup --------------------------------
def stop_other_app_py():
    current_pid = os.getpid()
    stopped = []
    errors = []
    if psutil:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    pid = proc.info['pid']
                    if pid == current_pid:
                        continue
                    cmdline = proc.info.get('cmdline') or []
                    name = proc.info.get('name') or ''
                    if any('app.py' in str(p) for p in cmdline) or 'app.py' in name:
                        try:
                            proc.terminate()
                            proc.wait(timeout=5)
                            stopped.append(pid)
                        except Exception:
                            try:
                                proc.kill()
                                stopped.append(pid)
                            except Exception as e:
                                errors.append((pid, str(e)))
                except Exception:
                    continue
            return {"stopped": stopped, "errors": errors}
        except Exception as e:
            errors.append(("psutil_iter", str(e)))

    try:
        pgrep = subprocess.run(['pgrep', '-f', 'app.py'], capture_output=True, text=True)
        if pgrep.returncode == 0:
            for line in pgrep.stdout.splitlines():
                try:
                    pid = int(line.strip())
                except Exception:
                    continue
                if pid == current_pid:
                    continue
                try:
                    os.kill(pid, signal.SIGTERM)
                    stopped.append(pid)
                except Exception as e:
                    try:
                        os.kill(pid, signal.SIGKILL)
                        stopped.append(pid)
                    except Exception as e2:
                        errors.append((pid, f"{e} / {e2}"))
    except Exception as e:
        errors.append(("pgrep", str(e)))

    return {"stopped": stopped, "errors": errors}

try:
    stopped_info = stop_other_app_py()
    print(f"[STARTUP] stop_other_app_py result: {stopped_info}")
except Exception as e:
    print(f"[STARTUP] startup housekeeping failed: {e}")

# --- Utilities --------------------------------------------------------------
def load_json(path, fallback):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return fallback

def save_json(path, data):
    try:
        # Ensure the directory exists
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"[LOG] Error saving JSON to {path}: {e}")
        return False

# --- New: Append batch metadata to batch jsonl ------------------------------
def append_batch_metadata_to_batch_jsonl(color, batch_entry):
    """Append a batch_metadata event to the relevant batch JSONL file."""
    brewid = batch_entry.get("brewid")
    if not color or not brewid:
        return False
    path = batch_jsonl_filename(color, brewid)
    entry = {
        "event": "batch_metadata",
        "payload": dict(batch_entry, timestamp=datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    }
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except Exception as e:
        print(f"[LOG] Could not append batch_metadata for {color}: {e}")
        return False

# --- Restricted control-log writer -----------------------------------------
ALLOWED_EVENTS = {
    "tilt_reading": "SAMPLE",
    "heating_on": "HEATING-PLUG TURNED ON",
    "heating_off": "HEATING-PLUG TURNED OFF",
    "cooling_on": "COOLING-PLUG TURNED ON",
    "cooling_off": "COOLING-PLUG TURNED OFF",
    "temp_below_low_limit": "TEMP BELOW LOW LIMIT",
    "temp_above_high_limit": "TEMP ABOVE HIGH LIMIT",
    "temp_in_range": "IN RANGE",
    "temp_control_mode": "MODE_SELECTED",
    "temp_control_mode_changed": "MODE_CHANGED",
    "temp_control_started": "TEMP CONTROL STARTED",
}

# Create a set of allowed event values for O(1) lookup performance
ALLOWED_EVENT_VALUES = set(ALLOWED_EVENTS.values())

def _format_control_log_entry(event_type, payload):
    ts = datetime.utcnow()
    iso_ts = ts.replace(microsecond=0).isoformat() + "Z"
    date = ts.strftime("%Y-%m-%d")
    time_str = ts.strftime("%H:%M:%S")

    tilt_color = ""
    try:
        if isinstance(payload, dict):
            tilt_color = payload.get("tilt_color") or payload.get("tilt") or payload.get("color") or ""
    except Exception:
        tilt_color = ""

    def _to_float(val):
        try:
            if val is None or val == "":
                return None
            return float(val)
        except Exception:
            return None

    low = _to_float(payload.get("low_limit") if isinstance(payload, dict) else None)
    high = _to_float(payload.get("high_limit") if isinstance(payload, dict) else None)

    cur = None
    grav = None
    if isinstance(payload, dict):
        cur = payload.get("current_temp")
        if cur is None:
            cur = payload.get("temp_f") if payload.get("temp_f") is not None else payload.get("temp")
        grav = payload.get("gravity") or payload.get("grav") or payload.get("sg")

    cur = _to_float(cur)
    grav = _to_float(grav)

    event_label = ALLOWED_EVENTS.get(event_type, event_type)
    
    # Get brewid from tilt config if we have a tilt_color
    brewid = None
    if tilt_color and 'tilt_cfg' in globals():
        try:
            brewid = tilt_cfg.get(tilt_color, {}).get('brewid')
        except Exception:
            brewid = None

    entry = {
        "timestamp": iso_ts,
        "date": date,
        "time": time_str,
        "tilt_color": tilt_color,
        "brewid": brewid,
        "low_limit": low,
        "current_temp": cur,
        "temp_f": cur,
        "gravity": grav,
        "high_limit": high,
        "event": event_label
    }
    return entry

def append_control_log(event_type, payload):
    if event_type not in ALLOWED_EVENTS:
        return
    enable_heat = bool(temp_cfg.get("enable_heating")) if 'temp_cfg' in globals() else False
    enable_cool = bool(temp_cfg.get("enable_cooling")) if 'temp_cfg' in globals() else False
    if not (enable_heat or enable_cool):
        return
    try:
        d = os.path.dirname(LOG_PATH)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        entry = _format_control_log_entry(event_type, payload or {})
        with open(LOG_PATH, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[LOG] Failed to append to control log: {e}")

@app.template_filter('localtime')
def localtime_filter(iso_str):
    from datetime import datetime, timezone
    try:
        if not iso_str:
            return ''
        if isinstance(iso_str, datetime):
            dt = iso_str
        else:
            s = str(iso_str)
            if s.endswith('Z'):
                try:
                    dt = datetime.fromisoformat(s.rstrip('Z')).replace(tzinfo=timezone.utc)
                except Exception:
                    return s
            else:
                try:
                    dt = datetime.fromisoformat(s)
                except Exception:
                    try:
                        dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
                        dt = dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        return s

        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            dt = dt.replace(tzinfo=timezone.utc)

        local_tz = datetime.now().astimezone().tzinfo
        local_dt = dt.astimezone(local_tz)
        return local_dt.strftime('%Y-%m-%d %I:%M:%S %p')
    except Exception:
        return iso_str

# --- Load configs ----------------------------------------------------------
tilt_cfg = load_json(TILT_CONFIG_FILE, {})
temp_cfg = load_json(TEMP_CFG_FILE, {})
system_cfg = load_json(SYSTEM_CFG_FILE, {})

def ensure_temp_defaults():
    temp_cfg.setdefault("current_temp", None)
    temp_cfg.setdefault("low_limit", 0.0)
    temp_cfg.setdefault("high_limit", 0.0)
    temp_cfg.setdefault("enable_heating", False)
    temp_cfg.setdefault("enable_cooling", False)
    temp_cfg.setdefault("heating_plug", "")
    temp_cfg.setdefault("cooling_plug", "")
    temp_cfg.setdefault("heater_on", False)
    temp_cfg.setdefault("cooler_on", False)
    temp_cfg.setdefault("heater_pending", False)
    temp_cfg.setdefault("cooler_pending", False)
    temp_cfg.setdefault("heating_error", False)
    temp_cfg.setdefault("cooling_error", False)
    temp_cfg.setdefault("notifications_trigger", False)
    temp_cfg.setdefault("notification_last_sent", None)
    temp_cfg.setdefault("notification_comm_failure", False)
    temp_cfg.setdefault("sms_error", False)
    temp_cfg.setdefault("email_error", False)
    temp_cfg.setdefault("control_initialized", False)
    temp_cfg.setdefault("last_logged_low_limit", temp_cfg.get("low_limit"))
    temp_cfg.setdefault("last_logged_high_limit", temp_cfg.get("high_limit"))
    temp_cfg.setdefault("last_logged_enable_heating", temp_cfg.get("enable_heating"))
    temp_cfg.setdefault("last_logged_enable_cooling", temp_cfg.get("enable_cooling"))
    # New flag to turn on/off the entire temp-control UI and behavior:
    temp_cfg.setdefault("temp_control_enabled", True)
    # New flag to control active monitoring/recording (user-controlled switch):
    temp_cfg.setdefault("temp_control_active", False)
    # Trigger states for event-based logging:
    temp_cfg.setdefault("in_range_trigger_armed", True)
    temp_cfg.setdefault("above_limit_trigger_armed", True)
    temp_cfg.setdefault("below_limit_trigger_armed", True)

ensure_temp_defaults()

def ensure_all_tilts():
    try:
        for color in TILT_UUIDS.values():
            if color not in tilt_cfg:
                tilt_cfg[color] = {
                    "beer_name": "",
                    "batch_name": "",
                    "ferm_start_date": "",
                    "recipe_og": "",
                    "recipe_fg": "",
                    "recipe_abv": "",
                    "actual_og": None,
                    "brewid": "",
                    "og_confirmed": False
                }
    except Exception:
        pass

ensure_all_tilts()

_TZ_ABBREV_MAP = {
    'EST': 'America/New_York',
    'EDT': 'America/New_York',
    'CST': 'America/Chicago',
    'CDT': 'America/Chicago',
    'MST': 'America/Denver',
    'MDT': 'America/Denver',
    'PST': 'America/Los_Angeles',
    'PDT': 'America/Los_Angeles',
    'UTC': 'UTC'
}
tz = (system_cfg.get('timezone') if isinstance(system_cfg, dict) else None) or os.environ.get('TZ') or 'UTC'
tz = _TZ_ABBREV_MAP.get(tz, tz)
os.environ['TZ'] = tz
try:
    time.tzset()
except Exception:
    pass

# --- Inter-process queues and kasa worker startup --------------------------
kasa_queue = Queue()
kasa_result_queue = Queue()
kasa_proc = None

if kasa_worker:
    try:
        kasa_proc = Process(target=kasa_worker, args=(kasa_queue, kasa_result_queue))
        kasa_proc.daemon = True
        kasa_proc.start()
        print("[LOG] Started kasa_worker process")
    except Exception as e:
        print("[LOG] Could not start kasa_worker:", e)
else:
    print("[LOG] kasa_worker not available — plug control disabled")

# --- Live runtime data -----------------------------------------------------
live_tilts = {}
tilt_status = {}

last_tilt_log_ts = {}
batch_notification_state = {}  # Track notification state per tilt/brewid

# Notification timing constants
DAILY_REPORT_COOLDOWN_HOURS = 23  # Prevent duplicate daily reports (allows timing variance)
DAILY_REPORT_WINDOW_MINUTES = 5   # Time window for daily report triggering
BATCH_MONITORING_INTERVAL_SECONDS = 300  # Check signal loss and daily reports every 5 minutes

def generate_brewid(beer_name, batch_name, date_str):
    id_str = f"{beer_name}-{batch_name}-{date_str}"
    return hashlib.sha256(id_str.encode('utf-8')).hexdigest()[:8]

def update_live_tilt(color, gravity, temp_f, rssi):
    cfg = tilt_cfg.get(color, {})
    live_tilts[color] = {
        "gravity": round(gravity, 3) if gravity is not None else None,
        "temp_f": temp_f,
        "rssi": rssi,
        "timestamp": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "color_code": COLOR_MAP.get(color, "#333"),
        "beer_name": cfg.get("beer_name", ""),
        "batch_name": cfg.get("batch_name", ""),
        "brewid": cfg.get("brewid", ""),
        "recipe_og": cfg.get("recipe_og", ""),
        "recipe_fg": cfg.get("recipe_fg", ""),
        "recipe_abv": cfg.get("recipe_abv", ""),
        "actual_og": cfg.get("actual_og", ""),
        "og_confirmed": cfg.get("og_confirmed", False),
        "original_gravity": cfg.get("actual_og", 0),
    }

def get_current_temp_for_control_tilt():
    color = temp_cfg.get("tilt_color")
    if color and color in live_tilts:
        return live_tilts[color].get("temp_f")
    for info in live_tilts.values():
        if info.get("temp_f") is not None:
            return info.get("temp_f")
    return None

def log_tilt_reading(color, gravity, temp_f, rssi):
    """
    Log tilt readings with interval-based rate limiting and batch tracking.
    
    This function handles:
    - Rate-limited logging based on tilt_logging_interval_minutes
    - Recording readings to control log and batch-specific JSONL files
    - Forwarding to third-party services if configured
    - Triggering batch notifications (signal loss, fermentation start, etc.)
    
    Args:
        color: Tilt color identifier
        gravity: Specific gravity reading
        temp_f: Temperature in Fahrenheit
        rssi: Bluetooth signal strength
    """
    cfg = tilt_cfg.get(color, {})
    brewid = cfg.get('brewid', '')
    
    # Rate limiting based on tilt_logging_interval_minutes
    interval_minutes = int(system_cfg.get('tilt_logging_interval_minutes', 15))
    now = datetime.utcnow()
    last_log = last_tilt_log_ts.get(color)
    
    if last_log:
        elapsed = (now - last_log).total_seconds() / 60.0
        if elapsed < interval_minutes:
            return
    
    last_tilt_log_ts[color] = now
    
    # Create payload
    payload = {
        "timestamp": now.replace(microsecond=0).isoformat() + "Z",
        "tilt_color": color,
        "gravity": round(gravity, 3) if gravity is not None else None,
        "temp_f": temp_f,
        "rssi": rssi,
        "beer_name": cfg.get("beer_name", ""),
        "batch_name": cfg.get("batch_name", ""),
        "brewid": brewid,
        "recipe_og": cfg.get("recipe_og", ""),
        "actual_og": cfg.get("actual_og"),
        "og_confirmed": cfg.get("og_confirmed", False)
    }
    
    # Log to control log
    append_control_log("tilt_reading", payload)
    
    # Log to batch-specific jsonl
    if brewid:
        append_sample_to_batch_jsonl(color, brewid, payload)
    
    # Forward to third-party if configured
    forward_to_third_party_if_configured(payload)
    
    # Track batch notification state and check triggers
    check_batch_notifications(color, gravity, temp_f, brewid, cfg)

def detection_callback(device, advertisement_data):
    try:
        mfg_data = advertisement_data.manufacturer_data
        if not mfg_data:
            return
        raw = list(mfg_data.values())[0]
        if len(raw) < 22:
            return
        uuid = raw[2:18].hex()
        color = TILT_UUIDS.get(uuid) or TILT_UUIDS.get(uuid.lower()) or TILT_UUIDS.get(uuid.upper())
        if not color:
            return
        try:
            temp_f = int.from_bytes(raw[18:20], byteorder='big')
            gravity = int.from_bytes(raw[20:22], byteorder='big') / 1000.0
        except Exception:
            return
        rssi = advertisement_data.rssi
        update_live_tilt(color, gravity, temp_f, rssi)
        try:
            log_tilt_reading(color, gravity, temp_f, rssi)
        except Exception as log_err:
            print(f"[BLE] log_tilt_reading failed for {color}: {log_err}")
    except Exception as e:
        print("[BLE] detection_callback exception:", e)

# --- Batch rotation / archival (legacy, kept for compatibility) ------------
def rotate_and_archive_old_history(color, old_brewid, old_cfg):
    try:
        if not old_brewid and not color:
            return False
        os.makedirs(BATCHES_DIR, exist_ok=True)
        archive_name = f"{color}_{old_cfg.get('beer_name','unknown')}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jsonl"
        safe_archive = os.path.join(BATCHES_DIR, archive_name.replace(' ', '_'))
        moved = 0
        remaining_lines = []
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                    except Exception:
                        remaining_lines.append(line)
                        continue
                    if obj.get('event') != 'SAMPLE':
                        remaining_lines.append(line)
                        continue
                    payload = obj or {}
                    if isinstance(payload, dict) and payload.get('tilt_color') and old_cfg.get('brewid') == old_brewid:
                        with open(safe_archive, 'a') as af:
                            af.write(json.dumps(obj) + "\n")
                        moved += 1
                    else:
                        remaining_lines.append(line)
        try:
            with open(LOG_PATH, 'w') as f:
                f.writelines(remaining_lines)
        except Exception as e:
            print(f"[LOG] Error rewriting main log after archive: {e}")

        append_control_log("temp_control_mode_changed", {"tilt_color": color, "low_limit": temp_cfg.get("low_limit"), "current_temp": temp_cfg.get("current_temp"), "high_limit": temp_cfg.get("high_limit")})
        return True
    except Exception as e:
        print(f"[LOG] rotate_and_archive_old_history error: {e}")
        return False

# --- batches: per-batch jsonl helpers --------------------------------------
def ensure_batches_dir():
    try:
        os.makedirs(BATCHES_DIR, exist_ok=True)
    except Exception as e:
        print(f"[LOG] Could not create batches dir {BATCHES_DIR}: {e}")

def normalize_to_mmddyyyy(date_str):
    if not date_str:
        return datetime.utcnow().strftime("%m%d%Y")
    for fmt in ("%m-%d-%Y", "%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d", "%m%d%Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%m%d%Y")
        except Exception:
            continue
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%m%d%Y")
    except Exception:
        return datetime.utcnow().strftime("%m%d%Y")

def normalize_to_yyyymmdd(date_str):
    """Convert various date formats to YYYYmmdd format."""
    if not date_str:
        return datetime.utcnow().strftime("%Y%m%d")
    for fmt in ("%m-%d-%Y", "%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d", "%m%d%Y", "%Y%m%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y%m%d")
        except Exception:
            continue
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y%m%d")
    except Exception:
        return datetime.utcnow().strftime("%Y%m%d")

def sanitize_filename(name):
    """Sanitize a string for use in a filename."""
    # Replace invalid characters with underscore
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\r', '\t']
    result = name
    for char in invalid_chars:
        result = result.replace(char, '_')
    # Also replace spaces and remove control characters
    result = result.replace(' ', '_')
    # Remove ASCII control characters (0-31)
    result = ''.join(c if ord(c) >= 32 else '_' for c in result)
    # Limit length to avoid overly long filenames
    return result[:MAX_FILENAME_LENGTH]

def batch_jsonl_filename(color, brewid, created_date_mmddyyyy=None, beer_name=None, batch_name=None):
    """Generate batch JSONL filename in format: brewname_YYYYmmdd_brewid.jsonl
    
    First searches for an existing file containing the brewid.
    If found, returns that file to prevent multiple files for the same batch.
    If not found, generates a new filename.
    """
    ensure_batches_dir()
    bid = (brewid or "unknown")
    
    # First, search for any existing file that contains this brewid
    # Match brewid as complete token: either whole filename or preceded by underscore
    try:
        for fn in os.listdir(BATCHES_DIR):
            if not fn.endswith('.jsonl'):
                continue
            # Remove .jsonl extension for matching
            name_without_ext = fn.removesuffix('.jsonl')
            # Match if brewid is the entire name, or ends with _brewid
            # This ensures exact token matching: "abc" matches "abc.jsonl" or "name_abc.jsonl"
            # but NOT "xyzabc.jsonl" (no underscore separator before brewid)
            if name_without_ext == bid or name_without_ext.endswith(f"_{bid}"):
                # Found an existing file with this brewid
                existing_path = os.path.join(BATCHES_DIR, fn)
                print(f"[BATCH] Found existing batch file for brewid {bid}: {fn}")
                return existing_path
    except Exception as e:
        print(f"[BATCH] Error searching for existing batch file: {e}")
    
    # No existing file found, generate a new filename
    # Get beer_name from tilt config if not provided
    if beer_name is None:
        cfg = tilt_cfg.get(color, {})
        beer_name = cfg.get("beer_name", "")
    
    # Create filename with brew name, date, and brewid
    if beer_name:
        safe_beer_name = sanitize_filename(beer_name)
    else:
        safe_beer_name = "Batch"
    
    # Convert date to YYYYmmdd format
    if created_date_mmddyyyy:
        date_yyyymmdd = normalize_to_yyyymmdd(created_date_mmddyyyy)
    else:
        date_yyyymmdd = datetime.utcnow().strftime("%Y%m%d")
    
    fname = f"{safe_beer_name}_{date_yyyymmdd}_{bid}.jsonl"
    print(f"[BATCH] Creating new batch file for brewid {bid}: {fname}")
    return os.path.join(BATCHES_DIR, fname)

def ensure_batch_jsonl_exists(color, brewid, meta=None, created_date_mmddyyyy=None):
    beer_name = None
    if meta and isinstance(meta, dict):
        beer_name = meta.get("beer_name", "")
    if not beer_name:
        cfg = tilt_cfg.get(color, {})
        beer_name = cfg.get("beer_name", "")
    
    path = batch_jsonl_filename(color, brewid, created_date_mmddyyyy=created_date_mmddyyyy, beer_name=beer_name)
    if not os.path.exists(path):
        # Try to migrate legacy files (both old formats)
        try:
            # Try pattern 1: batch_{COLOR}_{brewid}_
            legacy_pattern1 = f"batch_{(color or '').upper()}_{brewid}_"
            # Try pattern 2: {brewid}.jsonl
            legacy_pattern2 = f"{brewid}.jsonl"
            
            migrated = False
            for fn in os.listdir(BATCHES_DIR):
                if migrated:
                    break
                if fn.startswith(legacy_pattern1) or fn == legacy_pattern2:
                    legacy_path = os.path.join(BATCHES_DIR, fn)
                    try:
                        os.rename(legacy_path, path)
                        print(f"[MIGRATE] Renamed legacy {legacy_path} -> {path}")
                        migrated = True
                    except Exception as e:
                        print(f"[MIGRATE] Could not rename {legacy_path} -> {path}: {e}")
        except Exception as e:
            print(f"[MIGRATE] Migration scan failed: {e}")
        try:
            header = {
                "event": "batch_metadata",
                "payload": {
                    "tilt_color": color,
                    "brewid": brewid,
                    "created_date": (created_date_mmddyyyy or datetime.utcnow().strftime("%m%d%Y")),
                    "meta": meta or {}
                }
            }
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(header) + "\n")
        except Exception as e:
            print(f"[LOG] Could not create batch jsonl {path}: {e}")
    return path

def append_sample_to_batch_jsonl(color, brewid, sample_payload, created_date_mmddyyyy=None):
    cfg = tilt_cfg.get(color, {})
    beer_name = cfg.get("beer_name", "")
    path = batch_jsonl_filename(color, brewid, created_date_mmddyyyy=created_date_mmddyyyy, beer_name=beer_name)
    try:
        if not os.path.exists(path):
            ensure_batch_jsonl_exists(color, brewid, meta={"beer_name": beer_name, "batch_name": cfg.get("batch_name", "")}, created_date_mmddyyyy=created_date_mmddyyyy)
        entry = {"event": "sample", "payload": sample_payload}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except Exception as e:
        print(f"[LOG] append_sample_to_batch_jsonl failed for {color}/{brewid}: {e}")
        return False

def write_normalized_tilt_reading(payload, event_name="tilt_reading"):
    try:
        entry = {"event": event_name, "payload": payload}
        dirname = os.path.dirname(LOG_PATH)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except Exception as e:
        print(f"[LOG] write_normalized_tilt_reading failed: {e}")
        return False

def forward_to_third_party_if_configured(payload):
    """
    Forward tilt reading data to configured external services.
    
    Supports two configuration methods:
    1. Per-tilt external_url in tilt_cfg[color] (highest priority)
    2. System-wide external_url_0, external_url_1, external_url_2 in system_cfg
    
    The function will try to send to all configured URLs.
    Automatically transforms the payload to Brewers Friend format if URL contains "brewersfriend.com".
    """
    color = (payload.get("tilt_color") or "").upper()
    if not color:
        return {"forwarded": False, "reason": "no color"}
    
    if requests is None:
        return {"forwarded": False, "reason": "requests library not available"}
    
    # Collect all URLs to forward to
    urls_to_forward = []
    
    # 1. Check per-tilt configuration
    tc = tilt_cfg.get(color) or {}
    tilt_url = tc.get("external_url")
    if tilt_url:
        urls_to_forward.append({
            "url": tilt_url,
            "method": (tc.get("external_method") or "POST").upper(),
            "send_json": bool(tc.get("external_json")) if ("external_json" in tc) else True
        })
    
    # 2. Check system-wide configuration (external_url_0, external_url_1, external_url_2)
    for i in range(3):
        sys_url = system_cfg.get(f"external_url_{i}")
        if sys_url:
            urls_to_forward.append({
                "url": sys_url,
                "method": system_cfg.get("external_method", "POST").upper(),
                "send_json": (system_cfg.get("external_content_type", "form") == "json")
            })
    
    if not urls_to_forward:
        return {"forwarded": False, "reason": "no external_url configured"}
    
    # Forward to all configured URLs
    results = []
    for config in urls_to_forward:
        url = config["url"]
        method = config["method"]
        send_json = config["send_json"]
        
        # Transform payload for Brewers Friend if needed
        if "brewersfriend.com" in url.lower():
            # Brewers Friend expects a specific format with numeric values
            transformed_payload = {
                "name": payload.get("tilt_color", "Tilt"),
                "temp": payload.get("temp_f") if payload.get("temp_f") is not None else 0,
                "temp_unit": "F",
                "gravity": payload.get("gravity") if payload.get("gravity") is not None else 0,
                "gravity_unit": "G",
                "beer": payload.get("beer_name", "") or payload.get("batch_name", ""),
                "comment": f"Batch: {payload.get('batch_name', '')} | BrewID: {payload.get('brewid', '')}"
            }
            forwarding_payload = transformed_payload
            # Brewers Friend always uses JSON
            send_json = True
        else:
            # Use original payload for other services
            forwarding_payload = payload
        
        headers = {}
        try:
            timeout = int(system_cfg.get("external_timeout_seconds", 8) or 8)
            if send_json:
                headers["Content-Type"] = "application/json"
                resp = requests.request(method, url, json=forwarding_payload, headers=headers, timeout=timeout)
            else:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                formdata = {k: ("" if v is None else v) for k, v in forwarding_payload.items() if isinstance(v, (str, int, float)) or v is None}
                resp = requests.request(method, url, data=formdata, headers=headers, timeout=timeout)
            
            result = {"url": url, "forwarded": True, "status_code": resp.status_code, "text": resp.text[:500]}
            results.append(result)
            print(f"[FORWARD] Successfully forwarded tilt {color} to {url}, status: {resp.status_code}")
        except Exception as e:
            result = {"url": url, "forwarded": False, "error": str(e)}
            results.append(result)
            print(f"[FORWARD] Error forwarding tilt {color} to {url}: {e}")
    
    # Return summary
    success_count = sum(1 for r in results if r.get("forwarded"))
    return {
        "forwarded": success_count > 0,
        "success_count": success_count,
        "total_count": len(results),
        "results": results
    }

# --- Notifications helpers -------------------------------------------------
def _smtp_send(recipient, subject, body):
    cfg = system_cfg
    sending_email = cfg.get("sending_email") or cfg.get("email")
    if not (isinstance(cfg, dict) and sending_email):
        print("[LOG] SMTP not configured: no sender email in system_cfg")
        return False
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sending_email
        msg["To"] = recipient
        server = smtplib.SMTP(cfg.get("smtp_host", "localhost"), int(cfg.get("smtp_port", 25)), timeout=10)
        if cfg.get("smtp_starttls"):
            server.starttls()
        # Use sending_email as username and smtp_password (or sending_email_password) for authentication
        smtp_password = cfg.get("smtp_password") or cfg.get("sending_email_password")
        if sending_email and smtp_password and len(smtp_password) > 0:
            server.login(sending_email, smtp_password)
        server.sendmail(sending_email, [recipient], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[LOG] SMTP send failed: {e}")
        return False

def send_email(subject, body):
    recipient = system_cfg.get("email")
    if not recipient:
        print("[LOG] No recipient email configured")
        temp_cfg["email_error"] = True
        return False
    result = _smtp_send(recipient, subject, body)
    temp_cfg["email_error"] = not result
    return result

def send_sms(body):
    mobile = system_cfg.get("mobile")
    gateway = system_cfg.get("sms_gateway_domain")
    if not mobile or not gateway:
        print("[LOG] SMS gateway not configured (mobile or sms_gateway_domain missing)")
        temp_cfg["sms_error"] = True
        return False
    recipient = f"{mobile}@{gateway}"
    result = _smtp_send(recipient, "Fermenter Notification", body)
    temp_cfg["sms_error"] = not result
    return result

def attempt_send_notifications(subject, body):
    # Use system_cfg for notification mode
    mode = (system_cfg.get('warning_mode') or 'NONE').upper()
    success_any = False
    temp_cfg['notifications_trigger'] = True
    
    # Reset error flags before attempting
    temp_cfg['sms_error'] = False
    temp_cfg['email_error'] = False
    
    try:
        if mode == 'EMAIL':
            success_any = send_email(subject, body)
        elif mode == 'SMS':
            success_any = send_sms(body)
        elif mode == 'BOTH':
            e = send_email(subject, body)
            s = send_sms(body)
            success_any = e or s
        else:
            success_any = False
    except Exception:
        success_any = False

    temp_cfg['notifications_trigger'] = False
    if success_any:
        temp_cfg['notification_last_sent'] = datetime.utcnow().isoformat()
        temp_cfg['notification_comm_failure'] = False
        return True
    else:
        temp_cfg['notification_comm_failure'] = True
        # Don't disable notifications on failure - just track the failure
        return False

def send_warning(subject, body):
    mode = (system_cfg.get('warning_mode') or 'NONE').upper()
    if mode == 'NONE':
        return False
    try:
        rate_limit = int(system_cfg.get('notification_rate_limit_seconds', 3600))
    except Exception:
        rate_limit = 3600

    last = temp_cfg.get('notification_last_sent')
    if last:
        try:
            last_dt = datetime.fromisoformat(last)
            elapsed = (datetime.utcnow() - last_dt).total_seconds()
            if elapsed < rate_limit:
                return False
        except Exception:
            pass

    temp_cfg['notifications_trigger'] = True
    ok = attempt_send_notifications(subject, body)
    return ok

def send_temp_control_notification(event_type, temp, low_limit, high_limit, tilt_color):
    """
    Send notifications for temperature control events if enabled in settings.
    """
    # Get temp control notification settings
    temp_notif_cfg = system_cfg.get('temp_control_notifications', {})
    
    # Check if this specific event type is enabled
    if not temp_notif_cfg.get(f'enable_{event_type}', False):
        return
    
    brewery_name = system_cfg.get('brewery_name', 'Unknown Brewery')
    now = datetime.utcnow()
    
    # Create caption based on event type
    caption_map = {
        'temp_below_low_limit': f'Temperature Below Low Limit - Current: {temp:.1f}°F, Low Limit: {low_limit:.1f}°F',
        'temp_above_high_limit': f'Temperature Above High Limit - Current: {temp:.1f}°F, High Limit: {high_limit:.1f}°F',
        'heating_on': f'Heating Turned On - Current: {temp:.1f}°F, Low Limit: {low_limit:.1f}°F',
        'heating_off': f'Heating Turned Off - Current: {temp:.1f}°F',
        'cooling_on': f'Cooling Turned On - Current: {temp:.1f}°F, High Limit: {high_limit:.1f}°F',
        'cooling_off': f'Cooling Turned Off - Current: {temp:.1f}°F'
    }
    
    caption = caption_map.get(event_type, f'Temperature Control Event: {event_type}')
    
    subject = f"{brewery_name} - Temperature Control Alert"
    body = f"""Brewery Name: {brewery_name}
Date: {now.strftime('%Y-%m-%d')}
Time: {now.strftime('%H:%M:%S')}
Tilt Color: {tilt_color}

{caption}"""
    
    attempt_send_notifications(subject, body)

def check_batch_notifications(color, gravity, temp_f, brewid, cfg):
    """
    Check and trigger batch-specific notifications:
    1. Loss of signal detection
    2. Fermentation starting detection
    3. Daily report scheduling (handled separately in periodic task)
    """
    if not brewid:
        return
    
    # Get notification settings from system config
    notif_cfg = system_cfg.get('batch_notifications', {})
    
    # Initialize state for this brewid if needed
    if brewid not in batch_notification_state:
        batch_notification_state[brewid] = {
            'last_reading_time': datetime.utcnow(),
            'signal_lost': False,
            'signal_loss_notified': False,
            'fermentation_started': False,
            'fermentation_start_notified': False,
            'gravity_history': [],
            'last_daily_report': None
        }
    
    state = batch_notification_state[brewid]
    state['last_reading_time'] = datetime.utcnow()
    
    # Reset signal loss flag when we receive a reading
    if state['signal_lost']:
        state['signal_lost'] = False
        state['signal_loss_notified'] = False
    
    # Track gravity history for fermentation start detection
    if gravity is not None:
        state['gravity_history'].append({
            'gravity': gravity,
            'timestamp': datetime.utcnow()
        })
        # Keep only recent readings (last 10)
        if len(state['gravity_history']) > 10:
            state['gravity_history'].pop(0)
    
    # Check fermentation starting condition
    if notif_cfg.get('enable_fermentation_starting', True):
        check_fermentation_starting(color, brewid, cfg, state)

def check_fermentation_starting(color, brewid, cfg, state):
    """
    Detect fermentation start: 3 consecutive readings at least 0.010 below starting gravity.
    """
    if state.get('fermentation_start_notified'):
        return
    
    actual_og = cfg.get('actual_og')
    if not actual_og:
        return
    
    try:
        starting_gravity = float(actual_og)
    except (ValueError, TypeError):
        return
    
    history = state.get('gravity_history', [])
    if len(history) < 3:
        return
    
    # Check last 3 readings
    last_three = history[-3:]
    all_below_threshold = all(
        reading['gravity'] is not None and reading['gravity'] <= (starting_gravity - 0.010)
        for reading in last_three
    )
    
    if all_below_threshold:
        current_gravity = last_three[-1]['gravity']
        brewery_name = system_cfg.get('brewery_name', 'Unknown Brewery')
        beer_name = cfg.get('beer_name', 'Unknown Beer')
        
        subject = f"{brewery_name} - Fermentation Started"
        body = f"""Brewery Name: {brewery_name}
Tilt Color: {color}
Brew Name: {beer_name}
Date/Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

Fermentation has started.
Gravity at start: {starting_gravity:.3f}
Gravity now: {current_gravity:.3f}"""
        
        if attempt_send_notifications(subject, body):
            state['fermentation_start_notified'] = True
            state['fermentation_started'] = True

def check_signal_loss():
    """
    Periodic check for loss of signal on all active tilts.
    Run this in a separate thread or periodic task.
    """
    notif_cfg = system_cfg.get('batch_notifications', {})
    if not notif_cfg.get('enable_loss_of_signal', True):
        return
    
    loss_timeout_minutes = int(notif_cfg.get('loss_of_signal_timeout_minutes', 30))
    now = datetime.utcnow()
    
    for brewid, state in batch_notification_state.items():
        if state.get('signal_loss_notified'):
            continue
        
        last_reading = state.get('last_reading_time')
        if not last_reading:
            continue
        
        elapsed_minutes = (now - last_reading).total_seconds() / 60.0
        
        if elapsed_minutes >= loss_timeout_minutes:
            # Find the tilt color and config for this brewid
            color = None
            cfg = None
            for tilt_color, tilt_data in tilt_cfg.items():
                if tilt_data.get('brewid') == brewid:
                    color = tilt_color
                    cfg = tilt_data
                    break
            
            if color and cfg:
                brewery_name = system_cfg.get('brewery_name', 'Unknown Brewery')
                beer_name = cfg.get('beer_name', 'Unknown Beer')
                
                subject = f"{brewery_name} - Loss of Signal"
                body = f"""Brewery Name: {brewery_name}
Tilt Color: {color}
Brew Name: {beer_name}
Date/Time: {now.strftime('%Y-%m-%d %H:%M:%S')}

Loss of Signal -- Receiving no tilt readings"""
                
                if attempt_send_notifications(subject, body):
                    state['signal_lost'] = True
                    state['signal_loss_notified'] = True

def send_daily_report():
    """
    Send daily progress report for all active tilts.
    Should be scheduled to run at user-specified time.
    """
    notif_cfg = system_cfg.get('batch_notifications', {})
    if not notif_cfg.get('enable_daily_report', True):
        return
    
    brewery_name = system_cfg.get('brewery_name', 'Unknown Brewery')
    
    for color, cfg in tilt_cfg.items():
        brewid = cfg.get('brewid')
        if not brewid:
            continue
        
        # Check if we have recent data for this tilt
        if color not in live_tilts:
            continue
        
        state = batch_notification_state.get(brewid, {})
        
        # Check if we already sent today's report (within last 23 hours to allow for timing variance)
        last_report = state.get('last_daily_report')
        if last_report:
            try:
                last_report_dt = datetime.fromisoformat(last_report)
                # Use DAILY_REPORT_COOLDOWN_HOURS to ensure daily (once per ~24h) but allow for timing variance
                if (datetime.utcnow() - last_report_dt).total_seconds() < DAILY_REPORT_COOLDOWN_HOURS * 3600:
                    continue
            except Exception:
                pass
        
        beer_name = cfg.get('beer_name', 'Unknown Beer')
        actual_og = cfg.get('actual_og')
        
        if not actual_og:
            continue
        
        try:
            starting_gravity = float(actual_og)
        except (ValueError, TypeError):
            continue
        
        current_data = live_tilts.get(color, {})
        current_gravity = current_data.get('gravity')
        
        if current_gravity is None:
            continue
        
        net_change = starting_gravity - current_gravity
        
        # Calculate change since yesterday (24 hours ago)
        change_since_yesterday = 0.0
        history = state.get('gravity_history', [])
        if history:
            # Find reading closest to 24 hours ago
            target_time = datetime.utcnow() - timedelta(hours=24)
            closest_reading = None
            min_diff = float('inf')
            
            for reading in history:
                time_diff = abs((reading['timestamp'] - target_time).total_seconds())
                if time_diff < min_diff:
                    min_diff = time_diff
                    closest_reading = reading
            
            if closest_reading and closest_reading['gravity'] is not None:
                change_since_yesterday = closest_reading['gravity'] - current_gravity
        
        subject = f"{brewery_name} - Daily Report"
        body = f"""Brewery Name: {brewery_name}
Tilt Color: {color}
Brew Name: {beer_name}
Date/Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

Starting Gravity: {starting_gravity:.3f}
Last Gravity: {current_gravity:.3f}
Net Change: {net_change:.3f}
Change since yesterday: {change_since_yesterday:.3f}"""
        
        if attempt_send_notifications(subject, body):
            state['last_daily_report'] = datetime.utcnow().isoformat()

# --- Kasa command dedupe & rate limit -------------------------------------
_last_kasa_command = {}
_KASA_RATE_LIMIT_SECONDS = int(system_cfg.get("kasa_rate_limit_seconds", 10) or 10)

def _should_send_kasa_command(url, action):
    if not url:
        return False
    if not kasa_worker:
        return False
    if url == temp_cfg.get("heating_plug") and temp_cfg.get("heater_pending"):
        return False
    if url == temp_cfg.get("cooling_plug") and temp_cfg.get("cooler_pending"):
        return False
    if url == temp_cfg.get("heating_plug"):
        if temp_cfg.get("heater_on") and action == "on":
            return False
        if (not temp_cfg.get("heater_on")) and action == "off":
            return False
    if url == temp_cfg.get("cooling_plug"):
        if temp_cfg.get("cooler_on") and action == "on":
            return False
        if (not temp_cfg.get("cooler_on")) and action == "off":
            return False
    last = _last_kasa_command.get(url)
    if last and last.get("action") == action:
        if (time.time() - last.get("ts", 0.0)) < _KASA_RATE_LIMIT_SECONDS:
            return False
    return True

def _record_kasa_command(url, action):
    _last_kasa_command[url] = {"action": action, "ts": time.time()}

# --- Control functions -----------------------------------------------------
def control_heating(state):
    enabled = temp_cfg.get("enable_heating")
    url = temp_cfg.get("heating_plug", "")
    if not enabled or not url:
        temp_cfg["heater_pending"] = False
        temp_cfg["heater_on"] = False
        return
    if not _should_send_kasa_command(url, state):
        return
    kasa_queue.put({'mode': 'heating', 'url': url, 'action': state})
    _record_kasa_command(url, state)
    temp_cfg["heater_pending"] = True

def control_cooling(state):
    enabled = temp_cfg.get("enable_cooling")
    url = temp_cfg.get("cooling_plug", "")
    if not enabled or not url:
        temp_cfg["cooler_pending"] = False
        temp_cfg["cooler_on"] = False
        return
    if not _should_send_kasa_command(url, state):
        return
    kasa_queue.put({'mode': 'cooling', 'url': url, 'action': state})
    _record_kasa_command(url, state)
    temp_cfg["cooler_pending"] = True

# --- Temperature control logic (normalized + limited logging) -------------
def temperature_control_logic():
    """
    Main control loop logic.

    Important behavior change:
    - If temp_control_enabled is False, the function will NOT modify or clear the stored
      temp_cfg fields (heater_on, cooler_on, pending flags, limits, plugs, etc.).
      It only sets a 'Disabled' status and returns. This preserves configuration so that
      when the controller is turned back on the previous settings are used as the
      starting point.
    - All control actions (control_heating/control_cooling) are skipped while disabled.
    """
    # If the overall temp control subsystem is disabled, do not perform any actions.
    # Preserve the saved configuration and active-state flags — don't clear them.
    if not temp_cfg.get("temp_control_enabled", True):
        temp_cfg['status'] = "Disabled"
        # Do NOT change heater_on/cooler_on/heater_pending/cooler_pending or limits here.
        # Returning early prevents any control commands from being issued.
        return

    enable_heat = bool(temp_cfg.get("enable_heating"))
    enable_cool = bool(temp_cfg.get("enable_cooling"))
    if enable_heat and enable_cool:
        temp_cfg['mode'] = "Heating and Cooling Selected"
    elif enable_heat:
        temp_cfg['mode'] = "Heating Selected"
    elif enable_cool:
        temp_cfg['mode'] = "Cooling Selected"
    else:
        temp_cfg['mode'] = "Off"

    temp = temp_cfg.get("current_temp")
    if temp is None:
        temp_from_tilt = get_current_temp_for_control_tilt()
        if temp_from_tilt is not None:
            try:
                temp = float(temp_from_tilt)
                temp_cfg['current_temp'] = round(temp, 1)
            except Exception:
                temp = None

    low = temp_cfg.get("low_limit")
    high = temp_cfg.get("high_limit")
    
    # Check if temp control monitoring is active
    is_monitoring_active = bool(temp_cfg.get("temp_control_active"))

    if not temp_cfg.get("control_initialized"):
        if enable_heat or enable_cool:
            append_control_log("temp_control_mode", {
                "low_limit": low,
                "current_temp": temp,
                "high_limit": high,
                "tilt_color": temp_cfg.get("tilt_color", "")
            })
        temp_cfg["control_initialized"] = True
        temp_cfg["last_logged_low_limit"] = low
        temp_cfg["last_logged_high_limit"] = high
        temp_cfg["last_logged_enable_heating"] = enable_heat
        temp_cfg["last_logged_enable_cooling"] = enable_cool

    if (temp_cfg.get("last_logged_low_limit") != low or
        temp_cfg.get("last_logged_high_limit") != high or
        temp_cfg.get("last_logged_enable_heating") != enable_heat or
        temp_cfg.get("last_logged_enable_cooling") != enable_cool):
        if enable_heat or enable_cool:
            append_control_log("temp_control_mode_changed", {
                "low_limit": low,
                "current_temp": temp,
                "high_limit": high,
                "tilt_color": temp_cfg.get("tilt_color", "")
            })
        temp_cfg["last_logged_low_limit"] = low
        temp_cfg["last_logged_high_limit"] = high
        temp_cfg["last_logged_enable_heating"] = enable_heat
        temp_cfg["last_logged_enable_cooling"] = enable_cool

    if temp is None:
        control_heating("off")
        control_cooling("off")
        temp_cfg["status"] = "Device Offline"
        return

    current_action = None

    if enable_heat and temp < low:
        control_heating("on")
        current_action = "Heating"
        # Log with trigger when temp goes below low limit
        if temp_cfg.get("below_limit_trigger_armed") and is_monitoring_active:
            append_control_log("temp_below_low_limit", {"low_limit": low, "current_temp": temp, "high_limit": high, "tilt_color": temp_cfg.get("tilt_color", "")})
            temp_cfg["below_limit_logged"] = True
            # Send notification if enabled
            send_temp_control_notification("temp_below_low_limit", temp, low, high, temp_cfg.get("tilt_color", ""))
            temp_cfg["below_limit_trigger_armed"] = False
            temp_cfg["above_limit_trigger_armed"] = False  # Ensure above is disarmed
    else:
        control_heating("off")

    if enable_cool and temp > high:
        control_cooling("on")
        current_action = "Cooling"
        # Log with trigger when temp goes above high limit
        if temp_cfg.get("above_limit_trigger_armed") and is_monitoring_active:
            append_control_log("temp_above_high_limit", {"low_limit": low, "current_temp": temp, "high_limit": high, "tilt_color": temp_cfg.get("tilt_color", "")})
            temp_cfg["above_limit_logged"] = True
            # Send notification if enabled
            send_temp_control_notification("temp_above_high_limit", temp, low, high, temp_cfg.get("tilt_color", ""))
            temp_cfg["above_limit_trigger_armed"] = False
            temp_cfg["below_limit_trigger_armed"] = False  # Ensure below is disarmed
    else:
        control_cooling("off")

    try:
        if isinstance(low, (int, float)) and isinstance(high, (int, float)) and (low <= temp <= high):
            # Temperature is in range
            # Log with trigger when entering range
            if temp_cfg.get("in_range_trigger_armed") and is_monitoring_active:
                append_control_log("temp_in_range", {"low_limit": low, "current_temp": temp, "high_limit": high, "tilt_color": temp_cfg.get("tilt_color", "")})
                temp_cfg["in_range_trigger_armed"] = False
            # Re-arm the out-of-range triggers when in range
            temp_cfg["above_limit_trigger_armed"] = True
            temp_cfg["below_limit_trigger_armed"] = True
            temp_cfg["status"] = "In Range"
            return
        else:
            # Temperature is out of range - re-arm in_range trigger
            temp_cfg["in_range_trigger_armed"] = True
    except Exception:
        pass

    if current_action == "Heating":
        temp_cfg["status"] = "Heating"
    elif current_action == "Cooling":
        temp_cfg["status"] = "Cooling"
    else:
        temp_cfg["status"] = "Idle"

# --- kasa result listener (log confirmed ON/OFF events) --------------------
def kasa_result_listener():
    while True:
        try:
            result = kasa_result_queue.get(timeout=5)
            mode = result.get('mode')
            action = result.get('action')
            success = result.get('success', False)
            url = result.get('url', '')
            if mode == 'heating':
                temp_cfg["heater_pending"] = False
                if success:
                    temp_cfg["heater_on"] = (action == 'on')
                    temp_cfg["heating_error"] = False
                    temp_cfg["heating_error_msg"] = ""
                    event = "heating_on" if action == 'on' else "heating_off"
                    append_control_log(event, {"low_limit": temp_cfg.get("low_limit"), "current_temp": temp_cfg.get("current_temp"), "high_limit": temp_cfg.get("high_limit"), "tilt_color": temp_cfg.get("tilt_color", "")})
                    # Send notification if enabled
                    send_temp_control_notification(event, temp_cfg.get("current_temp", 0), temp_cfg.get("low_limit", 0), temp_cfg.get("high_limit", 0), temp_cfg.get("tilt_color", ""))
                else:
                    temp_cfg["heating_error"] = True
                    temp_cfg["heating_error_msg"] = result.get('error', '') or ''
            elif mode == 'cooling':
                temp_cfg["cooler_pending"] = False
                if success:
                    temp_cfg["cooler_on"] = (action == 'on')
                    temp_cfg["cooling_error"] = False
                    temp_cfg["cooling_error_msg"] = ""
                    event = "cooling_on" if action == 'on' else "cooling_off"
                    append_control_log(event, {"low_limit": temp_cfg.get("low_limit"), "current_temp": temp_cfg.get("current_temp"), "high_limit": temp_cfg.get("high_limit"), "tilt_color": temp_cfg.get("tilt_color", "")})
                    # Send notification if enabled
                    send_temp_control_notification(event, temp_cfg.get("current_temp", 0), temp_cfg.get("low_limit", 0), temp_cfg.get("high_limit", 0), temp_cfg.get("tilt_color", ""))
                else:
                    temp_cfg["cooling_error"] = True
                    temp_cfg["cooling_error_msg"] = result.get('error', '') or ''
        except Exception:
            continue

threading.Thread(target=kasa_result_listener, daemon=True).start()

# --- Offsite push helpers (kept, forwarding enabled) -----------------------
def build_offsite_payload(field_map=None):
    default_map = {
        'timestamp': 'timestamp',
        'tilt_color': 'tilt_color',
        'gravity': 'gravity',
        'temp_f': 'temp',
        'brew_id': 'brewid',
        'device': 'device'
    }
    if not field_map:
        field_map = default_map
    payload = {
        'timestamp': datetime.utcnow().isoformat(),
        'temp_control': {
            'current_temp': temp_cfg.get("current_temp"),
            'low_limit': temp_cfg.get("low_limit"),
            'high_limit': temp_cfg.get("high_limit"),
            'status': temp_cfg.get("status"),
        },
        'tilts': []
    }
    for color, info in live_tilts.items():
        entry = {
            field_map.get('tilt_color', 'tilt_color'): color,
            field_map.get('gravity', 'gravity'): info.get('gravity'),
            field_map.get('temp_f', 'temp'): info.get('temp_f'),
            field_map.get('brew_id', 'brewid'): info.get('brewid'),
            field_map.get('device', 'device'): color
        }
        payload['tilts'].append(entry)
    return payload

def push_offsite_snapshot():
    return

# --- Periodic temp control thread -----------------------------------------
def periodic_temp_control():
    while True:
        try:
            file_cfg = load_json(TEMP_CFG_FILE, {})
            if 'current_temp' in file_cfg and file_cfg['current_temp'] is None and temp_cfg.get('current_temp') is not None:
                file_cfg.pop('current_temp')
            temp_cfg.update(file_cfg)
            temperature_control_logic()
        except Exception as e:
            append_control_log("temp_control_mode_changed", {"low_limit": temp_cfg.get("low_limit"), "current_temp": temp_cfg.get("current_temp"), "high_limit": temp_cfg.get("high_limit"), "tilt_color": temp_cfg.get("tilt_color", "")})
            print("[LOG] Exception in periodic_temp_control:", e)

        try:
            interval_minutes = int(system_cfg.get("update_interval", 1))
        except Exception:
            interval_minutes = 1
        interval_seconds = max(1, interval_minutes * 60)
        time.sleep(interval_seconds)

threading.Thread(target=periodic_temp_control, daemon=True).start()

# --- Periodic batch monitoring thread -------------------------------------
def periodic_batch_monitoring():
    """Monitor for signal loss and schedule daily reports."""
    last_daily_check = None
    
    while True:
        try:
            # Check for signal loss every 5 minutes
            check_signal_loss()
            
            # Check if it's time for daily reports
            notif_cfg = system_cfg.get('batch_notifications', {})
            daily_report_time = notif_cfg.get('daily_report_time', '09:00')  # Default 9 AM
            
            now = datetime.utcnow()
            current_time_str = now.strftime('%H:%M')
            
            # Check if we should send daily report (within 5 minute window)
            if daily_report_time:
                try:
                    report_hour, report_min = map(int, daily_report_time.split(':'))
                    current_hour = now.hour
                    current_min = now.minute
                    
                    # Check if current time is within DAILY_REPORT_WINDOW_MINUTES of report time
                    time_match = (current_hour == report_hour and 
                                 abs(current_min - report_min) < DAILY_REPORT_WINDOW_MINUTES)
                    
                    # Only send once per day
                    if time_match:
                        if not last_daily_check or (now - last_daily_check).total_seconds() > 3600:
                            send_daily_report()
                            last_daily_check = now
                except Exception as e:
                    print(f"[LOG] Error checking daily report time: {e}")
        
        except Exception as e:
            print(f"[LOG] Exception in periodic_batch_monitoring: {e}")
        
        # Sleep for BATCH_MONITORING_INTERVAL_SECONDS
        time.sleep(BATCH_MONITORING_INTERVAL_SECONDS)

threading.Thread(target=periodic_batch_monitoring, daemon=True).start()

# --- BLE scanner thread ---------------------------------------------------
def ble_loop():
    async def run_scanner():
        if BleakScanner is None:
            print("[LOG] BleakScanner not available; BLE scanning disabled")
            return
        scanner = BleakScanner(detection_callback)
        await scanner.start()
        while True:
            await asyncio.sleep(5)
            try:
                temp = get_current_temp_for_control_tilt()
                if temp is not None:
                    temp_cfg['current_temp'] = round(float(temp), 1)
            except Exception as e:
                print(f"[LOG] Error in ble_loop run_scanner: {e}")
    try:
        asyncio.run(run_scanner())
    except Exception as e:
        print(f"[LOG] BLE loop failed to start: {e}")

threading.Thread(target=ble_loop, daemon=True).start()

# --- Flask routes ---------------------------------------------------------
@app.route('/')
def dashboard():
    return render_template('maindisplay.html',
        system_settings=system_cfg,
        tilt_cfg=tilt_cfg,
        COLOR_MAP=COLOR_MAP,
        tilts=live_tilts,
        tilt_status=tilt_status,
        temp_control=temp_cfg,
        live_tilts=live_tilts
    )

@app.route('/system_config')
def system_config():
    return render_template('system_config.html', system_settings=system_cfg)

@app.route('/update_system_config', methods=['POST'])
def update_system_config():
    data = request.form
    old_warn = system_cfg.get('warning_mode', 'NONE')
    
    # Handle password field - only update if provided
    sending_email_password = data.get("sending_email_password", "")
    if sending_email_password:
        # Store as smtp_password for SMTP authentication
        system_cfg["smtp_password"] = sending_email_password
    
    system_cfg.update({
        "brewery_name": data.get("brewery_name", ""),
        "brewer_name": data.get("brewer_name", ""),
        "street": data.get("street", ""),
        "city": data.get("city", ""),
        "state": data.get("state", ""),
        "email": data.get("email", ""),
        "mobile": data.get("mobile", ""),
        "timezone": data.get("timezone", ""),
        "timestamp_format": data.get("timestamp_format", ""),
        "update_interval": data.get("update_interval", "1"),
        "temp_logging_interval": data.get("temp_logging_interval", system_cfg.get('temp_logging_interval', 10)),
        "external_refresh_rate": data.get("external_refresh_rate", "0"),
        "external_name_0": data.get("external_name_0", system_cfg.get('external_name_0','')),
        "external_url_0": data.get("external_url_0", system_cfg.get('external_url_0','')),
        "external_name_1": data.get("external_name_1", system_cfg.get('external_name_1','')),
        "external_url_1": data.get("external_url_1", system_cfg.get('external_url_1','')),
        "external_name_2": data.get("external_name_2", system_cfg.get('external_name_2','')),
        "external_url_2": data.get("external_url_2", system_cfg.get('external_url_2','')),
        "warning_mode": data.get("warning_mode", "NONE"),
        "sending_email": data.get("sending_email", system_cfg.get('sending_email','')),
        "smtp_host": data.get("smtp_host", system_cfg.get('smtp_host', 'smtp.gmail.com')),
        "smtp_port": int(data.get("smtp_port", system_cfg.get('smtp_port', 587))),
        "smtp_starttls": 'smtp_starttls' in data,
        "sms_gateway_domain": data.get("sms_gateway_domain", system_cfg.get('sms_gateway_domain','')),
        "external_method": data.get("external_method", system_cfg.get('external_method','POST')),
        "external_content_type": data.get("external_content_type", system_cfg.get('external_content_type','form')),
        "external_timeout_seconds": data.get("external_timeout_seconds", system_cfg.get('external_timeout_seconds',8)),
        "external_field_map": data.get("external_field_map", system_cfg.get('external_field_map','')),
        "kasa_rate_limit_seconds": data.get("kasa_rate_limit_seconds", system_cfg.get('kasa_rate_limit_seconds', 10)),
        "tilt_logging_interval_minutes": int(data.get("tilt_logging_interval_minutes", system_cfg.get("tilt_logging_interval_minutes", 15)))
    })
    
    # Update temperature control notifications settings
    temp_control_notif = {
        'enable_temp_below_low_limit': 'enable_temp_below_low_limit' in data,
        'enable_temp_above_high_limit': 'enable_temp_above_high_limit' in data,
        'enable_heating_on': 'enable_heating_on' in data,
        'enable_heating_off': 'enable_heating_off' in data,
        'enable_cooling_on': 'enable_cooling_on' in data,
        'enable_cooling_off': 'enable_cooling_off' in data,
    }
    system_cfg['temp_control_notifications'] = temp_control_notif
    
    # Update batch notifications settings
    batch_notif = {
        'enable_loss_of_signal': 'enable_loss_of_signal' in data,
        'loss_of_signal_timeout_minutes': int(data.get('loss_of_signal_timeout_minutes', 30)),
        'enable_fermentation_starting': 'enable_fermentation_starting' in data,
        'enable_fermentation_completion': 'enable_fermentation_completion' in data,
        'enable_daily_report': 'enable_daily_report' in data,
        'daily_report_time': data.get('daily_report_time', '09:00'),
    }
    system_cfg['batch_notifications'] = batch_notif
    
    save_json(SYSTEM_CFG_FILE, system_cfg)

    new_warn = system_cfg.get('warning_mode','NONE')
    # Reset notification state when warning mode changes
    if old_warn.upper() == 'NONE' and new_warn.upper() in ('EMAIL','SMS','BOTH'):
        temp_cfg['notifications_trigger'] = False
        temp_cfg['notification_comm_failure'] = False
    elif new_warn.upper() == 'NONE':
        temp_cfg['notifications_trigger'] = False
        temp_cfg['notification_comm_failure'] = False

    return redirect('/system_config')

@app.route('/tilt_config', methods=['GET', 'POST'])
def tilt_config():
    selected = request.args.get('tilt_color') or request.form.get('tilt_color')
    batch_history = []
    if selected:
        try:
            with open(f'batches/batch_history_{selected}.json', 'r') as f:
                batch_history = json.load(f)
        except Exception:
            batch_history = []
    if request.method == 'POST':
        color = request.form.get('tilt_color')
        action = request.form.get('action')
        # --- PATCH: Capture quick OG/recipe/metadata changes as batch_metadata ----
        actual_og = request.form.get("actual_og")
        recipe_og = request.form.get("recipe_og")
        # update tilt_cfg fields from the form (for quick-edit path)
        changed = False
        if color in tilt_cfg:
            batch_entry = tilt_cfg[color].copy()
            if actual_og is not None:
                batch_entry['actual_og'] = actual_og
                tilt_cfg[color]['actual_og'] = actual_og
                changed = True
            if recipe_og is not None:
                batch_entry['recipe_og'] = recipe_og
                tilt_cfg[color]['recipe_og'] = recipe_og
                changed = True
            # Keep og_confirmed in data structure for backward compatibility (always False)
            batch_entry['og_confirmed'] = False
            tilt_cfg[color]['og_confirmed'] = False
            batch_entry['brewid'] = tilt_cfg[color].get("brewid")
            if changed:
                try:
                    save_json(TILT_CONFIG_FILE, tilt_cfg)
                except Exception:
                    pass
                # Append batch_metadata to batch file
                append_batch_metadata_to_batch_jsonl(color, batch_entry)
        if color and action:
            if action == "cancel":
                return redirect("/")
            return redirect(f"/batch_settings?tilt_color={color}&action={action}")
    config = tilt_cfg.get(selected, {}) if selected else {}
    return render_template('tilt_config.html',
        tilt_cfg=tilt_cfg,
        tilt_colors=list(TILT_UUIDS.values()),
        selected_tilt=selected,
        selected_config=config,
        system_settings=system_cfg,
        batch_history=batch_history
    )

@app.route('/batch_settings', methods=['GET', 'POST'])
def batch_settings():
    if request.method == 'POST':
        data = request.form
        color = data.get('tilt_color')
        if not color:
            return "No Tilt color selected", 400
        beer_name = data.get('beer_name', '').strip()
        batch_name = data.get('batch_name', '').strip()
        start_date = data.get('ferm_start_date', '').strip()
        existing = tilt_cfg.get(color, {})
        old_brew_id = existing.get('brewid')
        brew_id = existing.get('brewid')
        if not brew_id:
            brew_id = generate_brewid(beer_name, batch_name, start_date)
        if old_brew_id and old_brew_id != brew_id:
            rotate_and_archive_old_history(color, old_brew_id, existing)
            tilt_cfg[color] = {
                "beer_name": "",
                "batch_name": "",
                "ferm_start_date": "",
                "recipe_og": "",
                "recipe_fg": "",
                "recipe_abv": "",
                "actual_og": None,
                "brewid": "",
                "og_confirmed": False
            }
            save_json(TILT_CONFIG_FILE, tilt_cfg)

        og_confirmed = False  # No longer using og_confirmed checkbox

        batch_entry = {
            "beer_name": beer_name,
            "batch_name": batch_name,
            "ferm_start_date": start_date,
            "recipe_og": data.get('recipe_og', '') or '',
            "recipe_fg": data.get('recipe_fg', '') or '',
            "recipe_abv": data.get('recipe_abv', '') or '',
            "actual_og": (data.get('actual_og', '') or None),
            "og_confirmed": False,  # Keep field for backward compatibility
            "brewid": brew_id
        }

        try:
            with open(f'batches/batch_history_{color}.json', 'r') as f:
                batches = json.load(f)
        except Exception:
            batches = []
        batches.append(batch_entry)
        try:
            with open(f'batches/batch_history_{color}.json', 'w') as f:
                json.dump(batches, f, indent=2)
        except Exception as e:
            print(f"[LOG] Could not append batch history for {color}: {e}")
        tilt_cfg[color] = batch_entry
        try:
            save_json(TILT_CONFIG_FILE, tilt_cfg)
        except Exception as e:
            print(f"[LOG] Could not save tilt_config in batch_settings: {e}")
        # --- PATCH: Append batch_metadata to .jsonl whenever batch is edited
        append_batch_metadata_to_batch_jsonl(color, batch_entry)
        return redirect(f"/batch_settings?tilt_color={color}")

    selected = request.args.get('tilt_color')
    action = request.args.get('action')
    config = tilt_cfg.get(selected, {}) if selected else {}
    batch_history = []
    if selected:
        try:
            with open(f'batches/batch_history_{selected}.json', 'r') as f:
                batch_history = json.load(f)
        except Exception:
            batch_history = []
    all_colors = list(TILT_UUIDS.values())
    active_colors = list(live_tilts.keys())
    return render_template('batch_settings.html',
        tilt_cfg=tilt_cfg,
        tilt_colors=all_colors,
        active_colors=active_colors,
        live_tilts=live_tilts,
        selected_tilt=selected,
        selected_config=config,
        system_settings=system_cfg,
        action=action,
        batch_history=batch_history,
        color_map=COLOR_MAP
    )

@app.route('/temp_config')
def temp_config():
    report_colors = list(tilt_cfg.keys())
    return render_template('temp_control_config.html',
        temp_control=temp_cfg,
        tilt_cfg=tilt_cfg,
        system_settings=system_cfg,
        batch_cfg=tilt_cfg,
        report_colors=report_colors,
        live_tilts=live_tilts
    )


@app.route('/update_temp_config', methods=['POST'])
def update_temp_config():
    data = request.form
    try:
        temp_cfg.update({
            "tilt_color": data.get('tilt_color', ''),
            "low_limit": float(data.get('low_limit', 0)),
            "high_limit": float(data.get('high_limit', 100)),
            "enable_heating": 'enable_heating' in data,
            "enable_cooling": 'enable_cooling' in data,
            "heating_plug": data.get("heating_plug", ""),
            "cooling_plug": data.get("cooling_plug", ""),
            "mode": data.get("mode", temp_cfg.get('mode','')),
            "status": data.get("status", temp_cfg.get('status',''))
        })
    except Exception as e:
        print(f"[LOG] Error parsing temp config form: {e}")
    try:
        save_json(TEMP_CFG_FILE, temp_cfg)
    except Exception as e:
        print(f"[LOG] Error saving config in update_temp_config: {e}")


    # Run control logic immediately (it will normalize mode/status and log selection change if any)
    temperature_control_logic()


    return redirect('/temp_config')


@app.route('/toggle_temp_control', methods=['POST'])
def toggle_temp_control():
    """Toggle the temp_control_active state (ON/OFF switch on temp control card).
    
    When turning ON, if 'new_session' is True in the request, archive the existing log.
    """
    try:
        data = request.get_json() if request.is_json else request.form
        # Standardize on boolean JSON values
        active_value = data.get('active')
        if isinstance(active_value, bool):
            new_state = active_value
        elif isinstance(active_value, str):
            new_state = active_value.lower() in ('true', '1')
        else:
            new_state = bool(active_value)
        
        # Check if this is a new session request (archive existing log)
        new_session = data.get('new_session', False)
        if isinstance(new_session, str):
            new_session = new_session.lower() in ('true', '1')
        
        # If turning ON and new_session is requested, archive the existing log
        if new_state and new_session:
            try:
                if os.path.exists(LOG_PATH):
                    # Create logs directory if it doesn't exist
                    logs_dir = 'logs'
                    os.makedirs(logs_dir, exist_ok=True)
                    
                    # Generate archive filename with timestamp
                    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                    tilt_color = temp_cfg.get("tilt_color", "unknown")
                    archive_name = f"temp_control_{tilt_color}_{timestamp}.jsonl"
                    archive_path = os.path.join(logs_dir, archive_name)
                    
                    # Move the existing log to archive
                    shutil.move(LOG_PATH, archive_path)
                    print(f"[LOG] Archived temp control log to {archive_path}")
            except Exception as e:
                print(f"[LOG] Error archiving temp control log: {e}")
                return jsonify({"success": False, "error": f"Failed to archive log: {str(e)}"}), 500
        
        temp_cfg['temp_control_active'] = new_state
        
        if new_state:
            # When turning ON, arm all triggers and log the start event
            temp_cfg['in_range_trigger_armed'] = True
            temp_cfg['above_limit_trigger_armed'] = True
            temp_cfg['below_limit_trigger_armed'] = True
            append_control_log("temp_control_started", {
                "low_limit": temp_cfg.get("low_limit"),
                "current_temp": temp_cfg.get("current_temp"),
                "high_limit": temp_cfg.get("high_limit"),
                "tilt_color": temp_cfg.get("tilt_color", "")
            })
        
        # Save the state
        save_json(TEMP_CFG_FILE, temp_cfg)
        
        return jsonify({"success": True, "active": new_state})
    except Exception as e:
        print(f"[LOG] Error toggling temp control: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/temp_report', methods=['GET', 'POST'])
def temp_report():
    if request.method == 'POST':
        color = request.form.get('tilt_color')
        if not color:
            return redirect('/temp_report')
        return redirect(f"/temp_report?tilt_color={color}&page=1")


    tilt_color = request.args.get('tilt_color')
    try:
        page = int(request.args.get('page', '1'))
    except Exception:
        page = 1


    if not tilt_color:
        colors = list(tilt_cfg.keys())
        default_color = colors[0] if colors else None
        return render_template('temp_report_select.html', colors=colors, default_color=default_color)


    entries = []
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    if obj.get('event') != 'tilt_reading' and obj.get('event') != 'SAMPLE':
                        continue
                    payload = obj.get('payload') or obj if isinstance(obj, dict) else {}
                    entries.append(payload)
    except Exception as e:
        print(f"[LOG] Could not read log for temp_report: {e}")


    filtered = []
    brewid = tilt_cfg.get(tilt_color, {}).get('brewid')
    tc = tilt_cfg.get(tilt_color, {}) or {}
    for p in entries:
        if brewid:
            if p.get('brewid') == brewid:
                filtered.append(p)
        else:
            if p.get('batch_name') == tc.get('batch_name') or p.get('beer_name') == tc.get('beer_name'):
                filtered.append(p)


    lines = []
    filtered = list(reversed(filtered))
    for p in filtered:
        ts = p.get('timestamp', '')
        bn = p.get('beer_name') or ''
        batch = p.get('batch_name') or ''
        tempf = p.get('temp_f', '')
        grav = p.get('gravity', '')
        bid = p.get('brewid') or '--'
        lines.append(f"{ts} — {bn or batch} — Temp: {tempf}°F — Gravity: {grav} — Brew ID: {bid}")


    total_pages = max(1, ceil(len(lines) / PER_PAGE))
    page = max(1, min(page, total_pages))
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    page_data = lines[start:end]
    at_end = page >= total_pages


    return render_template('temp_report_display.html',
                           color=tilt_color,
                           page=page,
                           total_pages=total_pages,
                           page_data=page_data,
                           at_end=at_end)


@app.route('/export_temp_log', methods=['GET', 'POST'])
def export_temp_log():
    return redirect('/temp_config')


@app.route('/export_temp_csv', methods=['GET', 'POST'])
def export_temp_csv():
    return redirect('/temp_config')


@app.route('/export_temp_control_csv', methods=['POST'])
def export_temp_control_csv():
    """Export temperature control log data to CSV in the /export directory."""
    try:
        import csv
        from datetime import datetime
        
        # Create export directory if it doesn't exist
        export_dir = 'export'
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'temp_control_{timestamp}.csv'
        filepath = os.path.join(export_dir, filename)
        
        # Read data from temp_control_log.jsonl
        data_rows = []
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        # Only include events that are in ALLOWED_EVENTS
                        if obj.get('event') in ALLOWED_EVENT_VALUES:
                            data_rows.append(obj)
                    except Exception as e:
                        print(f"[LOG] Error parsing line in export: {e}")
                        continue
        
        # Write to CSV
        if data_rows:
            with open(filepath, 'w', newline='') as csvfile:
                # Define fieldnames from the data
                fieldnames = ['timestamp', 'date', 'time', 'tilt_color', 'brewid', 'low_limit', 'current_temp', 'temp_f', 'gravity', 'high_limit', 'event']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for row in data_rows:
                    writer.writerow(row)
            
            return jsonify({'success': True, 'filename': filename, 'rows': len(data_rows)})
        else:
            return jsonify({'success': False, 'error': 'No data to export'})
            
    except Exception as e:
        print(f"[LOG] Error exporting temp control CSV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/scan_kasa_plugs')
def scan_kasa_plugs():
    try:
        from kasa import Discover
        found_devices = asyncio.run(Discover.discover())
        devices = {str(addr): dev.alias for addr, dev in found_devices.items()}
    except Exception as e:
        devices = {}
        print(f"[LOG] Kasa scan failed: {e}")
    return render_template("kasa_scan_results.html", devices=devices, error=None)


@app.route('/live_snapshot')
def live_snapshot():
    snapshot = {
        "live_tilts": {},
        "temp_control": {
            "current_temp": temp_cfg.get("current_temp"),
            "low_limit": temp_cfg.get("low_limit"),
            "high_limit": temp_cfg.get("high_limit"),
            "heater_on": temp_cfg.get("heater_on"),
            "cooler_on": temp_cfg.get("cooler_on"),
            "heater_pending": temp_cfg.get("heater_pending"),
            "cooler_pending": temp_cfg.get("cooler_pending"),
            "enable_heating": temp_cfg.get("enable_heating"),
            "enable_cooling": temp_cfg.get("enable_cooling"),
            "status": temp_cfg.get("status"),
            "mode": temp_cfg.get("mode", 'Off'),
            "warning_mode": system_cfg.get('warning_mode'),
            "notifications_trigger": temp_cfg.get('notifications_trigger'),
            "notification_comm_failure": temp_cfg.get('notification_comm_failure'),
            "temp_control_active": temp_cfg.get('temp_control_active', False),
            "heating_error": temp_cfg.get('heating_error', False),
            "cooling_error": temp_cfg.get('cooling_error', False),
            "sms_error": temp_cfg.get('sms_error', False),
            "email_error": temp_cfg.get('email_error', False)
        }
    }
    for color, info in live_tilts.items():
        snapshot["live_tilts"][color] = {
            "gravity": info.get("gravity"),
            "temp_f": info.get("temp_f"),
            "timestamp": info.get("timestamp"),
            "beer_name": info.get("beer_name"),
            "batch_name": info.get("batch_name"),
            "brewid": info.get("brewid"),
            "recipe_og": info.get("recipe_og"),
            "recipe_fg": info.get("recipe_fg"),
            "recipe_abv": info.get("recipe_abv"),
            "actual_og": info.get("actual_og"),
            "og_confirmed": info.get("og_confirmed", False),
            "original_gravity": info.get("original_gravity"),
            "color_code": info.get("color_code")
        }
    return jsonify(snapshot)


# --- Chart routes and data endpoint ---------------------------------------
@app.route('/chart_plotly')
def chart_plotly_index():
    colors = list(tilt_cfg.keys())
    if colors:
        return redirect(f'/chart_plotly/{colors[0]}')
    return render_template('chart_plotly.html', tilt_color=None, system_settings=system_cfg)


@app.route('/chart_plotly/<tilt_color>')
def chart_plotly_for(tilt_color):
    # Allow "Fermenter" as a special identifier for temperature control
    if tilt_color and tilt_color != "Fermenter" and tilt_color not in tilt_cfg:
        abort(404)
    return render_template(
        'chart_plotly.html',
        tilt_color=tilt_color,
        tilt_cfg=tilt_cfg,
        system_settings=system_cfg
    )

@app.route('/chart_data/<tilt_color>')
def chart_data_for(tilt_color):
    all_flag = str(request.args.get('all', '')).lower() in ('1', 'true', 'yes', 'on')
    limit_param = request.args.get('limit', None)
    limit = None
    if limit_param:
        try:
            limit = int(limit_param)
        except Exception:
            limit = None
    if not all_flag and (limit is None or limit <= 0):
        limit = DEFAULT_CHART_LIMIT
    if not all_flag and limit is not None:
        limit = max(10, min(limit, MAX_CHART_LIMIT))

    # Handle "Fermenter" as temperature control monitor data
    if tilt_color == "Fermenter":
        points = deque(maxlen=limit) if (not all_flag and limit is not None) else []
        matched = 0
        
        if os.path.exists(LOG_PATH):
            try:
                with open(LOG_PATH, 'r') as f:
                    for line in f:
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        # Include all temp control events
                        event = obj.get('event', '')
                        if event not in ALLOWED_EVENT_VALUES:
                            continue
                        
                        matched += 1
                        ts = obj.get('timestamp')
                        tf = obj.get('temp_f') if obj.get('temp_f') is not None else obj.get('current_temp')
                        g = obj.get('gravity')
                        
                        try:
                            ts_str = str(ts) if ts is not None else None
                        except Exception:
                            ts_str = None
                        try:
                            temp_num = float(tf) if (tf is not None and tf != '') else None
                        except Exception:
                            temp_num = None
                        try:
                            grav_num = float(g) if (g is not None and g != '') else None
                        except Exception:
                            grav_num = None
                        
                        entry = {"timestamp": ts_str, "temp_f": temp_num, "gravity": grav_num, "event": event}
                        if isinstance(points, deque):
                            points.append(entry)
                        else:
                            points.append(entry)
                            if len(points) > MAX_ALL_LIMIT:
                                points.pop(0)
            except Exception as e:
                print(f"[LOG] Error reading temp control log for chart_data: {e}")
        
        if isinstance(points, deque):
            pts = list(points)
            truncated = (matched > len(pts))
        else:
            pts = list(points)
            truncated = (matched > len(pts))
        return jsonify({"tilt_color": tilt_color, "points": pts, "truncated": truncated, "matched": matched})

    # Original tilt color logic
    if tilt_color and tilt_color not in tilt_cfg:
        return jsonify({"tilt_color": tilt_color, "points": [], "truncated": False, "matched": 0})


    brewid = tilt_cfg.get(tilt_color, {}).get('brewid')


    points = deque(maxlen=limit) if (not all_flag and limit is not None) else []
    matched = 0


    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, 'r') as f:
                for line in f:
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    if obj.get('event') != 'tilt_reading' and obj.get('event') != 'SAMPLE':
                        continue
                    payload = obj.get('payload') or obj or {}
                    if brewid:
                        if payload.get('brewid') != brewid:
                            # if payload doesn't contain brewid but contains tilt_color, try matching that
                            if payload.get('tilt_color') and payload.get('tilt_color') != tilt_color:
                                continue
                        # else matched by brewid
                    matched += 1
                    ts = payload.get('timestamp')
                    tf = payload.get('temp_f') if payload.get('temp_f') is not None else payload.get('current_temp')
                    g = payload.get('gravity')
                    try:
                        ts_str = str(ts) if ts is not None else None
                    except Exception:
                        ts_str = None
                    try:
                        temp_num = float(tf) if (tf is not None and tf != '') else None
                    except Exception:
                        temp_num = None
                    try:
                        grav_num = float(g) if (g is not None and g != '') else None
                    except Exception:
                        grav_num = None
                    entry = {"timestamp": ts_str, "temp_f": temp_num, "gravity": grav_num}
                    if isinstance(points, deque):
                        points.append(entry)
                    else:
                        points.append(entry)
                        if len(points) > MAX_ALL_LIMIT:
                            points.pop(0)
        except Exception as e:
            print(f"[LOG] Error reading log for chart_data: {e}")


    if isinstance(points, deque):
        pts = list(points)
        truncated = (matched > len(pts))
    else:
        pts = list(points)
        truncated = (matched > len(pts))
    return jsonify({"tilt_color": tilt_color, "points": pts, "truncated": truncated, "matched": matched})


# --- Reset logs endpoint ---------------------------------------------------
@app.route('/reset_logs', methods=['POST'])
def reset_logs():
    """
    Reset (clear) the main temp_control_log.jsonl file after backing it up.
    """
    try:
        if os.path.exists(LOG_PATH):
            backup_name = f"{LOG_PATH}.{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.bak"
            try:
                os.rename(LOG_PATH, backup_name)
                append_control_log("temp_control_mode_changed", {"low_limit": temp_cfg.get("low_limit"), "current_temp": temp_cfg.get("current_temp"), "high_limit": temp_cfg.get("high_limit"), "tilt_color": temp_cfg.get("tilt_color", "")})
            except Exception as e:
                print(f"[LOG] Could not backup log: {e}")
        open(LOG_PATH, 'w').close()
        return redirect('/temp_config')
    except Exception as e:
        print(f"[LOG] reset_logs error: {e}")
        return "Error resetting logs", 500


# --- Misc UI routes -------------------------------------------------------
@app.route('/export_temp_csv')
def export_temp_csv_get():
    return redirect('/temp_config')


@app.route('/backup_system', methods=['POST'])
def backup_system():
    """Create a backup of all system files to the specified USB device."""
    import tarfile
    import shutil
    
    backup_path = request.form.get('backup_path', '/media/usb')
    
    # Validate that the backup path exists
    if not os.path.exists(backup_path):
        return jsonify({
            'success': False,
            'message': f'Backup path does not exist: {backup_path}. Please ensure USB device is mounted.'
        }), 400
    
    # Check if the path is writable
    if not os.access(backup_path, os.W_OK):
        return jsonify({
            'success': False,
            'message': f'Backup path is not writable: {backup_path}. Check permissions.'
        }), 400
    
    try:
        # Create timestamped backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'fermenter_backup_{timestamp}.tar.gz'
        backup_full_path = os.path.join(backup_path, backup_filename)
        
        # Files and directories to backup
        items_to_backup = [
            # Python program files
            'app.py',
            'kasa_worker.py',
            'logger.py',
            'batch_history.py',
            'batch_storage.py',
            'fermentation_monitor.py',
            'tilt_static.py',
            'archive_compact_logs.py',
            'backfill_temp_control_jsonl.py',
            # Configuration files
            'config/',
            # Data files
            'batches/',
            'temp_control/',
            'temp_control_log.jsonl',
            # Web interface
            'templates/',
            'static/',
            # Documentation
            'requirements.txt',
            'start.sh',
            'README.md',
        ]
        
        # Create the tar.gz archive
        with tarfile.open(backup_full_path, 'w:gz') as tar:
            for item in items_to_backup:
                if os.path.exists(item):
                    tar.add(item)
        
        # Get the size of the backup file
        backup_size = os.path.getsize(backup_full_path)
        backup_size_mb = backup_size / (1024 * 1024)
        
        return jsonify({
            'success': True,
            'message': f'Backup created successfully: {backup_filename}',
            'filename': backup_filename,
            'size_mb': f'{backup_size_mb:.2f}',
            'path': backup_full_path
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Backup failed: {str(e)}'
        }), 500


@app.route('/restore_system', methods=['POST'])
def restore_system():
    """Restore system from a backup file."""
    import tarfile
    import shutil
    
    backup_path = request.form.get('backup_path', '/media/usb')
    backup_filename = request.form.get('backup_filename', '')
    
    if not backup_filename:
        return jsonify({
            'success': False,
            'message': 'No backup file specified.'
        }), 400
    
    # Security: Validate filename to prevent directory traversal
    if '..' in backup_filename or '/' in backup_filename or '\\' in backup_filename:
        return jsonify({
            'success': False,
            'message': 'Invalid backup filename.'
        }), 400
    
    # Security: Ensure filename has expected format
    if not backup_filename.startswith('fermenter_backup_') or not backup_filename.endswith('.tar.gz'):
        return jsonify({
            'success': False,
            'message': 'Invalid backup file format.'
        }), 400
    
    backup_full_path = os.path.join(backup_path, backup_filename)
    
    # Validate that the backup file exists
    if not os.path.exists(backup_full_path):
        return jsonify({
            'success': False,
            'message': f'Backup file does not exist: {backup_full_path}'
        }), 400
    
    try:
        # Create a secure temporary directory for extraction validation
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='fermenter_restore_')
        
        try:
            # Extract the backup to temporary directory first
            with tarfile.open(backup_full_path, 'r:gz') as tar:
                # Security check: ensure no absolute paths or parent directory references
                safe_members = []
                for member in tar.getmembers():
                    if member.name.startswith('/') or '..' in member.name:
                        shutil.rmtree(temp_dir)
                        return jsonify({
                            'success': False,
                            'message': f'Invalid backup file: contains unsafe paths'
                        }), 400
                    safe_members.append(member)
                
                # Extract only validated members to temp directory
                tar.extractall(temp_dir, members=safe_members)
            
            # Now copy files from temp to current directory
            # This allows us to validate before overwriting
            current_dir = os.getcwd()
            
            for item in os.listdir(temp_dir):
                src = os.path.join(temp_dir, item)
                dst = os.path.join(current_dir, item)
                
                # Backup existing files before overwriting
                if os.path.exists(dst):
                    backup_old = f'{dst}.backup_before_restore'
                    if os.path.isdir(dst):
                        if os.path.exists(backup_old):
                            shutil.rmtree(backup_old)
                        shutil.copytree(dst, backup_old)
                    else:
                        shutil.copy2(dst, backup_old)
                
                # Copy from temp to current
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            
            return jsonify({
                'success': True,
                'message': f'System restored successfully from {backup_filename}. Please restart the application for changes to take effect.',
                'restart_required': True
            })
            
        finally:
            # Always cleanup temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Restore failed: {str(e)}'
        }), 500


@app.route('/list_backups', methods=['POST'])
def list_backups():
    """List available backup files in the specified directory."""
    backup_path = request.form.get('backup_path', '/media/usb')
    
    if not os.path.exists(backup_path):
        return jsonify({
            'success': False,
            'message': f'Backup path does not exist: {backup_path}',
            'backups': []
        })
    
    try:
        # List all .tar.gz files in the backup directory
        backups = []
        if os.path.isdir(backup_path):
            for filename in os.listdir(backup_path):
                if filename.startswith('fermenter_backup_') and filename.endswith('.tar.gz'):
                    full_path = os.path.join(backup_path, filename)
                    file_stat = os.stat(full_path)
                    backups.append({
                        'filename': filename,
                        'size_mb': f'{file_stat.st_size / (1024 * 1024):.2f}',
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        # Sort by filename (which includes timestamp) in reverse order
        backups.sort(key=lambda x: x['filename'], reverse=True)
        
        return jsonify({
            'success': True,
            'backups': backups,
            'path': backup_path
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to list backups: {str(e)}',
            'backups': []
        })


@app.route('/exit_system')
def exit_system():
    return redirect('/')


# --- Program entry ---------------------------------------------------------
if __name__ == '__main__':
    try:
        os.makedirs(BATCHES_DIR, exist_ok=True)
    except Exception:
        pass


    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)

