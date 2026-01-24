# Fermenter Temperature Controller - Notifications Guide

This comprehensive guide explains how to configure email and push notifications for your fermenter temperature controller.

## 📱 Overview

The Fermenter Temperature Controller sends real-time notifications to keep you informed about your fermentation batches. The notification system supports:

- **Email notifications** via SMTP (Gmail, Outlook, Yahoo, etc.)
- **Push notifications** via Pushover or ntfy
- **Flexible routing** - Email only, Push only, or Both

### Notification Categories

1. **Temperature Control Notifications**
   - Temperature below low limit
   - Temperature above high limit  
   - Heating device turned on/off
   - Cooling device turned on/off
   - Temperature control started/stopped
   - Control mode changed

2. **Batch Notifications**
   - Loss of Tilt signal
   - Fermentation starting (activity detected)
   - Fermentation completion detected
   - Fermentation finished
   - Daily progress reports

Each notification type can be individually enabled or disabled in the web interface.

---

## 🚫 Why Push Notifications Instead of SMS?

**SMS email gateways were discontinued by major carriers in 2024-2025**, making traditional SMS notifications unreliable or impossible. Push notifications are the modern replacement with significant advantages:

### Problems with SMS
- ❌ **Discontinued service** - AT&T, T-Mobile, and Verizon shut down email-to-SMS gateways
- ❌ **Unreliable delivery** - Messages often delayed or never delivered
- ❌ **Limited functionality** - Plain text only, no rich features
- ❌ **Privacy concerns** - Requires sharing phone numbers
- ❌ **Carrier dependent** - Different gateways for each carrier

### Advantages of Push Notifications
- ✅ **Highly reliable** - Direct delivery to your devices
- ✅ **Cost-effective** - Free (ntfy) or $5 one-time (Pushover)
- ✅ **Rich features** - Images, priorities, action buttons, sounds
- ✅ **Cross-platform** - Works on iOS, Android, Desktop, Web
- ✅ **Privacy-friendly** - No phone number required
- ✅ **Instant delivery** - Near real-time notifications
- ✅ **Internet-based** - Works anywhere with data/WiFi

---

## 📊 Pushover vs ntfy Comparison

| Feature | Pushover | ntfy |
|---------|----------|------|
| **Cost** | $5 one-time per platform | 100% FREE |
| **Reliability** | Extremely high (99.9%+) | Very high |
| **Setup Difficulty** | Easy | Very easy |
| **iOS App** | ✅ Official app | ✅ Official app |
| **Android App** | ✅ Official app | ✅ Official app |
| **Desktop/Web** | ✅ Via browser | ✅ Via browser or app |
| **Self-hosting** | ❌ Cloud only | ✅ Can self-host |
| **Privacy** | Good (US company) | Excellent (open-source, self-hostable) |
| **Message History** | 7 days (free), 1 year (paid) | 12 hours (public server), unlimited (self-hosted) |
| **Priority Levels** | 5 levels | 5 levels |
| **Custom Sounds** | ✅ Extensive library | ✅ Custom sounds |
| **Delivery Confirmation** | ✅ Yes | ✅ Yes |
| **API Rate Limits** | 10,000 messages/month | Unlimited (public server has soft limits) |
| **Max Message Length** | 1024 characters | 4096 characters |
| **Attachments** | Images up to 2.5 MB | Images/files (any size on self-hosted) |
| **Commercial Support** | ✅ Paid support available | ❌ Community only |

### 🏆 Recommendation

- **Choose Pushover if:** You want the most reliable, polished experience and don't mind paying $5 once per platform (iOS, Android, Desktop)
- **Choose ntfy if:** You want a completely free, open-source solution or need self-hosting for privacy

Both work excellently for homebrewing notifications. Pushover is slightly more polished, while ntfy offers more flexibility and zero cost.

---

## 🔧 Setup Instructions

### Option 1: Pushover Setup (Recommended - $5 One-Time)

