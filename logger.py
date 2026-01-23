import logging
import os
import json
from datetime import datetime

# --- Legacy Kasa error logging ---
logging.basicConfig(
    filename='logs/kasa_errors.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s %(message)s'
)

def log_error(msg):
    """
    Log Kasa-specific errors to kasa_errors.log and print to terminal.
    Use this for legacy Kasa plug error logging.
    """
    print(msg)  # Terminal output
    logging.error(msg)  # Log to kasa_errors.log

# --- General event logging and notifications ---
LOG_DIR = "logs"
BATCHES_DIR = "batches"
TEMP_CONTROL_LOG = 'temp_control/temp_control_log.jsonl'

# Temperature control event types (go to temp_control_log.jsonl)
TEMP_CONTROL_EVENTS = {
    'temp_below_low_limit',
    'temp_above_high_limit',
    'heating_on',
    'heating_off',
    'cooling_on',
    'cooling_off',
    'temp_control_started',
    'temp_control_stopped',
    'temp_control_mode_changed',
}

# Batch event types (go to batch-specific JSONL files)
BATCH_EVENTS = {
    'loss_of_signal',
    'fermentation_starting',
    'fermentation_completion',
    'fermentation_finished',
    'daily_report',
}

def ensure_log_dir():
    """Ensure the /logs directory exists."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def ensure_batches_dir():
    """Ensure the /batches directory exists."""
    if not os.path.exists(BATCHES_DIR):
        os.makedirs(BATCHES_DIR)

def log_event(event_type, message, tilt_color=None):
    """
    Log any event to the appropriate log file:
    - Temperature control events go to temp_control_log.jsonl
    - Batch events go to batches/{brewid}.jsonl
    - Other events go to /logs/{event_type}.log
    
    Also triggers notifications (email/PUSH/both) as per system config.
    """
    # Route to appropriate log based on event type
    if event_type in TEMP_CONTROL_EVENTS:
        log_to_temp_control_log(event_type, message, tilt_color)
    elif event_type in BATCH_EVENTS and tilt_color:
        log_to_batch_log(event_type, message, tilt_color)
    else:
        # Generic log to /logs directory
        log_to_generic_log(event_type, message, tilt_color)
    
    # Send notification
    send_notification(event_type, message, tilt_color)

def log_to_temp_control_log(event_type, message, tilt_color=None):
    """Log temperature control events to temp_control_log.jsonl"""
    try:
        d = os.path.dirname(TEMP_CONTROL_LOG)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "message": message,
        }
        if tilt_color:
            entry["tilt_color"] = tilt_color
        
        with open(TEMP_CONTROL_LOG, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[LOG] Failed to log to temp_control_log.jsonl: {e}")

def log_to_batch_log(event_type, message, tilt_color):
    """Log batch events to batch-specific JSONL file"""
    try:
        ensure_batches_dir()
        
        # Try to get brewid from tilt_cfg, fallback to tilt_color if not available
        brewid = tilt_color  # Default to tilt_color
        try:
            from app import tilt_cfg
            brewid = tilt_cfg.get(tilt_color, {}).get("brewid", tilt_color)
        except (ImportError, AttributeError):
            # If app is not available or tilt_cfg doesn't exist, use tilt_color as brewid
            pass
        
        batch_file = f"{BATCHES_DIR}/{brewid}.jsonl"
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "message": message,
            "tilt_color": tilt_color,
        }
        
        with open(batch_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[LOG] Failed to log to batch log: {e}")
        # Fallback to generic log
        log_to_generic_log(event_type, message, tilt_color)

def log_to_generic_log(event_type, message, tilt_color=None):
    """Log to generic /logs/{event_type}.log file"""
    ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{LOG_DIR}/{event_type}.log"
    entry = f"[{timestamp}]"
    if tilt_color:
        entry += f" [{tilt_color}]"
    entry += f" {message}\n"
    with open(filename, "a") as f:
        f.write(entry)

def send_notification(event_type, message, tilt_color=None):
    """
    Send notifications (email/PUSH/both) according to system_cfg["warning_mode"].
    Only sends if the specific notification type is enabled in system_cfg.
    """
    # Import system_cfg and notification functions from app.py
    try:
        from app import system_cfg, attempt_send_notifications
    except ImportError:
        # If not running in app context, skip notification
        return

    # Check if notifications are enabled for this event type
    enabled = False
    
    # Check temperature control notifications
    if event_type in TEMP_CONTROL_EVENTS:
        temp_notif = system_cfg.get('temp_control_notifications', {})
        notif_key = f'enable_{event_type}'
        enabled = temp_notif.get(notif_key, True)
    
    # Check batch notifications
    elif event_type in BATCH_EVENTS:
        batch_notif = system_cfg.get('batch_notifications', {})
        notif_key = f'enable_{event_type}'
        enabled = batch_notif.get(notif_key, True)
    
    # Always enable for other event types
    else:
        enabled = True
    
    if not enabled:
        return
    
    # Send notification
    mode = system_cfg.get("warning_mode", "none").upper()
    if mode in ("EMAIL", "PUSH", "BOTH"):
        subject = f"{event_type.replace('_', ' ').title()} Notification"
        body = message
        if tilt_color:
            body = f"Tilt: {tilt_color}\n{body}"
        attempt_send_notifications(subject, body)