# Notification System Troubleshooting Guide

## Issue 1: Email Notifications Sent Every 5 Minutes (FIXED)

### Problem
Notifications were being sent repeatedly every 5 minutes instead of once per condition. For example, when temperature dropped below the low limit, an email would be sent, then another 5 minutes later, and so on, even though the temperature hadn't moved back into range.

### Root Cause
The `periodic_temp_control()` function reloads the temperature control configuration from disk every loop iteration (every 1-5 minutes depending on `update_interval` setting). This reload was overwriting the runtime trigger flags (`below_limit_trigger_armed`, `above_limit_trigger_armed`, `in_range_trigger_armed`) with the values from the config file.

**The flow that caused the bug:**
1. Temperature drops below low limit
2. Notification is queued and sent
3. Trigger flag `below_limit_trigger_armed` is set to `False` in memory (correct!)
4. Next iteration of `periodic_temp_control()` runs
5. Config is reloaded from disk: `temp_cfg.update(file_cfg)`
6. The config file on disk still has `below_limit_trigger_armed: true`
7. In-memory flag is overwritten back to `True`
8. Notification is sent again!

### Solution
Modified `app.py` function `periodic_temp_control()` (lines 3135-3147) to:
1. Save trigger flag states before reloading config
2. Reload config from disk (to pick up user changes to limits, etc.)
3. Restore the saved trigger flag states after reload

This ensures that:
- User configuration changes (like low_limit, high_limit) are picked up from the config file
- Runtime trigger states are preserved and not reset
- Notifications are only sent once per condition
- Triggers only reset when temperature crosses back into range

### Verification
Created test `test_notification_trigger_fix.py` that demonstrates:
- The old buggy behavior (triggers reset on config reload)
- The new fixed behavior (triggers preserved on config reload)
- Test passes, confirming the fix works correctly

---

## Issue 2: Push Notifications Not Working

### Current Status
The code for push notifications appears to be correct. The issue is most likely a **configuration problem** rather than a code bug.

### How Push Notifications Work

1. **System Config**: Set `warning_mode` to `PUSH` or `BOTH`
2. **Provider Selection**: Choose between Pushover (paid) or ntfy (free)
3. **Credentials**: Configure provider-specific credentials
4. **Event Enablement**: Enable specific notification types in System Config
5. **Trigger**: When an event occurs and trigger is armed
6. **Queueing**: Notification is queued with 10-second delay for deduplication
7. **Processing**: Every 5 minutes, `process_pending_notifications()` runs
8. **Sending**: After 10+ seconds in queue, `attempt_send_notifications()` is called
9. **Routing**: Based on `warning_mode`, calls `send_push()` function
10. **Delivery**: Provider-specific function sends the push notification

### Common Reasons Push Doesn't Work

#### 1. Warning Mode Not Set
**Problem**: `warning_mode` is set to `EMAIL` or `NONE` instead of `PUSH` or `BOTH`

**Solution**:
1. Go to System Config → Notifications tab
2. Set "Warning Mode" to either:
   - `PUSH` (push notifications only)
   - `BOTH` (both email and push notifications)
3. Save settings

#### 2. Push Provider Not Configured
**Problem**: No push provider selected or credentials not entered

**For Pushover (paid service, $5 one-time per platform):**
1. Sign up at https://pushover.net
2. Get your User Key from your account
3. Create an application to get an API Token
4. In System Config:
   - Set "Push Provider" to `pushover`
   - Enter "Pushover User Key"
   - Enter "Pushover API Token"
   - Optionally enter device name in "Pushover Device"
5. Save settings

