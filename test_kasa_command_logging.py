#!/usr/bin/env python3
"""
Test for Kasa command and response logging to kasa_activity_monitoring.jsonl.

This test validates that:
1. Commands sent to Kasa plugs are logged
2. Responses from Kasa plugs are logged
3. Both success and failure cases are logged
4. Log file is in JSONL format
"""

import sys
import os
import json
import tempfile
import shutil
from datetime import datetime

def test_kasa_command_logging():
    """Test that Kasa commands and responses are logged to kasa_activity_monitoring.jsonl."""
    print("=" * 80)
    print("TEST: KASA COMMAND AND RESPONSE LOGGING")
    print("=" * 80)
    
    # Create a temporary logs directory
    temp_logs_dir = tempfile.mkdtemp(prefix="test_logs_")
    print(f"\nUsing temporary logs directory: {temp_logs_dir}")
    
    try:
        # Import the logging function
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Monkey-patch the logger module to use our temp directory
        import logger
        original_log_dir = logger.LOG_DIR
        logger.LOG_DIR = temp_logs_dir
        
        from logger import log_kasa_command
        
        log_file = os.path.join(temp_logs_dir, 'kasa_activity_monitoring.jsonl')
        
        print("\n" + "-" * 80)
        print("Test 1: Log heating command sent")
        print("-" * 80)
        log_kasa_command('heating', '192.168.1.100', 'on')
        
        # Verify the file was created
        assert os.path.exists(log_file), "Log file was not created"
        print("✓ Log file created")
        
        # Read and verify the entry
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1, f"Expected 1 line, got {len(lines)}"
        entry = json.loads(lines[0])
        
        assert entry['mode'] == 'heating', f"Expected mode='heating', got {entry['mode']}"
        assert entry['url'] == '192.168.1.100', f"Expected url='192.168.1.100', got {entry['url']}"
        assert entry['action'] == 'on', f"Expected action='on', got {entry['action']}"
        assert 'timestamp' in entry, "Missing timestamp"
        print(f"✓ Command logged: {json.dumps(entry, indent=2)}")
        
        print("\n" + "-" * 80)
        print("Test 2: Log successful response")
        print("-" * 80)
        log_kasa_command('heating', '192.168.1.100', 'on', success=True)
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
        entry = json.loads(lines[1])
        
        assert entry['success'] is True, f"Expected success=True, got {entry['success']}"
        assert 'error' not in entry or entry.get('error') is None, "Should not have error on success"
        print(f"✓ Success response logged: {json.dumps(entry, indent=2)}")
        
        print("\n" + "-" * 80)
        print("Test 3: Log failed response with error")
        print("-" * 80)
        log_kasa_command('cooling', '192.168.1.101', 'off', success=False, error='Connection timeout')
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}"
        entry = json.loads(lines[2])
        
        assert entry['mode'] == 'cooling', f"Expected mode='cooling', got {entry['mode']}"
        assert entry['success'] is False, f"Expected success=False, got {entry['success']}"
        assert entry['error'] == 'Connection timeout', f"Expected error message, got {entry.get('error')}"
        print(f"✓ Failed response logged: {json.dumps(entry, indent=2)}")
        
        print("\n" + "-" * 80)
        print("Test 4: Verify JSONL format (one valid JSON object per line)")
        print("-" * 80)
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            try:
                entry = json.loads(line)
                print(f"✓ Line {i+1} is valid JSON")
            except json.JSONDecodeError as e:
                print(f"✗ Line {i+1} is invalid JSON: {e}")
                return False
        
        print("\n" + "-" * 80)
        print("Test 5: Verify log content structure")
        print("-" * 80)
        
        with open(log_file, 'r') as f:
            for i, line in enumerate(f):
                entry = json.loads(line)
                
                # Required fields
                assert 'timestamp' in entry, f"Entry {i+1} missing timestamp"
                assert 'mode' in entry, f"Entry {i+1} missing mode"
                assert 'url' in entry, f"Entry {i+1} missing url"
                assert 'action' in entry, f"Entry {i+1} missing action"
                
                # Validate timestamp format
                try:
                    datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    print(f"✓ Entry {i+1} has valid timestamp: {entry['timestamp']}")
                except ValueError:
                    print(f"✗ Entry {i+1} has invalid timestamp: {entry['timestamp']}")
                    return False
        
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print("\nSummary:")
        print("  - Kasa commands are logged when sent")
        print("  - Kasa responses are logged when received")
        print("  - Success and failure cases both logged")
        print("  - Log file format is valid JSONL")
        print("  - All entries have required fields")
        print("=" * 80)
        
        # Restore original LOG_DIR
        logger.LOG_DIR = original_log_dir
        
        return True
        
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_logs_dir):
            shutil.rmtree(temp_logs_dir)
            print(f"\nCleaned up temporary directory: {temp_logs_dir}")

if __name__ == '__main__':
    try:
        success = test_kasa_command_logging()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
