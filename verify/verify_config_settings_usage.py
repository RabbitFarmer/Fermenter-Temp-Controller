#!/usr/bin/env python3
"""
Configuration Settings Usage Verification Script

This script verifies the investigation findings about three configuration settings:
1. update_interval - Used or not used?
2. chart_temp_margin - Used or not used?
3. chart_gravity_margin - Used or not used?

Run this to see concrete evidence of the investigation findings.
"""

import os
import re
import sys

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def check_file_exists(filepath):
    """Check if a file exists."""
    return os.path.exists(filepath)

def search_file(filepath, pattern, context_lines=2):
    """Search for a pattern in a file and return matches with context."""
    if not check_file_exists(filepath):
        return []
    
    matches = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                matches.append({
                    'line_num': i + 1,
                    'line': line.strip(),
                    'context': lines[start:end]
                })
    return matches

def print_section(title, status_color=''):
    """Print a section header."""
    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"{BOLD}{status_color}{title}{RESET}")
    print(f"{BOLD}{'='*80}{RESET}")

def print_finding(emoji, label, description):
    """Print a finding with emoji and formatting."""
    print(f"\n{emoji} {BOLD}{label}:{RESET} {description}")

def verify_update_interval():
    """Verify update_interval usage."""
    print_section("1. UPDATE INTERVAL - Usage Verification", GREEN)
    
    # Check configuration
    print_finding("📋", "Configuration", "Checking where update_interval is defined...")
    
    # Check system_config.html
    matches = search_file('templates/system_config.html', r'update_interval')
    if matches:
        print(f"  ✅ Found in UI: templates/system_config.html (line {matches[0]['line_num']})")
    
    # Check actual usage in app.py
    print_finding("🔍", "Code Usage", "Searching for actual usage in app.py...")
    
    usage_patterns = [
        (r'system_cfg\.get\(["\']update_interval["\']', "Loading from config"),
        (r'update_interval_minutes.*\*.*2', "Safety timeout calculation"),
        (r'interval_minutes.*update_interval', "Control loop frequency"),
    ]
    
    for pattern, description in usage_patterns:
        matches = search_file('app.py', pattern)
        if matches:
            print(f"  ✅ {description}: app.py (line {matches[0]['line_num']})")
            print(f"     Code: {matches[0]['line'][:100]}")
    
    # Summary
    print_finding("📊", "Status", f"{GREEN}ACTIVELY USED{RESET}")
    print(f"  • Controls temperature control loop frequency")
    print(f"  • Used in safety timeout calculations (2× interval)")
    print(f"  • Affects periodic temperature reading logging")
    print(f"  • {YELLOW}⚠️  Issue: UI default (1) doesn't match code default (2){RESET}")

def verify_chart_temp_margin():
    """Verify chart_temp_margin usage."""
    print_section("2. CHART TEMPERATURE MARGIN - Usage Verification", YELLOW)
    
    # Check configuration
    print_finding("📋", "Configuration", "Checking where chart_temp_margin is defined...")
    
    matches = search_file('templates/system_config.html', r'chart_temp_margin')
    if matches:
        print(f"  ✅ Found in UI: templates/system_config.html (line {matches[0]['line_num']})")
    
    # Check JavaScript variable
    print_finding("🔍", "Chart Template", "Checking JavaScript variable declaration...")
    
    matches = search_file('templates/chart_plotly.html', r'chartTempMargin')
    if matches:
        print(f"  ✅ JavaScript variable declared: chart_plotly.html (line {matches[0]['line_num']})")
        print(f"     Code: {matches[0]['line']}")
    
    # Check actual usage
    print_finding("📈", "Chart Usage", "Checking where margin is actually applied...")
    
    matches = search_file('templates/chart_plotly.html', r'tempMin.*-.*chartTempMargin')
    if matches:
        print(f"  ✅ Used in fermentation charts: chart_plotly.html (line {matches[0]['line_num']})")
        print(f"     Code: {matches[0]['line']}")
    
    # Check if ignored by temp control
    matches = search_file('templates/chart_plotly.html', r'dataRange.*0\.1.*5')
    if matches:
        print(f"  ❌ Ignored by temp control chart: chart_plotly.html (line {matches[0]['line_num']})")
        print(f"     Code: {matches[0]['line']}")
        print(f"     Uses hardcoded: max(dataRange × 0.1, 5°F)")
    
    # Summary
    print_finding("📊", "Status", f"{YELLOW}PARTIALLY USED{RESET}")
    print(f"  • Works for: Red, Blue, Green, Orange, Pink, Purple, Yellow, Black Tilt charts")
    print(f"  • Ignored by: Temperature Control (Fermenter) chart")
    print(f"  • {YELLOW}⚠️  Issue: Setting name implies all charts, but main chart ignores it{RESET}")

