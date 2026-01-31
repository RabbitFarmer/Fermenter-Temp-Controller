#!/usr/bin/env python3
"""
Test to verify that the Flask app starts correctly without debug mode
and responds to health checks.
"""
import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error

def test_app_startup_without_debug():
    """Test that app starts and responds without Flask debug mode"""
    print("Testing app startup WITHOUT Flask debug mode...")
    
    # Ensure FLASK_DEBUG is not set (default behavior)
    env = os.environ.copy()
    env['SKIP_BROWSER_OPEN'] = '1'
    if 'FLASK_DEBUG' in env:
        del env['FLASK_DEBUG']
    
    # Start the Flask app
    print("Starting Flask app...")
    proc = subprocess.Popen(
        [sys.executable, 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    # Wait for app to start
    max_retries = 30
    retry_delay = 1
    app_started = False
    
    print(f"Waiting for app to respond (max {max_retries} retries)...")
    for i in range(max_retries):
        try:
            response = urllib.request.urlopen('http://127.0.0.1:5000', timeout=2)
            if response.status == 200:
                print(f"✓ App responded successfully after {i+1} attempts!")
                app_started = True
                break
        except (urllib.error.URLError, ConnectionRefusedError, TimeoutError):
            if i % 5 == 0:
                print(f"  Attempt {i+1}/{max_retries}...")
            time.sleep(retry_delay)
    
    # Clean up: terminate the process
    print("Terminating Flask app...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    
    if app_started:
        print("✓ SUCCESS: App started and responded to health check without debug mode")
        return True
    else:
        print("✗ FAILED: App did not respond within timeout")
        return False

def test_app_startup_with_debug():
    """Test that app starts with Flask debug mode when FLASK_DEBUG=1"""
    print("\nTesting app startup WITH Flask debug mode...")
    
    # Set FLASK_DEBUG=1
    env = os.environ.copy()
    env['SKIP_BROWSER_OPEN'] = '1'
    env['FLASK_DEBUG'] = '1'
    
    # Start the Flask app
    print("Starting Flask app with FLASK_DEBUG=1...")
    proc = subprocess.Popen(
        [sys.executable, 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    # Wait for app to start (debug mode takes longer due to reloader)
    max_retries = 30
    retry_delay = 1
    app_started = False
    
    print(f"Waiting for app to respond (max {max_retries} retries)...")
    for i in range(max_retries):
        try:
            response = urllib.request.urlopen('http://127.0.0.1:5000', timeout=2)
            if response.status == 200:
                print(f"✓ App responded successfully after {i+1} attempts!")
                app_started = True
                break
        except (urllib.error.URLError, ConnectionRefusedError, TimeoutError):
            if i % 5 == 0:
                print(f"  Attempt {i+1}/{max_retries}...")
            time.sleep(retry_delay)
    
    # Clean up: terminate the process (and reloader child if present)
    print("Terminating Flask app...")
    try:
        # Kill process group to ensure reloader child is also killed
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except:
        proc.terminate()
    
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except:
            proc.kill()
        proc.wait()
    
    if app_started:
        print("✓ SUCCESS: App started and responded with debug mode enabled")
        return True
    else:
        print("✗ FAILED: App did not respond within timeout with debug mode")
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("Flask App Startup Test")
    print("=" * 70)
    
    # Test 1: Without debug mode (production default)
    test1_passed = test_app_startup_without_debug()
    
    # Test 2: With debug mode (development option)
    test2_passed = test_app_startup_with_debug()
    
    print("\n" + "=" * 70)
    print("Test Results:")
    print(f"  Without debug mode: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"  With debug mode: {'PASSED' if test2_passed else 'FAILED'}")
    print("=" * 70)
    
    if test1_passed and test2_passed:
        print("\n✓ All tests PASSED!")
        sys.exit(0)
    else:
        print("\n✗ Some tests FAILED!")
        sys.exit(1)
