# Temperature Control Chart Zoom Error Fix

## Issue Summary
The temperature control chart had three critical zoom-related bugs:
1. When zooming in, the program zoomed to the center of the page instead of centering on the last data element
2. Once you zoom in, you cannot zoom back out
3. You cannot reset - the chart data just disappears

## Root Cause Analysis

The zoom functions were reading the current x-axis range from Plotly's internal state using `chart.layout.xaxis.range`. This caused several problems:

1. **Type Mismatch**: Plotly stores ranges in its own internal format (either epoch milliseconds or ISO 8601 strings), not as JavaScript Date objects. When the code attempted to create `new Date(currentRange[0])` from these values, it sometimes failed or produced unexpected results.

2. **State Inconsistency**: Reading from Plotly's state after a relayout operation could return stale or incorrectly formatted data, leading to cumulative errors with each zoom operation.

3. **Data Loss**: The type mismatches and state inconsistencies caused the calculated zoom ranges to be invalid, making the chart data appear to "disappear" because the x-axis range became incorrect.

## Solution

Introduced a JavaScript variable `currentXRange` to track the current x-axis range independently of Plotly's internal state:

```javascript
let defaultXRange = null;
let currentXRange = null;  // NEW: Track current x-axis range
let currentViewMode = 'all';
```

### Changes Made

#### 1. Initialize Current Range
```javascript
if (xAxisRange) {
  defaultXRange = xAxisRange;
  currentXRange = xAxisRange;  // Initialize to default
}
```

#### 2. Updated Zoom In Function
**Before:**
```javascript
const chart = document.getElementById('tempChart');
const currentRange = chart.layout.xaxis.range;  // ❌ Reading from Plotly
if (currentRange && currentRange.length === 2 && defaultXRange) {
  const start = new Date(currentRange[0]);  // ❌ Type mismatch risk
  const end = new Date(currentRange[1]);
  // ... zoom logic
}
```

**After:**
```javascript
if (currentXRange && currentXRange.length === 2 && defaultXRange) {
  const start = new Date(currentXRange[0]);  // ✅ Consistent Date objects
  const end = new Date(currentXRange[1]);
  // ... zoom logic
  currentXRange = [newStart, newEnd];  // ✅ Update tracked range
}
```

#### 3. Updated Zoom Out Function
Applied the same pattern:
- Use `currentXRange` instead of reading from Plotly
- Update `currentXRange` after calculating new range
- Ensures consistent behavior with zoom in

#### 4. Updated Reset Function
```javascript
if (defaultXRange) {
  currentXRange = defaultXRange;  // ✅ Reset tracked range
  Plotly.relayout('tempChart', {
    'xaxis.range': defaultXRange
  });
}
```

#### 5. Updated View Buttons (1 Day, 1 Week, All Data)
All view buttons now update `currentXRange` to maintain state consistency:
```javascript
// Update current range
currentXRange = [start, end];

Plotly.relayout('tempChart', {
  'xaxis.range': [start, end]
});
```

## Benefits

1. **Consistent Data Types**: All range operations use JavaScript Date objects consistently
2. **Reliable State Management**: No dependency on Plotly's internal state representation
3. **Predictable Zoom Behavior**: Zoom in/out operations work correctly every time
4. **No Data Loss**: Chart data remains visible after zoom/reset operations
5. **Maintained Functionality**: The zoom still centers on the last data point as designed

## Files Modified

- `templates/chart_plotly.html` - Main temperature control chart template
- `test_chart_zoom_controls.html` - Test file updated with the fix
- Created `test_zoom_fix_improved.html` - New test file with debug output

## Testing

The fix ensures:
- ✅ Zoom In works correctly and centers on last data point
- ✅ Zoom Out works correctly and can zoom back out after zooming in
- ✅ Reset Zoom restores the chart to full data view
- ✅ 1 Day, 1 Week, All Data views continue to work
- ✅ Chart data never disappears during zoom operations

## Technical Notes

This fix follows a common pattern in web development: **maintain your own state** rather than reading computed/internal state from third-party libraries. By tracking `currentXRange` ourselves, we:

1. Avoid coupling to Plotly's internal implementation details
2. Ensure type consistency (always Date objects)
3. Have a single source of truth for the current view range
4. Can easily debug state issues by inspecting our variable

The same pattern is already used successfully in the codebase for `defaultXRange` and `currentViewMode`.