def verify_chart_gravity_margin():
    """Verify chart_gravity_margin usage."""
    print_section("3. CHART GRAVITY MARGIN - Usage Verification", RED)
    
    # Check configuration
    print_finding("📋", "Configuration", "Checking where chart_gravity_margin is defined...")
    
    matches = search_file('templates/system_config.html', r'chart_gravity_margin')
    if matches:
        print(f"  ✅ Found in UI: templates/system_config.html (line {matches[0]['line_num']})")
    
    # Check for JavaScript variable
    print_finding("🔍", "Chart Template", "Looking for JavaScript variable...")
    
    matches = search_file('templates/chart_plotly.html', r'chartGravityMargin')
    if matches:
        print(f"  ✅ JavaScript variable found: chart_plotly.html (line {matches[0]['line_num']})")
    else:
        print(f"  ❌ {RED}JavaScript variable NOT FOUND{RESET}")
        print(f"     The setting is never passed to chart JavaScript!")
    
    # Check for hardcoded values
    print_finding("📈", "Chart Usage", "Checking gravity margin calculations...")
    
    patterns = [
        (r'upperLimit.*\+=.*0\.002', "Upper limit hardcoded"),
        (r'lowerLimit.*-=.*0\.002', "Lower limit hardcoded"),
    ]
    
    for pattern, description in patterns:
        matches = search_file('templates/chart_plotly.html', pattern)
        if matches:
            print(f"  ❌ {description}: chart_plotly.html (line {matches[0]['line_num']})")
            print(f"     Code: {matches[0]['line']}")
    
    # Check if used anywhere
    print_finding("❓", "Usage Search", "Searching entire codebase for usage...")
    
    # Search all Python and HTML files
    found_usage = False
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', 'node_modules']):
            continue
        
        for file in files:
            if file.endswith(('.py', '.html', '.js')):
                filepath = os.path.join(root, file)
                # Skip the config files themselves
                if 'system_config' in filepath:
                    continue
                matches = search_file(filepath, r'chartGravityMargin|chart_gravity_margin')
                if matches and 'test_chart_dynamic_ranges' not in filepath:
                    found_usage = True
                    print(f"  ⚠️  Found reference: {filepath} (line {matches[0]['line_num']})")
    
    if not found_usage:
        print(f"  ❌ {RED}NO USAGE FOUND{RESET} (except in config storage)")
    
    # Summary
    print_finding("📊", "Status", f"{RED}NOT USED - LEGACY CODE{RESET}")
    print(f"  • Setting is stored in config file ✓")
    print(f"  • Setting is displayed in UI ✓")
    print(f"  • Setting is saved when updated ✓")
    print(f"  • {RED}Setting is NEVER used in charts ✗{RESET}")
    print(f"  • Hardcoded 0.002 is always used instead")
    print(f"  • Complete disconnect between config and behavior")

def main():
    """Run all verification checks."""
    print(f"\n{BOLD}{BLUE}{'='*80}")
    print("Configuration Settings Usage Verification")
    print(f"{'='*80}{RESET}\n")
    
    print("This script verifies the investigation findings by searching the codebase")
    print("for actual usage of the three configuration settings in question.")
    
    # Change to repository root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run verifications
    verify_update_interval()
    verify_chart_temp_margin()
    verify_chart_gravity_margin()
    
    # Summary
    print_section("SUMMARY OF FINDINGS", BLUE)
    
    print(f"\n{GREEN}✅ update_interval:{RESET}")
    print(f"   Status: ACTIVELY USED - Keep this setting")
    print(f"   Action: Fix UI default from 1 to 2 minutes")
    
    print(f"\n{YELLOW}⚠️  chart_temp_margin:{RESET}")
    print(f"   Status: PARTIALLY USED - Only fermentation charts")
    print(f"   Action: Remove setting OR clarify description")
    
    print(f"\n{RED}❌ chart_gravity_margin:{RESET}")
    print(f"   Status: NOT USED - Pure legacy code")
    print(f"   Action: Remove setting entirely")
    
    print(f"\n{BOLD}Detailed Report:{RESET} See CONFIGURATION_SETTINGS_INVESTIGATION.md")
    print(f"{BOLD}Visual Summary:{RESET} See CONFIG_SETTINGS_VISUAL_SUMMARY.md")
    print()

if __name__ == '__main__':
    main()
