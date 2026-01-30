# Temperature Control Chart Fixes

This document summarizes the fixes applied to resolve 5 issues with the temperature control chart.

## Issues Fixed

### Issue #1: Temperature Range (0-1000°F → 34-100°F)

**Problem:** Chart displayed temperature range from 0 to 1000°F, which is inappropriate for fermentation monitoring.

**Root Cause:** Invalid 999 temperature readings (from battery/connection issues) were forcing the range to expand to 0-1000.

**Solution:**
- Filter out 999 readings (see Issue #2)
- Updated base temperature range from 40-100°F to 34-100°F
- Range automatically expands if actual temperatures go beyond this base range

**Code Changes:**
- `templates/chart_plotly.html` line 156: `tempMin = Math.min(34, tempMin - chartTempMargin);`
- `templates/chart_plotly.html` line 165: `tempRange = [34, 100];`
- `templates/chart_plotly.html` line 308: `range: tempRange || [34, 100],`

---

### Issue #2: Filter 999 Temperature Readings

**Problem:** Tilt hydrometers occasionally report "999" readings due to battery weakness or connection spikes. These invalid readings should not be recorded or displayed.

**Solution:** Added filtering logic in the backend to set `temp_num = None` whenever a reading equals 999.

**Code Changes:**
- `app.py` lines 4479-4483 (temperature control data):
  ```python
  try:
      temp_num = float(tf) if (tf is not None and tf != '') else None
      # Filter out 999 readings (battery/connection issues)
      if temp_num == 999:
          temp_num = None
  except Exception:
      temp_num = None
  ```

- `app.py` lines 4566-4570 (regular tilt data):
  ```python
  try:
      temp_num = float(tf) if (tf is not None and tf != '') else None
      # Filter out 999 readings (battery/connection issues)
      if temp_num == 999:
          temp_num = None
  except Exception:
      temp_num = None
  ```

**Tests Added:**
- `test_999_filter.py`: Unit test for 999 filtering logic
- `test_chart_fixes.py`: Integration test with sample data containing 999 readings

---

### Issue #3: Show Only Active Tilt in Legend

**Problem:** Chart legend showed multiple tilts (e.g., "Black Tilt" and "Blue Tilt") even when only one tilt was active.

**Solution:** Modified chart rendering to only create traces for tilts that have valid temperature data.

**Code Changes:**
- `templates/chart_plotly.html` lines 124-128:
  ```javascript
  // Only create a trace if there are actual data points with valid temperatures
  const validPoints = points.filter(p => p.temp_f != null && !isNaN(p.temp_f));
  if (validPoints.length > 0) {
      // Create trace...
  }
  ```

---

### Issue #4: Cooling ON Indicator

**Problem:** "Cooling ON" indicator was missing from the legend while "Cooling OFF" was shown.

**Original Approach:** Conditionally show indicators only when events exist.

**Simplified Solution:** Always show all 4 heating/cooling indicators in the legend. Users can see from the chart which ones are actually in use.

**Code Changes:**
- `templates/chart_plotly.html` lines 214-262: Removed conditional `if` statements that checked for event existence
- All 4 traces are now always added:
  - Heating ON (red triangle up)
  - Heating OFF (pink triangle down)
  - Cooling ON (blue square)
  - Cooling OFF (light blue square)

**Benefits:**
- Simpler code - no conditional logic
- Consistent legend appearance
- Users can easily identify which controls are in use by looking at the chart

---

### Issue #5: Duplicate Date Range

**Problem:** Date range was displayed both in the chart title AND beneath the legend, creating duplication.

**Solution:** Hidden the duplicate date range div beneath the legend using CSS.

**Code Changes:**
- `templates/chart_plotly.html` line 16:
  ```css
  .date-range { text-align: center; margin-top: 8px; font-size: 14px; color: #555; display: none; }
  ```

**Note:** The date range is still displayed in the chart title where it belongs.

---

## Testing

### Unit Tests
- **test_999_filter.py**: Validates the 999 filtering logic with various test cases
- **test_chart_fixes.py**: Integration test that simulates chart data processing

### Test Results
```
✓ None temperature: None -> None
✓ Empty string temperature:  -> None
✓ Valid temperature: 65.5 -> 65.5
✓ 999 reading (battery/connection issue): 999 -> None
✓ 999.0 reading: 999.0 -> None
✓ Valid integer temperature: 72 -> 72.0

✅ All 999 filtering tests passed!
✅ Active tilt filtering test passed!
✅ Temperature range calculation test passed!
```

### Security Testing
- CodeQL security scan: **0 vulnerabilities found**

---

## Summary of Changed Files

1. **app.py**
   - Added 999 filtering in `chart_data_for()` endpoint (2 locations)
   - Lines 4479-4483: Temperature control data path
   - Lines 4566-4570: Regular tilt data path

2. **templates/chart_plotly.html**
   - Line 16: Hide duplicate date range div
   - Line 156: Update base range minimum to 34°F
   - Line 165: Update default range to [34, 100]
   - Lines 124-128: Filter tilts with valid data
   - Lines 214-262: Always show all 4 heating/cooling indicators
   - Line 308: Update fallback range to [34, 100]

3. **test_999_filter.py** (NEW)
   - Unit test for 999 filtering logic

4. **test_chart_fixes.py** (NEW)
   - Integration test for all chart fixes

---

## Impact

These fixes ensure:
1. ✅ Temperature charts display appropriate ranges for fermentation (34-100°F base)
2. ✅ Invalid 999 readings don't corrupt the chart or data
3. ✅ Only active tilts appear in the legend
4. ✅ All heating/cooling control indicators are always visible
5. ✅ No duplicate date ranges clutter the display

All changes are backward compatible and don't affect existing functionality.
