# Temperature Control Chart Line Fix - Visual Explanation

## The Problem

**Before the fix**, heating and cooling state changes were displayed as scattered markers without any connecting lines:

```
Temperature (°F)
    |
70° |                    *      (Heating OFF - pink triangle)
    |
68° |          *                 (Heating ON - red triangle)
    |                                        □  (Cooling ON - blue square)
66° |    *                                      
    |                  *                        (Heating OFF - pink)
64° |                           *               (Heating ON - red)
    |                                   □       (Cooling OFF - lightblue)
    +----+----+----+----+----+----+----+----+----
        Time →
```

**Issue**: The markers appeared to "retreat to some base position then jump up again" because each marker was independent, with no visual connection between successive state changes.

## The Solution

**After the fix**, heating and cooling state changes are connected by lines showing the progression of state changes over time:

```
Temperature (°F)
    |
70° |                    ▼      (Heating OFF - pink triangle)
    |                   /
68° |          ▲-------/         (Heating ON - red triangle connected by red line)
    |         /                                ■  (Cooling ON - blue square)
66° |    ▲---/                                /   
    |   /              ▼                     /    (Heating OFF - pink)
64° |  /               |-------▲           /      (Heating ON - red)
    | /                        |----------■       (Cooling OFF - lightblue connected by blue line)
    +----+----+----+----+----+----+----+----+----
        Time →
        
Legend:
  Red line with triangles = Heating Control (▲ = ON, ▼ = OFF)
  Blue line with squares = Cooling Control (■ = ON, □ = OFF)
```

## Technical Changes

### Before (4 separate marker-only traces)
```javascript
// Heating ON markers only
traces.push({
  x: heatingOnEvents.map(p => p.timestamp),
  y: heatingOnEvents.map(p => p.temp_f),
  mode: 'markers',  // ← No lines
  name: 'Heating ON',
  ...
});

// Heating OFF markers only
traces.push({
  x: heatingOffEvents.map(p => p.timestamp),
  y: heatingOffEvents.map(p => p.temp_f),
  mode: 'markers',  // ← No lines
  name: 'Heating OFF',
  ...
});

// Same for Cooling ON and Cooling OFF
```

### After (2 line+marker traces combining ON/OFF)
```javascript
// Combine all heating events and sort chronologically
const heatingEvents = [...heatingOnEvents, ...heatingOffEvents].sort((a, b) => 
  a.timestamp.getTime() - b.timestamp.getTime()
);

// Single heating control trace with connected line
traces.push({
  x: heatingEvents.map(p => p.timestamp),
  y: heatingEvents.map(p => p.temp_f),
  mode: 'lines+markers',  // ← Lines connect the markers!
  name: 'Heating Control',
  line: { color: 'red', width: 2, shape: 'linear' },
  marker: { 
    color: heatingEvents.map(p => p.event === 'HEATING-PLUG TURNED ON' ? 'red' : 'pink'),
    symbol: heatingEvents.map(p => p.event === 'HEATING-PLUG TURNED ON' ? 'triangle-up' : 'triangle-down')
  },
  ...
});

// Same approach for cooling
```

## Benefits

1. **Clear progression**: Lines show how state changes progress over time
2. **No "retreating"**: Each point connects directly to the next point
3. **Better visualization**: Easy to see when heating/cooling was active
4. **Cleaner legend**: 2 traces instead of 4
5. **Same information**: ON/OFF still distinguished by marker color/shape

## Result

The temperature control chart now displays as a proper line chart where:
- Successive data points are connected directly
- No jumping or retreating to base positions
- State changes are clearly visible as a continuous line
- The chart is easier to read and understand
