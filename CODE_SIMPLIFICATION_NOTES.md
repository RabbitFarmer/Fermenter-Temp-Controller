# Code Simplification Notes

## Current State
- `app.py`: 5,790 lines
- Growth: ~4X from original size
- Main concerns: File size, complexity, maintainability

## Areas for Future Simplification

### 1. Split app.py into Multiple Modules

**Recommendation**: Break app.py into logical modules:
- `temperature_control.py` - All temp control logic, control_heating/cooling, temperature_control_logic()
- `kasa_integration.py` - Kasa worker, result listener, plug state management
- `chart_routes.py` - Chart-related routes and data endpoints
- `batch_management.py` - Batch history, storage, monitoring
- `notification_system.py` - Email, push notifications, retry logic
- `config_routes.py` - Configuration routes and form handling
- `tilt_integration.py` - BLE scanning, Tilt detection, data processing

**Benefits**:
- Easier to navigate and maintain
- Better separation of concerns
- Each file ~500-800 lines instead of 5,790
- Easier to test individual components

**Risks**:
- Import circular dependencies need careful management
- Shared state (temp_cfg, system_cfg) needs clear ownership
- Breaking changes if done incorrectly

### 2. Reduce Redundancy in Control Logic

**Current Issue**: Multiple checks for same conditions throughout codebase

**Examples**:
- Tilt active checks scattered across multiple functions
- Redundancy/rate limiting checks duplicated for heating and cooling
- Config validation repeated in multiple routes

**Recommendation**:
- Create decorator functions for common checks (@require_active_tilt, @validate_config)
- Consolidate heating and cooling control into a single parameterized function
- Create shared validation utilities

### 3. Simplify Configuration Management

**Current Issue**: Multiple config files with overlapping settings

**Files**:
- `tilt_config.json` - Tilt settings
- `temp_control_config.json` - Temp control settings
- `system_config.json` - System settings
- `batch_settings.json` - Batch settings

**Recommendation**:
- Consider consolidating into single config with sections
- Use JSON schema for validation
- Create ConfigManager class to handle all config operations

### 4. Template Consolidation

**Current Issue**: Some templates have duplicate boilerplate

**Recommendation**:
- Create base template with common layout
- Use Jinja2 template inheritance more extensively
- Extract common components (navigation, headers) into includes

### 5. Notification System Refactoring

**Current Issue**: Notification code is complex with multiple retry queues and triggers

**Recommendation**:
- Create NotificationManager class
- Simplify trigger/arming logic
- Consolidate email and push notification handling
- Use event-driven architecture instead of multiple flags

### 6. Chart Data Pipeline

**Current Issue**: Chart data processing mixes file I/O, in-memory buffers, and event filtering

**Recommendation**:
- Create ChartDataProvider class
- Separate data collection from data presentation
- Use consistent data format throughout pipeline

### 7. Remove Unused/Legacy Code

**Areas to Review**:
- Check for unused imports
- Remove commented-out code
- Identify deprecated functions with no callers
- Remove duplicate utility functions

### 8. Type Hints and Documentation

**Recommendation**:
- Add type hints to all functions
- Use dataclasses for structured data (configs, events)
- Generate API documentation with Sphinx
- Create architecture diagram

## Implementation Strategy

### Phase 1: Low-Risk Improvements (Do First)
1. Add type hints
2. Extract small utility functions
3. Remove unused imports and commented code
4. Add docstrings where missing

### Phase 2: Medium-Risk Refactoring
1. Split routes into separate files
2. Create helper classes (ConfigManager, NotificationManager)
3. Consolidate templates

### Phase 3: High-Risk Architecture Changes (Do Last)
1. Break app.py into modules
2. Refactor shared state management
3. Redesign notification system
4. Consolidate config files

## Immediate Actions (Already Implemented)

### ✓ Separated Temperature Control Interval
- **Issue**: Single `update_interval` controlling both fermentation and temp control
- **Fix**: Added `temp_control_update_interval` (default 2 min)
- **Result**: Responsive temperature control without affecting fermentation logging
- **Lines saved**: ~0 (added feature, not removed code)
- **Clarity gained**: Much clearer separation of concerns

### ✓ Improved Chart Visualization
- **Issue**: Overly complex chart with thick lines and confusing markers
- **Fix**: Simplified to thin temperature line (1.5px) with clear markers
- **Result**: Cleaner, more readable charts
- **Lines changed**: ~30 lines in chart_plotly.html

### ✓ Enhanced Browser Autostart
- **Issue**: Unreliable browser opening at boot
- **Fix**: Better desktop detection, window manager checks, longer timeout
- **Result**: More reliable autostart
- **Lines changed**: ~40 lines in start.sh

## Guidelines for Future Development

1. **Before adding new features**: Check if existing code can be reused
2. **Keep functions focused**: Each function should do one thing well
3. **Prefer configuration over code**: Use config files instead of hardcoded values
4. **Write tests**: Especially for critical temperature control logic
5. **Document decisions**: Add comments explaining "why", not just "what"

## Metrics to Track

- Lines of code per module (target: <800)
- Cyclomatic complexity (target: <10 per function)
- Code coverage (target: >70% for critical paths)
- Load time (target: <5 seconds)

## Notes

This document should be updated as simplification work progresses. Each refactoring should:
1. Have a clear goal
2. Be tested thoroughly
3. Be backwards compatible
4. Be documented in commit messages
5. Update this file with results

## Questions for User

1. Which features are most critical? (Focus simplification efforts there)
2. Are there features that can be removed? (Dead code elimination)
3. What is the deployment environment? (Affects architecture decisions)
4. How often are updates deployed? (Affects risk tolerance for changes)
