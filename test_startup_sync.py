#!/usr/bin/env python3
"""
Test script to verify plug state synchronization at startup.
This simulates the startup sync behavior without requiring actual Kasa plugs.
"""

import asyncio
import sys

# Mock the kasa_query_state function to simulate different scenarios
async def mock_kasa_query_state_success(url):
    """Mock successful query - returns ON state"""
    print(f"[MOCK] Querying {url}...")
    await asyncio.sleep(0.1)  # Simulate network delay
    is_on = True  # Simulate plug is ON
    return is_on, None

async def mock_kasa_query_state_off(url):
    """Mock successful query - returns OFF state"""
    print(f"[MOCK] Querying {url}...")
    await asyncio.sleep(0.1)
    is_on = False  # Simulate plug is OFF
    return is_on, None

async def mock_kasa_query_state_error(url):
    """Mock failed query"""
    print(f"[MOCK] Querying {url}...")
    await asyncio.sleep(0.1)
    return None, "Connection timeout"

async def mock_kasa_query_state_timeout(url):
    """Mock timeout - query takes too long"""
    print(f"[MOCK] Querying {url}...")
    await asyncio.sleep(10)  # Simulate long delay that will cause timeout
    return True, None  # This won't be reached due to timeout

def test_sync_logic(kasa_query_state_func, test_name, use_timeout=False):
    """Test the sync logic with different scenarios"""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")
    
    # Simulate temp_cfg
    temp_cfg = {
        "heating_plug": "192.168.1.100",
        "cooling_plug": "192.168.1.101",
        "enable_heating": True,
        "enable_cooling": True,
        "heater_on": True,  # Old state from config file
        "cooler_on": True,  # Old state from config file
    }
    
    print(f"\nInitial state (from config file):")
    print(f"  heater_on: {temp_cfg['heater_on']}")
    print(f"  cooler_on: {temp_cfg['cooler_on']}")
    
    # Simulate sync function
    heating_url = temp_cfg.get("heating_plug", "")
    cooling_url = temp_cfg.get("cooling_plug", "")
    enable_heating = temp_cfg.get("enable_heating", False)
    enable_cooling = temp_cfg.get("enable_cooling", False)
    
    print(f"\nSyncing plug states...")
    
    # Helper function to query plug state with timeout
    async def query_plug_with_timeout(url, plug_name):
        """Query a plug's state with timeout. Returns (is_on, error) or raises TimeoutError."""
        # Timeout set to 7 seconds to allow internal kasa_query_state timeout (6s) to complete
        # For testing with mock timeout, use shorter timeout
        timeout_val = 1.0 if use_timeout else 7.0
        return await asyncio.wait_for(kasa_query_state_func(url), timeout=timeout_val)
    
    # Query heating plug state with timeout
    if enable_heating and heating_url:
        try:
            is_on, error = asyncio.run(query_plug_with_timeout(heating_url, "heating"))
            if error is None:
                temp_cfg["heater_on"] = is_on
                print(f"  Heating plug state synced: {'ON' if is_on else 'OFF'}")
            else:
                # If we can't query the state, keep current value and let control loop handle it
                # Don't override to False as this causes UI flicker when network is slow
                print(f"  Failed to query heating plug: {error}, keeping current state")
        except asyncio.TimeoutError:
            # If query times out, keep current value and let control loop handle it
            print(f"  Heating plug query timed out, keeping current state")
        except Exception as e:
            # If query fails, keep current value and let control loop handle it
            print(f"  Error querying heating plug: {e}, keeping current state")
    else:
        # Only set to False if heating is not enabled
        temp_cfg["heater_on"] = False
    
    # Query cooling plug state with timeout
    if enable_cooling and cooling_url:
        try:
            is_on, error = asyncio.run(query_plug_with_timeout(cooling_url, "cooling"))
            if error is None:
                temp_cfg["cooler_on"] = is_on
                print(f"  Cooling plug state synced: {'ON' if is_on else 'OFF'}")
            else:
                # If we can't query the state, keep current value and let control loop handle it
                # Don't override to False as this causes UI flicker when network is slow
                print(f"  Failed to query cooling plug: {error}, keeping current state")
        except asyncio.TimeoutError:
            # If query times out, keep current value and let control loop handle it
            print(f"  Cooling plug query timed out, keeping current state")
        except Exception as e:
            # If query fails, keep current value and let control loop handle it
            print(f"  Error querying cooling plug: {e}, keeping current state")
    else:
        # Only set to False if cooling is not enabled
        temp_cfg["cooler_on"] = False
    
    print(f"\nFinal state (after sync):")
    print(f"  heater_on: {temp_cfg['heater_on']}")
    print(f"  cooler_on: {temp_cfg['cooler_on']}")
    
    return temp_cfg

if __name__ == '__main__':
    print("Testing Plug State Synchronization at Startup")
    print("="*70)
    
    # Test 1: Both plugs are ON
    result1 = test_sync_logic(mock_kasa_query_state_success, "Both plugs ON")
    assert result1["heater_on"], "Heating should be ON"
    assert result1["cooler_on"], "Cooling should be ON"
    print("✅ PASS: Correctly detected both plugs ON")
    
    # Test 2: Both plugs are OFF
    result2 = test_sync_logic(mock_kasa_query_state_off, "Both plugs OFF")
    assert not result2["heater_on"], "Heating should be OFF"
    assert not result2["cooler_on"], "Cooling should be OFF"
    print("✅ PASS: Correctly detected both plugs OFF")
    
    # Test 3: Query fails (connection error) - should keep previous state
    result3 = test_sync_logic(mock_kasa_query_state_error, "Query fails")
    assert result3["heater_on"], "Heating should keep previous state (ON) on error"
    assert result3["cooler_on"], "Cooling should keep previous state (ON) on error"
    print("✅ PASS: Correctly kept previous state on query failure")
    
    # Test 4: Query times out - should keep previous state
    result4 = test_sync_logic(mock_kasa_query_state_timeout, "Query times out", use_timeout=True)
    assert result4["heater_on"], "Heating should keep previous state (ON) on timeout"
    assert result4["cooler_on"], "Cooling should keep previous state (ON) on timeout"
    print("✅ PASS: Correctly kept previous state on query timeout")
    
    print(f"\n{'='*70}")
    print("All tests passed! ✅")
    print(f"{'='*70}")
