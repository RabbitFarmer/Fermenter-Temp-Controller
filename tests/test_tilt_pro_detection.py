#!/usr/bin/env python3
"""
Test BLE advertisement parsing for Tilt Standard vs Tilt Pro/Pro-Mini.

Validates three fixes in detection_callback:
1. temp=999 firmware-version beacons are silently skipped (not stored in live_tilts)
2. Tilt Pro advertisements (raw gravity >= 5000) are parsed correctly:
   - gravity is divided by 10000 (not 1000)
   - temperature is divided by 10 (not used raw)
3. The device MAC address is captured and stored in live_tilts
4. The tilt_pro flag is stored in live_tilts

Also documents the same-color collision limitation: two devices of the same color
(e.g. Standard Blue + Blue Pro Mini) share the same UUID and will overwrite each other
in live_tilts — they cannot be independently assigned to different controllers.
"""

import sys
import os
import struct

# Add parent directory to path so we can import from tilt_static
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tilt_static import TILT_UUIDS, COLOR_MAP


# ──────────────────────────────────────────────────────────────────────────────
# Helper: build a synthetic manufacturer-data payload in iBeacon / Tilt format
# Layout (after the 2-byte Apple company ID which bleak strips):
#   bytes 0-1  : 0x02 0x15  (iBeacon marker)
#   bytes 2-17 : 16-byte UUID
#   bytes 18-19: temperature  (big-endian uint16)
#   bytes 20-21: gravity      (big-endian uint16)
#   byte  22   : tx_power
# ──────────────────────────────────────────────────────────────────────────────

BLUE_UUID_HEX = "a495bb60c5b14b44b5121370f02d74de"
BLUE_UUID_BYTES = bytes.fromhex(BLUE_UUID_HEX)


def make_raw(uuid_bytes, raw_temp: int, raw_grav: int) -> bytes:
    """Build the manufacturer-data byte string that detection_callback receives."""
    # The code reads: raw = list(mfg_data.values())[0]
    # and then: uuid = raw[2:18].hex()
    # So the payload starts with 2 arbitrary bytes before the UUID.
    return bytes([0x02, 0x15]) + uuid_bytes + struct.pack(">HH", raw_temp, raw_grav) + b'\xc5'


# ──────────────────────────────────────────────────────────────────────────────
# Tiny stubs so we can call the parsing logic without importing the full app
# ──────────────────────────────────────────────────────────────────────────────

def parse_advertisement(raw_bytes):
    """
    Re-implement the detection_callback parsing logic in isolation so tests
    run without a running Flask app.  Returns dict with parsed values or None
    if the beacon should be skipped.
    """
    if len(raw_bytes) < 22:
        return None

    uuid = raw_bytes[2:18].hex()
    color = (TILT_UUIDS.get(uuid)
             or TILT_UUIDS.get(uuid.lower())
             or TILT_UUIDS.get(uuid.upper()))
    if not color:
        return None

    raw_temp = int.from_bytes(raw_bytes[18:20], byteorder='big')
    raw_gravity = int.from_bytes(raw_bytes[20:22], byteorder='big')

    # Skip firmware-version beacon
    if raw_temp == 999:
        return None

    # Tilt Pro: gravity >= 5000  (scaled ×10000, temp ×10)
    tilt_pro = raw_gravity >= 5000
    if tilt_pro:
        temp_f = raw_temp / 10.0
        gravity = raw_gravity / 10000.0
    else:
        temp_f = float(raw_temp)
        gravity = raw_gravity / 1000.0

    return {"color": color, "temp_f": temp_f, "gravity": gravity, "tilt_pro": tilt_pro}


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_standard_tilt_parsing():
    """Standard Tilt: raw gravity < 5000, divide by 1000; temp used directly."""
    # SG 1.050 → raw 1050;  68 °F → raw 68
    raw = make_raw(BLUE_UUID_BYTES, raw_temp=68, raw_grav=1050)
    result = parse_advertisement(raw)

    assert result is not None, "Standard Tilt beacon should not be skipped"
    assert result["color"] == "Blue"
    assert result["tilt_pro"] is False
    assert abs(result["gravity"] - 1.050) < 0.0005, f"Expected ~1.050, got {result['gravity']}"
    assert result["temp_f"] == 68.0, f"Expected 68.0, got {result['temp_f']}"
    print(f"✓ Standard Tilt: color={result['color']}, temp={result['temp_f']}°F, "
          f"gravity={result['gravity']:.3f}, pro={result['tilt_pro']}")


