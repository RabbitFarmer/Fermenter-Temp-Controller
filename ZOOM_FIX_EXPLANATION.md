# Temperature Control Chart Zoom Fix

## Problem
The zoom feature had an issue where it centered on the middle of the currently visible range, which caused problems:

1. **On new instances**: When data was on the left side of the chart and you zoomed in, the graph would disappear because the zoom was focused on the middle of the visible range, which might not have any data.
2. **Poor user experience**: Users expected to see the most recent data (last data point) when zooming in, not the middle of the visible range.

## Solution
Modified the zoom functions to **center on the last data point** (most recent data) instead of the middle of the visible range.

### Changes Made

#### Zoom In Function (`chart_plotly.html` lines 593-611)
**Before:**
```javascript
const center = new Date((start.getTime() + end.getTime()) / 2);
const newStart = new Date(center.getTime() - newDuration / 2);
const newEnd = new Date(center.getTime() + newDuration / 2);
```

**After:**
```javascript
// Center on the last data point (most recent data)
const lastDataPoint = new Date(defaultXRange[1]);
const newStart = new Date(lastDataPoint.getTime() - newDuration);
const newEnd = lastDataPoint;
```

#### Zoom Out Function (`chart_plotly.html` lines 613-641)
**Before:**
```javascript
const center = new Date((start.getTime() + end.getTime()) / 2);
let newStart = new Date(center.getTime() - newDuration / 2);
let newEnd = new Date(center.getTime() + newDuration / 2);
```

**After:**
```javascript
// Center on the last data point (most recent data)
const lastDataPoint = new Date(defaultXRange[1]);
let newStart = new Date(lastDataPoint.getTime() - newDuration);
let newEnd = lastDataPoint;
```

### How It Works

1. **Last Data Point**: The zoom functions now use `defaultXRange[1]` which represents the last (most recent) data point in the dataset.

2. **Zoom In**: 
   - Reduces the visible time range by 50%
   - Always keeps the end at the last data point
   - Moves the start point backward from the last data point by the new duration

3. **Zoom Out**:
   - Doubles the visible time range
   - Always keeps the end at the last data point (unless it would exceed the full data range)
   - Moves the start point further backward from the last data point
   - Respects the minimum boundary (won't go before the first data point)

### Benefits

1. **Predictable behavior**: Zoom always centers on the most recent data, which is what users expect in a fermentation monitoring application
2. **No disappearing data**: Since we always anchor to the last data point, the graph won't disappear when zooming in on new instances
3. **Consistent with time range filters**: The "1 Day" and "1 Week" views already center on the last data point, so this makes all zoom operations consistent

### Files Modified

- `templates/chart_plotly.html` - Main chart template used by the Flask application
- `test_chart_zoom_controls.html` - Test file demonstrating the zoom functionality
