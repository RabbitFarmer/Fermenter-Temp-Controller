#!/usr/bin/env python3
"""
Import Brewer's Friend JSON data into the fermentation monitoring system.

This script converts Brewer's Friend export format to the internal JSONL format
used by the Fermenter Temperature Controller. It's designed for importing demo
data or historical fermentation logs.

Usage:
    python3 utils/import_brewers_friend.py <input_json> --color <tilt_color> --brewid <brewid>
    
    Or for automatic brewid generation:
    python3 utils/import_brewers_friend.py <input_json> --color <tilt_color> --beer-name "Beer Name" --batch-name "Batch Name"
"""

import argparse
import json
import os
import sys
from datetime import datetime
import hashlib


def generate_brewid(beer_name, batch_name, date_str):
    """Generate brewid from beer name, batch name, and date."""
    id_str = f"{beer_name}-{batch_name}-{date_str}"
    return hashlib.sha256(id_str.encode('utf-8')).hexdigest()[:8]


def parse_timestamp(ts_str):
    """Parse various timestamp formats from Brewer's Friend data."""
    # Try ISO 8601 formats
    for fmt in [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]:
        try:
            dt = datetime.strptime(ts_str.replace('+00:00', '+0000'), fmt)
            # Convert to UTC ISO format
            if dt.tzinfo:
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                # For naive datetime, just format without microseconds and add Z
                base_time = ts_str.split('.')[0]
                return f"{base_time}Z"
        except ValueError:
            continue
    return ts_str


def convert_brewers_friend_to_jsonl(input_file, tilt_color, brewid, beer_name="", batch_name=""):
    """
    Convert Brewer's Friend JSON format to internal JSONL format.
    
    Args:
        input_file: Path to Brewer's Friend JSON file
        tilt_color: Tilt color (e.g., "Black", "Blue", etc.)
        brewid: Brew ID for this batch
        beer_name: Optional beer name for metadata
        batch_name: Optional batch name for metadata
        
    Returns:
        List of JSONL entries (dicts) to be written
    """
    # Read the Brewer's Friend JSON file
    with open(input_file, 'r') as f:
        bf_data = json.load(f)
    
    if not isinstance(bf_data, list):
        raise ValueError("Expected Brewer's Friend data to be a JSON array")
    
    # Extract first timestamp for created_date
    first_entry = bf_data[0] if bf_data else {}
    first_timestamp = first_entry.get('created_at', '')
    
    # Try to parse the date from the first entry
    try:
        # Parse ISO timestamp to get date
        dt = datetime.fromisoformat(first_timestamp.replace('Z', '+00:00'))
        created_date = dt.strftime("%m%d%Y")  # mmddyyyy format
    except:
        created_date = datetime.now().strftime("%m%d%Y")
    
    # Extract beer name from data if not provided
    if not beer_name:
        for entry in bf_data:
            if entry.get('beer'):
                beer_name = entry['beer']
                break
    
    # Create metadata entry
    metadata_entry = {
        "event": "batch_metadata",
        "payload": {
            "tilt_color": tilt_color,
            "brewid": brewid,
            "created_date": created_date,
            "meta": {
                "beer_name": beer_name,
                "batch_name": batch_name
            }
        }
    }
    
    # Convert each data point to sample format
    jsonl_entries = [metadata_entry]
    
    for entry in bf_data:
        # Skip non-tilt entries (like manual brew log entries)
        # or include them based on what data is available
        gravity = entry.get('gravity')
        temp = entry.get('temp')
        created_at = entry.get('created_at')
        
        if gravity is None or temp is None or created_at is None:
            continue
        
        # Parse and normalize timestamp
        timestamp = parse_timestamp(created_at)
        
        # Create sample entry in the expected format
        sample_entry = {
            "event": "sample",
            "payload": {
                "timestamp": timestamp,
                "tilt_color": tilt_color,
                "gravity": float(gravity),
                "temp_f": int(temp),
                "current_temp": float(temp),
                "brewid": brewid,
                "rssi": -70  # Default RSSI since BF data doesn't include it
            }
        }
        
        jsonl_entries.append(sample_entry)
    
    return jsonl_entries


