# Gmail Email Configuration Fix

## Problem
When attempting to use Gmail for email notifications with username `fermentercontroller@gmail.com` and password `Alpaca1968`, the test fails with:

```
✗ Failed to send test email: (535, b'5.7.8 Username and Password not accepted. 
For more information, go to 5.7.8 https://support.google.com/mail/?p=BadCredentials')
```

## Root Cause
Gmail no longer accepts regular account passwords for third-party applications. Google has deprecated "Less Secure Apps" access and now requires:
1. **2-Factor Authentication (2FA)** to be enabled on the account
2. **App Passwords** for third-party applications like this Fermenter Controller

The password `Alpaca1968` is a regular Gmail password, which Gmail will reject.

## Solution
You must generate and use a Gmail **App Password** instead of the regular password.

### Step-by-Step Fix

#### 1. Enable 2-Factor Authentication
- Log into https://myaccount.google.com with `fermentercontroller@gmail.com`
- Navigate to https://myaccount.google.com/security
- Click on "2-Step Verification"
- Follow the setup process (you'll need access to a phone for verification)

#### 2. Generate an App Password
- Once 2FA is enabled, go to https://myaccount.google.com/apppasswords
- You may need to sign in again
- Select "Mail" for app type
- Select "Other (Custom name)" for device
- Enter "Fermenter Controller" as the name
- Click "Generate"
- Google will display a 16-character password like: `abcd efgh ijkl mnop`
- **Copy this password** - you won't be able to see it again

#### 3. Configure the Fermenter Controller
- Navigate to **System Settings → SMS/eMail** in the web interface
- Enter the following settings:
  - **Fermenter Email Account Address**: `fermentercontroller@gmail.com`
  - **Fermenter Email Password**: [paste the 16-character App Password from step 2]
  - **SMTP Server Host**: `smtp.gmail.com`
  - **SMTP Server Port**: `587`
  - **Use STARTTLS**: ✓ Enabled
  - **Recipient Email Address**: [your email where you want to receive notifications]

#### 4. Test the Configuration
- Click "Save" to save your settings
- Click "Test Email" button
- You should receive a test email within a few seconds

## Changes Made to Fix This Issue

### 1. Enhanced Error Messages (`app.py`)
- The `_smtp_send()` function now detects Gmail authentication errors
- Provides helpful guidance about App Passwords when authentication fails
- Example error message now shows:
  ```
  Gmail authentication failed. Gmail requires an App Password when 2-Factor 
  Authentication is enabled. Regular Gmail passwords will not work. To fix this: 
  1) Enable 2-Factor Authentication on your Google account, 
  2) Generate an App Password at https://myaccount.google.com/apppasswords, 
  3) Use the App Password (not your regular password) in the Fermenter Email Password field.
  ```

### 2. Updated UI Instructions (`templates/sms_email_config.html`)
- Added prominent warning in the password field
- Includes direct links to:
  - App Password documentation
  - App Password generation page
- Makes it immediately clear that Gmail users need App Passwords

### 3. Improved Documentation (`NOTIFICATIONS.md`)
- Complete step-by-step guide for Gmail App Password setup
- Common error messages and solutions
- Clear examples using `fermentercontroller@gmail.com`

## Testing

A test script is included to verify the fix: `test_gmail_fermentercontroller.py`

```bash
python3 test_gmail_fermentercontroller.py
```

This demonstrates:
- Using a regular password fails with a helpful error message
- The error message guides users to the solution
- Step-by-step instructions for fixing the issue

## Security Note

**DO NOT** commit the App Password to the repository. The `config/system_config.json` file (which stores the password) is already in `.gitignore` to prevent accidental commits.

## Summary

The issue was caused by Gmail's security requirements, not a bug in the code. The fix:
1. ✅ Detects Gmail authentication errors
2. ✅ Provides clear, actionable error messages  
3. ✅ Updates the UI with prominent instructions
4. ✅ Improves documentation with step-by-step guides

**Action Required**: Generate an App Password for `fermentercontroller@gmail.com` and use it instead of `Alpaca1968`.
