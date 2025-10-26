#!/usr/bin/env python3
"""
app.py - Flask web app for the Fermenter Temp Controller.

This app:
- Loads configuration files (tilt_config.json, temp_control_config.json, system_config.json)
- Ensures a valid IANA timezone before starting the kasa_worker (maps common abbreviations)
- Starts the kasa_worker process (kasa_worker runs Kasa/IotPlug control)
- Runs BLE Tilt scanning (Bleak) to populate live_tilts
- Runs periodic temperature control logic that queues kasa commands
- Listens for confirmations from the kasa_worker and updates temp_cfg in a stable way
- Serves the dashboard and an /api/live_snapshot used by the UI polling script
"""
import hashlib
import json
import os
import time
import threading
from datetime import datetime
from multiprocessing import Process, Queue

from flask import Flask, render_template, request, redirect, jsonify

# BLE scanning
from bleak import BleakScanner

# Local modules
from tilt_static import TILT_UUIDS, COLOR_MAP
from kasa_worker import kasa_worker   # separate process handles kasa / SmartPlug/IotPlug
from logger import log_error          # for error logging

# Notifications (email placeholder)
import smtplib
from email.mime.text import MIMEText

# Async imports used by BLE runner
import asyncio

app = Flask(__name__)

LOG_PATH = 'temp_control_log.jsonl'

# --- Utilities --------------------------------------------------------------

@app.template_filter('localtime')
def localtime_filter(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime('%Y-%m-%d %I:%M:%S %p')
    except Exception:
        return iso_str

def load_json(path, fallback):
    try:
        with open(path, 'r') as f:
            print(f"[LOG] Loaded JSON from {path}")
            return json.load(f)
    except Exception as e:
        print(f"[LOG] Failed to load JSON from {path}: {e}")
        return fallback

def save_json(path, data):
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[LOG] Saved JSON to {path}")
    except Exception as e:
        print(f"[LOG] Error saving JSON to {path}: {e}")

def append_control_log(event_type, payload):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        "payload": payload
    }
    try:
        with open(LOG_PATH, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[LOG] Failed to append to control log: {e}")

# --- Load configs ----------------------------------------------------------
tilt_cfg = load_json('tilt_config.json', {})
temp_cfg = load_json('temp_control_config.json', {})
system_cfg = load_json('system_config.json', {})

# Ensure tilt config contains known tilt colors
def ensure_all_tilts():
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
                "brewid": ""
            }
ensure_all_tilts()

# Ensure expected keys in temp_cfg
temp_cfg.setdefault("current_temp", None)
temp_cfg.setdefault("low_limit", 0.0)
temp_cfg.setdefault("high_limit", 0.0)
temp_cfg.setdefault("enable_heating", False)
temp_cfg.setdefault("enable_cooling", False)
temp_cfg.setdefault("override_mode", False)
temp_cfg.setdefault("manual_heating", False)
temp_cfg.setdefault("manual_cooling", False)
temp_cfg.setdefault("heating_plug", "")
temp_cfg.setdefault("cooling_plug", "")
temp_cfg.setdefault("heater_on", False)
temp_cfg.setdefault("cooler_on", False)
temp_cfg.setdefault("heater_pending", False)
temp_cfg.setdefault("cooler_pending", False)
temp_cfg.setdefault("heating_error", False)
temp_cfg.setdefault("cooling_error", False)
temp_cfg.setdefault("heating_error_msg", "")
temp_cfg.setdefault("cooling_error_msg", "")
temp_cfg.setdefault("status", "Idle")
temp_cfg.setdefault("tilt_color", "")

# --- Ensure valid IANA TZ before starting kasa worker -----------------------
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
except AttributeError:
    pass
print(f"[LOG] Using TZ='{os.environ.get('TZ')}' for app and kasa_worker")

# --- Inter-process queues and kasa worker startup --------------------------
kasa_queue = Queue()
kasa_result_queue = Queue()

kasa_proc = Process(target=kasa_worker, args=(kasa_queue, kasa_result_queue))
kasa_proc.daemon = True
kasa_proc.start()
print("[LOG] Started kasa_worker process")

# --- Live runtime data -----------------------------------------------------
live_tilts = {}
tilt_status = {}

def generate_brewid(beer_name, batch_name, date_str):
    id_str = f"{beer_name}-{batch_name}-{date_str}"
    return hashlib.sha256(id_str.encode('utf-8')).hexdigest()[:8]

