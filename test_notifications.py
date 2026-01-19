#!/usr/bin/env python3
"""
Test script to verify email/SMS notification functionality.
This script simulates various notification scenarios without requiring actual Tilt hardware.
"""

import json
import sys
from datetime import datetime

# Load configuration
try:
    with open('config/system_config.json', 'r') as f:
        system_cfg = json.load(f)
except Exception as e:
    print(f"Error loading config/system_config.json: {e}")
    sys.exit(1)

print("=" * 80)
print("NOTIFICATION CONFIGURATION TEST")
print("=" * 80)
print()

# Check warning mode
warning_mode = system_cfg.get('warning_mode', 'NONE')
print(f"Warning Mode: {warning_mode}")
print()

if warning_mode == 'NONE':
    print("⚠️  WARNING: Notifications are disabled (warning_mode = NONE)")
    print("   To enable, set warning_mode to 'EMAIL', 'SMS', or 'BOTH' in system settings")
    print()

# Check email configuration
print("Email Configuration:")
print(f"  Sending Email: {system_cfg.get('sending_email', 'NOT SET')}")
print(f"  Recipient Email: {system_cfg.get('email', 'NOT SET')}")
print(f"  SMTP Host: {system_cfg.get('smtp_host', 'NOT SET')}")
print(f"  SMTP Port: {system_cfg.get('smtp_port', 'NOT SET')}")
print(f"  SMTP STARTTLS: {system_cfg.get('smtp_starttls', False)}")
print(f"  SMTP Password: {'SET' if system_cfg.get('smtp_password') else 'NOT SET'}")
print()

# Check SMS configuration
print("SMS Configuration:")
print(f"  Mobile Number: {system_cfg.get('mobile', 'NOT SET')}")
print(f"  SMS Gateway Domain: {system_cfg.get('sms_gateway_domain', 'NOT SET')}")
print()

# Check temperature control notifications
print("Temperature Control Notifications:")
temp_notif = system_cfg.get('temp_control_notifications', {})
print(f"  Below Low Limit: {'ENABLED' if temp_notif.get('enable_temp_below_low_limit', True) else 'DISABLED'}")
print(f"  Above High Limit: {'ENABLED' if temp_notif.get('enable_temp_above_high_limit', True) else 'DISABLED'}")
print(f"  Heating On: {'ENABLED' if temp_notif.get('enable_heating_on', False) else 'DISABLED'}")
print(f"  Heating Off: {'ENABLED' if temp_notif.get('enable_heating_off', False) else 'DISABLED'}")
print(f"  Cooling On: {'ENABLED' if temp_notif.get('enable_cooling_on', False) else 'DISABLED'}")
print(f"  Cooling Off: {'ENABLED' if temp_notif.get('enable_cooling_off', False) else 'DISABLED'}")
print()

# Check batch notifications
print("Batch Notifications:")
batch_notif = system_cfg.get('batch_notifications', {})
print(f"  Loss of Signal: {'ENABLED' if batch_notif.get('enable_loss_of_signal', True) else 'DISABLED'}")
print(f"    Timeout: {batch_notif.get('loss_of_signal_timeout_minutes', 30)} minutes")
print(f"  Fermentation Starting: {'ENABLED' if batch_notif.get('enable_fermentation_starting', True) else 'DISABLED'}")
print(f"  Daily Report: {'ENABLED' if batch_notif.get('enable_daily_report', True) else 'DISABLED'}")
print(f"    Report Time: {batch_notif.get('daily_report_time', '09:00')}")
print()

# Configuration validation
print("=" * 80)
print("CONFIGURATION VALIDATION")
print("=" * 80)
print()

errors = []
warnings = []

if warning_mode == 'NONE':
    warnings.append("Notifications are globally disabled")
elif warning_mode in ['EMAIL', 'BOTH']:
    if not system_cfg.get('sending_email'):
        errors.append("Sending email address not configured")
    if not system_cfg.get('email'):
        errors.append("Recipient email address not configured")
    if not system_cfg.get('smtp_password'):
        warnings.append("SMTP password not set - email sending may fail")
    if not system_cfg.get('smtp_host'):
        errors.append("SMTP host not configured")

if warning_mode in ['SMS', 'BOTH']:
    if not system_cfg.get('mobile'):
        errors.append("Mobile number not configured")
    if not system_cfg.get('sms_gateway_domain'):
        errors.append("SMS gateway domain not configured")

if errors:
    print("❌ ERRORS:")
    for err in errors:
        print(f"   - {err}")
    print()

if warnings:
    print("⚠️  WARNINGS:")
    for warn in warnings:
        print(f"   - {warn}")
    print()

if not errors:
    print("✅ Configuration is valid")
    if warning_mode != 'NONE':
        print()
        print("The system is ready to send notifications!")
        print()
        print("Example notification messages that would be sent:")
        print()
        print("1. Temperature Below Low Limit:")
        print(f"   Subject: {system_cfg.get('brewery_name', 'Brewery')} - Temperature Control Alert")
        print(f"   Body: Brewery Name: {system_cfg.get('brewery_name', 'Brewery')}")
        print(f"         Date: {datetime.utcnow().strftime('%Y-%m-%d')}")
        print(f"         Time: {datetime.utcnow().strftime('%H:%M:%S')}")
        print(f"         Tilt Color: Black")
        print(f"         Temperature Below Low Limit - Current: 65.0°F, Low Limit: 68.0°F")
        print()
        print("2. Fermentation Starting:")
        print(f"   Subject: {system_cfg.get('brewery_name', 'Brewery')} - Fermentation Started")
        print(f"   Body: Brewery Name: {system_cfg.get('brewery_name', 'Brewery')}")
        print(f"         Tilt Color: Black")
        print(f"         Brew Name: My IPA")
        print(f"         Date/Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"         Fermentation has started.")
        print(f"         Gravity at start: 1.050")
        print(f"         Gravity now: 1.038")
        print()
        print("3. Daily Report:")
        print(f"   Subject: {system_cfg.get('brewery_name', 'Brewery')} - Daily Report")
        print(f"   Body: Brewery Name: {system_cfg.get('brewery_name', 'Brewery')}")
        print(f"         Tilt Color: Black")
        print(f"         Brew Name: My IPA")
        print(f"         Date/Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"         Starting Gravity: 1.050")
        print(f"         Last Gravity: 1.015")
        print(f"         Net Change: 0.035")
        print(f"         Change since yesterday: 0.003")
else:
    print()
    print("Please fix the errors above before notifications can be sent.")
    print()
    sys.exit(1)

print()
print("=" * 80)
