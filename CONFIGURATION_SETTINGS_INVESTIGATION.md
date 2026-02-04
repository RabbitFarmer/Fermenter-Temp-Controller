# Configuration Settings Investigation Report

**Date:** 2026-02-04  
**Issue:** Review data needs - System configuration elements usage investigation

## Executive Summary

This report investigates three configuration settings in the System Settings to determine if they are still actively used or are legacy remnants from early development.

### Quick Answer Summary

| Setting | Status | Recommendation |
|---------|--------|----------------|
| **Update Interval** | ✅ ACTIVELY USED | Keep - Critical for temperature control |
| **Chart Temperature Margin** | ⚠️ PARTIALLY USED | Keep with clarification or remove |
| **Chart Gravity Margin** | ❌ NOT USED | Remove - Pure legacy code |

---

## 1. Update Interval (minutes) - DEFAULT: 1 minute

### Current Configuration
- **Label:** "Update Interval (minutes)"
- **Description:** "Frequency of control loop checks for temperature adjustments and readings"
- **Default Value:** 1 minute (in UI) / 2 minutes (in code defaults)
- **Location:** System Settings > Main Settings tab

### Configuration Files
- **Template:** `config/system_config.json.template` (not explicitly shown but implied)
- **UI Definition:** `templates/system_config.html:145-148`
  ```html
  <label for="update_interval"><b>Update Interval (minutes)</b></label>
  <input type="number" name="update_interval" id="update_interval" value="{{ system_settings.get('update_interval','1') }}">
  ```

### Code Usage Analysis

#### ✅ ACTIVELY USED - Multiple Critical Functions

**1. Temperature Control Loop Frequency** (`app.py:3472-3477`)
```python
# Use system_cfg update_interval for temperature control loop frequency
# This is separate from tilt_logging_interval_minutes which controls fermentation logging
interval_minutes = int(system_cfg.get("update_interval", 2))
interval_seconds = max(1, interval_minutes * 60)
```
- **Impact:** Controls how often the temperature control system checks and adjusts heating/cooling
- **Default:** 2 minutes (120 seconds)
- **Purpose:** Balances responsive control with system resource usage

**2. Tilt Inactivity Timeout for Temperature Control** (`app.py:746-756`)
```python
# For temperature control, use a much shorter timeout than general monitoring
# Timeout = 2 × update_interval (2 missed readings)
# Example: 2 min update interval → 4 min timeout
try:
    update_interval_minutes = int(system_cfg.get("update_interval", 2))
except Exception:
    update_interval_minutes = 2

# Temperature control timeout: 2 missed readings
temp_control_timeout_minutes = update_interval_minutes * 2
```
- **Impact:** Safety mechanism - turns off heating/cooling if control Tilt stops responding
- **Calculation:** Timeout = 2 × update_interval
- **Example:** 2-minute interval → 4-minute timeout (2 missed readings)
- **Purpose:** Prevents runaway heating/cooling if sensor fails

**3. Periodic Temperature Reading Logging** (`app.py:360-378`)
```python
"""
Record a periodic temperature control reading in memory at update_interval frequency.

The readings are logged at the configured update_interval (default 2 minutes),
which is separate from Tilt readings that are logged at tilt_logging_interval_minutes
(default 15 minutes) for fermentation monitoring.
"""
```
- **Impact:** Determines frequency of temperature data points in the temperature control chart
- **Storage:** In-memory buffer (1440 entries = 2 days at 2-minute intervals)
- **Purpose:** Provides smooth temperature curves on charts

### Current Behavior
- **UI shows:** Default of 1 minute
- **Code uses:** Default of 2 minutes when not set
- **Discrepancy:** UI and code defaults don't match (1 vs 2 minutes)

### Status: ✅ **ACTIVELY USED - KEEP THIS SETTING**

**Rationale:**
- Critical for temperature control system responsiveness
- Directly affects safety timeout calculations
- Controls chart data density for temperature control
- Has real, measurable impact on system behavior