def update_live_tilt(color, gravity, temp_f, rssi):
    cfg = tilt_cfg.get(color, {})
    live_tilts[color] = {
        "gravity": round(gravity, 3),
        "temp_f": temp_f,
        "rssi": rssi,
        "timestamp": datetime.utcnow().isoformat(),
        "color_code": COLOR_MAP.get(color, "#333"),
        "beer_name": cfg.get("beer_name", ""),
        "batch_name": cfg.get("batch_name", ""),
        "brewid": cfg.get("brewid", ""),
        "recipe_og": cfg.get("recipe_og", ""),
        "recipe_fg": cfg.get("recipe_fg", ""),
        "recipe_abv": cfg.get("recipe_abv", ""),
        "actual_og": cfg.get("actual_og", ""),
        "original_gravity": cfg.get("actual_og", 0),
    }

def log_tilt_reading(color, gravity, temp_f, rssi):
    cfg = tilt_cfg.get(color, {})
    batch = {
        "beer_name": cfg.get("beer_name", "Unknown"),
        "batch_name": cfg.get("batch_name", "Unknown"),
        "brewid": cfg.get("brewid", generate_brewid(cfg.get("beer_name", ""), cfg.get("batch_name", ""), cfg.get("ferm_start_date", ""))),
        "ferm_start_date": cfg.get("ferm_start_date", "Unknown"),
        "original_gravity": cfg.get("actual_og", gravity),
        "gravity": gravity,
        "temp_f": temp_f,
        "rssi": rssi,
        "timestamp": datetime.utcnow().isoformat()
    }
    append_control_log("tilt_reading", batch)

def get_current_temp_for_control_tilt():
    color = temp_cfg.get("tilt_color")
    if color and color in live_tilts:
        return live_tilts[color].get("temp_f")
    return None

def detection_callback(device, advertisement_data):
    try:
        mfg_data = advertisement_data.manufacturer_data
        if not mfg_data:
            return
        raw = list(mfg_data.values())[0]
        if len(raw) != 23:
            return
        uuid = raw[2:18].hex()
        color = TILT_UUIDS.get(uuid)
        if not color:
            return
        temp_f = int.from_bytes(raw[18:20], byteorder='big')
        gravity = int.from_bytes(raw[20:22], byteorder='big') / 1000.0
        rssi = advertisement_data.rssi
        update_live_tilt(color, gravity, temp_f, rssi)
        log_tilt_reading(color, gravity, temp_f, rssi)
    except Exception as e:
        print(f"[LOG] Error in detection_callback: {e}")

# --- Notifications ---------------------------------------------------------
def send_email(subject, body):
    cfg = system_cfg
    if not (isinstance(cfg, dict) and cfg.get("email")):
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = cfg["email"]
        msg["To"] = cfg["email"]
        server = smtplib.SMTP(cfg.get("smtp_host", "localhost"), cfg.get("smtp_port", 25), timeout=10)
        if cfg.get("smtp_starttls"):
            server.starttls()
        if cfg.get("smtp_user") and cfg.get("smtp_password"):
            server.login(cfg["smtp_user"], cfg["smtp_password"])
        server.sendmail(cfg["email"], [cfg["email"]], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"[LOG] Email send failed: {e}")

def send_sms(body):
    print(f"[LOG] SMS: {body}")

def send_warning(subject, body):
    mode = (system_cfg.get("warning_mode") if isinstance(system_cfg, dict) else "none").lower()
    if mode == "email":
        send_email(subject, body)
    elif mode == "sms":
        send_sms(body)
    elif mode == "both":
        send_email(subject, body)
        send_sms(body)

# --- Control functions -----------------------------------------------------
def control_heating(state):
    enabled = temp_cfg.get("enable_heating")
    url = temp_cfg.get("heating_plug", "")
    if not enabled or not url:
        temp_cfg["heater_pending"] = False
        temp_cfg["heater_on"] = False
        append_control_log("plug_bypass", {"mode": "heating", "reason": "disabled_or_no_url", "url": url})
        print("[LOG] Heating control bypassed (not enabled or no URL).")
        return
    kasa_queue.put({'mode': 'heating', 'url': url, 'action': state})
    temp_cfg["heater_pending"] = True
    append_control_log("plug_command", {"mode": "heating", "action": state, "url": url})
    print(f"[LOG] control_heating queued state={state}, url={url}")

def control_cooling(state):
    enabled = temp_cfg.get("enable_cooling")
    url = temp_cfg.get("cooling_plug", "")
    if not enabled or not url:
        temp_cfg["cooler_pending"] = False
        temp_cfg["cooler_on"] = False
        append_control_log("plug_bypass", {"mode": "cooling", "reason": "disabled_or_no_url", "url": url})
        print("[LOG] Cooling control bypassed (not enabled or no URL).")
        return
    kasa_queue.put({'mode': 'cooling', 'url': url, 'action': state})
    temp_cfg["cooler_pending"] = True
    append_control_log("plug_command", {"mode": "cooling", "action": state, "url": url})
    print(f"[LOG] control_cooling queued state={state}, url={url}")