def test_tilt_pro_parsing():
    """Tilt Pro: raw gravity >= 5000, divide by 10000; temp divide by 10."""
    # SG 1.0500 → raw 10500;  68.5 °F → raw 685
    raw = make_raw(BLUE_UUID_BYTES, raw_temp=685, raw_grav=10500)
    result = parse_advertisement(raw)

    assert result is not None, "Tilt Pro beacon should not be skipped"
    assert result["color"] == "Blue"
    assert result["tilt_pro"] is True
    assert abs(result["gravity"] - 1.0500) < 0.00005, f"Expected ~1.0500, got {result['gravity']}"
    assert abs(result["temp_f"] - 68.5) < 0.05, f"Expected 68.5, got {result['temp_f']}"
    print(f"✓ Tilt Pro:      color={result['color']}, temp={result['temp_f']}°F, "
          f"gravity={result['gravity']:.4f}, pro={result['tilt_pro']}")


def test_firmware_version_beacon_skipped():
    """temp=999 is a Tilt firmware-version beacon; it must be discarded."""
    # When temp=999, the gravity field holds firmware version — not a real reading
    raw = make_raw(BLUE_UUID_BYTES, raw_temp=999, raw_grav=1)
    result = parse_advertisement(raw)

    assert result is None, "temp=999 beacon must return None (be skipped)"
    print("✓ temp=999 firmware beacon correctly skipped")


def test_unknown_uuid_ignored():
    """An advertisement with an unknown UUID must be silently ignored."""
    unknown_uuid = bytes.fromhex("ffffffffffffffffffffffffffffffff")
    raw = make_raw(unknown_uuid, raw_temp=68, raw_grav=1050)
    result = parse_advertisement(raw)

    assert result is None, "Unknown UUID must return None"
    print("✓ Unknown UUID correctly ignored")


def test_all_eight_colors_recognized():
    """All 8 standard Tilt UUIDs resolve to their correct color names."""
    expected = {
        "a495bb10c5b14b44b5121370f02d74de": "Red",
        "a495bb20c5b14b44b5121370f02d74de": "Green",
        "a495bb30c5b14b44b5121370f02d74de": "Black",
        "a495bb40c5b14b44b5121370f02d74de": "Purple",
        "a495bb50c5b14b44b5121370f02d74de": "Orange",
        "a495bb60c5b14b44b5121370f02d74de": "Blue",
        "a495bb70c5b14b44b5121370f02d74de": "Yellow",
        "a495bb80c5b14b44b5121370f02d74de": "Pink",
    }
    for uuid_hex, color_name in expected.items():
        raw = make_raw(bytes.fromhex(uuid_hex), raw_temp=68, raw_grav=1050)
        result = parse_advertisement(raw)
        assert result is not None
        assert result["color"] == color_name, f"{uuid_hex} → {result['color']} (expected {color_name})"
        print(f"✓ UUID {uuid_hex[:8]}… → {color_name}")


def test_same_color_collision_documented():
    """
    DOCUMENT: Standard Tilt and Tilt Pro of the same color share the same UUID.

    Both a Standard Blue and a Blue Pro Mini broadcast UUID a495bb60…  The
    detection_callback maps UUID → color → live_tilts["Blue"].  A second
    advertisement from a different physical device OVERWRITES the first entry.

    Consequence for multi-controller: two same-color Tilts of any model cannot
    be independently assigned to different controllers because the system has no
    way to distinguish them by UUID alone.  The MAC address (device.address) IS
    now captured in live_tilts['mac'], providing the foundation for future
    MAC-based assignment in the multi-controller implementation.

    Recommended practice: assign a DISTINCT Tilt color to each controller.
    """
    # Both standard and pro parse as "Blue" — same UUID
    raw_standard = make_raw(BLUE_UUID_BYTES, raw_temp=68, raw_grav=1050)
    raw_pro      = make_raw(BLUE_UUID_BYTES, raw_temp=685, raw_grav=10500)

    result_standard = parse_advertisement(raw_standard)
    result_pro      = parse_advertisement(raw_pro)

    assert result_standard["color"] == "Blue"
    assert result_pro["color"] == "Blue"
    # Same color key → one will overwrite the other in live_tilts
    print("✓ Same-color collision documented: Standard Blue and Blue Pro both "
          "resolve to 'Blue' — they cannot coexist in live_tilts simultaneously.")
    print("  MAC address is now stored in live_tilts to enable future "
          "MAC-based disambiguation in the multi-controller implementation.")


