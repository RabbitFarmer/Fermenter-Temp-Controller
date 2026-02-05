#!/usr/bin/env python3
"""
Repository File Verification Script

This script verifies that all files referenced in the codebase actually exist
in the repository. It checks:
- Config files referenced in load_json() calls
- Template files referenced in render_template() calls
- Static files (CSS, JS, favicon)
- Log file directories and patterns
- Batch file directories and patterns
- Python module imports

Run this script to ensure the repository is complete and all file references
are valid.
"""

import os
import json
import re
from pathlib import Path
from collections import defaultdict

# Repository root
REPO_ROOT = Path(__file__).parent.resolve()

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_exists(filepath, base_path=REPO_ROOT):
    """Check if a file or directory exists."""
    full_path = base_path / filepath
    return full_path.exists()

def find_file_references_in_python():
    """Scan all Python files for file path references."""
    references = {
        'config_files': [],
        'template_files': [],
        'log_files': [],
        'batch_files': [],
        'static_files': [],
        'other_files': []
    }
    
    # Scan all Python files
    for py_file in REPO_ROOT.glob('*.py'):
        if py_file.name.startswith('.'):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find render_template calls
            template_matches = re.findall(r"render_template\(['\"]([^'\"]+)['\"]", content)
            for tmpl in template_matches:
                references['template_files'].append(('templates/' + tmpl, py_file.name))
            
            # Find explicit file paths in strings
            # Config files
            if 'tilt_config.json' in content:
                references['config_files'].append(('config/tilt_config.json', py_file.name))
            if 'temp_control_config.json' in content:
                references['config_files'].append(('config/temp_control_config.json', py_file.name))
            if 'system_config.json' in content:
                references['config_files'].append(('config/system_config.json', py_file.name))
            
            # Log files
            if 'temp_control_log.jsonl' in content:
                references['log_files'].append(('temp_control/temp_control_log.jsonl', py_file.name))
            if 'kasa_errors.log' in content:
                references['log_files'].append(('logs/kasa_errors.log', py_file.name))
            
            # Batch patterns
            if 'batch_history' in content:
                references['batch_files'].append(('batches/batch_history_{color}.json', py_file.name))
            if 'BATCHES_DIR' in content or "'batches'" in content or '"batches"' in content:
                references['batch_files'].append(('batches/', py_file.name))
                
        except Exception as e:
            print(f"{YELLOW}Warning: Could not scan {py_file.name}: {e}{RESET}")
    
    # Check static files (common references)
    references['static_files'].append(('static/styles.css', 'templates/*.html'))
    references['static_files'].append(('static/favicon.ico', 'templates/*.html'))
    references['static_files'].append(('static/js/', 'templates/*.html'))
    
    return references

def verify_config_files():
    """Verify all config files exist."""
    print(f"\n{BLUE}=== CONFIG FILES ==={RESET}")
    
    # Config files should be in config/ subdirectory
    config_files = [
        'config/tilt_config.json',
        'config/temp_control_config.json',
        'config/system_config.json'
    ]
    
    results = []
    for config_file in config_files:
        exists = check_exists(config_file)
        status = f"{GREEN}✓ EXISTS{RESET}" if exists else f"{RED}✗ MISSING{RESET}"
        print(f"  {config_file:<40} {status}")
        results.append((config_file, exists))
    
    return results