def write_jsonl_to_batch_file(jsonl_entries, output_file):
    """Write JSONL entries to a batch file."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in jsonl_entries:
            f.write(json.dumps(entry) + '\n')
    
    print(f"✓ Wrote {len(jsonl_entries)} entries to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Import Brewer\'s Friend JSON data into Fermenter Temp Controller'
    )
    parser.add_argument('input_file', help='Path to Brewer\'s Friend JSON file')
    parser.add_argument('--color', required=True, 
                       help='Tilt color (Black, Blue, Green, Orange, Pink, Purple, Red, Yellow)')
    parser.add_argument('--brewid', help='Brew ID (8 character hex). If not provided, will be generated.')
    parser.add_argument('--beer-name', default='', help='Beer name for metadata')
    parser.add_argument('--batch-name', default='', help='Batch name for metadata')
    parser.add_argument('--output-dir', default='batches', help='Output directory for batch files')
    
    args = parser.parse_args()
    
    # Validate tilt color
    valid_colors = ['Black', 'Blue', 'Green', 'Orange', 'Pink', 'Purple', 'Red', 'Yellow']
    if args.color not in valid_colors:
        print(f"Error: Invalid tilt color '{args.color}'. Must be one of: {', '.join(valid_colors)}")
        sys.exit(1)
    
    # Generate brewid if not provided
    if not args.brewid:
        if not args.beer_name or not args.batch_name:
            print("Error: Either --brewid or both --beer-name and --batch-name must be provided")
            sys.exit(1)
        date_str = datetime.now().strftime("%m%d%Y")
        brewid = generate_brewid(args.beer_name, args.batch_name, date_str)
        print(f"Generated brewid: {brewid}")
    else:
        brewid = args.brewid
    
    # Convert the data
    print(f"Converting {args.input_file}...")
    try:
        jsonl_entries = convert_brewers_friend_to_jsonl(
            args.input_file,
            args.color,
            brewid,
            args.beer_name,
            args.batch_name
        )
    except Exception as e:
        print(f"Error converting data: {e}")
        sys.exit(1)
    
    # Create output filename
    if args.beer_name:
        # Sanitize filename: keep only alphanumeric and underscores
        import re
        safe_beer_name = re.sub(r'[^a-zA-Z0-9_]', '_', args.beer_name)
        # Get date from first entry
        if len(jsonl_entries) > 0:
            metadata = jsonl_entries[0]
            created_date = metadata['payload'].get('created_date', datetime.now().strftime("%m%d%Y"))
            # Convert mmddyyyy to yyyymmdd
            if len(created_date) == 8:
                date_yyyymmdd = created_date[4:8] + created_date[0:2] + created_date[2:4]
            else:
                date_yyyymmdd = datetime.now().strftime("%Y%m%d")
        else:
            date_yyyymmdd = datetime.now().strftime("%Y%m%d")
        output_file = os.path.join(args.output_dir, f"{safe_beer_name}_{date_yyyymmdd}_{brewid}.jsonl")
    else:
        output_file = os.path.join(args.output_dir, f"{brewid}.jsonl")
    
    # Write the output file
    write_jsonl_to_batch_file(jsonl_entries, output_file)
    
    print(f"\n✓ Import complete!")
    print(f"  Tilt Color: {args.color}")
    print(f"  Brew ID: {brewid}")
    print(f"  Beer Name: {args.beer_name or '(not set)'}")
    print(f"  Batch Name: {args.batch_name or '(not set)'}")
    print(f"  Output: {output_file}")
    print(f"\nTo view in the dashboard:")
    print(f"  1. Make sure tilt_config.json has a '{args.color}' entry with brewid='{brewid}'")
    print(f"  2. Navigate to the chart page for {args.color}")


if __name__ == '__main__':
    main()
