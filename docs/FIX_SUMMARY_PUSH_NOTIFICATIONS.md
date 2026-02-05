# Fix Summary: PUSH Notification Configuration Bug

## Problem
Users reported that PUSH notifications were not being received after setting them up.

## Root Cause
When saving system settings through the web UI, push notification configuration fields were being overwritten with empty strings or default values because the HTML form doesn't re-submit password fields (for security reasons).

### Before Fix (BUGGY)
```python
# In app.py, save_system_config() function
system_cfg.update({
    "pushover_user_key": data.get("pushover_user_key", ""),  # ❌ Overwrites with ""
    "pushover_device": data.get("pushover_device", ""),       # ❌ Overwrites with ""
    "ntfy_server": data.get("ntfy_server", "https://ntfy.sh"), # ❌ Overwrites
    "ntfy_topic": data.get("ntfy_topic", ""),                 # ❌ Overwrites with ""
    "push_provider": data.get("push_provider", "pushover"),   # ❌ Overwrites
})
```

### After Fix (CORRECTED)
```python
# In app.py, save_system_config() function
system_cfg.update({
    "pushover_user_key": data.get("pushover_user_key", system_cfg.get("pushover_user_key", "")),  # ✅ Preserves existing
    "pushover_device": data.get("pushover_device", system_cfg.get("pushover_device", "")),        # ✅ Preserves existing
    "ntfy_server": data.get("ntfy_server", system_cfg.get("ntfy_server", "https://ntfy.sh")),     # ✅ Preserves existing
    "ntfy_topic": data.get("ntfy_topic", system_cfg.get("ntfy_topic", "")),                       # ✅ Preserves existing
    "push_provider": data.get("push_provider", system_cfg.get("push_provider", "pushover")),      # ✅ Preserves existing
})
```

## Scenario that Triggered the Bug

1. User sets up Pushover credentials:
   - User Key: `u123456789abcdef...`
   - API Token: `a123456789abcdef...`
   - Device: `my-phone`

2. User saves settings → Credentials stored in config file ✅

3. Later, user edits a different setting (e.g., brewery name)

4. User saves settings → **BUG: Credentials cleared!** ❌

5. User tries to send test notification → **FAILURE: Missing credentials** ❌

## After Fix

1. User sets up Pushover credentials
2. User saves settings → Credentials stored ✅
3. User edits other settings
4. User saves settings → **Credentials preserved!** ✅
5. User sends test notification → **SUCCESS!** ✅

## Files Changed

1. **app.py** (lines 2802-2806)
   - Modified 5 configuration fields to preserve existing values

## Tests Added

1. **test_push_config_preservation.py**
   - Unit test demonstrating the bug and verifying the fix
   - Shows both buggy and corrected behavior side-by-side

2. **test_integration_push_config.py**
   - Integration test simulating real-world usage with the Flask app
   - Verifies end-to-end configuration persistence

## Security Review

- ✅ No security vulnerabilities introduced
- ✅ CodeQL scan passed with 0 alerts
- ✅ Existing password handling unchanged
- ✅ No sensitive data exposed

## Impact

- **Users affected:** All users using PUSH notifications (Pushover or ntfy)
- **Severity:** High - prevented notifications from being delivered
- **Fix complexity:** Minimal - 5 line changes in app.py
- **Breaking changes:** None
- **Migration needed:** None - existing configs will work correctly
