# Plotly Modebar Visual Guide

## What is the Modebar?

The modebar is Plotly's built-in toolbar that appears in the top-right corner of charts when you hover over them.

## Visual Representation

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TEMPERATURE CONTROL ACTIVITY                          [📷][📦][🔍][⤢]  │ ← Modebar appears here
│                                                        [⊕][⊖][🏠][📍]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  70°F ┤                                                                 │
│       │     ╱╲                        ╱╲                                │
│  68°F ┤────╱──╲──────────────────────╱──╲───── High Limit              │
│       │   ╱    ╲       ▼    ▲       ╱    ╲                             │
│  66°F ┤──╱──────╲─────────────────╱───────╲────────                    │
│       │ ╱        ╲   (markers)   ╱         ╲                           │
│  64°F ┤╱──────────╲─────────────╱───────────╲─── Low Limit             │
│       │            ╲           ╱                                        │
│       └────────────────────────────────────────────────────────────────│
│         Jan 1      Jan 2      Jan 3      Jan 4      Jan 5              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Modebar Icons and Functions

| Icon | Name | Function |
|------|------|----------|
| 📷 | Download | Save chart as PNG image |
| 📦 | Box Zoom | Click and drag to zoom into a specific area |
| 🔍 | Pan | Click and drag to move around the chart |
| ⊕ | Zoom In | Zoom in centered on the chart |
| ⊖ | Zoom Out | Zoom out centered on the chart |
| 🏠 | Reset | Return to original view (autoscale) |
| 📍 | Toggle Spike Lines | Show/hide crosshair lines when hovering |
| ⤢ | Hover Mode | Toggle between showing closest point or comparing multiple points |

## Before vs After

### Before (Custom Buttons)
```
┌──────────────────────────────────────────────┐
│  [Zoom In] [Zoom Out] [Reset] | [1 Day] ...  │ ← Custom buttons above chart
├──────────────────────────────────────────────┤
│                                              │
│  (Chart Area)                                │
│                                              │
└──────────────────────────────────────────────┘
```
- 6 custom HTML buttons
- ~160 lines of custom JavaScript
- Takes up vertical space
- Only available on temperature control chart

### After (Plotly Modebar)
```
┌──────────────────────────────────────────────┐
│  (Chart Area)                  [Icons...]    │ ← Modebar on hover, top-right
│                                              │
│                                              │
└──────────────────────────────────────────────┘
```
- Built-in Plotly functionality
- 10 lines of configuration
- No extra space needed (appears on hover)
- Available on ALL charts (tiltcards + temp control)

## How to Use

1. **View a chart** - Navigate to any chart (click "CHART" on a tiltcard or temperature control card)

2. **Hover over the chart** - The modebar will appear in the top-right corner

3. **Use the tools:**
   - Click the **camera icon** to download the chart as an image
   - Click the **box zoom icon**, then click and drag on the chart to zoom into a specific region
   - Click the **pan icon**, then click and drag to move around the zoomed chart
   - Click the **zoom in/out icons** to zoom centered on the current view
   - Click the **home icon** to reset the chart to its original view
   - Click the **spike lines icon** to toggle crosshairs when hovering over data points

## Advantages

✅ **More powerful** - Professional-grade chart interaction tools  
✅ **More consistent** - Same tools on every chart  
✅ **Less code** - 163 fewer lines to maintain  
✅ **Standard UX** - Familiar interface users expect from modern web apps  
✅ **More features** - Download, pan, box zoom, and more  
✅ **Space efficient** - Only appears on hover, doesn't take up permanent screen space  

## Notes

- The modebar only appears when you hover over the chart area
- On touch devices, the modebar may be always visible
- The Plotly logo has been hidden (`displaylogo: false`)
- All modebar buttons are enabled by default (`modeBarButtonsToRemove: []`)
