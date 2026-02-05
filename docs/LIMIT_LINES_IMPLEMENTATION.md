# Temperature Limit Lines - Implementation Summary

## User Request
> "Add thin horizontal red lines at the low limit and at the high limit."

## Implementation

### Backend Changes (app.py)
Added `low_limit` and `high_limit` fields to the chart data entry:

```python
entry = {
    "timestamp": ts_str, 
    "temp_f": temp_num, 
    "gravity": grav_num, 
    "event": event, 
    "tilt_color": obj.get('tilt_color', ''),
    "low_limit": obj.get('low_limit'),      # ← Added
    "high_limit": obj.get('high_limit')     # ← Added
}
```

### Frontend Changes (chart_plotly.html)

**1. Extract limit values from data points:**
```javascript
// Find the most recent limits from data points (iterate backwards)
let lowLimit = null;
let highLimit = null;

for (let i = allDataPoints.length - 1; i >= 0; i--) {
  const p = allDataPoints[i];
  // Get low limit if not yet found
  if (lowLimit === null && p.low_limit !== null && ...) {
    lowLimit = parseFloat(p.low_limit);
  }
  // Get high limit if not yet found
  if (highLimit === null && p.high_limit !== null && ...) {
    highLimit = parseFloat(p.high_limit);
  }
  // Break early if we have both limits
  if (lowLimit !== null && highLimit !== null) {
    break;
  }
}
```

**2. Add horizontal line traces:**
```javascript
// Add low limit line (thin red horizontal line)
if (lowLimit !== null && xAxisRange) {
  traces.push({
    x: [xAxisRange[0], xAxisRange[1]],
    y: [lowLimit, lowLimit],
    mode: 'lines',
    name: 'Low Limit',
    line: { color: 'red', width: 1, dash: 'solid' },
    yaxis: 'y1',
    showlegend: true,
    hoverinfo: 'y',
  });
}

// Add high limit line (thin red horizontal line)
if (highLimit !== null && xAxisRange) {
  traces.push({
    x: [xAxisRange[0], xAxisRange[1]],
    y: [highLimit, highLimit],
    mode: 'lines',
    name: 'High Limit',
    line: { color: 'red', width: 1, dash: 'solid' },
    yaxis: 'y1',
    showlegend: true,
    hoverinfo: 'y',
  });
}
```

## Visual Result

```
Temperature Control Chart
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    |
72° |━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ← High Limit (red, width: 1)
    |                    /\
70° |                   /  \
    |        /\        /    \
68° |       /  \      /      \        /\
    |      /    \    /        \      /  \
66° |     /      \  /          \    /    \
    |    /        \/            \  /      \
64° |━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ← Low Limit (red, width: 1)
    |   /                        \/
62° |  /
    +──────────────────────────────────────
       Time →

Legend:
  ▲ Heating ON
  ▼ Heating OFF  
  ■ Cooling ON
  □ Cooling OFF
  ─ Low Limit
  ─ High Limit
```

## Key Features

✅ **Thin lines** - Width set to 1 pixel for subtle visual guidance
✅ **Red color** - Clearly visible against the blue temperature line
✅ **Full width** - Lines span from start to end of x-axis range
✅ **In legend** - Labeled as "Low Limit" and "High Limit"
✅ **Hover info** - Shows limit temperature value on hover
✅ **Most recent values** - Uses the latest limit settings from data
✅ **Efficient** - Stops searching as soon as both limits are found

## Testing

Test file: `test_limit_lines.py`

Verifies:
- ✓ Backend includes low_limit and high_limit in chart data
- ✓ Frontend extracts limit values from data points
- ✓ Low Limit line trace exists
- ✓ High Limit line trace exists
- ✓ Both lines are thin (width: 1) and red

**All tests pass** ✅

## Commit
Short hash: `68032b8`

Message: "Add horizontal red limit lines to temperature control chart"
