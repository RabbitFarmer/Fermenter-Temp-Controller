# Temperature Control Chart Zoom and Time Range Features

## Overview
This document describes the new zoom and time range features added to the Temperature Control Chart to address issues with chart readability and usability.

## Problem Statement
The original issue identified several problems with the temperature control chart:
1. The chart had a line drawn from the left border to the first data point with no value
2. The chart layout detracted from readability
3. Users needed ability to zoom in and zoom out
4. Users wanted time range filters (1 day, 1 week, all data)
5. Curving lines were preferred over straight lines

## Solution

### 1. Fixed Limit Lines
**Problem**: Limit lines were drawn from `xAxisRange[0]` to `xAxisRange[1]`, causing a line from the left axis border to the first data point.

**Solution**: Modified limit lines to span only from the first data point to the last data point:
```javascript
// Calculate limit line boundaries based on actual data points
let limitLineStart = null;
let limitLineEnd = null;
if (dataPoints.length > 0) {
  limitLineStart = dataPoints[0].timestamp;
  limitLineEnd = dataPoints[dataPoints.length - 1].timestamp;
}

// Low limit line
x: [limitLineStart, limitLineEnd]  // Instead of [xAxisRange[0], xAxisRange[1]]
```

### 2. Curving Lines (Spline Shape)
Changed line shape from 'linear' to 'spline' for smoother, more readable temperature curves:
```javascript
line: { color: displayColor, shape: 'spline', width: 1.5 }
```

### 3. Zoom Controls
Added three zoom control buttons that manipulate the x-axis range:

**Zoom In**: Reduces visible time range by 50% centered on current view
```javascript
const newDuration = duration * 0.5;
const center = new Date((start.getTime() + end.getTime()) / 2);
const newStart = new Date(center.getTime() - newDuration / 2);
const newEnd = new Date(center.getTime() + newDuration / 2);
```

**Zoom Out**: Increases visible time range by 100% (won't exceed default range)
```javascript
const newDuration = duration * 2;
// Constrained to default range limits
```

**Reset Zoom**: Returns to default view showing all data
```javascript
Plotly.relayout('tempChart', { 'xaxis.range': defaultXRange });
```

### 4. Time Range Filters
Added three time range filter buttons:

**1 Day**: Shows last 24 hours from end of data
```javascript
const start = new Date(end.getTime() - MS_PER_DAY);
```

**1 Week**: Shows last 7 days from end of data
```javascript
const start = new Date(end.getTime() - MS_PER_WEEK);
```

**All Data**: Shows complete data range (default view)

Active button is highlighted with darker blue background using CSS `.active` class.

## UI Design

### Button Layout
```
[Zoom In] [Zoom Out] [Reset Zoom] | [1 Day] [1 Week] [All Data]
```

### Color Scheme
- Zoom controls: Blue buttons (#2196F3)
- Active state: Darker blue (#0d47a1)
- Controls only shown for Temperature Control charts (`tilt_color == "Fermenter"`)
- Hidden when printing

## Code Quality
- Constants defined for time calculations:
  - `MS_PER_DAY = 24 * 60 * 60 * 1000`
  - `MS_PER_WEEK = 7 * 24 * 60 * 60 * 1000`
- Button states managed with `updateViewButtonStates()` function
- Default range stored in `defaultXRange` variable

## Files Modified
- `templates/chart_plotly.html` - Main chart template with all new features

## Testing
A test file was created to demonstrate the new features:
- `test_chart_zoom_controls.html` - Standalone demo with sample data

## Usage
1. Navigate to the Temperature Control chart (tilt_color == "Fermenter")
2. Use zoom controls to adjust view:
   - Click "Zoom In" to see more detail (50% time reduction)
   - Click "Zoom Out" to see wider view (100% time increase)
   - Click "Reset Zoom" to return to default view
3. Use time range filters for quick navigation:
   - Click "1 Day" to see last 24 hours
   - Click "1 Week" to see last 7 days
   - Click "All Data" to see complete data range

## Benefits
1. **Better Readability**: Limit lines no longer extend from axis border
2. **Smoother Visualization**: Spline curves show temperature trends more naturally
3. **Flexible Navigation**: Users can zoom to desired detail level
4. **Quick Access**: Time range filters provide fast navigation to recent data
5. **Intuitive UI**: Clear button labels and active state indicators

## Future Enhancements
Potential improvements for future iterations:
- Add custom date range selector
- Implement pan functionality
- Add keyboard shortcuts for zoom controls
- Save user's preferred zoom level
- Add zoom slider for continuous zoom control
