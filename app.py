import hashlib
from flask import Flask, render_template, request, redirect, render_template_string
from datetime import datetime, timedelta
from tilt_static import TILT_UUIDS, COLOR_MAP
import json, time, threading, os
from bleak import BleakScanner
from multiprocessing import Process, Queue, Manager
from kasa_worker import kasa_worker
from logger import log_error
import asyncio
import smtplib
from email.mime.text import MIMEText

manager = Manager()
status_dict = manager.dict()
kasa_queue = Queue()
kasa_proc = Process(target=kasa_worker, args=(kasa_queue, status_dict))
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

batch_cfg = {}
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
        if color not in batch_cfg:
            batch_cfg[color] = {
                "beer_name": "",
                "batch_name": "",
                "ferm_start_date": "",
                "recipe_og": "",
                "recipe_fg": "",
                "recipe_abv": "",
                "actual_og": None,
                "brewid": "",
                "stall_days": 0
            }

batch_cfg = load_json('batch_settings.json', {})
temp_cfg = load_json('temp_control_config.json', {})
system_cfg = load_json('system_config.json', {})

if "stall_variance_threshold" not in system_cfg:
    system_cfg["stall_variance_threshold"] = 0.001
if "stall_notification_days" not in system_cfg:
    system_cfg["stall_notification_days"] = 3
ensure_all_tilts()

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default

def safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default

required_keys = [
    "temp", "high_limit", "low_limit",
    "heater_on", "cooler_on",
    "enable_heating", "enable_cooling",
    "tilt_color", "cooling_active",
    "heating_active", "current_temp", 
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
        with open(f'batch_history_{color}.jsonl', 'r') as f:
            return [json.loads(line) for line in f if line.strip()]
    except Exception as e:
        print(f"[LOG] Could not load batch history for {color}: {e}")
        return []

def append_batch_history(color, batch_entry):
    try:
        with open(f'batch_history_{color}.jsonl', 'a') as f:
            f.write(json.dumps(batch_entry) + '\n')
        print(f"[LOG] Appended batch history for {color}: {batch_entry}")
    except Exception as e:
        print(f"[LOG] Could not append batch history for {color}: {e}")

def count_stall_days(batch_records, gravity_threshold=0.001):
    stall_days = 0
    prev_gravity = None
    prev_date = None
    for r in batch_records:
        gravity = r.get("gravity")
        timestamp = r.get("timestamp")
        if gravity is not None and timestamp is not None:
            try:
                date = datetime.fromisoformat(timestamp).date()
            except Exception:
                continue
            if prev_gravity is not None and prev_date is not None:
                if date != prev_date and abs(float(gravity) - float(prev_gravity)) < gravity_threshold:
                    stall_days += 1
            prev_gravity = gravity
            prev_date = date
    return stall_days

def send_stall_notification(brewname, gravity):
    subject = f"{brewname} fermentation stalled"
    body = f"{brewname} has stalled at a gravity reading of {gravity}"
    send_warning(subject, body)

def daily_stall_check():
    last_checked_date = None
    while True:
        now = datetime.utcnow().date()
        if last_checked_date != now:
            last_checked_date = now
            gravity_threshold = safe_float(system_cfg.get("stall_variance_threshold", 0.001), 0.001)
            stall_notification_days = safe_int(system_cfg.get("stall_notification_days", 3), 3)
            for color in TILT_UUIDS.values():
                history_file = f'batch_history_{color}.jsonl'
                if not os.path.exists(history_file):
                    continue
                batch_records = get_batch_history(color)
                today_records = []
                prevday_records = []
                for r in batch_records:
                    ts = r.get("timestamp")
                    if not ts:
                        continue
                    try:
                        rec_date = datetime.fromisoformat(ts).date()
                    except Exception:
                        continue
                    if rec_date == now:
                        today_records.append(r)
                    elif rec_date == (now - timedelta(days=1)):
                        prevday_records.append(r)
                if today_records and prevday_records:
                    today_gravity = float(today_records[-1].get("gravity", 0))
                    prev_gravity = float(prevday_records[-1].get("gravity", 0))
                    if abs(today_gravity - prev_gravity) < gravity_threshold:
                        stall_days = batch_cfg.get(color, {}).get("stall_days", 0) + 1
                        if color in batch_cfg:
                            batch_cfg[color]["stall_days"] = stall_days
                        else:
                            batch_cfg[color] = {"stall_days": stall_days}
                        save_json('batch_settings.json', batch_cfg)
                        stall_entry = {
                            "date": str(now),
                            "stall_days": stall_days,
                            "brewname": batch_cfg.get(color, {}).get("beer_name", "Unknown"),
                            "gravity": today_gravity
                        }
                        with open(f'batch_settings_{color}.jsonl', 'a') as f:
                            f.write(json.dumps(stall_entry) + '\n')
                        if stall_days >= stall_notification_days:
                            brewname = stall_entry["brewname"]
                            gravity = stall_entry["gravity"]
                            send_stall_notification(brewname, gravity)
        time.sleep(60 * 60)

threading.Thread(target=daily_stall_check, daemon=True).start()

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

@app.route('/batch_settings', methods=['GET', 'POST'])
def batch_settings():
    if request.method == 'POST':
        data = request.form
        color = data.get('tilt_color')
        if not color:
            print("[LOG] No Tilt color selected in batch_settings")
            return "No Tilt color selected", 400

        beer_name = data.get('beer_name', '').strip()
        batch_name = data.get('batch_name', '').strip()
        start_date = data.get('ferm_start_date', '').strip()

        existing = batch_cfg.get(color, {})
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
            "brewid": brew_id,
            "stall_days": existing.get("stall_days", 0)
        }
        append_batch_history(color, batch_entry)
        batch_cfg[color] = batch_entry
        save_json('batch_settings.json', batch_cfg)
        return redirect(f"/batch_settings?tilt_color={color}")

    selected = request.args.get('tilt_color')
    if not selected and live_tilts:
        selected = next(iter(live_tilts.keys()))
    action = request.args.get('action')
    config = batch_cfg.get(selected, {}) if selected else {}
    batch_history = get_batch_history(selected) if selected else []
    return render_template('batch_settings.html',
        batch_cfg=batch_cfg,
        tilt_colors=list(TILT_UUIDS.values()),
        selected_tilt=selected,
        selected_config=config,
        system_settings=system_cfg,
        action=action,
        batch_history=batch_history
    )