**Recommendation:**
- **Keep the setting** - It's essential
- **Fix the default value mismatch** - Make UI default match code default (2 minutes)
- **Consider renaming** for clarity: "Temperature Control Update Interval (minutes)"

---

## 2. Chart Temperature Margin (°F) - DEFAULT: 1.0

### Current Configuration
- **Label:** "Chart Temperature Margin (°F)"
- **Description:** "Degrees to add above/below min/max temperature on charts (default: 1.0)"
- **Default Value:** 1.0°F
- **Location:** System Settings > Main Settings tab

### Configuration Files
- **Template:** `config/system_config.json.template:10`
  ```json
  "chart_temp_margin": 1.0
  ```
- **UI Definition:** `templates/system_config.html:169-172`
  ```html
  <label for="chart_temp_margin"><b>Chart Temperature Margin (°F)</b></label>
  <input type="number" name="chart_temp_margin" id="chart_temp_margin" step="0.1" min="0" value="{{ system_settings.get('chart_temp_margin', 1.0) }}">
  ```

### Code Usage Analysis

#### ⚠️ PARTIALLY USED - Only for Regular Fermentation Charts

**1. JavaScript Variable Declaration** (`templates/chart_plotly.html:40`)
```javascript
const chartTempMargin = {{ system_settings.get('chart_temp_margin', 1.0) }};
```
- Setting is passed to chart template as a JavaScript constant

**2. Regular Fermentation/Tilt Charts - USED** (`templates/chart_plotly.html:213-214`)
```javascript
} else {
  tempMin = tempMin - chartTempMargin;
  tempMax = tempMax + chartTempMargin;
}
```
- **Applies to:** Individual Tilt color charts (Red, Blue, Green, etc.)
- **Impact:** Adds configured margin above/below min/max temperatures
- **Example:** If temps range 65-75°F with 1.0°F margin → Y-axis shows 64-76°F

**3. Temperature Control Charts - NOT USED** (`templates/chart_plotly.html:206-211`)
```javascript
if (isTempControl) {
  // Use dynamic margin for temperature control (10% or 5°F minimum)
  const dataRange = tempMax - tempMin;
  const margin = Math.max(dataRange * 0.1, 5);  // 10% of range or 5°F minimum
  tempMin = tempMin - margin;
  tempMax = tempMax + margin;
```
- **Applies to:** Temperature Control chart (Fermenter)
- **Impact:** Uses HARDCODED calculation (10% of range or 5°F minimum)
- **Ignores:** The `chart_temp_margin` setting completely
- **Example:** If temps range 65-75°F (10°F range) → margin = 1°F (10%), Y-axis shows 64-76°F

### Current Behavior
- **Works for:** Red, Blue, Green, Orange, Pink, Purple, Yellow, Black Tilt charts
- **Ignored by:** Temperature Control (Fermenter) chart
- **UI Misleading:** Implies it applies to "charts" (plural, all charts), but doesn't apply to the main Temperature Control chart

### Status: ⚠️ **PARTIALLY USED - DECISION NEEDED**

**Two Options:**

**Option A: Remove the Setting**
- Most users only look at the Temperature Control chart
- That chart already has good automatic margin logic
- Regular Tilt charts could use the same automatic logic
- Simplifies configuration

**Option B: Keep with Clarification**
- Rename to: "Fermentation Chart Temperature Margin (°F)"
- Update description: "Degrees to add above/below min/max temperature on fermentation charts (does not apply to Temperature Control chart)"
- Consider also applying it to Temperature Control chart for consistency

**Recommendation:**
- **Option A preferred** - Remove the setting and apply the automatic margin logic to all charts
- Simpler user experience, one less configuration to maintain
- Current automatic logic (10% or 5°F minimum) works well

---

## 3. Chart Gravity Margin (SG) - DEFAULT: 0.005

