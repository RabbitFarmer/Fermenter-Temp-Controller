# Configuration Settings Usage - Visual Summary

## Quick Reference Chart

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SYSTEM CONFIGURATION SETTINGS                            │
│                         Investigation Results                                │
└─────────────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════╗
║ 1. UPDATE INTERVAL (minutes) - Default: 1 min (UI) / 2 min (code)        ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ Status: ✅ ACTIVELY USED                                                  ║
║                                                                            ║
║ Config Flow:                                                               ║
║   system_config.json → system_cfg → periodic_temp_control()              ║
║                                                                            ║
║ Where Used:                                                                ║
║   ┌────────────────────────────────────────────────────────────────┐     ║
║   │ 1. Temperature Control Loop Frequency                          │     ║
║   │    • Runs every `update_interval` minutes                      │     ║
║   │    • Controls heating/cooling check frequency                  │     ║
║   │    • Default: Every 2 minutes                                  │     ║
║   │    File: app.py:3472-3477                                      │     ║
║   └────────────────────────────────────────────────────────────────┘     ║
║                                                                            ║
║   ┌────────────────────────────────────────────────────────────────┐     ║
║   │ 2. Tilt Inactivity Safety Timeout                             │     ║
║   │    • Timeout = 2 × update_interval                             │     ║
║   │    • Turns off plugs if Tilt stops responding                  │     ║
║   │    • Example: 2 min interval → 4 min timeout                   │     ║
║   │    File: app.py:746-756                                        │     ║
║   └────────────────────────────────────────────────────────────────┘     ║
║                                                                            ║
║   ┌────────────────────────────────────────────────────────────────┐     ║
║   │ 3. Periodic Temperature Reading Logging                        │     ║
║   │    • Logs temp reading at `update_interval` frequency          │     ║
║   │    • Creates smooth curves on temperature charts               │     ║
║   │    • Stored in memory buffer (1440 entries)                    │     ║
║   │    File: app.py:360-378                                        │     ║
║   └────────────────────────────────────────────────────────────────┘     ║
║                                                                            ║
║ ⚠️  ISSUE FOUND: UI default (1) doesn't match code default (2)            ║
║                                                                            ║
║ Recommendation: KEEP - Critical for system operation                      ║
║                 FIX - Change UI default from 1 to 2 minutes               ║
╚═══════════════════════════════════════════════════════════════════════════╝


╔═══════════════════════════════════════════════════════════════════════════╗
║ 2. CHART TEMPERATURE MARGIN (°F) - Default: 1.0                          ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ Status: ⚠️  PARTIALLY USED                                                ║
║                                                                            ║
║ Config Flow:                                                               ║
║   system_config.json → templates → JavaScript chartTempMargin            ║
║                                                                            ║
║ Where Used:                                                                ║
║   ┌────────────────────────────────────────────────────────────────┐     ║
║   │ ✅ Regular Fermentation Charts (Tilt Colors)                   │     ║
║   │    • Red, Blue, Green, Orange, Pink, Purple, Yellow, Black     │     ║
║   │    • Adds margin above/below min/max temps                     │     ║
║   │    • Formula: [tempMin - margin, tempMax + margin]             │     ║
║   │    • File: chart_plotly.html:213-214                           │     ║
║   │    • Example: 65-75°F + 1.0° margin → Y-axis: 64-76°F          │     ║
║   └────────────────────────────────────────────────────────────────┘     ║
║                                                                            ║
║   ┌────────────────────────────────────────────────────────────────┐     ║
║   │ ❌ Temperature Control Chart (Fermenter)                       │     ║
║   │    • IGNORES the setting completely                            │     ║
║   │    • Uses hardcoded automatic margin instead                   │     ║
║   │    • Formula: max(dataRange × 0.1, 5°F)                        │     ║
║   │    • File: chart_plotly.html:206-211                           │     ║
║   │    • Example: 65-75°F (10° range) → 1° margin (10%)            │     ║
║   └────────────────────────────────────────────────────────────────┘     ║
║                                                                            ║
║ ⚠️  ISSUE: Setting name implies all charts, but doesn't apply to main     ║
║           temperature control chart (the one most users view)            ║
║                                                                            ║
║ Recommendations:                                                           ║
║   Option A (Preferred): REMOVE setting, use auto margin for all charts   ║
║   Option B: KEEP but rename to "Fermentation Chart Temp Margin"          ║
╚═══════════════════════════════════════════════════════════════════════════╝


