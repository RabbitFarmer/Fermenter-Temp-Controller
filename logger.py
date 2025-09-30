import logging
import os
from datetime import datetime

# --- Legacy Kasa error logging ---
logging.basicConfig(
    filename='kasa_errors.log',
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

def ensure_log_dir():
    """Ensure the /logs directory exists."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def log_event(event_type, message, tilt_color=None):
    """
    Log any event (error, warning, notice) to /logs/{event_type}.log,
    and trigger notifications (email/SMS/both) as per system config.
    """
    ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{LOG_DIR}/{event_type}.log"
    entry = f"[{timestamp}]"
    if tilt_color:
        entry += f" [{tilt_color}]"
    entry += f" {message}\n"
    with open(filename, "a") as f:
        f.write(entry)
    # Notification logic will trigger for every logged event
    send_notification(event_type, message, tilt_color)

def send_notification(event_type, message, tilt_color=None):
    """
    Send notifications (email/SMS/both) according to system_cfg["warning_mode"].
    The send_email and send_sms functions must be implemented elsewhere (e.g., in app.py).
    """
    # Import system_cfg and notification functions from app.py
    try:
        from app import system_cfg, send_email, send_sms
    except ImportError:
        # If not running in app context, skip notification
        return

    mode = system_cfg.get("warning_mode", "none").lower()
    subject = f"{event_type} Notification"
    body = message
    if tilt_color:
        body = f"Tilt: {tilt_color}\n{body}"
    if mode == "email":
        send_email(subject, body)
    elif mode == "sms":
        send_sms(body)
    elif mode == "both":
        send_email(subject, body)
        send_sms(body)