# --- Temperature control logic --------------------------------------------
def temperature_control_logic():
    temp = temp_cfg.get("current_temp")
    low = temp_cfg.get("low_limit")
    high = temp_cfg.get("high_limit")
    enable_heat = temp_cfg.get("enable_heating")
    enable_cool = temp_cfg.get("enable_cooling")
    override = temp_cfg.get("override_mode")
    manual_heat = temp_cfg.get("manual_heating")
    manual_cool = temp_cfg.get("manual_cooling")
    status = "Idle"

    print(f"[LOG] temperature_control_logic running: temp={temp}, low={low}, high={high}, enable_heat={enable_heat}, enable_cool={enable_cool}, override={override}")
    append_control_log("temperature", {"temp": temp})

    if temp is None:
        send_warning("Temperature Device Offline", "Tilt device not reporting temperature.")
        control_heating("off")
        control_cooling("off")
        status = "Device Offline"
        temp_cfg["status"] = status
        return

    if override:
        if manual_heat:
            control_heating("on")
            status = "Manual Heating"
        else:
            control_heating("off")
        if manual_cool:
            control_cooling("on")
            status = "Manual Cooling"
        else:
            control_cooling("off")
        temp_cfg["status"] = status
        return

    if enable_heat and temp < low:
        control_heating("on")
        status = "Heating"
        send_warning("Temperature Below Low Limit", f"Temperature {temp}°F below low limit {low}°F.")
    else:
        control_heating("off")

    if enable_cool and temp > high:
        control_cooling("on")
        status = "Cooling"
        send_warning("Temperature Above High Limit", f"Temperature {temp}°F above high limit {high}°F.")
    else:
        control_cooling("off")

    if enable_heat and enable_cool and low <= temp <= high:
        status = "In Range"

    temp_cfg["status"] = status
    print("[LOG] Finished temperature_control_logic update.")

# --- kasa result listener (stabilized behavior) ---------------------------
def kasa_result_listener():
    print("[LOG] Starting kasa_result_listener thread")
    while True:
        try:
            result = kasa_result_queue.get(timeout=5)
            print(f"[LOG] Received kasa result: {result}")
            mode = result.get('mode')
            action = result.get('action')
            success = result.get('success', False)
            url = result.get('url', '')
            append_control_log("plug_confirmation", {"mode": mode, "action": action, "success": success, "url": url, "raw": result})
            if mode == 'heating':
                # Always clear pending; only update on success
                temp_cfg["heater_pending"] = False
                if success:
                    temp_cfg["heater_on"] = (action == 'on')
                    temp_cfg["heating_error"] = False
                    temp_cfg["heating_error_msg"] = ""
                else:
                    # Do not flip heater_on on failure; record error instead
                    temp_cfg["heating_error"] = True
                    temp_cfg["heating_error_msg"] = result.get('error', '') or ''
            elif mode == 'cooling':
                temp_cfg["cooler_pending"] = False
                if success:
                    temp_cfg["cooler_on"] = (action == 'on')
                    temp_cfg["cooling_error"] = False
                    temp_cfg["cooling_error_msg"] = ""
                else:
                    temp_cfg["cooling_error"] = True
                    temp_cfg["cooling_error_msg"] = result.get('error', '') or ''
            else:
                print(f"[LOG] Unknown mode in kasa result: {mode}")
        except Exception:
            continue

threading.Thread(target=kasa_result_listener, daemon=True).start()

# --- Periodic temp control thread -----------------------------------------
def periodic_temp_control():
    while True:
        try:
            temp_cfg.update(load_json('temp_control_config.json', {}))
            print("[LOG] Reloaded temp_cfg in periodic_temp_control.")
            temperature_control_logic()
        except Exception as e:
            send_warning("Temperature Control Error", str(e))
            print("[LOG] Exception in periodic_temp_control:", e)
        try:
            interval = int(system_cfg.get("update_interval", 5))
        except Exception:
            interval = 5
        time.sleep(max(1, interval))

threading.Thread(target=periodic_temp_control, daemon=True).start()

# --- BLE scanner thread ---------------------------------------------------
def ble_loop():
    async def run_scanner():
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

@app.route('/tilt_config', methods=['GET', 'POST'])
def tilt_config():
    selected = request.args.get('tilt_color') or request.form.get('tilt_color')
    batch_history = []
    if selected:
        try:
            with open(f'batch_history_{selected}.json', 'r') as f:
                batch_history = json.load(f)
        except Exception:
            batch_history = []
    if request.method == 'POST':
        color = request.form.get('tilt_color')
        action = request.form.get('action')
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
    selected = request.args.get('tilt_color')
    action = request.args.get('action')
    config = tilt_cfg.get(selected, {}) if selected else {}
    batch_history = []
    if selected:
        try:
            with open(f'batch_history_{selected}.json', 'r') as f:
                batch_history = json.load(f)
        except Exception:
            batch_history = []
    return render_template('batch_settings.html',
        tilt_cfg=tilt_cfg,
        tilt_colors=list(TILT_UUIDS.values()),
        selected_tilt=selected,
        selected_config=config,
        system_settings=system_cfg,
        action=action,
        batch_history=batch_history
    )

