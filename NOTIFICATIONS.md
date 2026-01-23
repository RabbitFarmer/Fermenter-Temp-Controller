# Email and SMS Notifications Guide

This document explains how to configure and use the email and SMS notification features in the Fermenter Temperature Controller.

## Overview

The system can send notifications via email and/or SMS for two main categories:
1. **Temperature Control Messages** - Alerts when temperature goes out of range or when heating/cooling devices turn on/off
2. **Batch Messages** - Alerts for fermentation milestones like signal loss, fermentation start, and daily progress reports

## Configuration

### Step 1: Configure Email/SMS Settings

Navigate to **System Settings → SMS/eMail** tab and configure:

#### Email Configuration
- **Sending Email Address**: The email account that will send notifications (e.g., `fermentercontroller@gmail.com`)
- **Sending Email Password**: **For Gmail, use an App Password** (see Gmail Configuration Tips below), NOT your regular password
- **SMTP Server Host**: Email server address (e.g., `smtp.gmail.com` for Gmail)
- **SMTP Server Port**: Usually `587` for TLS or `465` for SSL
- **Use STARTTLS**: Check this for secure connections (recommended)
- **Recipient eMail Address**: Where notifications should be sent

#### SMS Configuration

> **⚠️ IMPORTANT NOTICE (2024-2025):** Major U.S. carriers (AT&T, Verizon, T-Mobile) have **discontinued their email-to-SMS gateway services** due to spam and security concerns. The traditional email-to-SMS method using `@txt.att.net`, `@vtext.com`, and `@tmomail.net` **no longer works** as of late 2024/mid-2025.
>
> **To receive SMS notifications, you must use a commercial SMS API service** such as:
> - [Twilio](https://www.twilio.com/) - Most popular, offers free trial credits
> - [TextP2P](https://textp2p.com/) - Simple email-to-SMS alternative
> - [SignalWire](https://signalwire.com/) - Twilio alternative with competitive pricing
> - [Notifyre](https://notifyre.com/) - Designed for business messaging
>
> These services provide email-to-SMS bridges, APIs, or webhooks that can be integrated with the Fermenter Controller. Check their documentation for integration options.
>
> **If you still see carrier gateway options below, they are kept for reference only and will not work.**

**Legacy SMS Configuration (No Longer Functional):**
- **Recipient Cell Phone Number**: Your mobile number (e.g., `8031234567`)
- **SMS Gateway Domain**: Your carrier's email-to-SMS gateway
  - ~~AT&T: `txt.att.net`~~ (Discontinued June 2025)
  - ~~T-Mobile: `tmomail.net`~~ (Discontinued late 2024)
  - ~~Verizon: `vtext.com`~~ (Discontinued late 2024)
  - ~~Sprint: `messaging.sprintpcs.com`~~ (Merged with T-Mobile, discontinued)

**Alternative:** Use **Email** mode for notifications until you set up an SMS API service.

#### Messaging Options
Select how you want to receive notifications:
- **None**: Notifications disabled
- **eMail**: Email only (recommended until SMS API is configured)
- **SMS**: SMS only (requires SMS API service, not carrier gateways)
- **Both**: Both email and SMS

### Step 2: Configure Temperature Control Notifications

In the **SMS/eMail** tab, scroll down to **Temperature Control Notifications**.

Enable the specific events you want to be notified about:
- ✅ **Temperature Below Low Limit** (Default: ON)
- ✅ **Temperature Above High Limit** (Default: ON)
- ☐ **Heating Turned On** (Default: OFF)
- ☐ **Heating Turned Off** (Default: OFF)
- ☐ **Cooling Turned On** (Default: OFF)
- ☐ **Cooling Turned Off** (Default: OFF)

**Note**: The system will NOT notify you about triggers/control modes that you haven't enabled. This gives you fine-grained control over which events generate notifications.

### Step 3: Configure Batch Notifications

Still in the **SMS/eMail** tab, configure **Batch Notifications**:

These settings apply system-wide to each active tilt:

#### Loss of Signal Alert
- ✅ **Enable**: Receive alerts when a tilt stops broadcasting (Default: ON)
- **Timeout**: Minutes before triggering alert (Default: 30 minutes)

When triggered, you'll receive:
- Brewery name, date, time
- Tilt color
- Brew name
- Caption: "Loss of Signal -- Receiving no tilt readings"

The alert will reset automatically when the signal returns.

#### Fermentation Starting Alert
- ✅ **Enable**: Receive alert when fermentation begins (Default: ON)

Triggers when the next 3 consecutive gravity readings (at your configured intervals) are at least 0.010 below the initial/starting gravity.

Message includes:
- Brewery name, date, time
- Tilt color
- Brew name
- Starting gravity and current gravity
- Caption: "Fermentation has started"

#### Daily Progress Report
- ✅ **Enable**: Receive daily fermentation progress (Default: ON)
- **Report Time**: Time to send daily report (24-hour format, e.g., `09:00`)

Each active tilt generates a separate daily report with:
- Brewery name, date, time
- Tilt color
- Brew name
- Starting gravity
- Last gravity reading
- Net change (starting - last)
- Change since yesterday (24 hours ago - last)

## Example Notification Messages

### Temperature Control Alert
```
Subject: Frank's Fermatorium - Temperature Control Alert

Brewery Name: Frank's Fermatorium
Date: 2026-01-17
Time: 14:30:00
Tilt Color: Black

Temperature Below Low Limit - Current: 65.0°F, Low Limit: 68.0°F
```

### Fermentation Starting
```
Subject: Frank's Fermatorium - Fermentation Started

Brewery Name: Frank's Fermatorium
Tilt Color: Black
Brew Name: West Coast IPA
Date/Time: 2026-01-17 14:30:00

Fermentation has started.
Gravity at start: 1.060
Gravity now: 1.048
```

### Loss of Signal
```
Subject: Frank's Fermatorium - Loss of Signal

Brewery Name: Frank's Fermatorium
Tilt Color: Black
Brew Name: West Coast IPA
Date/Time: 2026-01-17 14:30:00

Loss of Signal -- Receiving no tilt readings
```

### Daily Report
```
Subject: Frank's Fermatorium - Daily Report

Brewery Name: Frank's Fermatorium
Tilt Color: Black
Brew Name: West Coast IPA
Date/Time: 2026-01-17 09:00:00

Starting Gravity: 1.060
Last Gravity: 1.015
Net Change: 0.045
Change since yesterday: 0.003
```

## Gmail Configuration Tips

If using Gmail, you **must** use an App Password, not your regular Gmail password. Google has disabled "less secure app access" and requires App Passwords for third-party applications.

### How to Set Up Gmail App Password:

1. **Enable 2-Factor Authentication** (if not already enabled):
   - Go to https://myaccount.google.com/security
   - Click on "2-Step Verification" and follow the setup process

2. **Generate an App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - You may need to verify your identity
   - Select "Mail" and "Other (Custom name)" 
   - Enter a name like "Fermenter Controller"
   - Click "Generate"
   - Google will display a 16-character password (e.g., `abcd efgh ijkl mnop`)

3. **Use the App Password in Fermenter Controller**:
   - Copy the 16-character App Password (spaces don't matter)
   - In the Fermenter Controller SMS/Email configuration page
   - Enter your Gmail address (e.g., `yourname@gmail.com`) in "Fermenter Email Account Address"
   - Enter the App Password in "Fermenter Email Password" field
   - **Important**: Use the App Password, NOT your regular Gmail password

4. **SMTP Settings for Gmail**:
   - Host: `smtp.gmail.com`
   - Port: `587`
   - STARTTLS: Enabled (checked)

### Common Gmail Errors:

**Error: "Username and Password not accepted" or "BadCredentials"**
- This means you're using your regular Gmail password instead of an App Password
- Solution: Generate and use an App Password as described above

**Error: "Please log in via your web browser"**
- Gmail detected unusual activity or you haven't enabled 2FA
- Solution: Enable 2-Factor Authentication and generate an App Password

## Troubleshooting

### Not Receiving Notifications

1. **Check Warning Mode**: Ensure it's set to EMAIL, SMS, or BOTH (not NONE)
2. **Verify Email Settings**: Test by setting up a brew and triggering a temperature alert
3. **Check SMTP Credentials**: Ensure password is correct
4. **Review Logs**: Check the console output for "[LOG] SMTP send failed" messages
5. **Rate Limiting**: Notifications are rate-limited to prevent spam (default: 1 hour between similar notifications)

### SMS Not Working

**⚠️ CRITICAL: Email-to-SMS Gateways Are Discontinued (2024-2025)**

If you're trying to use traditional carrier gateways like `@txt.att.net`, `@vtext.com`, or `@tmomail.net`, **these will not work**. Major U.S. carriers discontinued these services:
- **AT&T** (`txt.att.net`, `mms.att.net`) - Shut down June 17, 2025
- **Verizon** (`vtext.com`, `vzwpix.com`) - Discontinued late 2024
- **T-Mobile** (`tmomail.net`) - Discontinued late 2024
- **Sprint** (`messaging.sprintpcs.com`) - Merged with T-Mobile, discontinued

**Solutions:**

1. **Switch to Email notifications** (recommended immediate fix):
   - Set Warning Mode to "Email" instead of "SMS" or "Both"
   - Email notifications work reliably and contain full details

2. **Use a commercial SMS API service** (for true SMS):
   - [Twilio](https://www.twilio.com/) - Industry standard, free trial available
   - [TextP2P](https://textp2p.com/) - Email-to-SMS replacement service
   - [SignalWire](https://signalwire.com/) - Twilio alternative
   - [Notifyre](https://notifyre.com/) - Business messaging platform
   
   These services typically offer:
   - Email-to-SMS bridges (use their custom email gateway addresses)
   - APIs for direct integration (requires code changes)
   - Webhook endpoints for notifications

3. **For legacy/custom gateways only:**
   - If you have access to a private/corporate SMS gateway, verify:
     - Gateway domain is configured correctly
     - Mobile number format is digits only (no dashes or spaces)
     - Gateway accepts email-based messages
     - Test email notifications work first

### Fermentation Starting Not Triggering

1. **Verify Actual OG**: Must be set in batch settings
2. **Check Tilt Logging Interval**: Readings must be frequent enough to detect the drop
3. **Gravity Threshold**: Needs 3 consecutive readings ≥0.010 below starting gravity

## Testing Your Configuration

Run the included test script to verify your configuration:

```bash
python3 test_notifications.py
```

This will show your current settings and any configuration issues.

## Security Notes

- Email passwords are stored in `system_config.json` - protect this file
- Use app-specific passwords when possible (Gmail, Yahoo, etc.)
- Keep your system updated and secure
