# Demo Chart Setup - Summary

## What Was Done

Successfully imported Brewer's Friend fermentation data into the Black tilt for demo/chart visualization purposes.

## Demo Data Details

**Batch Information:**
- **Tilt Color**: Black
- **Beer Name**: 803 Blonde Ale Clone of 805
- **Batch Name**: Demo Batch
- **Brew ID**: cf38d0a8
- **Fermentation Period**: December 25, 2025 - January 9, 2026 (15 days)

**Fermentation Summary:**
- **Starting Gravity**: 1.049 (OG)
- **Final Gravity**: 1.004 (FG)
- **Gravity Drop**: 0.045 points
- **Estimated ABV**: 5.9%
- **Temperature Range**: 65-74°F
- **Data Points**: 30 samples

## Files Created/Modified

### New Utility Files
1. **`utils/import_brewers_friend.py`** - Script to import Brewer's Friend JSON data
2. **`utils/verify_demo_data.py`** - Script to verify and display demo data
3. **`utils/setup_demo.sh`** - Automated setup script for demo configuration
4. **`utils/README.md`** - Documentation for import utilities and demo data

### Modified Data Files
1. **`batches/cf38d0a8.jsonl`** - Replaced with demo fermentation data
   - Backed up original to `batches/cf38d0a8.jsonl.backup`

### Configuration Files (created locally, not committed)
1. **`config/tilt_config.json`** - Active configuration for Black tilt
2. **`config/system_config.json`** - System-wide settings
3. **`config/temp_control_config.json`** - Temperature control settings

### Documentation Updates
1. **`README.md`** - Added "Demo Data" section

## How to Use

### Quick Setup
```bash
# Run the automated setup script
./utils/setup_demo.sh

# Start the Flask app
python3 app.py

# Open in browser
http://localhost:5000/chart_plotly/Black
```

### Manual Import
```bash
# Import custom Brewer's Friend data
python3 utils/import_brewers_friend.py data.json \
    --color Black \
    --beer-name "Your Beer Name" \
    --batch-name "Batch Name"
```

### Verify Demo Data
```bash
# Display demo data summary
python3 utils/verify_demo_data.py
```

## Chart Visualization

The demo data creates a complete fermentation chart showing:

**Gravity Curve:**
```
1.060 |--------------------------------------------------|
1.049 |                                       *          | Start
1.040 |                             *                    | Active
1.033 |                          *                       | 
1.026 |                    *                             | 
1.016 |            *                                     | 
1.014 |          *                                       | 
1.005 |   *                                              | Slowing
1.004 |  *                                               | Complete
1.000 |--------------------------------------------------|
      Dec 25                                        Jan 9
```

**Chart Features:**
- Interactive Plotly visualization
- Dual Y-axis (gravity and temperature)
- Zoom and pan capabilities
- Hover tooltips with exact values
- Full timeline with date/time labels
- Complete fermentation curve from pitch to completion

## Data Format

The system uses JSONL (JSON Lines) format:

**Metadata Entry (first line):**
```json
{
  "event": "batch_metadata",
  "payload": {
    "tilt_color": "Black",
    "brewid": "cf38d0a8",
    "created_date": "12252025",
    "meta": {
      "beer_name": "803 Blonde Ale Clone of 805",
      "batch_name": "Demo Batch"
    }
  }
}
```

**Sample Entry (subsequent lines):**
```json
{
  "event": "sample",
  "payload": {
    "timestamp": "2025-12-25T14:27:59Z",
    "tilt_color": "Black",
    "gravity": 1.049,
    "temp_f": 65,
    "current_temp": 65.0,
    "brewid": "cf38d0a8",
    "rssi": -70
  }
}
```

## Technical Notes

1. **Brewid Linking**: The `brewid` field links the batch file to the tilt configuration
2. **RSSI Default**: Signal strength set to -70 (not in Brewer's Friend exports)
3. **Timestamp Format**: ISO 8601 format preserved from source data
4. **Config Separation**: Config files are gitignored to prevent committing user data
5. **Backup**: Original batch file backed up before replacement

## Next Steps

Users can now:
1. Take screenshots of the full fermentation chart for documentation
2. Import their own historical data using the import script
3. Modify the demo data for different visualization scenarios
4. Use this as a template for batch data structure

## Support

See `utils/README.md` for detailed documentation on:
- Import script usage and parameters
- Data format specifications
- Verification procedures
- Troubleshooting tips
