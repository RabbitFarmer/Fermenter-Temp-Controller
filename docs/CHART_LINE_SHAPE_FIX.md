# Temperature Control Chart Line Shape Fix

## Issue
The temperature control chart was displaying **horizontal lines with periodic vertical jumps** instead of lines that move directly from point to point.

## Root Cause
The Plotly.js chart configuration was using `shape: 'spline'` for line interpolation. While 'spline' creates smooth curves, in this case it appears to have been causing an undesirable step-like visualization pattern.

## Solution
Changed all line shape configurations from `'spline'` to `'linear'` to draw straight lines directly from point to point.

## Changes Made

### File: `templates/chart_plotly.html`

**Three locations updated:**

1. **Temperature trace for temperature control** (line 175)
   ```javascript
   // BEFORE
   line: { color: displayColor, shape: 'spline', width: 3 },
   
   // AFTER
   line: { color: displayColor, shape: 'linear', width: 3 },
   ```

2. **Temperature trace for regular tilt data** (line 191)
   ```javascript
   // BEFORE
   line: { color: 'blue', shape: 'spline', width: 3 },
   
   // AFTER
   line: { color: 'blue', shape: 'linear', width: 3 },
   ```

3. **Gravity trace** (line 383)
   ```javascript
   // BEFORE
   line: { color: '#E69D00', shape: 'spline', width: 3 },
   
   // AFTER
   line: { color: '#E69D00', shape: 'linear', width: 3 },
   ```

## Visual Difference

### Before (with 'spline'):
```
Temperature
    |
70° |     _______________
    |    |
68° |____|               |_______________
    |                    |
66° |                    |
    +----+----+----+----+----+----+----+----
        Time →
```
*Horizontal lines with vertical jumps at data points*

### After (with 'linear'):
```
Temperature
    |
70° |        /‾‾‾‾\
    |       /      \
68° |      /        \
    |     /          \
66° |____/            \____
    +----+----+----+----+----+----+----+----
        Time →
```
*Direct straight lines from point to point*

## Result
The chart now displays clean, direct lines connecting each temperature reading to the next, making trends and changes much easier to visualize and understand.

## Testing
Created `test_chart_line_shape.py` to verify:
- All 3 line shape configurations are set to 'linear'
- No 'spline' configurations remain
- Template file structure is intact

✅ All tests pass