### Current Configuration
- **Label:** "Chart Gravity Margin (SG)"
- **Description:** "Specific gravity units to add above/below min/max on gravity charts (default: 0.005)"
- **Default Value:** 0.005
- **Location:** System Settings > Main Settings tab

### Configuration Files
- **Template:** `config/system_config.json.template:11`
  ```json
  "chart_gravity_margin": 0.005
  ```
- **UI Definition:** `templates/system_config.html:177-180`
  ```html
  <label for="chart_gravity_margin"><b>Chart Gravity Margin (SG)</b></label>
  <input type="number" name="chart_gravity_margin" id="chart_gravity_margin" step="0.001" min="0" value="{{ system_settings.get('chart_gravity_margin', 0.005) }}">
  ```

### Code Usage Analysis

#### ❌ NOT USED - Pure Legacy Code

**1. JavaScript Variable - NEVER DECLARED**
- Unlike `chartTempMargin`, there is NO corresponding JavaScript variable in `chart_plotly.html`
- Setting is saved to config but never passed to charts

**2. Gravity Range Calculation - HARDCODED VALUES** (`templates/chart_plotly.html:454-478`)
```javascript
// Calculate gravity range with new logic:
// Upper limit: max(recipe_og, actual_og) + 0.002
// Lower limit: min(recipe_fg, minimum_historical_gravity) - 0.002
const gravities = dataPoints.map(p => parseFloat(p.gravity)).filter(g => g != null && !isNaN(g));
let gravityMin = gravities.length > 0 ? Math.min(...gravities) : 0.990;
let gravityMax = gravities.length > 0 ? Math.max(...gravities) : 1.100;

// Calculate upper limit
let upperLimit = gravityMax;
if (recipeOg !== null && !isNaN(parseFloat(recipeOg))) {
  upperLimit = Math.max(upperLimit, parseFloat(recipeOg));
}
if (actualOg !== null && !isNaN(parseFloat(actualOg))) {
  upperLimit = Math.max(upperLimit, parseFloat(actualOg));
}
upperLimit += 0.002;  // ← HARDCODED, ignores chart_gravity_margin

// Calculate lower limit
let lowerLimit = gravityMin;
if (recipeFg !== null && !isNaN(parseFloat(recipeFg))) {
  lowerLimit = Math.min(lowerLimit, parseFloat(recipeFg));
}
lowerLimit -= 0.002;  // ← HARDCODED, ignores chart_gravity_margin
```

**Analysis:**
- Gravity charts ALWAYS use 0.002 SG margin
- The `chart_gravity_margin` setting (default 0.005) is completely ignored
- No code path references the setting value
- Setting exists only in config storage

**3. Test File References** (`tests/test_chart_dynamic_ranges.py`)
```python
def test_chart_calculates_dynamic_gravity_range(self):
    """Test that chart JavaScript includes dynamic gravity range calculation."""
    response = self.client.get('/chart_plotly/Fermenter')
    self.assertEqual(response.status_code, 200)
    html = response.data.decode('utf-8')
    
    # Check for gravity range calculation logic
    self.assertIn('gravityMin - chartGravityMargin', html)  # ← TEST FAILS
    self.assertIn('gravityMax + chartGravityMargin', html)  # ← TEST FAILS
```
- Test file expects `chartGravityMargin` to exist and be used
- **This test would FAIL** if run because the code never uses this variable

### Current Behavior
- **Setting is stored** in system_config.json
- **Setting is displayed** in System Settings UI
- **Setting is completely ignored** by all chart rendering code
- **Hardcoded 0.002** is always used regardless of configuration

### Status: ❌ **NOT USED - LEGACY CODE**

**Evidence:**
1. No JavaScript variable declared in chart template
2. Chart code uses hardcoded 0.002 values
3. No code path references the setting
4. Test file expectations don't match reality

**Recommendation:**
- **Remove the setting entirely:**
  1. Remove from `templates/system_config.html` (lines 175-183)
  2. Remove from `config/system_config.json.template` (line 11)
  3. Remove from `app.py` update_system_config save logic (line 3698)
  4. Update or remove test expectations in `tests/test_chart_dynamic_ranges.py`
  