@app.route('/chart')
def chart():
    color = request.args.get('color', 'Blue')
    beer_name = request.args.get('beer_name', 'OctoberFest')
    batch_name = request.args.get('batch_name', 'MainBatch')
    start_date = request.args.get('start_date', '2025-10-01')
    brew_id = request.args.get('brew_id', 'your_brew_id_here')

    batch_records = get_batch_history(color)
    timestamps = [r.get("timestamp") for r in batch_records if "timestamp" in r]
    gravities = [r.get("gravity") for r in batch_records if "gravity" in r]
    temps = [r.get("temp_f") for r in batch_records if "temp_f" in r]

    ferm_start_date = batch_records[0].get("ferm_start_date") if batch_records else start_date
    try:
        ferm_days = (datetime.utcnow() - datetime.strptime(ferm_start_date, "%Y-%m-%d")).days
    except Exception:
        ferm_days = 0

    gravity_threshold = safe_float(system_cfg.get("stall_variance_threshold", 0.001), 0.001)
    stall_days = batch_cfg.get(color, {}).get("stall_days", count_stall_days(batch_records, gravity_threshold))
    system_settings = system_cfg

    return render_template(
        "chart.html",
        color=color,
        system_settings=system_settings,
        ferm_start_date=ferm_start_date,
        ferm_days=ferm_days,
        stall_days=stall_days,
        timestamps=timestamps,
        gravities=gravities,
        temps=temps
    )

@app.route('/chart/<color>')
def chart_color(color):
    beer_name = request.args.get('beer_name', 'OctoberFest')
    batch_name = request.args.get('batch_name', 'MainBatch')
    start_date = request.args.get('start_date', '2025-10-01')
    brew_id = request.args.get('brew_id', 'your_brew_id_here')

    batch_records = get_batch_history(color)
    timestamps = [r.get("timestamp") for r in batch_records if "timestamp" in r]
    gravities = [r.get("gravity") for r in batch_records if "gravity" in r]
    temps = [r.get("temp_f") for r in batch_records if "temp_f" in r]

    ferm_start_date = batch_records[0].get("ferm_start_date") if batch_records else start_date
    try:
        ferm_days = (datetime.utcnow() - datetime.strptime(ferm_start_date, "%Y-%m-%d")).days
    except Exception:
        ferm_days = 0

    gravity_threshold = safe_float(system_cfg.get("stall_variance_threshold", 0.001), 0.001)
    stall_days = batch_cfg.get(color, {}).get("stall_days", count_stall_days(batch_records, gravity_threshold))
    system_settings = system_cfg

    return render_template(
        "chart.html",
        color=color,
        system_settings=system_settings,
        ferm_start_date=ferm_start_date,
        ferm_days=ferm_days,
        stall_days=stall_days,
        timestamps=timestamps,
        gravities=gravities,
        temps=temps
    )