**For ntfy (free, open-source):**
1. Choose a unique topic name (e.g., `my-brewery-alerts-abc123`)
2. In System Config:
   - Set "Push Provider" to `ntfy`
   - Enter your topic in "ntfy Topic"
   - Optionally change "ntfy Server" (defaults to https://ntfy.sh)
   - Optionally enter "ntfy Auth Token" if using authentication
3. Save settings
4. Install ntfy app on your phone and subscribe to your topic

#### 3. Notification Type Disabled
**Problem**: The specific notification type is disabled in settings

**Solution**:
1. Go to System Config → Notifications tab
2. Check "Temperature Control Notifications" section
3. Ensure the notification types you want are enabled:
   - ✅ Enable Temperature Below Low Limit
   - ✅ Enable Temperature Above High Limit
   - ✅ Enable Heating On/Off (optional)
   - ✅ Enable Cooling On/Off (optional)
   - ✅ Enable Kasa Error (optional)
4. Save settings

#### 4. Password Field Behavior
**Problem**: Push API tokens are treated as password fields for security

**Explanation**: When you save system config, password fields (like `pushover_api_token` and `ntfy_auth_token`) are only updated if you provide a value in the form. If you leave them blank and save, the existing values are preserved.

**This can cause issues if:**
- You configure other settings BEFORE entering the API token
- The token field is empty when you save
- An empty value gets saved to the config file

**Solution**:
1. Always enter push credentials BEFORE saving any config
2. If you need to change other settings later:
   - Re-enter the API token in the form (even though it shows as dots/asterisks)
   - Then save
3. Or verify the config file has your credentials:
   - Check `config/system_config.json`
   - Look for `pushover_api_token` or `ntfy_auth_token`
   - Should not be empty string `""`

#### 5. Trigger Already Fired
**Problem**: Notification already sent for current condition

**Explanation**: Triggers are armed/disarmed to prevent duplicate notifications:
- When temp drops below low limit, notification sent, trigger disarmed
- Trigger re-arms only when temp crosses back into range
- If you're testing and temp is already out of range, trigger might be disarmed

**Solution**:
1. Move temperature back into range (between low and high limits)
2. Wait for trigger to re-arm
3. Move temperature out of range again
4. Notification should be sent

#### 6. Waiting for Queue Processing
**Problem**: Notification is queued but hasn't been processed yet

**Explanation**:
- Notifications have a 10-second delay for deduplication
- Queue is processed every 5 minutes by `process_pending_notifications()`
- So a notification might take up to 5 minutes to send

**Solution**: Wait at least 5 minutes after triggering condition before concluding push isn't working

### Debugging Push Notifications

#### Check the Logs
Look for these messages in the console/logs:

**Success messages:**
```
[LOG] Pushover push notification sent successfully
[LOG] ntfy push notification sent successfully
[LOG] Pending notification sent successfully for temp_below_low_limit/Black
```

**Error messages:**
```
[LOG] Push notification failed: <error message>
[LOG] Pushover returned status <code>: <message>
[LOG] ntfy returned status <code>: <message>
[LOG] Pushover User Key and API Token must be configured
[LOG] ntfy Topic must be configured
```

#### Test Push Notification
1. Go to System Config → Notifications tab
2. Click "Send Test Push Notification" button
3. Check your phone/device for the test message
4. If test works, issue is with event triggering or settings
5. If test fails, check credentials and error messages

#### Verify Configuration
Check `config/system_config.json` (note: example below uses comments for clarity, but actual JSON cannot contain comments):
```
{
  "warning_mode": "PUSH",
  "push_provider": "pushover",
  "pushover_user_key": "u1234567890abcdef...",
  "pushover_api_token": "a1234567890abcdef...",
  
  For ntfy instead of Pushover:
  "ntfy_topic": "my-unique-topic",
  "ntfy_server": "https://ntfy.sh"
}
```

Key things to verify:
- `warning_mode` is `"PUSH"` or `"BOTH"` (not `"EMAIL"` or `"NONE"`)
- `push_provider` is `"pushover"` or `"ntfy"`
- For Pushover: both `pushover_user_key` and `pushover_api_token` should have values (not empty `""`)
- For ntfy: `ntfy_topic` should have a value (not empty `""`)

### Still Not Working?

If push notifications still don't work after checking all of the above:

1. **Check network connectivity**: Ensure the Raspberry Pi can reach the push service
   ```bash
   # For Pushover (replace YOUR_TOKEN and YOUR_USER with actual values):
   curl -X POST https://api.pushover.net/1/messages.json -d "token=YOUR_TOKEN&user=YOUR_USER&message=test"
   
   # For ntfy (replace YOUR_TOPIC with your actual topic):
   curl -X POST https://ntfy.sh/YOUR_TOPIC -d "test message"
   ```
   
   ⚠️ **Security Note**: Command-line arguments (including credentials) may be visible in process lists and shell history. For production use, consider storing credentials in environment variables or using the web UI's test button instead.

2. **Check Python requests library**: 
   ```bash
   python3 -c "import requests; print('OK')"
   ```
   If error, install: `pip3 install requests`

3. **Check for firewall/proxy issues**: Ensure outbound HTTPS is allowed

4. **Enable debug logging**: Look for detailed error messages in console output

5. **File an issue**: If all else fails, create a GitHub issue with:
   - Your `warning_mode` setting
   - Your `push_provider` setting
   - Whether test notification works
   - Any error messages from logs
   - Whether email notifications work (to rule out general notification issues)

---

## Summary of Fixes

### ✅ Fixed: Email Notifications Sent Too Frequently
- **What was fixed**: Trigger flags now preserved across config reloads
- **Impact**: Notifications will only be sent once per condition
- **Files modified**: `app.py` (lines 3135-3147)
- **Test created**: `test_notification_trigger_fix.py`

### ⚠️ Investigated: Push Notifications Not Working
- **Finding**: Code appears correct; most likely a configuration issue
- **What to check**: 
  1. `warning_mode` set to `PUSH` or `BOTH`
  2. Push credentials configured
  3. Notification types enabled
  4. Trigger not already fired
- **Documentation**: This troubleshooting guide
- **Test created**: `test_push_notification_flow.py` (flow analysis)

---

## For Developers

### Code Changes Made
- `app.py` lines 3135-3147: Added trigger flag preservation logic
- `test_notification_trigger_fix.py`: Verification test for trigger preservation
- `test_push_notification_flow.py`: Analysis tool for push notification flow

### Testing
```bash
# Test trigger preservation fix
python3 test_notification_trigger_fix.py

# Analyze push notification flow
python3 test_push_notification_flow.py
```

### Future Improvements
1. Add a "Test Push Notification" button in the UI (similar to email test)
2. Show push notification status/errors in the UI
3. Add more detailed logging for push notification attempts
4. Consider storing trigger flags separately from configuration (to avoid confusion)
