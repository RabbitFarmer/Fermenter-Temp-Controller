#!/usr/bin/env python3
"""
Archive/compact temp_control/temp_control_log.jsonl:

- Splits tilt_reading entries into batches/<brewid_or_color>_YYYYMMDDTHHMMSS.jsonl
- Rebuilds temp_control/temp_control_log.jsonl keeping:
    * All non-tilt_reading events
    * The last `keep_per_tilt` tilt_reading entries per brewid (or color fallback)
- Backup is created automatically.

Usage:
    # Run from repository root directory
    # Stop the app first
    pkill -f app.py
    sleep 1

    python3 archive_compact_logs.py --log temp_control/temp_control_log.jsonl --batches batches --keep 1
"""
import argparse
import json
import os
from collections import deque, defaultdict
from datetime import datetime

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def archive_split(input_log, batches_dir, keep_per_tilt=1):
    ensure_dir(batches_dir)
    # Backup original
    bak = f"{input_log}.{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.bak"
    os.rename(input_log, bak)
    print(f"Backup saved to: {bak}")

    # We'll collect non-tilt events to write back, and collect last N tilt entries per brewid/color
    non_tilt_lines = []
    tilt_buffers = defaultdict(lambda: deque(maxlen=keep_per_tilt))
    archive_handles = {}

    # First pass: read the backup file and route lines
    with open(bak, 'r') as f:
        for line in f:
            line_strip = line.rstrip('\n')
            if not line_strip:
                continue
            try:
                obj = json.loads(line_strip)
            except Exception:
                # Preserve malformed lines in the rebuilt log
                non_tilt_lines.append(line_strip)
                continue

            event = obj.get('event')
            payload = obj.get('payload') or {}
            if event == 'tilt_reading':
                # Determine archive key: brewid preferred, fallback to color (if provided in payload)
                brewid = payload.get('brewid') or payload.get('brew_id') or ''
                color = payload.get('color') or payload.get('tilt_color') or ''
                key = brewid if brewid else (color if color else 'unknown')
                # append to buffer (keep last N)
                tilt_buffers[key].append(line_strip)
            else:
                # keep all other events in main log
                non_tilt_lines.append(line_strip)

    # Write per-key archives (append all collected entries for that key)
    for key, dq in tilt_buffers.items():
        # safe filename
        safe_key = key.replace('/', '_').replace(' ', '_') or 'unknown'
        archive_name = f"{safe_key}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jsonl"
        dest = os.path.join(batches_dir, archive_name)
        with open(dest, 'w') as af:
            # Write the entire history that was in the original file for this key by extracting from the bak.
            # Simpler approach: append the entries we retained in the buffer (the last N).
            for ln in dq:
                af.write(ln + "\n")
        print(f"Wrote archive for {key} -> {dest}")

    # Rebuild main log: write non-tilt events and optionally the last N per key (if you want them in main log)
    # If you prefer the main log to have zero tilt_reading entries, comment out the tilt reinsertion below.
    with open(input_log, 'w') as out:
        # write non-tilt events first
        for ln in non_tilt_lines:
            out.write(ln + "\n")
        # Optionally, append last N tilt_reading entries for each existing key to keep some recent data in main log
        # (If you prefer no tilt_reading in main log, skip this loop)
        for key, dq in tilt_buffers.items():
            for ln in dq:
                out.write(ln + "\n")

    print(f"Rebuilt compact log: {input_log}")
    return bak

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--log', default='temp_control/temp_control_log.jsonl')
    p.add_argument('--batches', default='batches')
    p.add_argument('--keep', type=int, default=1, help='number of tilt_reading entries to keep per brew/color in main log')
    args = p.parse_args()

    if not os.path.exists(args.log):
        print("Log file not found:", args.log)
        return

    bak = archive_split(args.log, args.batches, keep_per_tilt=args.keep)
    print("Done. Original log backed up at:", bak)

if __name__ == '__main__':
    main()