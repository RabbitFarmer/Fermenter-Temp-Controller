#!/usr/bin/env python3
"""
Diagnostic test to understand multiprocessing start method and network access.

This test helps diagnose why KASA plug tests succeed in the main process
but fail in the worker process with "Network is unreachable" errors.
"""

import multiprocessing
import socket
import asyncio
import sys
from multiprocessing import Process, Queue

def test_network_in_worker(result_queue):
    """Test network access from within a worker process"""
    try:
        # Test 1: Can we create a socket?
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.close()
            result_queue.put({'socket_test': 'PASS', 'error': None})
        except Exception as e:
            result_queue.put({'socket_test': 'FAIL', 'error': str(e)})
        
        # Test 2: Can we resolve hostnames?
        try:
            socket.gethostbyname('localhost')
            result_queue.put({'dns_test': 'PASS', 'error': None})
        except Exception as e:
            result_queue.put({'dns_test': 'FAIL', 'error': str(e)})
        
        # Test 3: Can we connect to localhost?
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            # Try to connect to localhost on a common port
            # We don't expect this to succeed, but we want to see if we get
            # "Connection refused" (network works) vs "Network unreachable" (network broken)
            try:
                sock.connect(('127.0.0.1', 9999))
            except ConnectionRefusedError:
                result_queue.put({'localhost_test': 'PASS (network reachable)', 'error': 'Connection refused (expected)'})
            except OSError as e:
                if 'Network is unreachable' in str(e):
                    result_queue.put({'localhost_test': 'FAIL', 'error': f'Network unreachable: {e}'})
                else:
                    result_queue.put({'localhost_test': 'PASS (network reachable)', 'error': str(e)})
            sock.close()
        except Exception as e:
            result_queue.put({'localhost_test': 'FAIL', 'error': str(e)})
        
        # Test 4: Can we use asyncio event loop?
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def dummy_task():
                await asyncio.sleep(0.01)
                return "success"
            
            result = loop.run_until_complete(dummy_task())
            loop.close()
            result_queue.put({'asyncio_test': 'PASS', 'error': None, 'result': result})
        except Exception as e:
            result_queue.put({'asyncio_test': 'FAIL', 'error': str(e)})
            
    except Exception as e:
        result_queue.put({'worker_test': 'FAIL', 'error': str(e)})


def test_main_process_network():
    """Test network access from main process"""
    print("\n" + "="*70)
    print("MAIN PROCESS NETWORK TESTS")
    print("="*70)
    
    # Test 1: Socket creation
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.close()
        print("✓ Socket creation: PASS")
    except Exception as e:
        print(f"✗ Socket creation: FAIL - {e}")
    
    # Test 2: DNS resolution
    try:
        socket.gethostbyname('localhost')
        print("✓ DNS resolution: PASS")
    except Exception as e:
        print(f"✗ DNS resolution: FAIL - {e}")
    
    # Test 3: asyncio
    try:
        async def dummy():
            await asyncio.sleep(0.01)
            return "ok"
        result = asyncio.run(dummy())
        print(f"✓ AsyncIO test: PASS ({result})")
    except Exception as e:
        print(f"✗ AsyncIO test: FAIL - {e}")


def test_worker_process_network(start_method):
    """Test network access from worker process with specified start method"""
    print("\n" + "="*70)
    print(f"WORKER PROCESS NETWORK TESTS (start_method='{start_method}')")
    print("="*70)
    
    result_queue = Queue()
    
    # Start worker process
    proc = Process(target=test_network_in_worker, args=(result_queue,))
    proc.start()
    proc.join(timeout=10)
    
    if proc.is_alive():
        print("✗ Worker process hung - terminating")
        proc.terminate()
        return False
    
    # Collect results
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    
    # Display results
    all_passed = True
    for result in results:
        for test_name, status in result.items():
            if test_name == 'error':
                continue
            error = result.get('error')
            if status == 'PASS' or 'PASS' in str(status):
                print(f"✓ {test_name}: {status}")
                if error:
                    print(f"  └─ Note: {error}")
            else:
                print(f"✗ {test_name}: {status}")
                if error:
                    print(f"  └─ Error: {error}")
                all_passed = False
    
    return all_passed


def main():
    print("="*70)
    print("KASA PLUG NETWORK DIAGNOSTICS")
    print("="*70)
    print("\nThis test diagnoses why KASA plug tests work in the main process")
    print("but fail in the worker process with 'Network is unreachable' errors.")
    print("="*70)
    
    # Show current Python version and platform
    print(f"\nPython version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Show available multiprocessing start methods
    print(f"\nAvailable multiprocessing start methods: {multiprocessing.get_all_start_methods()}")
    print(f"Current start method: {multiprocessing.get_start_method(allow_none=True) or 'Not set'}")
    
    # Test main process
    test_main_process_network()
    
    # Test with current/default start method
    current_method = multiprocessing.get_start_method(allow_none=True)
    if current_method:
        worker_passed = test_worker_process_network(current_method)
    else:
        # Test with default for this platform
        default_method = multiprocessing.get_all_start_methods()[0]
        print(f"\nNo start method set, testing with platform default: '{default_method}'")
        
        # Need to set it to test
        try:
            multiprocessing.set_start_method(default_method, force=True)
        except RuntimeError:
            pass
        
        worker_passed = test_worker_process_network(default_method)
    
    # If spawn was used and failed, try fork
    if not worker_passed and 'fork' in multiprocessing.get_all_start_methods():
        print("\n" + "!"*70)
        print("Worker process network tests failed!")
        print("Attempting retry with 'fork' start method...")
        print("!"*70)
        
        try:
            multiprocessing.set_start_method('fork', force=True)
            worker_passed_fork = test_worker_process_network('fork')
            
            if worker_passed_fork:
                print("\n" + "="*70)
                print("✓ SOLUTION FOUND!")
                print("="*70)
                print("\nNetwork access works with 'fork' start method but not with")
                print("the default start method. This explains the KASA plug failures.")
                print("\nRECOMMENDATION: Set multiprocessing start method to 'fork'")
                print("in app.py before creating the worker process:")
                print("\n  import multiprocessing")
                print("  multiprocessing.set_start_method('fork')")
                print("="*70)
        except Exception as e:
            print(f"\nCould not test 'fork' method: {e}")
    
    print("\n" + "="*70)
    print("DIAGNOSTIC COMPLETE")
    print("="*70)
    
    if worker_passed:
        print("\n✓ Worker process has network access")
        print("  → Issue is likely in the event loop handling, not network access")
    else:
        print("\n✗ Worker process does NOT have network access")
        print("  → This is the root cause of 'Network is unreachable' errors")
        print("  → The persistent event loop fix helps, but start method matters too")


if __name__ == "__main__":
    main()