Pushover is the easiest and most reliable option for most users.

#### Step 1: Create Pushover Account

1. Visit [pushover.net](https://pushover.net) and sign up for a free account
2. The account includes a **30-day free trial** to test the service
3. After the trial, purchase the app for $5 (one-time payment per platform)
   - iOS: Purchase once in App Store
   - Android: Purchase once in Google Play Store
   - Desktop: Free browser-based client

#### Step 2: Install Pushover App

1. **iOS:** Download "Pushover Notifications" from the App Store
2. **Android:** Download "Pushover" from Google Play Store
3. **Desktop:** Use the web interface at [pushover.net](https://pushover.net)
4. Log in with your Pushover account

#### Step 3: Get Your User Key

1. Log in to [pushover.net](https://pushover.net)
2. Your **User Key** is displayed on the home page after login
3. It's a 30-character alphanumeric string (e.g., `uQiRzpo4DXghDmr9QzzfQu27cmVRsG`)
4. **Copy this key** - you'll need it for configuration

#### Step 4: Create an Application

1. Go to [pushover.net/apps/build](https://pushover.net/apps/build)
2. Click **Create an Application/API Token**
3. Fill in the application details:
   - **Name:** `Fermenter Controller` (or any name you prefer)
   - **Type:** Application
   - **Description:** `Fermentation monitoring notifications` (optional)
   - **URL:** Leave blank (optional)
   - **Icon:** Upload a beer/fermentation icon (optional)
4. Click **Create Application**
5. Your **API Token/Key** will be displayed (e.g., `azGDORePK8gMaC0QOYAMyEEuzJnyUi`)
6. **Copy this token** - you'll need it for configuration

#### Step 5: Configure in Fermenter Controller

1. Open your Fermenter Controller web interface (`http://<raspberry-pi-ip>:5000`)
2. Navigate to **System Settings**
3. Scroll to the **Notification Settings** section
4. Select **Pushover ($5 one-time - Recommended)** from the **Push Provider** dropdown
5. Enter your credentials:
   - **Pushover User Key:** Paste your 30-character user key
   - **Pushover API Token:** Paste your API token from the app you created
   - **Device Name:** (Optional) Leave blank to send to all your devices, or enter a specific device name
6. Set **Messaging Options** to:
   - `PUSH` - Push notifications only
   - `BOTH` - Email and push notifications
7. Click **Save Settings**

#### Step 6: Test Notifications

1. In System Settings, scroll to **Test Notifications**
2. Click **Send Test Email/Push Notification**
3. You should receive a test notification on your device within seconds
4. If it doesn't work, check:
   - User Key and API Token are correct (no extra spaces)
   - Your device has internet connectivity
   - The Pushover app is installed and logged in

---

### Option 2: ntfy Setup (Free and Open-Source)

ntfy is a completely free, open-source alternative that's perfect for privacy-conscious users or those who don't want to pay.

#### Step 1: Install ntfy App

1. **iOS:** Download "ntfy" from the App Store (free)
2. **Android:** Download "ntfy" from Google Play Store or F-Droid (free)
3. **Desktop:** Use web interface at [ntfy.sh](https://ntfy.sh) or install desktop app

#### Step 2: Choose a Unique Topic Name

ntfy uses "topics" to route notifications. You need to choose a unique topic name.

**Important:** Topics on the public server (ntfy.sh) are public by default. Anyone who knows your topic name can subscribe to it. Choose something unique and hard to guess.

**Topic name suggestions:**
- `fermentor_john_smith_2025_unique_xyz123` (long and random)
- `beerlab_secretcode_abc789def456` (include random characters)
- `homebrewing_monitor_[yourname]_[random]` (personalized)

**Topic name rules:**
- Letters, numbers, underscores, and hyphens only
- No spaces
- Case-sensitive
- Should be hard to guess for privacy

#### Step 3: Subscribe to Your Topic in the App

1. Open the ntfy app on your phone
2. Tap the **+** button to add a new subscription
3. **Using ntfy.sh (free public server):**
   - Server: `https://ntfy.sh` (default)
   - Topic: Enter your unique topic name (e.g., `my_fermenter_notifications_xyz789`)
   - Display name: `Fermenter` (or any name you like)
4. **Using self-hosted server (advanced):**
   - Server: Your self-hosted ntfy server URL (e.g., `https://ntfy.yourdomain.com`)
   - Topic: Your topic name
   - Auth: If required, enable authentication and enter username/password
5. Tap **Subscribe**

#### Step 4: Configure in Fermenter Controller

1. Open your Fermenter Controller web interface
2. Navigate to **System Settings**
3. Scroll to the **Notification Settings** section
4. Select **ntfy (100% FREE - Open Source)** from the **Push Provider** dropdown
5. Enter your configuration:
   - **ntfy Server URL:** `https://ntfy.sh` (or your self-hosted server)
   - **ntfy Topic:** Your unique topic name (must match what you subscribed to in the app)
   - **Auth Token:** Leave blank for public server (or enter token for self-hosted with auth)
6. Set **Messaging Options** to:
   - `PUSH` - Push notifications only
   - `BOTH` - Email and push notifications
7. Click **Save Settings**

#### Step 5: Test Notifications

1. In System Settings, scroll to **Test Notifications**
2. Click **Send Test Email/Push Notification**
3. You should receive a test notification within seconds
4. If it doesn't work, check:
   - Topic name in the app matches exactly (case-sensitive)
   - Server URL is correct
   - Your device has internet connectivity
   - You're subscribed to the correct topic in the ntfy app

#### Step 6: Optional - Self-Host ntfy for Privacy

For maximum privacy, you can host your own ntfy server:

1. **Install ntfy server** on any Linux server or Raspberry Pi:
   ```bash
   # Using Docker (easiest)
   docker run -p 80:80 -v /var/cache/ntfy:/var/cache/ntfy binwiederhier/ntfy serve
   
   # Or install natively (Debian/Ubuntu)
   curl -sSL https://archive.heckel.io/apt/pubkey.txt | sudo apt-key add -
   sudo apt install ntfy
   sudo systemctl enable ntfy
   sudo systemctl start ntfy
   ```

2. **Configure authentication** (recommended for self-hosted):
   - Edit `/etc/ntfy/server.yml`
   - Enable auth and create user accounts
   - Restart ntfy server

3. **Use your server** in the Fermenter Controller:
   - ntfy Server URL: `http://your-server-ip` or `https://your-domain.com`
   - ntfy Topic: Any topic name (private to your server)
   - Auth Token: If auth is enabled, generate a token in ntfy web UI

See [ntfy.sh documentation](https://docs.ntfy.sh) for detailed self-hosting instructions.

---

## 📧 Email Configuration (Optional)

Email notifications work alongside or instead of push notifications. Most users configure **both** for redundancy.

### Supported Email Providers

The system works with any SMTP email service:
- Gmail (most common)
- Outlook / Hotmail
- Yahoo Mail
- iCloud Mail
- Zoho Mail
- Custom SMTP servers

### Gmail Setup (Recommended)

Gmail is the most common and reliable option. **You must use an App Password** - your regular Gmail password won't work.

#### Step 1: Enable 2-Factor Authentication

App Passwords require 2FA to be enabled on your Google account.

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Under "Signing in to Google", click **2-Step Verification**
4. Follow the prompts to enable 2FA (using your phone)

#### Step 2: Generate an App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - If you don't see this option, make sure 2FA is enabled
2. You may need to sign in again
3. Under "Select app", choose **Mail**
4. Under "Select device", choose **Other (Custom name)**
5. Enter a name: `Fermenter Controller`
6. Click **Generate**
7. Google will display a 16-character app password (e.g., `abcd efgh ijkl mnop`)
8. **Copy this password** - you won't be able to see it again
9. Remove the spaces when entering it: `abcdefghijklmnop`

#### Step 3: Configure in Fermenter Controller

1. Open Fermenter Controller web interface
2. Navigate to **System Settings**
3. Scroll to **Email Settings** section
4. Configure the following:
   - **Recipient Email:** Your email address (where you want to receive notifications)
   - **Sending Email (From):** Your Gmail address (e.g., `yourname@gmail.com`)
   - **Sending Email Password:** Your 16-character app password (no spaces)
   - **SMTP Server Host:** `smtp.gmail.com` (auto-filled)
   - **SMTP Server Port:** `587` (auto-filled)
   - **Use STARTTLS:** ✅ Keep checked
5. Set **Messaging Options:**
   - `EMAIL` - Email only
   - `BOTH` - Email and push notifications
6. Click **Save Settings**

#### Step 4: Test Email

1. In System Settings, scroll to **Test Notifications**
2. Click **Send Test Email/Push Notification**
3. Check your email inbox (and spam folder)
4. If email doesn't arrive, verify:
   - App password is correct (16 characters, no spaces)
   - 2FA is enabled on your Google account
   - SMTP settings are correct (host: `smtp.gmail.com`, port: `587`)
   - STARTTLS is enabled

### Other Email Providers

#### Outlook / Hotmail Setup

1. Generate an app password at [account.microsoft.com/security](https://account.microsoft.com/security)
2. Configure SMTP settings:
   - SMTP Host: `smtp-mail.outlook.com`
   - SMTP Port: `587`
   - STARTTLS: ✅ Enabled
   - Email: Your Outlook/Hotmail address
   - Password: Your app password

#### Yahoo Mail Setup

1. Generate an app password at [login.yahoo.com/account/security](https://login.yahoo.com/account/security)
2. Configure SMTP settings:
   - SMTP Host: `smtp.mail.yahoo.com`
   - SMTP Port: `587`
   - STARTTLS: ✅ Enabled

#### iCloud Mail Setup

1. Generate an app password at [appleid.apple.com](https://appleid.apple.com) → Security → App-Specific Passwords
2. Configure SMTP settings:
   - SMTP Host: `smtp.mail.me.com`
   - SMTP Port: `587`
   - STARTTLS: ✅ Enabled

#### Custom SMTP Server

For custom email servers, configure:
- SMTP Host: Your mail server hostname
- SMTP Port: Usually 587 (STARTTLS) or 465 (SSL)
- STARTTLS: Enable if using port 587
- Username: Your email login username
- Password: Your email password

---

## ⚙️ Notification Settings Configuration

### Setting Notification Mode

Choose how you want to receive notifications:

1. Navigate to **System Settings**
2. Find **Messaging Options** dropdown
3. Select one:
   - **NONE** - Disable all notifications (logging only)
   - **EMAIL** - Email notifications only
   - **PUSH** - Push notifications only (Pushover or ntfy)
   - **BOTH** - Email AND push notifications (recommended)
4. Click **Save Settings**

### Temperature Control Notifications

Configure which temperature events trigger notifications:

1. Navigate to **Temperature Control Settings**
2. Scroll to **Temperature Control Notifications** section
3. Check/uncheck event types:
   - ✅ **Temperature Below Low Limit** - Alert when temp drops below threshold
   - ✅ **Temperature Above High Limit** - Alert when temp exceeds threshold
   - ✅ **Heating Turned On** - Alert when heating device activates
   - ✅ **Heating Turned Off** - Alert when heating device deactivates
   - ✅ **Cooling Turned On** - Alert when cooling device activates
   - ✅ **Cooling Turned Off** - Alert when cooling device deactivates
   - ✅ **Temperature Control Started** - Alert when control loop starts
   - ✅ **Temperature Control Stopped** - Alert when control loop stops
4. Click **Save Settings**

**Tip:** Most users keep all temperature control notifications enabled, as these are critical safety alerts.

### Batch Notifications

Configure which fermentation events trigger notifications:

1. Navigate to **System Settings** (or batch-specific settings)
2. Scroll to **Batch Notifications** section
3. Check/uncheck event types:
   - ✅ **Loss of Signal** - Alert when Tilt stops reporting data
   - ✅ **Fermentation Starting** - Alert when active fermentation begins
   - ✅ **Fermentation Completion** - Alert when fermentation appears complete
   - ✅ **Fermentation Finished** - Alert when batch is marked finished
   - ✅ **Daily Report** - Send daily progress summary
4. Click **Save Settings**

**Tip:** "Loss of Signal" and "Fermentation Starting" are the most important. Daily reports can be noisy for some users.

---

## 📬 Example Notification Messages

### Temperature Control Notifications

#### Temperature Out of Range
**Subject:** `Temp Below Low Limit Notification`  
**Message:**
```
Tilt: Purple
Temperature has dropped below the low limit.
Current temp: 64.2°F
Low limit: 66.0°F
High limit: 70.0°F
```

#### Heating/Cooling Events
**Subject:** `Heating On Notification`  
**Message:**
```
Tilt: Purple
Heating device has been turned ON.
Current temp: 65.8°F
Target range: 66.0°F - 70.0°F
```

#### Control Mode Changed
**Subject:** `Temp Control Started Notification`  
**Message:**
```
Temperature control has been started for Purple Tilt.
Low limit: 66.0°F
High limit: 70.0°F
```

### Batch Notifications

#### Fermentation Starting
**Subject:** `Fermentation Starting Notification`  
**Message:**
```
Tilt: Purple
Fermentation activity detected!
Batch: Hazy IPA 2025-01-15
Starting gravity: 1.058
Current gravity: 1.056
Temperature: 68.2°F
```

#### Fermentation Completion
**Subject:** `Fermentation Completion Notification`  
**Message:**
```
Tilt: Purple
Fermentation appears to be complete!
Batch: Hazy IPA 2025-01-15
Final gravity: 1.012 (stable for 48 hours)
Starting gravity: 1.058
Apparent attenuation: 79.3%
```

#### Loss of Signal
**Subject:** `Loss Of Signal Notification`  
**Message:**
```
Tilt: Purple
Signal lost from Tilt hydrometer!
Last reading: 15 minutes ago
Last gravity: 1.024
Last temp: 67.8°F
Check Bluetooth connection and battery.
```

#### Daily Report
**Subject:** `Daily Report Notification`  
**Message:**
```
Tilt: Purple
Daily Fermentation Report
Batch: Hazy IPA 2025-01-15
Day 3 of fermentation

Current gravity: 1.018
Starting gravity: 1.058
Change (24h): -0.008

Temperature: 67.5°F
Apparent attenuation: 69.0%

Fermentation status: Active
```

---

## 🔍 Troubleshooting

### Push Notifications Not Working

#### Pushover Issues

**Problem:** Not receiving Pushover notifications

1. **Verify credentials:**
   - User Key is 30 characters (e.g., `uQiRzpo4DXghDmr9QzzfQu27cmVRsG`)
   - API Token is from your created application
   - No extra spaces before/after keys
   
2. **Check device:**
   - Pushover app is installed and logged in
   - Device has internet connectivity
   - If you specified a device name, make sure it matches exactly (case-sensitive)
   
3. **Test the API directly:**
   ```bash
   curl -X POST https://api.pushover.net/1/messages.json \
     -d "token=YOUR_API_TOKEN" \
     -d "user=YOUR_USER_KEY" \
     -d "message=Test from command line"
   ```
   If this works, the issue is in the Fermenter Controller configuration.

4. **Check Pushover status:**
   - Visit [pushover.net/status](https://pushover.net/status) to verify service is operational
   
5. **Review subscription:**
   - After 30-day trial, verify you purchased the app ($5)

**Problem:** Notifications delayed or inconsistent

- Pushover is highly reliable. If you experience delays:
  - Check your device's notification settings (not in Do Not Disturb mode)
  - Verify app has permission to show notifications
  - Try logging out and back in to the Pushover app

#### ntfy Issues

**Problem:** Not receiving ntfy notifications

1. **Verify topic name:**
   - Topic in app matches exactly (case-sensitive)
   - No spaces or special characters
   - Check for typos

2. **Check server URL:**
   - Public server: `https://ntfy.sh`
   - Self-hosted: Verify your server is accessible
   - Test by visiting the URL in a browser

3. **Verify subscription:**
   - Open ntfy app and check you're subscribed to the correct topic
   - Try unsubscribing and re-subscribing

4. **Test manually:**
   ```bash
   # Send test notification
   curl -X POST https://ntfy.sh/YOUR_TOPIC \
     -H "Title: Test" \
     -d "This is a test message"
   ```
   If you receive this in your app, the issue is in the Fermenter Controller.

5. **Check ntfy app settings:**
   - App has notification permissions
   - Not in battery optimization mode (Android)
   - App is not force-stopped

**Problem:** Topic is public and others might see my notifications

- Use a very long, random topic name
- Or self-host ntfy with authentication
- Never use simple topic names like `fermenter` or `beer`

### Email Notifications Not Working

**Problem:** Emails not being received

1. **Check spam folder:**
   - First place to check!
   - Mark as "Not Spam" if found there

2. **Verify Gmail app password:**
   - Must use app password, not regular Gmail password
   - 16 characters, no spaces
   - 2FA must be enabled
   - Generate new app password if unsure

3. **Check SMTP settings:**
   - Gmail: `smtp.gmail.com`, port `587`, STARTTLS enabled
   - Outlook: `smtp-mail.outlook.com`, port `587`
   - Yahoo: `smtp.mail.yahoo.com`, port `587`

4. **Test SMTP manually:**
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your-email@gmail.com', 'your-app-password')
   server.sendmail('your-email@gmail.com', 'your-email@gmail.com', 'Test message')
   server.quit()
   ```

5. **Check Fermenter Controller logs:**
   - Look for SMTP errors in `/logs/error.log`
   - Common errors: authentication failure, connection timeout

**Problem:** "App Password" option not available in Google account

- Ensure 2-Factor Authentication is enabled
- Sign out and sign back in to Google account
- Try accessing directly: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

**Problem:** SMTP authentication errors

- Regenerate app password
- Verify email address is correct
- For Gmail: Ensure "Less secure app access" is NOT required (app passwords don't need this)

### General Issues

**Problem:** Test notification fails with "requests library not installed"

```bash
pip install requests
```
Restart the Fermenter Controller application.

**Problem:** Notifications sent but not for specific events

1. Check notification settings:
   - Navigate to **System Settings** or **Temperature Control Settings**
   - Verify the specific event type is **enabled** (checkbox checked)
   
2. Verify notification mode:
   - Must be set to `EMAIL`, `PUSH`, or `BOTH` (not `NONE`)

**Problem:** Too many notifications

1. **Disable daily reports:**
   - Uncheck "Daily Report" in batch notification settings
   
2. **Disable heating/cooling cycle notifications:**
   - Uncheck "Heating On/Off" and "Cooling On/Off"
   - Keep temperature limit alerts enabled for safety
   
3. **Adjust temperature limits:**
   - Wider temperature range = fewer out-of-range alerts

**Problem:** Missing notifications for important events

- Check that event type is enabled in notification settings
- Verify correct notification mode (not `NONE`)
- Review logs to confirm events are being detected
- Test notifications to verify system is working

---

## 🎯 Best Practices

### For Reliability

1. **Configure BOTH push and email:**
   - Set messaging mode to `BOTH`
   - Redundancy ensures you never miss critical alerts
   - Push is instant, email is a reliable backup

2. **Test before brewing:**
   - Always send test notifications before starting a batch
   - Verify both push and email are working
   - Check devices have internet connectivity

3. **Monitor notification status:**
   - Dashboard shows notification errors
   - Fix issues promptly when error indicators appear

### For Privacy

1. **Use ntfy with self-hosting:**
   - Full control over your data
   - No third-party services
   - Messages stored only on your server

2. **Use long, random topic names:**
   - If using public ntfy server, make topics hard to guess
   - Example: `fermentor_john_abc789xyz456def123`

3. **Enable authentication:**
   - Self-hosted ntfy: Enable auth tokens
   - Protects your notification endpoint

### For Cost Savings

1. **Use ntfy for free notifications:**
   - Zero cost, fully functional
   - Great for hobbyists and home use

2. **Pushover family plan:**
   - One $5 purchase covers unlimited devices on same platform
   - Share with household members if desired

### For Homebrewing Workflow

1. **Enable critical alerts only:**
   - Loss of signal (Tilt battery/connection issues)
   - Temperature out of range (safety)
   - Fermentation starting (confirms activity)
   - Fermentation completion (time to package)

2. **Disable noisy alerts:**
   - Heating/cooling cycles (can be frequent)
   - Daily reports (unless you really want them)

3. **Set appropriate temperature limits:**
   - Not too tight (causes frequent alerts)
   - Not too loose (misses problems)
   - Typical: ±2-3°F from target

---

## 📚 Additional Resources

### Pushover
- Website: [pushover.net](https://pushover.net)
- API Documentation: [pushover.net/api](https://pushover.net/api)
- Support: [pushover.net/support](https://pushover.net/support)
- Status Page: [pushover.net/status](https://pushover.net/status)

### ntfy
- Website: [ntfy.sh](https://ntfy.sh)
- Documentation: [docs.ntfy.sh](https://docs.ntfy.sh)
- GitHub: [github.com/binwiederhier/ntfy](https://github.com/binwiederhier/ntfy)
- Self-Hosting Guide: [docs.ntfy.sh/install](https://docs.ntfy.sh/install)

### Gmail App Passwords
- Create App Password: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- 2FA Setup: [myaccount.google.com/security](https://myaccount.google.com/security)
- Gmail Help: [support.google.com/mail](https://support.google.com/mail)

### SMTP Settings Reference
- Gmail: `smtp.gmail.com:587` (STARTTLS)
- Outlook: `smtp-mail.outlook.com:587` (STARTTLS)
- Yahoo: `smtp.mail.yahoo.com:587` (STARTTLS)
- iCloud: `smtp.mail.me.com:587` (STARTTLS)

---

## 🆘 Getting Help

If you're still having issues after following this guide:

1. **Check the logs:**
   - `/logs/error.log` for error messages
   - Look for SMTP or push notification errors

2. **Review configuration:**
   - Double-check all settings in System Settings
   - Verify no extra spaces in keys/passwords

3. **Test components separately:**
   - Test push notifications first
   - Test email separately
   - Isolate which component is failing

4. **Create a GitHub issue:**
   - Visit the repository: [github.com/RabbitFarmer/Fermenter-Temp-Controller](https://github.com/RabbitFarmer/Fermenter-Temp-Controller)
   - Include: error messages, configuration (redact passwords!), what you've tried

---

## 📝 Summary

This notification system provides reliable, modern push notifications to keep you informed about your fermentation:

- **Choose Pushover** for maximum reliability and polish ($5 one-time)
- **Choose ntfy** for free, open-source, self-hostable notifications
- **Configure email** as a backup (Gmail with app password recommended)
- **Enable BOTH** modes for redundancy
- **Customize** which events trigger notifications
- **Test** before brewing to ensure everything works

Happy brewing! 🍺