@app.route('/chart')
def chart():
    return render_template('chart.html')

@app.route('/temp_config')
def temp_config():
    report_colors = list(tilt_cfg.keys())
    return render_template('temp_control_config.html',
        temp_control=temp_cfg,
        tilt_cfg=tilt_cfg,
        system_settings=system_cfg,
        batch_cfg=tilt_cfg,
        report_colors=report_colors
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
            "override_mode": 'override_mode' in data,
            "manual_heating": 'manual_heating' in data,
            "manual_cooling": 'manual_cooling' in data,
            "heating_plug": data.get("heating_plug", ""),
            "cooling_plug": data.get("cooling_plug", ""),
            "current_temp": float(data.get('current_temp', 0.0)) if data.get('current_temp') else None,
            "mode": data.get("mode", "Cooling Selected"),
            "status": data.get("status", "Idle"),
        })
    except Exception as e:
        print(f"[LOG] Error parsing temp config form: {e}")
    try:
        save_json('temp_control_config.json', temp_cfg)
    except Exception as e:
        print(f"[LOG] Error saving config in update_temp_config: {e}")
    temperature_control_logic()
    return redirect('/temp_config')

@app.route('/api/batch_settings', methods=['POST'])
def api_update_tilt_config():
    data = request.form
    color = data.get('tilt_color')
    if not color:
        return "No Tilt color selected", 400
    beer_name = data.get('beer_name', '').strip()
    batch_name = data.get('batch_name', '').strip()
    start_date = data.get('ferm_start_date', '').strip()
    existing = tilt_cfg.get(color, {})
    brew_id = existing.get('brewid')
    if not brew_id:
        brew_id = generate_brewid(beer_name, batch_name, start_date)
    batch_entry = {
        "beer_name": beer_name,
        "batch_name": batch_name,
        "ferm_start_date": start_date,
        "recipe_og": data.get('recipe_og', ''),
        "recipe_fg": data.get('recipe_fg', ''),
        "recipe_abv": data.get('recipe_abv', ''),
        "actual_og": data.get('actual_og', ''),
        "brewid": brew_id
    }
    try:
        with open(f'batch_history_{color}.json', 'r') as f:
            batches = json.load(f)
    except Exception:
        batches = []
    batches.append(batch_entry)
    try:
        with open(f'batch_history_{color}.json', 'w') as f:
            json.dump(batches, f, indent=2)
    except Exception as e:
        print(f"[LOG] Could not append batch history for {color}: {e}")
    tilt_cfg[color] = batch_entry
    save_json('tilt_config.json', tilt_cfg)
    return redirect(f"/tilt_config?tilt_color={color}")

@app.route('/api/update_system_config', methods=['POST'])
def update_system_config():
    data = request.form
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
        "update_interval": data.get("update_interval", "5"),
        "external_refresh_rate": data.get("external_refresh_rate", "15"),
        "external_name_0": data.get("external_name_0", ""),
        "external_url_0": data.get("external_url_0", ""),
        "external_name_1": data.get("external_name_1", ""),
        "external_url_1": data.get("external_url_1", ""),
        "external_name_2": data.get("external_name_2", ""),
        "external_url_2": data.get("external_url_2", ""),
        "warning_mode": data.get("warning_mode", "none"),
    })
    save_json('system_config.json', system_cfg)
    return redirect('/system_config')

@app.route('/scan_kasa_plugs')
def scan_kasa_plugs():
    from kasa import Discover
    devices = {}
    try:
        found_devices = asyncio.run(Discover.discover())
        for addr, dev in found_devices.items():
            devices[str(addr)] = dev.alias
    except Exception as e:
        print(f"[LOG] Error scanning Kasa plugs: {e}")
        return render_template("kasa_scan_results.html", error=str(e), devices={})
    return render_template("kasa_scan_results.html", devices=devices, error=None)

@app.route('/api/live_snapshot')
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
            "original_gravity": info.get("original_gravity"),
            "color_code": info.get("color_code")
        }
    return jsonify(snapshot)

# --- Simple stubs ---------------------------------------------------------
@app.route('/temp_report', methods=['POST'])
def temp_report():
    return redirect('/temp_config')

@app.route('/export_temp_log', methods=['POST'])
def export_temp_log():
    return redirect('/temp_config')

@app.route('/export_temp_csv', methods=['POST'])
def export_temp_csv():
    return redirect('/temp_config')

# --- Program entry ---------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
