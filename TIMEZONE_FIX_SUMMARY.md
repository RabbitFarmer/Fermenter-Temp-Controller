# Timezone Fix Summary

## Issue
The Temperature Control chart and Tilt charts were displaying timestamps in UTC time (16:50) instead of the user's local time (11:50 EST), causing a 5-hour discrepancy.

## Root Cause
- Data is stored in UTC format with timestamps ending in "Z" (e.g., "2026-01-31T16:50:00Z")
- When UTC timestamp strings were passed directly to Plotly.js, it displayed them as UTC time
- The browser's timezone was not being applied to the chart display

## Solution
Modified `templates/chart_plotly.html` to convert UTC timestamp strings to JavaScript Date objects before passing them to Plotly:

### Changes Made

1. **Data Normalization (Lines 84-100)**
   ```javascript
   // Convert UTC timestamp to local time for display
   let localTimestamp = ts;
   if (ts) {
     try {
       const date = new Date(ts);
       if (!isNaN(date.getTime())) {
         // Convert to local time by using the Date object directly
         // This will automatically use the browser's timezone
         localTimestamp = date;
       }
     } catch (e) {
       console.warn('Failed to convert timestamp:', ts, e);
     }
   }
   ```

2. **X-axis Range Calculation (Lines 220-260)**
   - Changed from: `xAxisRange = [rangeStart.toISOString(), rangeEnd.toISOString()]`
   - Changed to: `xAxisRange = [rangeStart, rangeEnd]`
   - This ensures Date objects are used directly instead of ISO strings

## How It Works

### Before Fix
```javascript
// UTC string passed directly to Plotly
x: ["2026-01-31T16:50:00Z", ...]
// Plotly displays: 16:50 (UTC time)
```

### After Fix
```javascript
// UTC string converted to Date object
const date = new Date("2026-01-31T16:50:00Z");
x: [date, ...]
// Plotly displays: 11:50 (Local EST time - automatically converted by browser)
```

## Impact

This fix affects:
- ✅ Temperature Control charts (`/chart_plotly/Fermenter`)
- ✅ Tilt card charts (`/chart_plotly/Black`, `/chart_plotly/Blue`, etc.)
- ✅ All historical data (converted on-the-fly during display)
- ✅ Future data (will continue to be stored in UTC but displayed in local time)

## Testing

Created validation files:
- `test_timezone_validation.py` - Validates timestamp conversion logic
- `test_chart_before_after.html` - Visual demonstration of before/after
- `test_timezone_fix.html` - Interactive comparison

## Verification

1. ✅ Code review - No issues found
2. ✅ Security scan (CodeQL) - No vulnerabilities found
3. ✅ All chart types will now display correct local time

## No Breaking Changes

- Data storage format remains unchanged (UTC timestamps)
- Only display/rendering is affected
- Backward compatible with existing data
- No configuration changes required
