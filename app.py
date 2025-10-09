import hashlib
from flask import Flask, render_template, request, redirect
from datetime import datetime
from tilt_static import TILT_UUIDS, COLOR_MAP
import json, time, threading
from bleak import BleakScanner
from multiprocessing import Process, Queue
from kasa_worker import kasa_worker   # assuming kasa_worker.py is in the same folder
from logger import log_error          # for error logging
import asyncio

# New imports for notifications
import smtplib
from email.mime.text import MIMEText

kasa_queue = Queue()
kasa_proc = Process(target=kasa_worker, args=(kasa_queue,))
kasa_proc.daemon = True
kasa_proc.start()

app = Flask(__name__)

@app.template_filter('localtime')
def localtime_filter(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return iso_str

tilt_cfg = {}
temp_cfg = {}
system_cfg = {}
live_tilts = {}
tilt_status = {}

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
        print(f"[LOG] Saved JSON to {path}: {data}")
    except Exception as e:
        print(f"[LOG] Error saving JSON to {path}: {e}")

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

tilt_cfg = load_json('tilt_config.json', {})
temp_cfg = load_json('temp_control_config.json', {})
system_cfg = load_json('system_config.json', {})
ensure_all_tilts()

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default

required_keys = [
    "temp", "high_limit", "low_limit",
    "heater_on", "cooler_on",
    "override_mode", "enable_heating", "enable_cooling",
    "tilt_color", "manual_cooling", "cooling_active",
    "manual_heating", "heating_active", "current_temp", 
    "original_gravity", "gravity",
    "mode", "status"
] 

for key in required_keys:
    if "temp" in key or "limit" in key:
        temp_cfg.setdefault(key, 0.0)
    else:
        temp_cfg.setdefault(key, False)

def generate_brewid(beer_name, batch_name, date_str):
    id_str = f"{beer_name}-{batch_name}-{date_str}"
    return hashlib.sha256(id_str.encode('utf-8')).hexdigest()[:8]

def get_batch_history(color):
    try:
        with open(f'batch_history_{color}.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[LOG] Could not load batch history for {color}: {e}")
        return []

def append_batch_history(color, batch_entry):
    batches = get_batch_history(color)
    batches.append(batch_entry)
    try:
        with open(f'batch_history_{color}.json', 'w') as f:
            json.dump(batches, f, indent=2)
        print(f"[LOG] Appended batch history for {color}: {batch_entry}")
    except Exception as e:
        print(f"[LOG] Could not append batch history for {color}: {e}")

@app.route('/')
def dashboard():
    return render_template('maindisplay.html',
        system_settings=system_cfg,
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
    batch_history = get_batch_history(selected) if selected else []
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
    batch_history = get_batch_history(selected) if selected else []
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
    return render_template('temp_control_config.html',
        temp_control=temp_cfg,
        tilt_cfg=tilt_cfg,
        system_settings=system_cfg
    )

@app.route('/api/batch_settings', methods=['POST'])
def update_tilt_config():
    data = request.form
    color = data.get('tilt_color')
    if not color:
        print("[LOG] No Tilt color selected in batch_settings")
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
    append_batch_history(color, batch_entry)

    tilt_cfg[color] = batch_entry
    save_json('tilt_config.json', tilt_cfg)
    return redirect(f"/tilt_config?tilt_color={color}")

@app.route('/api/update_temp_config', methods=['POST'])
def update_temp_config():
    data = request.form
    print("[DEBUG] /api/update_temp_config POST route triggered")
    print("[LOG] Received form data in update_temp_config:", dict(data))
    temp_cfg.update({
        "tilt_color": data.get('tilt_color', ''),
        "low_limit": float(data.get('low_limit', 0)),
        "high_limit": float(data.get('high_limit', 100)),
        "enable_heating": 'enable_heating' in data,
        "enable_cooling": 'enable_cooling' in data,
        "override_mode": 'override_mode' in data,
        "manual_heating": 'manual_heating' in data,
        "manual_cooling": 'manual_cooling' in data,
        # Plugs are optional. If left blank, key is an empty string.
        "heating_plug": data.get("heating_plug", ""),
        "cooling_plug": data.get("cooling_plug", ""),
        # Optionally handle "current_temp", "mode", "status" if present in form
        "current_temp": float(data.get('current_temp', 0.0)) if data.get('current_temp') else None,
        "mode": data.get("mode", "Cooling Selected"),
        "status": data.get("status", "Idle"),
    })
    print("[LOG] Updated temp_cfg in update_temp_config:", temp_cfg)
    try:
        save_json('temp_control_config.json', temp_cfg)
        print("[LOG] Saved config to disk from update_temp_config.")
    except Exception as e:
        print("[LOG] Error saving config in update_temp_config:", e)
    # Also run control logic here, but DO NOT save to disk in the thread
    temperature_control_logic()
    print("[LOG] Ran temperature_control_logic after POST update.")
    return redirect('/temp_config')

def periodic_temp_control():
    while True:
        try:
            # Reload latest config:
            temp_cfg.update(load_json('temp_control_config.json', {}))
            print("[LOG] Reloaded temp_cfg in periodic_temp_control:", temp_cfg)
            temperature_control_logic()
            print("[LOG] Ran temperature_control_logic in periodic_temp_control.")
            # DO NOT save temp_cfg to disk here!
        except Exception as e:
            send_warning("Temperature Control Error", str(e))
            print("[LOG] Exception in periodic_temp_control:", e)
        time.sleep(int(system_cfg.get("update_interval", 5)))

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
        "warning_mode": data.get("warning_mode", "none"),  # <-- new
    })
    save_json('system_config.json', system_cfg)
    print("[LOG] Updated and saved system_cfg in update_system_config:", system_cfg)
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
    # Optional: append to log file or database

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

# --- KASA PLUG CONTROL AND NOTIFICATIONS ---

def send_email(subject, body):
    cfg = system_cfg
    if not cfg.get("email"):
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = cfg["email"]
        msg["To"] = cfg["email"]

        # For local SMTP, adjust as needed (Gmail, etc. requires authentication)
        server = smtplib.SMTP("localhost")
        server.sendmail(cfg["email"], [cfg["email"]], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"[LOG] Email send failed: {e}")

def send_sms(body):
    # Placeholder for SMS (Twilio, etc.)
    print(f"[LOG] SMS: {body}")  # Implement Twilio or other service as needed

def send_warning(subject, body):
    mode = system_cfg.get("warning_mode", "none").lower()  # "sms", "email", "both", "none"
    if mode == "email":
        send_email(subject, body)
    elif mode == "sms":
        send_sms(body)
    elif mode == "both":
        send_email(subject, body)
        send_sms(body)
    # "none" does nothing

def control_heating(state):
    enabled = temp_cfg.get("enable_heating")
    url = temp_cfg.get("heating_plug", "")
    if not enabled or not url:
        print("[LOG] Heating control bypassed (not enabled or no URL)")
        return
    kasa_queue.put({'mode': 'heating', 'url': url, 'action': state, 'enabled': enabled})
    print(f"[LOG] control_heating called with state={state}, enabled={enabled}, url={url}")

def control_cooling(state):
    enabled = temp_cfg.get("enable_cooling")
    url = temp_cfg.get("cooling_plug", "")
    if not enabled or not url:
        print("[LOG] Cooling control bypassed (not enabled or no URL)")
        return
    kasa_queue.put({'mode': 'cooling', 'url': url, 'action': state, 'enabled': enabled})
    print(f"[LOG] control_cooling called with state={state}, enabled={enabled}, url={url}")

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

    # Device offline detection
    if temp is None:
        send_warning("Temperature Device Offline", "Tilt device not reporting temperature.")
        control_heating("off")
        control_cooling("off")
        status = "Device Offline"
        temp_cfg["status"] = status
        print("[LOG] Device offline detected in temperature_control_logic.")
        return

    # Manual override
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
        print("[LOG] Manual override in temperature_control_logic:", temp_cfg)
        return

    # Auto control logic
    # Heating
    if enable_heat and temp < low:
        control_heating("on")
        status = "Heating"
        send_warning("Temperature Below Low Limit", f"Temperature {temp}°F below low limit {low}°F.")
    else:
        control_heating("off")
    # Cooling
    if enable_cool and temp > high:
        control_cooling("on")
        status = "Cooling"
        send_warning("Temperature Above High Limit", f"Temperature {temp}°F above high limit {high}°F.")
    else:
        control_cooling("off")
    # In range
    if enable_heat and enable_cool and low <= temp <= high:
        status = "In Range"
    temp_cfg["status"] = status
    print("[LOG] Finished temperature_control_logic update:", temp_cfg)

# Start periodic control thread
threading.Thread(target=periodic_temp_control, daemon=True).start()

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

    asyncio.run(run_scanner())

threading.Thread(target=ble_loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

### END OF PROGRAM ###