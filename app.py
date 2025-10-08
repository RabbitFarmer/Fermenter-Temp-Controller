import hashlib
from flask import Flask, render_template, request, redirect, send_file, Response
from datetime import datetime
from tilt_static import TILT_UUIDS, COLOR_MAP
import json, time, threading
from bleak import BleakScanner
from multiprocessing import Process, Queue, Manager
from kasa_worker import kasa_worker
from logger import log_error, log_event
from fermentation_monitor import monitor_fermentation
import asyncio
import smtplib
from email.mime.text import MIMEText
import os
import glob

from batch_history import load_batch_history_jsonl, save_batch_jsonl, generate_brewid

manager = Manager()
status_dict = manager.dict()  # Shared status for plug errors

kasa_queue = Queue()
kasa_proc = Process(target=kasa_worker, args=(kasa_queue, status_dict))
kasa_proc.daemon = True
kasa_proc.start()

app = Flask(__name__)

# ... all previous code unchanged ...

@app.route('/temp_config')
def temp_config():
    temp_cfg["heating_error"] = status_dict.get("heating_error", False)
    temp_cfg["cooling_error"] = status_dict.get("cooling_error", False)
    temp_cfg["heating_error_msg"] = status_dict.get("heating_error_msg", "")
    temp_cfg["cooling_error_msg"] = status_dict.get("cooling_error_msg", "")
    refresh = request.args.get('refresh')
    refresh_needed = False
    prev_heater_on = temp_cfg.get("heater_on", False)
    prev_cooler_on = temp_cfg.get("cooler_on", False)
    temperature_control_logic()
    if not refresh:
        if prev_heater_on != temp_cfg.get("heater_on") or prev_cooler_on != temp_cfg.get("cooler_on"):
            refresh_needed = True
    # Find all temp_control_*.jsonl files for the report dropdowns
    report_files = glob.glob('temp_control_*.jsonl')
    report_colors = [f.split('_')[2].split('.')[0] for f in report_files]
    if refresh_needed:
        return redirect('/temp_config?refresh=1')
    return render_template('temp_control_config.html',
        temp_control=temp_cfg,
        batch_cfg=batch_cfg,
        system_settings=system_cfg,
        refresh=refresh,
        report_colors=report_colors
    )

@app.route('/temp_report', methods=['GET', 'POST'])
def temp_report():
    files = glob.glob('temp_control_*.jsonl')
    colors = [f.split('_')[2].split('.')[0] for f in files]
    default_color = temp_cfg.get("tilt_color", colors[0] if colors else None)
    selected_color = request.form.get('tilt_color', default_color)
    if request.method == 'POST':
        return redirect(f'/temp_report_display/{selected_color}')
    if len(colors) > 1:
        return render_template('temp_report_select.html', colors=colors, default_color=default_color)
    elif colors:
        return redirect(f'/temp_report_display/{colors[0]}')
    else:
        return "No temp report files found.", 404

@app.route('/temp_report_display/<color>')
def temp_report_display(color):
    PAGE_SIZE = 25
    page = int(request.args.get('page', 0))
    filename = f'temp_control_{color}.jsonl'
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
    except Exception:
        return "No temp report data found.", 404
    total = len(lines)
    start = page * PAGE_SIZE
    end = min((page + 1) * PAGE_SIZE, total)
    page_data = lines[start:end]
    at_end = end >= total
    return render_template('temp_report_display.html',
                           color=color,
                           page_data=page_data,
                           page=page,
                           total=total,
                           at_end=at_end)

@app.route('/export_temp_log', methods=['POST'])
def export_temp_log():
    color = request.form.get('tilt_color')
    filename = f'temp_control_{color}.jsonl'
    if not color or not os.path.exists(filename):
        return "No log file found.", 404
    return send_file(filename, as_attachment=True)

@app.route('/export_temp_csv', methods=['POST'])
def export_temp_csv():
    color = request.form.get('tilt_color')
    filename = f'temp_control_{color}.jsonl'
    if not color or not os.path.exists(filename):
        return "No log file found.", 404
    lines = []
    with open(filename, 'r') as f:
        for entry in f:
            try:
                obj = json.loads(entry)
                ordered_keys = ['timestamp', 'event', 'temp_f', 'current_temp', 'high_limit', 'low_limit']
                row = [str(obj.get(k, '')) for k in ordered_keys]
                lines.append(','.join(row))
            except Exception:
                continue
    header = ','.join(['timestamp', 'event', 'temp_f', 'current_temp', 'high_limit', 'low_limit'])
    csv_data = header + '\n' + '\n'.join(lines)
    return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename=temp_control_{color}.csv"})

# ... rest of your app.py unchanged ...