╔═══════════════════════════════════════════════════════════════════════════╗
║ 3. CHART GRAVITY MARGIN (SG) - Default: 0.005                            ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ Status: ❌ NOT USED - LEGACY CODE                                         ║
║                                                                            ║
║ Config Flow (broken):                                                      ║
║   system_config.json → saved but NEVER USED                               ║
║                                                                            ║
║ Where It Should Be Used (but isn't):                                       ║
║   ┌────────────────────────────────────────────────────────────────┐     ║
║   │ ❌ Gravity Range Calculation                                    │     ║
║   │    • Setting is saved to config file                           │     ║
║   │    • Setting is displayed in UI                                │     ║
║   │    • Setting is NEVER passed to chart JavaScript               │     ║
║   │    • No chartGravityMargin variable exists                     │     ║
║   │    • Hardcoded 0.002 always used instead                       │     ║
║   │    • File: chart_plotly.html:469, 476                          │     ║
║   └────────────────────────────────────────────────────────────────┘     ║
║                                                                            ║
║ Code Evidence:                                                             ║
║   Expected:   const chartGravityMargin = {{ ... }};  ← MISSING           ║
║   Expected:   gravityMin - chartGravityMargin        ← MISSING           ║
║   Expected:   gravityMax + chartGravityMargin        ← MISSING           ║
║                                                                            ║
║   Actual:     upperLimit += 0.002;  ← HARDCODED                          ║
║   Actual:     lowerLimit -= 0.002;  ← HARDCODED                          ║
║                                                                            ║
║ Impact of Setting:                                                         ║
║   • User changes value: NO EFFECT on charts                               ║
║   • Default 0.005 vs hardcoded 0.002: Charts use 0.002                   ║
║   • Complete disconnect between config and usage                          ║
║                                                                            ║
║ Recommendation: REMOVE - Pure legacy code from early development          ║
╚═══════════════════════════════════════════════════════════════════════════╝


┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPARISON MATRIX                                    │
├──────────────────────┬──────────────┬──────────────┬─────────────────────────┤
│ Setting              │ Status       │ Impact       │ Recommendation          │
├──────────────────────┼──────────────┼──────────────┼─────────────────────────┤
│ update_interval      │ ✅ USED      │ HIGH         │ KEEP + fix default      │
│ chart_temp_margin    │ ⚠️  PARTIAL  │ MEDIUM       │ REMOVE or clarify       │
│ chart_gravity_margin │ ❌ NOT USED  │ NONE         │ REMOVE                  │
└──────────────────────┴──────────────┴──────────────┴─────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                    CODE REFERENCE QUICK LINKS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Configuration UI:     templates/system_config.html                          │
│   • update_interval:       lines 145-148                                    │
│   • chart_temp_margin:     lines 169-172                                    │
│   • chart_gravity_margin:  lines 177-180                                    │
│                                                                              │
│ Configuration Save:   app.py                                                 │
│   • update_system_config:  line 3686                                        │
│   • chart_temp_margin:     line 3697                                        │
│   • chart_gravity_margin:  line 3698                                        │
│                                                                              │
│ Update Interval Usage:                                                       │
│   • Control loop:          app.py:3472-3477                                 │
│   • Safety timeout:        app.py:746-756                                   │
│   • Logging frequency:     app.py:360-378                                   │
│                                                                              │
│ Chart Margin Usage:                                                          │
│   • Temp margin (used):    chart_plotly.html:213-214                        │
│   • Temp margin (ignored): chart_plotly.html:206-211                        │
│   • Gravity (hardcoded):   chart_plotly.html:469, 476                       │
│                                                                              │
│ Config Template:      config/system_config.json.template                    │
│   • chart_temp_margin:     line 10                                          │
│   • chart_gravity_margin:  line 11                                          │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEXT STEPS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ User Decision Required:                                                      │
│                                                                              │
│ 1. update_interval:                                                          │
│    → Keep the setting (it's critical)                                       │
│    → Fix UI default from 1 to 2 minutes to match code                       │
│                                                                              │
│ 2. chart_temp_margin:                                                        │
│    → Option A: Remove setting, use auto margin for all charts (simpler)     │
│    → Option B: Keep setting, clarify it only applies to fermentation charts │
│                                                                              │
│ 3. chart_gravity_margin:                                                     │
│    → Remove setting (it's completely unused legacy code)                    │
│                                                                              │
│ After Decision:                                                              │
│    • Update affected files (listed in detailed report)                      │
│    • Test system config save/load                                           │
│    • Verify charts render correctly                                         │
│    • Check backward compatibility with old config files                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File Impact Summary

If you decide to clean up the unused/misleading settings:

### Remove chart_gravity_margin
- [ ] `templates/system_config.html` - Remove form field
- [ ] `config/system_config.json.template` - Remove from template
- [ ] `app.py` - Remove from update_system_config function
- [ ] `tests/test_chart_dynamic_ranges.py` - Update test expectations

### Remove chart_temp_margin (if choosing Option A)
- [ ] `templates/system_config.html` - Remove form field
- [ ] `config/system_config.json.template` - Remove from template
- [ ] `app.py` - Remove from update_system_config function
- [ ] `templates/chart_plotly.html` - Remove variable and apply auto margin to all charts

### Fix update_interval default
- [ ] `templates/system_config.html:148` - Change default from '1' to '2'

## Backward Compatibility Notes

✅ All changes are backward compatible:
- Removing settings won't break existing installations
- Old config files will load successfully (unused values ignored)
- Charts will continue to work with hardcoded or automatic margins
- No database migrations needed (JSON-based config)