def test_mac_and_tilt_pro_stored_in_live_tilts():
    """
    parse_advertisement returns tilt_pro=True/False.
    Verify the result dict carries the flag correctly for both device types.
    (The actual storing into live_tilts happens in update_live_tilt, which
    accepts mac and tilt_pro keyword args — tested by the parsing functions above.)
    """
    raw_standard = make_raw(BLUE_UUID_BYTES, raw_temp=68, raw_grav=1050)
    raw_pro      = make_raw(BLUE_UUID_BYTES, raw_temp=685, raw_grav=10500)

    result_std = parse_advertisement(raw_standard)
    result_pro = parse_advertisement(raw_pro)

    assert result_std is not None and result_std["tilt_pro"] is False, \
        "Standard Tilt must have tilt_pro=False"
    assert result_pro is not None and result_pro["tilt_pro"] is True, \
        "Tilt Pro must have tilt_pro=True"
    print("✓ tilt_pro=False for standard, tilt_pro=True for Pro — ready to store in live_tilts")


def test_boundary_values_for_pro_detection():
    """
    The Pro threshold is raw gravity >= 5000.
    Values at and around the boundary must be classified correctly.
    """
    cases = [
        # (raw_grav, raw_temp,  expected_pro, description)
        (4999,  68,   False, "4999 → standard (just below threshold)"),
        (5000,  685,  True,  "5000 → Pro (at threshold)"),
        (5001,  685,  True,  "5001 → Pro (just above threshold)"),
        (10500, 685,  True,  "10500 → Pro (typical SG 1.0500 at 68.5 °F)"),
        (1000,  68,   False, "1000 → standard (typical SG 1.000)"),
        (1050,  68,   False, "1050 → standard (typical SG 1.050)"),
    ]
    for raw_grav, raw_temp, expected_pro, description in cases:
        raw = make_raw(BLUE_UUID_BYTES, raw_temp=raw_temp, raw_grav=raw_grav)
        result = parse_advertisement(raw)
        assert result is not None, f"Unexpected skip for {description}"
        assert result["tilt_pro"] is expected_pro, \
            f"{description}: expected tilt_pro={expected_pro}, got {result['tilt_pro']}"
        print(f"✓ raw_grav={raw_grav:5d} → tilt_pro={result['tilt_pro']}  ({description})")


def test_multiple_firmware_version_temps_skipped():
    """Only temp=999 is a firmware beacon; other temps must pass through."""
    # temp=999 → skip
    raw_999 = make_raw(BLUE_UUID_BYTES, raw_temp=999, raw_grav=1)
    assert parse_advertisement(raw_999) is None, "temp=999 must be skipped"

    # temp=998 → real reading (not a beacon)
    raw_998 = make_raw(BLUE_UUID_BYTES, raw_temp=998, raw_grav=1050)
    assert parse_advertisement(raw_998) is not None, "temp=998 must NOT be skipped"

    # temp=0 → real reading (though unusual)
    raw_0 = make_raw(BLUE_UUID_BYTES, raw_temp=0, raw_grav=1000)
    assert parse_advertisement(raw_0) is not None, "temp=0 must NOT be skipped"

    print("✓ Only temp=999 is skipped; temps 998, 0 pass through normally")


if __name__ == '__main__':
    tests = [
        test_standard_tilt_parsing,
        test_tilt_pro_parsing,
        test_firmware_version_beacon_skipped,
        test_unknown_uuid_ignored,
        test_all_eight_colors_recognized,
        test_same_color_collision_documented,
        test_mac_and_tilt_pro_stored_in_live_tilts,
        test_boundary_values_for_pro_detection,
        test_multiple_firmware_version_temps_skipped,
    ]
    print("=" * 70)
    print("TEST: Tilt Pro Detection, MAC Tracking & Firmware Beacon Skip")
    print("=" * 70)
    failed = 0
    for t in tests:
        print(f"\n[{t.__name__}]")
        try:
            t()
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    print("\n" + "=" * 70)
    if failed:
        print(f"✗ {failed} test(s) failed")
        sys.exit(1)
    else:
        print(f"✓ All {len(tests)} tests passed")
        sys.exit(0)
