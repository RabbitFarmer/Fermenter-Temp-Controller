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

def test_sync_logic(kasa_query_state_func, test_name):
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
    
    # Query heating plug state
    if enable_heating and heating_url:
        try:
            is_on, error = asyncio.run(kasa_query_state_func(heating_url))
            if error is None:
                temp_cfg["heater_on"] = is_on
                print(f"  Heating plug state synced: {'ON' if is_on else 'OFF'}")
            else:
                temp_cfg["heater_on"] = False
                print(f"  Failed to query heating plug: {error}, assuming OFF")
        except Exception as e:
            temp_cfg["heater_on"] = False
            print(f"  Error querying heating plug: {e}, assuming OFF")
    else:
        temp_cfg["heater_on"] = False
    
    # Query cooling plug state
    if enable_cooling and cooling_url:
        try:
            is_on, error = asyncio.run(kasa_query_state_func(cooling_url))
            if error is None:
                temp_cfg["cooler_on"] = is_on
                print(f"  Cooling plug state synced: {'ON' if is_on else 'OFF'}")
            else:
                temp_cfg["cooler_on"] = False
                print(f"  Failed to query cooling plug: {error}, assuming OFF")
        except Exception as e:
            temp_cfg["cooler_on"] = False
            print(f"  Error querying cooling plug: {e}, assuming OFF")
    else:
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
    
    # Test 3: Query fails (connection error)
    result3 = test_sync_logic(mock_kasa_query_state_error, "Query fails")
    assert not result3["heater_on"], "Heating should default to OFF on error"
    assert not result3["cooler_on"], "Cooling should default to OFF on error"
    print("✅ PASS: Correctly defaulted to OFF on query failure")
    
    print(f"\n{'='*70}")
    print("All tests passed! ✅")
    print(f"{'='*70}")
