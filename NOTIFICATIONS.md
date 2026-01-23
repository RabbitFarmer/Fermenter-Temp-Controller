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

> **📱 Two SMS Options Available**
>
> Major U.S. carriers discontinued their free email-to-SMS gateways in 2024-2025. 
> You now have **two options** for SMS notifications:
>
> 1. **Android SMS Gateway (FREE!)** - Perfect for homebrewers
> 2. **Twilio API (Paid)** - Professional SMS service

##### Option 1: Android SMS Gateway (100% FREE!) ⭐ Recommended for Hobbyists

**Why Android SMS Gateway?**
- **Zero cost** - Uses your phone's existing SMS plan
- **No signup required** - No accounts, no credit cards
- **Privacy** - Messages stay on your network
- **Perfect for hobbyists** - Ideal for homebrewing use

**Setup Steps:**

1. **Find an old Android phone** (Android 5.0 or newer):
   - Dust off that old phone sitting in a drawer
   - Needs WiFi connectivity
   - Doesn't need a data plan (just SMS)

2. **Install SMS Gateway app**:
   - Open Google Play Store
   - Search for "SMS Gateway" (popular apps: "SMS Gateway", "WaSMS", "SMS Gateway API")
   - Install and open the app

3. **Start the gateway service**:
   - Open the app
   - Click "Start Service" or similar
   - Note the URL displayed (e.g., `http://192.168.1.100:8080`)
   - Keep the app running (can run in background)

4. **Configure in Fermenter Controller**:
   - Navigate to **System Settings → SMS/eMail** tab
   - **SMS Provider**: Select "Android SMS Gateway (FREE)"
   - **Recipient Cell Phone Number**: Your mobile number (e.g., `5551234567`)
   - **Android Gateway URL**: The URL from the app (e.g., `http://192.168.1.100:8080/api/send`)
   - **API Key**: Leave blank unless your app requires one
   - Click **Save**

5. **Test it**:
   - Click the **Test SMS** button
   - You should receive a test message within seconds

**Tips:**
- Keep the Android phone plugged in and connected to WiFi
- The phone should be on the same network as your Raspberry Pi (or configure port forwarding)
- Most apps have a web interface to monitor messages sent

##### Option 2: Twilio API (Professional Service)

**Why Twilio?**
- Industry-standard, reliable SMS delivery
- Free trial includes $15 credit (~2000 SMS messages)
- Pay-as-you-go: ~$0.0075 per SMS after trial
- Works anywhere, no local device needed

**Setup Steps:**

1. **Sign up for Twilio** (free trial available):
   - Visit [twilio.com/try-twilio](https://www.twilio.com/try-twilio)
   - Create a free account (no credit card required for trial)

2. **Get a Twilio phone number**:
   - Navigate to Console → Phone Numbers → Buy a Number
   - Choose any available number ($1/month)
   - This is the "From" number for your SMS messages

3. **Get your API credentials**:
   - Go to Console Dashboard
   - Copy your **Account SID** (starts with "AC...")
   - Copy your **Auth Token** (click to reveal)

4. **Configure in Fermenter Controller**:
   - Navigate to **System Settings → SMS/eMail** tab
   - **SMS Provider**: Select "Twilio (Paid - Reliable)"
   - **Recipient Cell Phone Number**: Your mobile number (e.g., `+15551234567` or `5551234567`)
   - **Twilio Account SID**: Paste your Account SID
   - **Twilio Auth Token**: Paste your Auth Token
   - **Twilio From Number**: Your Twilio phone number (e.g., `+15551234567`)
   - Click **Save**

5. **Test it**:
   - Click the **Test SMS** button
   - You should receive a test message within seconds

**Trial Account Notes:**
- Trial accounts can send to verified phone numbers only
- To send to any number, upgrade your account (still pay-as-you-go, no monthly fee)
- Verify additional phone numbers at: Console → Phone Numbers → Verified Caller IDs

#### Messaging Options
Select how you want to receive notifications:
- **None**: Notifications disabled
- **eMail**: Email only
- **SMS**: SMS only (requires Android Gateway or Twilio)
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

**Which SMS provider are you using?**

#### Using Android SMS Gateway (Free):

1. **Check Android phone**:
   - Is the phone powered on and connected to WiFi?
   - Is the SMS Gateway app running?
   - Can you see the gateway URL in the app?

2. **Check network connectivity**:
   - Is the Raspberry Pi on the same network as the Android phone?
   - Can you ping the phone's IP from the Pi? `ping 192.168.1.100`
   - Try opening the gateway URL in a browser from the Pi

3. **Check gateway URL**:
   - Verify the URL format matches the app's requirements
   - Common formats: `http://IP:PORT/api/send` or `http://IP:PORT/send`
   - Some apps use different endpoints - check the app's documentation

4. **Test directly**:
   - Most apps have a web interface - try sending a test SMS from there
   - If that works, the issue is in the Fermenter Controller configuration

5. **Check API key**:
   - If the app requires an API key, make sure it's entered correctly
   - Try without an API key first if the app allows it

#### Using Twilio (Paid):

1. **Check Twilio Configuration**:
   - Verify Account SID and Auth Token are correct
   - Ensure From Number matches your Twilio phone number (include +1)
   - Ensure Recipient Number is in correct format (+15551234567)

2. **Trial Account Limitations**:
   - Trial accounts can only send to verified phone numbers
   - Verify your number at: Twilio Console → Phone Numbers → Verified Caller IDs
   - Or upgrade to paid account (still pay-as-you-go, no monthly fee)

3. **Check Twilio Console**:
   - Log into [twilio.com/console](https://www.twilio.com/console)
   - Check "Monitor → Logs → Messaging" for delivery status
   - Look for error messages or failed deliveries

4. **Common Twilio Errors**:
   - "Unable to create record: Account not authorized" → Need to verify recipient number or upgrade account
   - "Invalid 'To' phone number" → Phone number format is wrong (needs +1 for US)
   - "Authentication Error" → Check Account SID and Auth Token are correct

5. **Test in Twilio Console First**:
   - Go to Console → Messaging → Try it Out
   - Send a test SMS directly from Twilio to confirm your setup works
   - Then try the Fermenter Controller Test SMS button

**Still Having Issues?**
- Check the console output for "[LOG] SMS..." messages
- Try Email mode instead while troubleshooting
- For Android Gateway: Ensure `requests` library is installed (`pip install requests`)
- For Twilio: Ensure `twilio` library is installed (`pip install twilio`)

**What about carrier email-to-SMS gateways?**
- Carrier gateways (AT&T, Verizon, T-Mobile) were **permanently discontinued** in 2024-2025
- They will not work and cannot be restored
- You must use Android SMS Gateway (free) or Twilio, or switch to Email notifications

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
