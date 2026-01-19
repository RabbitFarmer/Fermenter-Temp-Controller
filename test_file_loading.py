#!/usr/bin/env python3
"""
Integration test to verify all files referenced in code can be loaded.

This test simulates application startup to ensure:
1. All Python modules can be imported
2. All configuration files can be loaded (or have proper fallbacks)
3. All template files exist and can be found
4. All static files exist
5. All data directories exist and are writable
"""

import os
import sys
import json
from pathlib import Path

# Add repository root to path
REPO_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

def test_python_imports():
    """Test that all Python modules can be imported."""
    print("\n=== Testing Python Module Imports ===")
    
    modules_to_test = [
        'tilt_static',
        'kasa_worker',
        'logger',
        'fermentation_monitor',
        'batch_history',
        'batch_storage',
        'archive_compact_logs',
        'backfill_temp_control_jsonl'
    ]
    
    failed = []
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
            failed.append(module_name)
    
    if failed:
        print(f"\n❌ {len(failed)} modules failed to import: {failed}")
        return False
    else:
        print("\n✓ All modules imported successfully")
        return True

def test_tilt_static_data():
    """Test that tilt_static.py has the required data."""
    print("\n=== Testing Tilt Static Data ===")
    
    try:
        from tilt_static import TILT_UUIDS, COLOR_MAP
        
        # Check TILT_UUIDS
        if not TILT_UUIDS:
            print("✗ TILT_UUIDS is empty")
            return False
        
        print(f"✓ TILT_UUIDS loaded with {len(TILT_UUIDS)} entries")
        
        # Check COLOR_MAP
        if not COLOR_MAP:
            print("✗ COLOR_MAP is empty")
            return False
        
        print(f"✓ COLOR_MAP loaded with {len(COLOR_MAP)} colors")
        
        # Verify expected colors
        expected_colors = ['Red', 'Green', 'Black', 'Purple', 'Orange', 'Blue', 'Yellow', 'Pink']
        tilt_colors = list(TILT_UUIDS.values())
        
        missing_colors = set(expected_colors) - set(tilt_colors)
        if missing_colors:
            print(f"⚠ Missing expected colors: {missing_colors}")
        
        print(f"✓ Tilt colors available: {', '.join(sorted(set(tilt_colors)))}")
        return True
        
    except Exception as e:
        print(f"✗ Error loading tilt_static: {e}")
        return False

def test_config_file_loading():
    """Test that config files can be loaded with fallbacks."""
    print("\n=== Testing Config File Loading ===")
    
    # This mimics the load_json function from app.py
    def load_json(path, fallback):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return fallback
    
    config_files = {
        'config/tilt_config.json': {},
        'config/temp_control_config.json': {},
        'config/system_config.json': {}
    }
    
    all_passed = True
    for config_path, fallback in config_files.items():
        result = load_json(config_path, fallback)
        
        if result == fallback:
            print(f"○ {config_path} - using fallback (expected for fresh install)")
        else:
            print(f"✓ {config_path} - loaded successfully")
    
    # Check template configs exist
    template_configs = [
        'tilt_config.json',
        'temp_control_config.json',
        'system_config.json'
    ]
    
    for config_file in template_configs:
        if os.path.exists(config_file):
            print(f"✓ Template config exists: {config_file}")
        else:
            print(f"✗ Template config missing: {config_file}")
            all_passed = False
    
    return all_passed

def test_template_files():
    """Test that all template files exist."""
    print("\n=== Testing Template Files ===")
    
    templates_dir = REPO_ROOT / 'templates'
    if not templates_dir.exists():
        print(f"✗ Templates directory does not exist: {templates_dir}")
        return False
    
    required_templates = [
        'maindisplay.html',
        'system_config.html',
        'tilt_config.html',
        'batch_settings.html',
        'temp_control_config.html',
        'temp_report_select.html',
        'temp_report_display.html',
        'kasa_scan_results.html',
        'chart_plotly.html'
    ]
    
    missing = []
    for template in required_templates:
        template_path = templates_dir / template
        if template_path.exists():
            print(f"✓ {template}")
        else:
            print(f"✗ {template} - MISSING")
            missing.append(template)
    
    if missing:
        print(f"\n❌ {len(missing)} templates missing: {missing}")
        return False
    else:
        print(f"\n✓ All {len(required_templates)} required templates exist")
        return True

def test_static_files():
    """Test that static files exist."""
    print("\n=== Testing Static Files ===")
    
    static_files = [
        'static/styles.css',
        'static/favicon.ico',
        'static/js/'
    ]
    
    all_passed = True
    for static_file in static_files:
        static_path = REPO_ROOT / static_file
        if static_path.exists():
            print(f"✓ {static_file}")
        else:
            print(f"✗ {static_file} - MISSING")
            all_passed = False
    
    # List JS files
    js_dir = REPO_ROOT / 'static' / 'js'
    if js_dir.exists():
        js_files = list(js_dir.glob('*.js'))
        print(f"✓ Found {len(js_files)} JavaScript files")
    
    return all_passed

def test_data_directories():
    """Test that data directories exist and are writable."""
    print("\n=== Testing Data Directories ===")
    
    required_dirs = [
        'config',
        'batches',
        'logs',
        'temp_control',
        'export',
        'chart'
    ]
    
    all_passed = True
    for dir_name in required_dirs:
        dir_path = REPO_ROOT / dir_name
        
        # Check existence
        if not dir_path.exists():
            print(f"✗ {dir_name}/ - MISSING")
            all_passed = False
            continue
        
        # Check if writable
        test_file = dir_path / '.test_write'
        try:
            test_file.write_text('test')
            test_file.unlink()
            print(f"✓ {dir_name}/ - exists and writable")
        except Exception as e:
            print(f"⚠ {dir_name}/ - exists but not writable: {e}")
            all_passed = False
    
    return all_passed

def test_flask_app_imports():
    """Test that Flask app can be imported without errors."""
    print("\n=== Testing Flask App Import ===")
    
    try:
        # This will execute app.py's module-level code
        # We'll capture any import errors
        import app
        print("✓ app.py imported successfully")
        
        # Check that Flask app was created
        if hasattr(app, 'app'):
            print("✓ Flask app object created")
        else:
            print("✗ Flask app object not found")
            return False
        
        # Check key constants are defined
        constants_to_check = ['LOG_PATH', 'BATCHES_DIR', 'TILT_CONFIG_FILE']
        for const in constants_to_check:
            if hasattr(app, const):
                print(f"✓ Constant defined: {const} = {getattr(app, const)}")
            else:
                print(f"✗ Constant missing: {const}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error importing app.py: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Repository File Loading Integration Test")
    print("=" * 60)
    print(f"Repository root: {REPO_ROOT}")
    
    tests = [
        ("Python Module Imports", test_python_imports),
        ("Tilt Static Data", test_tilt_static_data),
        ("Config File Loading", test_config_file_loading),
        ("Template Files", test_template_files),
        ("Static Files", test_static_files),
        ("Data Directories", test_data_directories),
        ("Flask App Import", test_flask_app_imports)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results[test_name] = passed
        except Exception as e:
            print(f"\n❌ Test '{test_name}' raised exception: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<40} {status}")
    
    print("=" * 60)
    if failed == 0:
        print(f"✓✓✓ ALL {total} TESTS PASSED ✓✓✓")
        print("Repository file structure is complete and valid!")
        return 0
    else:
        print(f"❌ {failed}/{total} TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
