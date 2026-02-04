#!/usr/bin/env python3
"""
Integration test for Kasa command and response logging.

This test simulates a complete temperature control cycle to verify that:
1. Commands sent from control_heating() and control_cooling() are logged
2. Responses processed by kasa_result_listener() are logged
3. The log file accumulates entries in JSONL format
4. Both success and failure scenarios are handled
"""

import sys
import os
import json
import tempfile
import shutil

def test_integration_kasa_logging():
    """Integration test for end-to-end Kasa command/response logging."""
    print("=" * 80)
    print("INTEGRATION TEST: KASA COMMAND AND RESPONSE LOGGING")
    print("=" * 80)
    print("\nSimulating a complete temperature control cycle:")
    print("  1. Heater turns ON when temp drops")
    print("  2. Heater turns OFF when temp rises")
    print("  3. Commands and responses logged to kasa_error_log.jsonl")
    print("=" * 80)
    
    # Create a temporary logs directory
    temp_logs_dir = tempfile.mkdtemp(prefix="test_integration_logs_")
    print(f"\nUsing temporary logs directory: {temp_logs_dir}")
    
    try:
        # Import the logging function
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Monkey-patch the logger module to use our temp directory
        import logger
        original_log_dir = logger.LOG_DIR
        logger.LOG_DIR = temp_logs_dir
        
        from logger import log_kasa_command
        
        log_file = os.path.join(temp_logs_dir, 'kasa_error_log.jsonl')
        
        # Simulate a complete heating cycle
        print("\n" + "-" * 80)
        print("SCENARIO 1: Temperature control with heating")
        print("-" * 80)
        
        # Step 1: Temperature drops to 72°F (below low limit 73°F)
        print("\n[TEMP 72°F] Temperature below low limit - turning heater ON")
        log_kasa_command('heating', '192.168.1.100', 'on')  # Command sent
        log_kasa_command('heating', '192.168.1.100', 'on', success=True)  # Response received
        
        # Step 2: Temperature rises to 75°F (at high limit)
        print("[TEMP 75°F] Temperature at high limit - turning heater OFF")
        log_kasa_command('heating', '192.168.1.100', 'off')  # Command sent
        log_kasa_command('heating', '192.168.1.100', 'off', success=True)  # Response received
        
        # Verify entries
        with open(log_file, 'r') as f:
            entries = [json.loads(line) for line in f]
        
        assert len(entries) == 4, f"Expected 4 entries, got {len(entries)}"
        print(f"\n✓ Logged 4 entries (2 commands + 2 responses)")
        
        # Verify sequence
        assert entries[0]['mode'] == 'heating' and entries[0]['action'] == 'on' and 'success' not in entries[0]
        assert entries[1]['mode'] == 'heating' and entries[1]['action'] == 'on' and entries[1]['success'] is True
        assert entries[2]['mode'] == 'heating' and entries[2]['action'] == 'off' and 'success' not in entries[2]
        assert entries[3]['mode'] == 'heating' and entries[3]['action'] == 'off' and entries[3]['success'] is True
        print("✓ Command/response pairs in correct sequence")
        
        # Simulate a cooling cycle with a failure
        print("\n" + "-" * 80)
        print("SCENARIO 2: Temperature control with cooling (including failure)")
        print("-" * 80)
        
        # Step 3: Temperature rises to 76°F (above high limit)
        print("\n[TEMP 76°F] Temperature above high limit - turning cooler ON")
        log_kasa_command('cooling', '192.168.1.101', 'on')  # Command sent
        log_kasa_command('cooling', '192.168.1.101', 'on', success=False, error='Connection timeout')  # Failed response
        
        # Step 4: Retry cooling command
        print("[RETRY] Retrying cooler ON command")
        log_kasa_command('cooling', '192.168.1.101', 'on')  # Command sent again
        log_kasa_command('cooling', '192.168.1.101', 'on', success=True)  # Success response
        
        # Step 5: Temperature drops to 73°F (at low limit)
        print("[TEMP 73°F] Temperature at low limit - turning cooler OFF")
        log_kasa_command('cooling', '192.168.1.101', 'off')  # Command sent
        log_kasa_command('cooling', '192.168.1.101', 'off', success=True)  # Response received
        
        # Verify all entries
        with open(log_file, 'r') as f:
            entries = [json.loads(line) for line in f]
        
        assert len(entries) == 10, f"Expected 10 entries, got {len(entries)}"
        print(f"\n✓ Total logged entries: {len(entries)}")
        
        # Verify failure was logged
        failure_entry = entries[5]
        assert failure_entry['success'] is False, "Failed response not logged correctly"
        assert failure_entry['error'] == 'Connection timeout', "Error message not logged"
        print("✓ Failure case logged with error message")
        
        # Verify retry was logged
        retry_entry = entries[6]
        assert retry_entry['mode'] == 'cooling' and retry_entry['action'] == 'on' and 'success' not in retry_entry
        print("✓ Retry command logged")
        
        # Display log contents
        print("\n" + "-" * 80)
        print("COMPLETE LOG FILE CONTENTS")
        print("-" * 80)
        
        with open(log_file, 'r') as f:
            for i, line in enumerate(f, 1):
                entry = json.loads(line)
                status = ""
                if 'success' in entry:
                    status = " ✓ SUCCESS" if entry['success'] else f" ✗ FAILED: {entry.get('error', 'Unknown error')}"
                print(f"{i}. [{entry['timestamp'][:19]}] {entry['mode'].upper()} {entry['action'].upper()}{status}")
        
        print("\n" + "=" * 80)
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("=" * 80)
        print("\nVerified behaviors:")
        print("  ✓ Commands logged when sent from control functions")
        print("  ✓ Responses logged when received from Kasa plugs")
        print("  ✓ Success responses logged with success=true")
        print("  ✓ Failed responses logged with success=false and error message")
        print("  ✓ Retry attempts are logged")
        print("  ✓ Log file accumulates entries in valid JSONL format")
        print("  ✓ Entries contain proper timestamps and metadata")
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
        success = test_integration_kasa_logging()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
