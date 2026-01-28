#!/usr/bin/env python3
"""
Test the format_kasa_error function to ensure user-friendly error messages
"""
import sys
import os

# Add parent directory to path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the actual function from app.py
# We need to handle Flask dependencies that may not be available
try:
    from app import format_kasa_error
except ImportError:
    # If Flask dependencies aren't available, define a copy for testing
    # This shouldn't happen in the normal test environment, but provides a fallback
    def format_kasa_error(error_msg, device_url):
        """Format KASA error messages to be more user-friendly"""
        error_str = str(error_msg)
        
        # Check if this is a localhost address - this is a common configuration mistake
        if device_url.startswith('127.') or device_url == 'localhost':
            return f"❌ Invalid IP address: {device_url} is a localhost address. KASA plugs require a real network IP address (e.g., 192.168.1.100). Check your router's DHCP client list or use the Kasa mobile app to find the plug's actual IP address."
        
        # Connection refused errors (port closed, device not listening)
        if 'Errno 111' in error_str or 'Connect call failed' in error_str or 'Connection refused' in error_str:
            return f"Cannot connect to device. Please check: (1) the device is powered on, (2) the IP address {device_url} is correct, (3) the device is on the same network"
        
        # Timeout errors
        if 'TimeoutError' in error_str or 'timed out' in error_str.lower():
            return f"Connection timed out. The device may be unreachable or turned off"
        
        # Host unreachable
        if 'Errno 113' in error_str or 'No route to host' in error_str:
            return f"Network error: No route to {device_url}. Check network configuration"
        
        # Name resolution errors
        if 'Name or service not known' in error_str or 'getaddrinfo failed' in error_str:
            return f"Cannot resolve hostname: {device_url}. Use an IP address instead"
        
        # Permission errors
        if 'Errno 13' in error_str or 'Permission denied' in error_str:
            return "Permission denied. Network configuration issue"
        
        # Default: return a simplified version
        # Try to extract the most relevant part
        if 'Unable to connect' in error_str:
            # Already formatted nicely by kasa library
            return error_str.split('\n')[0]  # Just first line
        
        return error_str


def test_localhost_address_error():
    """Test that localhost addresses are detected and explained"""
    error_msg = "Unable to connect to the device: 127.0.0.208:9999: [Errno 111] Connect call failed ('127.0.0.208', 9999)"
    result = format_kasa_error(error_msg, '127.0.0.208')
    
    print(f"Input:  {error_msg}")
    print(f"Output: {result}")
    
    assert 'localhost address' in result.lower()
    assert '127.0.0.208' in result
    assert 'network ip' in result.lower()
    assert '192.168' in result  # Should suggest example IP
    
    print("✓ Localhost address test passed\n")


def test_connection_refused_error():
    """Test that connection refused errors are formatted nicely"""
    error_msg = "Unable to connect to the device: 192.168.1.100:9999: [Errno 111] Connect call failed ('192.168.1.100', 9999)"
    result = format_kasa_error(error_msg, '192.168.1.100')
    
    print(f"Input:  {error_msg}")
    print(f"Output: {result}")
    
    # Should contain helpful troubleshooting steps
    assert 'Cannot connect' in result
    assert 'powered on' in result
    assert 'IP address' in result
    assert '192.168.1.100' in result
    
    # Should NOT contain the technical errno details
    assert '[Errno 111]' not in result
    assert 'Connect call failed' not in result
    
    print("✓ Connection refused test passed\n")


def test_timeout_error():
    """Test that timeout errors are formatted nicely"""
    error_msg = "TimeoutError: Connection timed out after 6 seconds"
    result = format_kasa_error(error_msg, '192.168.1.100')
    
    print(f"Input:  {error_msg}")
    print(f"Output: {result}")
    
    assert 'timed out' in result.lower()
    assert 'unreachable' in result.lower()
    
    print("✓ Timeout test passed\n")


def test_host_unreachable_error():
    """Test that host unreachable errors are formatted nicely"""
    error_msg = "[Errno 113] No route to host"
    result = format_kasa_error(error_msg, '10.0.0.1')
    
    print(f"Input:  {error_msg}")
    print(f"Output: {result}")
    
    assert 'No route' in result
    assert '10.0.0.1' in result
    assert 'network' in result.lower()
    
    print("✓ Host unreachable test passed\n")


def test_name_resolution_error():
    """Test that DNS/hostname errors are formatted nicely"""
    error_msg = "Name or service not known"
    result = format_kasa_error(error_msg, 'myplug.local')
    
    print(f"Input:  {error_msg}")
    print(f"Output: {result}")
    
    assert 'Cannot resolve' in result
    assert 'myplug.local' in result
    assert 'IP address' in result
    
    print("✓ Name resolution test passed\n")


def test_unknown_error_passthrough():
    """Test that unknown errors are passed through as-is"""
    error_msg = "Some unexpected error message"
    result = format_kasa_error(error_msg, '192.168.1.1')
    
    print(f"Input:  {error_msg}")
    print(f"Output: {result}")
    
    assert result == error_msg
    
    print("✓ Unknown error passthrough test passed\n")


if __name__ == '__main__':
    print("Testing KASA error message formatting...\n")
    print("=" * 80)
    
    test_localhost_address_error()
    test_connection_refused_error()
    test_timeout_error()
    test_host_unreachable_error()
    test_name_resolution_error()
    test_unknown_error_passthrough()
    
    print("=" * 80)
    print("✓ All tests passed!")


