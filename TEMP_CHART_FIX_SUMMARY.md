# Temperature Control Chart Fix Summary

## Issue
The Temperature Control Chart (accessed via the [Chart] button on the Temperature Control Card) failed to load with the message "Failed to load data" even though 445 records were available and could be successfully exported.

## Root Cause
The chart JavaScript code had two bugs:

### Bug 1: Filtering out all data when `tilt_color` is empty
In `templates/chart_plotly.html` at line 99 (before fix):
```javascript
const validDataPoints = dataPoints.filter(p => p.tilt_color && p.tilt_color.trim() !== '');
```

When all temperature control log entries had an empty `tilt_color` field (which can happen with older data or when the system isn't tracking which tilt is active), this filter would remove ALL data points, resulting in:
- `validDataPoints = []`  (empty array)
- `activeTiltColor = null`
- `activeTiltData = []`  (empty array)
- No temperature trace created
- Chart failed to render

### Bug 2: Variable scoping issue
The variable `allDataPoints` was declared inside the first `if (isTempControl)` block but was used in a second `if (isTempControl)` block later in the code, causing a `ReferenceError: allDataPoints is not defined`.

## Solution
### Fix 1: Fixed the scoping bug (PRIMARY FIX)
Moved the `allDataPoints` variable declaration to before the `if (isTempControl)` block (line 96) so it's accessible throughout the function. This was the root cause that prevented the chart from rendering.

### Fix 2: Added defensive handling for empty tilt_color (DEFENSIVE CODE)
Modified the chart logic to gracefully handle cases where `tilt_color` might be empty:

1. **When `tilt_color` data exists (NORMAL PATH):** Show only the active tilt's data with the tilt name (e.g., "Black Tilt")
2. **When `tilt_color` is empty (DEFENSIVE PATH):** Show ALL data with a generic "Temperature" label

**Why the defensive code exists:**
The `tilt_color` field can be empty in several scenarios:
- **System events** like `startup_plug_sync` that don't relate to a specific tilt
- **Legacy data** from older versions before tilt_color tracking was added
- **Configuration states** where temperature control is enabled but no tilt assigned yet
- **Data migration** or manual edits that left the field empty

Without this defensive handling, the chart would fail with "no data" even though temperature records exist. With it, users can view their data in any scenario.

**See DEFENSIVE_CODE_EXPLANATION.md for detailed explanation of when and why this code runs.**

```javascript
// Moved allDataPoints declaration outside the if block
const allDataPoints = dataPoints;

// Determine which data to display
let displayData = [];
let displayLabel = 'Temperature';
let displayColor = '#808080';

if (activeTiltColor) {
  // If we have an active tilt, show only that tilt's data
  displayData = validDataPoints.filter(p => p.tilt_color === activeTiltColor);
  displayLabel = `${activeTiltColor} Tilt`;
  displayColor = colorMap[activeTiltColor] || '#808080';
} else {
  // No tilt_color data available, show all data points
  displayData = allDataPoints;  // THE FIX
  displayLabel = 'Temperature';
  displayColor = '#0066CC';
}
```

### Fix 2: Move variable declaration to correct scope
Moved the `allDataPoints` variable declaration to before the `if (isTempControl)` block so it's accessible throughout the function.

## Files Changed
- `templates/chart_plotly.html` - Fixed chart rendering logic

## Testing
Created comprehensive tests to verify:
1. Chart works with empty `tilt_color` (original bug scenario)
2. Chart works with valid `tilt_color` (normal operation)
3. Chart works with mixed data (some empty, some valid)

All tests pass successfully.

## Impact
- Users can now view temperature control charts even when historical data doesn't include `tilt_color` information
- The chart gracefully handles both legacy data and current data formats
- Event markers (heating/cooling on/off) continue to work correctly
- No impact on normal operation when `tilt_color` is present
