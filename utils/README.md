# Demo Data Import

This directory contains utilities for importing fermentation data into the Fermenter Temperature Controller system.

## Overview

The demo data has been imported for the **Black tilt** to showcase a complete fermentation cycle:

- **Beer**: 803 Blonde Ale Clone of 805
- **Batch**: Demo Batch  
- **Brew ID**: cf38d0a8
- **Duration**: ~15 days (Dec 25, 2025 - Jan 9, 2026)
- **Starting Gravity**: 1.049
- **Final Gravity**: 1.004
- **Estimated ABV**: 5.9%
- **Data Points**: 30 samples

## Import Script

### `import_brewers_friend.py`

Converts Brewer's Friend JSON export format to the internal JSONL format used by the Fermenter Temp Controller.

**Usage:**

```bash
# Import with auto-generated brewid
python3 utils/import_brewers_friend.py data.json \
    --color Black \
    --beer-name "Beer Name" \
    --batch-name "Batch Name"

# Import with specific brewid
python3 utils/import_brewers_friend.py data.json \
    --color Black \
    --brewid cf38d0a8 \
    --beer-name "Beer Name" \
    --batch-name "Batch Name"
```

**Parameters:**
- `input_file`: Path to Brewer's Friend JSON export file
- `--color`: Tilt color (Black, Blue, Green, Orange, Pink, Purple, Red, Yellow)
- `--brewid`: Optional brew ID (8-character hex). If omitted, will be auto-generated
- `--beer-name`: Beer name for metadata
- `--batch-name`: Batch name for metadata
- `--output-dir`: Output directory (default: `batches`)

## Verification Script

### `verify_demo_data.py`

Displays the imported demo data and verifies it's ready for chart visualization.

**Usage:**

```bash
python3 utils/verify_demo_data.py
```

This will show:
- Batch metadata (beer name, brew ID, etc.)
- Total sample count
- Fermentation start and end data
- Gravity drop and estimated ABV
- Sample data points

## Data Format

The system uses JSONL (JSON Lines) format where each line is a valid JSON object.

### Batch Metadata Entry

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

### Sample Entry

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

## Viewing the Chart

1. Start the Flask application:
   ```bash
   python3 app.py
   ```

2. Open your browser to:
   ```
   http://localhost:5000/chart_plotly/Black
   ```

3. The chart will display the complete fermentation curve with:
   - Gravity over time (showing the fermentation progress)
   - Temperature over time
   - Interactive Plotly charts for zooming and analysis

## Configuration

The demo data is configured in `config/tilt_config.json`:

```json
{
  "Black": {
    "beer_name": "803 Blonde Ale Clone of 805",
    "batch_name": "Demo Batch",
    "ferm_start_date": "12/25/2025",
    "recipe_og": "1.050",
    "recipe_fg": "1.010",
    "recipe_abv": "5.2",
    "actual_og": "1.049",
    "brewid": "cf38d0a8",
    "og_confirmed": true
  }
}
```

## Notes

- All data in this system is for demonstration purposes only
- The import script preserves timestamps from the original Brewer's Friend export
- RSSI (signal strength) is set to a default value of -70 since it's not included in BF exports
- The brewid is used to link the batch file to the tilt configuration
