#!/usr/bin/env python3
"""
Test that temperature control chart shows heating/cooling as connected line traces.

This test verifies the fix for the issue where heating/cooling state changes
should be displayed as line charts connecting successive data points, rather
than scattered markers that "retreat to base position then jump up again".
"""

import os
import re

def test_temp_control_chart_lines():
    """Verify that heating/cooling traces use lines+markers mode and have line configurations"""
    
    template_path = 'templates/chart_plotly.html'
    
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    print("Temperature Control Chart Line Test")
    print("=" * 70)
    print(f"Template: {template_path}")
    print()
    
    # Check that we're combining events and sorting them
    heating_events_pattern = r"const heatingEvents = \[\.\.\.heatingOnEvents, \.\.\.heatingOffEvents\]\.sort"
    cooling_events_pattern = r"const coolingEvents = \[\.\.\.coolingOnEvents, \.\.\.coolingOffEvents\]\.sort"
    
    has_heating_events = bool(re.search(heating_events_pattern, content))
    has_cooling_events = bool(re.search(cooling_events_pattern, content))
    
    print("✓ Checking event combination and sorting:")
    print(f"  {'✓' if has_heating_events else '✗'} Heating events combined and sorted")
    print(f"  {'✓' if has_cooling_events else '✗'} Cooling events combined and sorted")
    print()
    
    # Check that traces use 'lines+markers' mode
    # Mode appears before name in the object
    heating_trace_pattern = r"mode:\s*'lines\+markers'[^}]*name:\s*'Heating Control'"
    cooling_trace_pattern = r"mode:\s*'lines\+markers'[^}]*name:\s*'Cooling Control'"
    
    has_heating_trace = bool(re.search(heating_trace_pattern, content, re.DOTALL))
    has_cooling_trace = bool(re.search(cooling_trace_pattern, content, re.DOTALL))
    
    print("✓ Checking trace modes:")
    print(f"  {'✓' if has_heating_trace else '✗'} Heating Control uses 'lines+markers' mode")
    print(f"  {'✓' if has_cooling_trace else '✗'} Cooling Control uses 'lines+markers' mode")
    print()
    
    # Check that traces have line configurations with shape: 'linear'
    heating_line_config = bool(re.search(r"name:\s*'Heating Control'[^}]*line:\s*\{[^}]*shape:\s*'linear'", content, re.DOTALL))
    cooling_line_config = bool(re.search(r"name:\s*'Cooling Control'[^}]*line:\s*\{[^}]*shape:\s*'linear'", content, re.DOTALL))
    
    print("✓ Checking line configurations:")
    print(f"  {'✓' if heating_line_config else '✗'} Heating Control has linear line shape")
    print(f"  {'✓' if cooling_line_config else '✗'} Cooling Control has linear line shape")
    print()
    
    # Check that old marker-only traces are removed
    old_heating_on_marker = bool(re.search(r"name:\s*'Heating ON'[^}]*mode:\s*'markers'", content, re.DOTALL))
    old_heating_off_marker = bool(re.search(r"name:\s*'Heating OFF'[^}]*mode:\s*'markers'", content, re.DOTALL))
    old_cooling_on_marker = bool(re.search(r"name:\s*'Cooling ON'[^}]*mode:\s*'markers'", content, re.DOTALL))
    old_cooling_off_marker = bool(re.search(r"name:\s*'Cooling OFF'[^}]*mode:\s*'markers'", content, re.DOTALL))
    
    no_old_markers = not (old_heating_on_marker or old_heating_off_marker or old_cooling_on_marker or old_cooling_off_marker)
    
    print("✓ Checking old marker traces removed:")
    print(f"  {'✓' if not old_heating_on_marker else '✗'} No 'Heating ON' marker-only trace")
    print(f"  {'✓' if not old_heating_off_marker else '✗'} No 'Heating OFF' marker-only trace")
    print(f"  {'✓' if not old_cooling_on_marker else '✗'} No 'Cooling ON' marker-only trace")
    print(f"  {'✓' if not old_cooling_off_marker else '✗'} No 'Cooling OFF' marker-only trace")
    print()
    
    all_tests_pass = (
        has_heating_events and
        has_cooling_events and
        has_heating_trace and
        has_cooling_trace and
        heating_line_config and
        cooling_line_config and
        no_old_markers
    )
    
    if all_tests_pass:
        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nTemperature control chart will now display:")
        print("  • Heating state changes connected by a red line")
        print("  • Cooling state changes connected by a blue line")
        print("  • Lines connect directly from point to point")
        print("  • No 'retreating to base position' behavior")
        print("  • Different marker colors/shapes for ON vs OFF events")
        return True
    else:
        print("=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        return False

if __name__ == '__main__':
    success = test_temp_control_chart_lines()
    exit(0 if success else 1)