- **Alternative:** Implement the feature properly
  - Add JavaScript variable to `chart_plotly.html`
  - Replace hardcoded 0.002 with `chartGravityMargin`
  - Make the setting actually functional
  - However, 0.002 works well, so removal is simpler

---

## Summary and Recommendations

### Update Interval ✅ KEEP
- **Status:** Actively used, critical system function
- **Action:** Keep the setting, fix default value mismatch (change UI default from 1 to 2 minutes)
- **Optional:** Rename to "Temperature Control Update Interval" for clarity

### Chart Temperature Margin ⚠️ DECISION NEEDED
- **Status:** Used for fermentation charts only, not temperature control
- **Recommended Action:** Remove setting and use automatic margin logic for all charts
- **Alternative:** Keep with clearer description that it doesn't apply to Temperature Control

### Chart Gravity Margin ❌ REMOVE
- **Status:** Pure legacy code, completely unused
- **Action:** Remove from UI, config template, and save logic
- **Impact:** None - setting never affected behavior

---

## Implementation Notes

### If Removing Chart Gravity Margin

**Files to Modify:**
1. `templates/system_config.html` - Remove form field (lines ~175-183)
2. `config/system_config.json.template` - Remove setting (line 11)
3. `app.py` - Remove from update_system_config (line 3698)
4. `tests/test_chart_dynamic_ranges.py` - Update test expectations

**Backward Compatibility:**
- Old config files with `chart_gravity_margin` will continue to work
- Setting will be loaded but ignored (as it already is)
- No breaking changes for existing installations

### If Removing Chart Temperature Margin

**Files to Modify:**
1. `templates/system_config.html` - Remove form field (lines ~169-173)
2. `config/system_config.json.template` - Remove setting (line 10)
3. `app.py` - Remove from update_system_config (line 3697)
4. `templates/chart_plotly.html` - Remove chartTempMargin variable and usage
5. Apply automatic margin logic to all charts (copy temp control logic to fermentation charts)

### If Fixing Update Interval Default

**Files to Modify:**
1. `templates/system_config.html:148` - Change default from '1' to '2'
   ```html
   <!-- Before -->
   value="{{ system_settings.get('update_interval','1') }}"
   
   <!-- After -->
   value="{{ system_settings.get('update_interval','2') }}"
   ```

---

## Testing Recommendations

After any changes:
1. Test system config page loads correctly
2. Test config updates save properly
3. Test temperature control charts render correctly
4. Test fermentation charts render correctly
5. Test that temperature control loop uses correct interval
6. Verify backward compatibility with existing config files

---

## Appendix: Configuration Setting Lifecycle

### How Settings Flow Through the System

1. **Default Definition**
   - Code defaults in `app.py` (e.g., `system_cfg.get("update_interval", 2)`)
   - Template defaults in `config/system_config.json.template`
   - UI defaults in `templates/system_config.html` form values

2. **User Configuration**
   - User edits in System Settings UI
   - POST to `/update_system_config` endpoint
   - Saved to `system_config.json`

3. **Runtime Usage**
   - Loaded into `system_cfg` global dict at startup
   - Accessed throughout application via `system_cfg.get(key, default)`
   - Passed to templates via render context

4. **Chart Rendering**
   - Settings passed to JavaScript in chart template
   - JavaScript uses values to calculate chart parameters
   - Applied to Plotly chart configuration

### Discovery: Broken Links

During investigation, discovered that `chart_gravity_margin`:
- Exists in configuration storage (Step 1-3) ✓
- Never reaches chart rendering (Step 4) ✗
- Missing JavaScript variable declaration
- Hardcoded values used instead

---

**Report Generated:** 2026-02-04  
**Prepared by:** GitHub Copilot Agent  
**Issue Reference:** Review data needs