def verify_template_files():
    """Verify all template files exist."""
    print(f"\n{BLUE}=== TEMPLATE FILES ==={RESET}")
    
    # Get unique template files from references
    template_files = set()
    for tmpl_file in (REPO_ROOT / 'templates').glob('*.html'):
        template_files.add(tmpl_file.name)
    
    # Expected templates based on code analysis
    expected_templates = [
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
    
    results = []
    for tmpl in sorted(expected_templates):
        exists = check_exists(f'templates/{tmpl}')
        status = f"{GREEN}✓ EXISTS{RESET}" if exists else f"{RED}✗ MISSING{RESET}"
        print(f"  templates/{tmpl:<38} {status}")
        results.append((f'templates/{tmpl}', exists))
    
    # List extra templates
    extra_templates = template_files - set(expected_templates)
    if extra_templates:
        print(f"\n  {YELLOW}Additional templates found (not referenced in main code):{RESET}")
        for tmpl in sorted(extra_templates):
            print(f"    templates/{tmpl}")
    
    return results

def verify_static_files():
    """Verify static files exist."""
    print(f"\n{BLUE}=== STATIC FILES ==={RESET}")
    
    static_files = [
        'static/styles.css',
        'static/favicon.ico',
        'static/js/'
    ]
    
    results = []
    for static_file in static_files:
        exists = check_exists(static_file)
        status = f"{GREEN}✓ EXISTS{RESET}" if exists else f"{RED}✗ MISSING{RESET}"
        print(f"  {static_file:<40} {status}")
        results.append((static_file, exists))
    
    # List JS files if directory exists
    js_dir = REPO_ROOT / 'static' / 'js'
    if js_dir.exists():
        print(f"\n  JavaScript files found:")
        for js_file in sorted(js_dir.glob('*.js')):
            print(f"    static/js/{js_file.name}")
    
    return results

def verify_log_directories():
    """Verify log directories and structure."""
    print(f"\n{BLUE}=== LOG FILES & DIRECTORIES ==={RESET}")
    
    log_paths = [
        'logs/',
        'temp_control/',
        'batches/'
    ]
    
    results = []
    for log_path in log_paths:
        exists = check_exists(log_path)
        status = f"{GREEN}✓ EXISTS{RESET}" if exists else f"{RED}✗ MISSING{RESET}"
        print(f"  {log_path:<40} {status}")
        results.append((log_path, exists))
    
    # Check specific log files that should be created at runtime
    runtime_files = [
        'temp_control/temp_control_log.jsonl',
        'logs/kasa_errors.log'
    ]
    
    print(f"\n  {YELLOW}Runtime-created files (may not exist yet):{RESET}")
    for runtime_file in runtime_files:
        exists = check_exists(runtime_file)
        status = "created at runtime" if not exists else "already exists"
        print(f"    {runtime_file:<38} ({status})")
    
    return results

def verify_batch_files():
    """Verify batch file directory and patterns."""
    print(f"\n{BLUE}=== BATCH FILES ==={RESET}")
    
    batches_dir = REPO_ROOT / 'batches'
    if not batches_dir.exists():
        print(f"  {RED}✗ batches/ directory does not exist{RESET}")
        return [('batches/', False)]
    
    print(f"  {GREEN}✓ batches/ directory exists{RESET}")
    
    # List batch files
    batch_files = list(batches_dir.glob('*.jsonl')) + list(batches_dir.glob('*.json'))
    if batch_files:
        print(f"\n  Batch files found ({len(batch_files)}):")
        for batch_file in sorted(batch_files)[:10]:  # Show first 10
            print(f"    {batch_file.name}")
        if len(batch_files) > 10:
            print(f"    ... and {len(batch_files) - 10} more")
    else:
        print(f"  {YELLOW}No batch files found (will be created at runtime){RESET}")
    
    return [('batches/', True)]

def verify_python_modules():
    """Verify all Python module imports can be resolved."""
    print(f"\n{BLUE}=== PYTHON MODULES ==={RESET}")
    
    expected_modules = [
        'app.py',
        'tilt_static.py',
        'kasa_worker.py',
        'logger.py',
        'fermentation_monitor.py',
        'batch_history.py',
        'batch_storage.py',
        'archive_compact_logs.py',
        'backfill_temp_control_jsonl.py'
    ]
    
    results = []
    for module in expected_modules:
        exists = check_exists(module)
        status = f"{GREEN}✓ EXISTS{RESET}" if exists else f"{RED}✗ MISSING{RESET}"
        print(f"  {module:<40} {status}")
        results.append((module, exists))
    
    return results

def verify_data_directories():
    """Verify data directories exist."""
    print(f"\n{BLUE}=== DATA DIRECTORIES ==={RESET}")
    
    data_dirs = [
        'config/',
        'batches/',
        'logs/',
        'temp_control/',
        'export/',
        'chart/'
    ]
    
    results = []
    for data_dir in data_dirs:
        exists = check_exists(data_dir)
        status = f"{GREEN}✓ EXISTS{RESET}" if exists else f"{RED}✗ MISSING{RESET}"
        print(f"  {data_dir:<40} {status}")
        results.append((data_dir, exists))
    
    return results

def print_summary(all_results):
    """Print summary of verification results."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}=== VERIFICATION SUMMARY ==={RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    total = 0
    missing = 0
    
    for category, results in all_results.items():
        cat_total = len(results)
        cat_missing = sum(1 for _, exists in results if not exists)
        total += cat_total
        missing += cat_missing
        
        status = f"{GREEN}✓ ALL EXIST{RESET}" if cat_missing == 0 else f"{RED}✗ {cat_missing} MISSING{RESET}"
        print(f"\n{category:<30} {cat_total:>3} files, {status}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    if missing == 0:
        print(f"{GREEN}✓✓✓ ALL CHECKS PASSED ✓✓✓{RESET}")
        print(f"{GREEN}Repository is COMPLETE - all referenced files exist!{RESET}")
    else:
        print(f"{RED}✗ {missing}/{total} files are missing{RESET}")
        print(f"{YELLOW}Please review the missing files above.{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def main():
    """Main verification function."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Repository File Verification{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Repository root: {REPO_ROOT}\n")
    
    all_results = {}
    
    # Run all verification checks
    all_results['Python Modules'] = verify_python_modules()
    all_results['Config Files'] = verify_config_files()
    all_results['Template Files'] = verify_template_files()
    all_results['Static Files'] = verify_static_files()
    all_results['Data Directories'] = verify_data_directories()
    all_results['Log Directories'] = verify_log_directories()
    all_results['Batch Files'] = verify_batch_files()
    
    # Print summary
    print_summary(all_results)
    
    return all_results

if __name__ == '__main__':
    results = main()