@app.route('/temp_config')
def temp_config():
    return render_template('temp_control_config.html',
        temp_control=temp_cfg,
        batch_cfg=batch_cfg,
        system_settings=system_cfg
    )

@app.route('/update_temp_config', methods=['POST'])
def update_temp_config():
    data = request.form
    print("[DEBUG] /update_temp_config POST route triggered")
    print("[LOG] Received form data in update_temp_config:", dict(data))
    temp_cfg.update({
        "tilt_color": data.get('tilt_color', ''),
        "low_limit": float(data.get('low_limit', 0)),
        "high_limit": float(data.get('high_limit', 100)),
        "enable_heating": 'enable_heating' in data,
        "enable_cooling": 'enable_cooling' in data,
        "heating_plug": data.get("heating_plug", ""),
        "cooling_plug": data.get("cooling_plug", ""),
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
    temperature_control_logic()
    print("[LOG] Ran temperature_control_logic after POST update.")
    return redirect('/temp_config')

@app.route('/view_temp_log')
def view_temp_log():
    tilt_color = request.args.get('tilt_color')
    page = int(request.args.get('page', 1))
    log_file = f"temp_log_{tilt_color}.txt"
    try:
        with open(log_file) as f:
            lines = f.readlines()
    except Exception as e:
        return f"Could not load log for {tilt_color}: {e}"

    lines_per_page = 25
    start = (page - 1) * lines_per_page
    end = start + lines_per_page
    page_lines = lines[start:end]
    total_pages = (len(lines) + lines_per_page - 1) // lines_per_page

    html = """
    <h2>Temperature Log for {{ tilt_color }}</h2>
    <pre>{{ page_lines|join('') }}</pre>
    <div>
      <p>Page {{ page }} of {{ total_pages }}</p>
      <form method="get" style="display:inline;">
        <input type="hidden" name="tilt_color" value="{{ tilt_color }}">
        <input type="hidden" name="page" value="{{ page - 1 }}">
        <button type="submit" {% if page <= 1 %}disabled{% endif %}>Previous</button>
      </form>
      <form method="get" style="display:inline;">
        <input type="hidden" name="tilt_color" value="{{ tilt_color }}">
        <input type="hidden" name="page" value="{{ page + 1 }}">
        <button type="submit" {% if page >= total_pages %}disabled{% endif %}>Next</button>
      </form>
      <button onclick="window.location.href='/temp_config'">Return</button>
    </div>
    <p>Use Next/Previous buttons to navigate, Return to go back.</p>
    """
    return render_template_string(html, tilt_color=tilt_color, page_lines=page_lines, page=page, total_pages=total_pages)

@app.route('/export_temp_log')
def export_temp_log():
    tilt_color = request.args.get('tilt_color')
    log_file = f"temp_log_{tilt_color}.txt"
    try:
        with open(log_file) as f:
            log_data = f.read()
    except Exception as e:
        return f"Could not load log for {tilt_color}: {e}"
    return app.response_class(log_data, mimetype='text/plain', headers={'Content-Disposition': f'attachment;filename={log_file}'})

@app.route('/export_temp_csv')
def export_temp_csv():
    tilt_color = request.args.get('tilt_color')
    csv_file = f"temp_log_{tilt_color}.csv"
    try:
        with open(csv_file) as f:
            csv_data = f.read()
    except Exception as e:
        return f"Could not load CSV for {tilt_color}: {e}"
    return app.response_class(csv_data, mimetype='text/csv', headers={'Content-Disposition': f'attachment;filename={csv_file}'})

@app.route('/exit_system')
def exit_system():
    # Force all plugs OFF for safety
    for color in TILT_UUIDS.values():
        # Turn heating plug OFF
        temp_cfg['tilt_color'] = color
        temp_cfg['enable_heating'] = True
        temp_cfg['enable_cooling'] = True
        control_heating("off")
        control_cooling("off")
    return render_template_string("""
        <h2>System Exit Requested</h2>
        <p>All plugs have been forced OFF. You may now close this browser tab or shut down the server.</p>
        <button onclick="window.location.href='/'">Return to Dashboard</button>
    """)


@app.route('/update_system_config', methods=['POST'])
def update_system_config():
    data = request.form
    # Convert minute-based timers back to seconds
    update_interval_sec = safe_float(data.get("update_interval", 1)) * 60
    external_refresh_rate_sec = safe_float(data.get("external_refresh_rate", 1)) * 60
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
        "update_interval": update_interval_sec,
        "external_refresh_rate": external_refresh_rate_sec,
        "offsite_name_1": data.get("offsite_name_1", ""),
        "offsite_url_1": data.get("offsite_url_1", ""),
        "offsite_name_2": data.get("offsite_name_2", ""),
        "offsite_url_2": data.get("offsite_url_2", ""),
        "warning_mode": data.get("warning_mode", "none"),
        "stall_variance_threshold": safe_float(data.get("stall_variance_threshold", 0.001), 0.001),
        "stall_notification_days": safe_int(data.get("stall_notification_days", 3), 3)
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
    cfg = batch_cfg.get(color, {})
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
        "stall_days": cfg.get("stall_days", 0)
    }

def log_tilt_reading(color, gravity, temp_f, rssi):
    cfg = batch_cfg.get(color, {})
    batch = {
        "beer_name": cfg.get("beer_name", "Unknown"),
        "batch_name": cfg.get("batch_name", "Unknown"),
        "brewid": cfg.get("brewid", generate_brewid(cfg.get("beer_name", ""), cfg.get("batch_name", ""), cfg.get("ferm_start_date", ""))),
        "ferm_start_date": cfg.get("ferm_start_date", "Unknown"),
        "original_gravity": cfg.get("actual_og", gravity),
        "gravity": gravity,
        "temp_f": temp_f,
        "rssi": rssi,
        "timestamp": datetime.utcnow().isoformat(),
        "stall_days": cfg.get("stall_days", 0)
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

def send_email(subject, body):
    cfg = system_cfg
    if not cfg.get("email"):
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = cfg["email"]
        msg["To"] = cfg["email"]
        server = smtplib.SMTP("localhost")
        server.sendmail(cfg["email"], [cfg["email"]], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"[LOG] Email send failed: {e}")

def send_sms(body):
    print(f"[LOG] SMS: {body}")  # Implement Twilio or other service as needed

def send_warning(subject, body):
    mode = system_cfg.get("warning_mode", "none").lower()
    if mode == "email":
        send_email(subject, body)
    elif mode == "sms":
        send_sms(body)
    elif mode == "both":
        send_email(subject, body)
        send_sms(body)

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
    mid = (high + low) / 2 if (high is not None and low is not None) else None

    temp_cfg['heater_on'] = False
    temp_cfg['cooler_on'] = False

    if temp is None or mid is None:
        control_heating("off")
        control_cooling("off")
        temp_cfg["status"] = "Device Offline"
        return

    # 1. Heating logic
    if enable_heat:
        if temp < low:
            control_heating("on")
            temp_cfg["heater_on"] = True
            control_cooling("off")
            temp_cfg["cooler_on"] = False
            temp_cfg["status"] = "Heating"
            return
        elif temp_cfg.get("heater_on", False) and temp >= mid:
            control_heating("off")
            temp_cfg["heater_on"] = False
            temp_cfg["status"] = "In Range"
            return

    # 2. Cooling logic
    if enable_cool:
        if temp > high:
            control_cooling("on")
            temp_cfg["cooler_on"] = True
            control_heating("off")
            temp_cfg["heater_on"] = False
            temp_cfg["status"] = "Cooling"
            return
        elif temp_cfg.get("cooler_on", False) and temp <= mid:
            control_cooling("off")
            temp_cfg["cooler_on"] = False
            temp_cfg["status"] = "In Range"
            return

    # 3. If neither heating nor cooling active, both off
    control_heating("off")
    temp_cfg["heater_on"] = False
    control_cooling("off")
    temp_cfg["cooler_on"] = False
    temp_cfg["status"] = "In Range"

def periodic_temp_control():
    while True:
        try:
            temp_cfg.update(load_json('temp_control_config.json', {}))
            print("[LOG] Reloaded temp_cfg in periodic_temp_control:", temp_cfg)
            temperature_control_logic()
            print("[LOG] Ran temperature_control_logic in periodic_temp_control.")
        except Exception as e:
            send_warning("Temperature Control Error", str(e))
            print("[LOG] Exception in periodic_temp_control:", e)
        time.sleep(int(system_cfg.get("update_interval", 300)))

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