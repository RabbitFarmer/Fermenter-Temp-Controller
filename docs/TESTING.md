# Testing Guide for Active Tilt Integration

This directory contains comprehensive tests for the active tilt integration functionality.

## Test Files

### 1. test_tilt_integration.py
Tests the core integration functionality:
- Configuration file loading with `og_confirmed` attribute
- Backend `update_live_tilt()` function
- Live snapshot data structure
- JavaScript function presence in templates

**Run it:**
```bash
python3 test_tilt_integration.py
```

### 2. test_live_snapshot.py
Tests the `/live_snapshot` API endpoint:
- HTTP response validation
- JSON structure verification
- Field presence and type checking
- Data value validation

**Run it:**
```bash
python3 test_live_snapshot.py
```

### 3. test_data_flow.py
Tests the complete data flow from BLE to frontend:
- BLE scan simulation
- Backend data processing
- API response structure
- Frontend data requirements
- ABV calculation validation

**Run it:**
```bash
python3 test_data_flow.py
```

## Running All Tests

To run all tests at once:

```bash
python3 test_tilt_integration.py && \
python3 test_live_snapshot.py && \
python3 test_data_flow.py
```

## Prerequisites

Install required dependencies:

```bash
pip3 install flask flask-cors bleak
```

## Expected Results

All tests should pass with output showing:
- ✓ Green checkmarks for each test
- "All tests PASSED!" message
- 100% success rate

## Test Configuration

The tests use sample configuration files in the `config/` directory:
- `config/tilt_config.json` - Sample tilt configuration with og_confirmed
- `config/system_config.json` - Basic system settings
- `config/temp_control_config.json` - Temperature control settings

These files are gitignored and safe to modify for testing.

## Understanding Test Failures

If a test fails:

1. **Check the error message** - It will indicate which assertion failed
2. **Review the test code** - Look at what's being tested
3. **Check the implementation** - Verify the code matches expectations
4. **Check configuration** - Ensure config files are properly formatted

## Adding New Tests

When adding features to the active tilt integration:

1. Add test cases to the appropriate test file
2. Follow the existing test structure
3. Use descriptive assertion messages
4. Run all tests to ensure no regressions
5. Update this README if adding new test files

## Test Coverage

Current test coverage includes:
- ✅ Configuration loading and validation
- ✅ Backend data processing
- ✅ API endpoint responses
- ✅ JavaScript function presence
- ✅ Complete data flow from BLE to frontend
- ✅ OG confirmed attribute handling
- ✅ ABV calculation accuracy

## Continuous Integration

These tests can be integrated into a CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    python3 test_tilt_integration.py
    python3 test_live_snapshot.py
    python3 test_data_flow.py
```

## Documentation

For more details on the active tilt integration, see:
- **ACTIVE_TILT_INTEGRATION.md** - Complete feature documentation
- **app.py** - Backend implementation
- **templates/maindisplay.html** - Frontend implementation

## Support

If tests fail or you encounter issues:
1. Check that all dependencies are installed
2. Verify Python version is 3.7+
3. Ensure configuration files exist in `config/` directory
4. Review error messages for specific failures
5. Check that the Flask app can start successfully
