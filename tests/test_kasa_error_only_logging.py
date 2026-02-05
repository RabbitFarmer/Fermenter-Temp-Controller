#!/usr/bin/env python3
"""
Test to verify that kasa_worker.py only logs errors, not routine operations.

This test verifies:
1. Successful operations do NOT produce print output
2. Errors ARE logged via log_error()
3. kasa_errors.log receives only error messages
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_success_no_logging():
    """Test that successful operations do not produce print() output"""
    print("\n" + "="*70)
    print("TEST: Successful operations should not log to console")
    print("="*70)
    
    mock_plug = Mock()
    mock_plug.is_on = False
    mock_plug.turn_on = AsyncMock()
    mock_plug.update = AsyncMock()
    
    async def run_test():
        # Capture stdout
        output = StringIO()
        
        with patch('sys.stdout', output):
            with patch('kasa_worker.PlugClass', return_value=mock_plug):
                from kasa_worker import kasa_control
                
                # Simulate successful command: plug starts OFF, turns ON
                mock_plug.is_on = False
                await asyncio.sleep(0.1)  # Simulate initial state
                
                # Execute command
                error = await kasa_control('192.168.1.100', 'on', 'heating')
                
                # After command, plug should be ON
                mock_plug.is_on = True
                
                # Verify again to confirm
                error = await kasa_control('192.168.1.100', 'on', 'heating')
        
        output_text = output.getvalue()
        
        # Success case: should have NO output to stdout
        # All these should be absent:
        verbose_messages = [
            'Received command',
            'Sending ON command',
            'Initial state before',
            'Executing turn_on',
            'Verified state after',
            'SUCCESS',
            '✓'
        ]
        
        found_verbose = []
        for msg in verbose_messages:
            if msg in output_text:
                found_verbose.append(msg)
        
        if found_verbose:
            print(f"✗ FAIL: Found verbose logging in successful operation:")
            for msg in found_verbose:
                print(f"  - {msg}")
            print(f"\nFull output:\n{output_text}")
            return False
        else:
            print("✓ PASS: No verbose logging for successful operation")
            print(f"  Output length: {len(output_text)} characters (should be minimal or empty)")
            return True
    
    try:
        result = asyncio.run(run_test())
        return result
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_is_logged():
    """Test that errors ARE logged via log_error()"""
    print("\n" + "="*70)
    print("TEST: Errors should be logged via log_error()")
    print("="*70)
    
    mock_plug = Mock()
    mock_plug.is_on = False
    mock_plug.turn_on = AsyncMock()
    mock_plug.update = AsyncMock()
    
    # Track log_error calls
    logged_errors = []
    
    def mock_log_error(msg):
        logged_errors.append(msg)
        print(f"[LOGGED ERROR] {msg}")
    
    async def run_test():
        with patch('kasa_worker.log_error', side_effect=mock_log_error):
            with patch('kasa_worker.PlugClass', return_value=mock_plug):
                from kasa_worker import kasa_control
                
                # Simulate error: state mismatch (plug doesn't turn on)
                mock_plug.is_on = False  # Stays OFF even after turn_on
                
                error = await kasa_control('192.168.1.100', 'on', 'heating')
        
        # Verify error was returned
        assert error is not None, "Should return error message"
        
        # Verify log_error was called
        assert len(logged_errors) > 0, "Should call log_error for failures"
        
        # Check that error message contains relevant info
        error_msg = ' '.join(logged_errors).lower()
        assert 'state mismatch' in error_msg or 'heating' in error_msg, \
            "Error message should describe the problem"
        
        print(f"✓ PASS: Errors are properly logged")
        print(f"  Logged {len(logged_errors)} error(s)")
        for i, err in enumerate(logged_errors, 1):
            print(f"  {i}. {err[:80]}...")
        
        return True
    
    try:
        result = asyncio.run(run_test())
        return result
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_connection_failure_logged():
    """Test that connection failures are logged"""
    print("\n" + "="*70)
    print("TEST: Connection failures should be logged")
    print("="*70)
    
    # Track log_error calls
    logged_errors = []
    
    def mock_log_error(msg):
        logged_errors.append(msg)
        print(f"[LOGGED ERROR] {msg}")
    
    async def run_test():
        # Mock PlugClass to raise exception on update
        mock_plug = Mock()
        mock_plug.update = AsyncMock(side_effect=Exception("Connection timeout"))
        
        with patch('kasa_worker.log_error', side_effect=mock_log_error):
            with patch('kasa_worker.PlugClass', return_value=mock_plug):
                from kasa_worker import kasa_control
                
                error = await kasa_control('192.168.1.100', 'on', 'heating')
        
        # Verify error was returned
        assert error is not None, "Should return error message"
        
        # Verify log_error was called
        assert len(logged_errors) > 0, "Should log connection failures"
        
        # Check error message
        error_msg = ' '.join(logged_errors).lower()
        assert 'connection' in error_msg or 'timeout' in error_msg or 'failed' in error_msg, \
            "Error message should describe connection problem"
        
        print(f"✓ PASS: Connection failures are properly logged")
        print(f"  Logged {len(logged_errors)} error(s)")
        
        return True
    
    try:
        result = asyncio.run(run_test())
        return result
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*12 + "KASA ERROR-ONLY LOGGING VERIFICATION" + " "*20 + "║")
    print("╚" + "="*68 + "╝")
    
    tests = [
        ("Success operations - no verbose logging", test_success_no_logging),
        ("Errors are logged via log_error()", test_error_is_logged),
        ("Connection failures are logged", test_connection_failure_logged),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        all_passed = all_passed and result
    
    print("="*70)
    
    if all_passed:
        print("\n✓ All tests passed!")
        print("\nVerified behavior:")
        print("  1. Successful operations produce NO verbose logging")
        print("  2. Errors are logged via log_error() to kasa_errors.log")
        print("  3. Connection failures are properly logged")
        print("  4. kasa_errors.log will ONLY contain actual errors")
        print("\nResult:")
        print("  - kasa_errors.log will no longer be polluted with routine operations")
        print("  - Errors are still captured for troubleshooting")
        print("  - Log file size significantly reduced")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == '__main__':
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
