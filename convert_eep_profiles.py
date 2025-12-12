#!/usr/bin/env python3
"""
Convert ioBroker EEP profiles to Home Assistant format
Adds RSSI and timestamp sensors to all profiles
"""
import json
import os
import shutil
from pathlib import Path

# Source and destination directories
SOURCE_DIR = Path("/Users/erik.seel/Desktop/ioBroker.enocean/lib/definitions/eep")
DEST_DIR = Path("/Users/erik.seel/AI/ha-enocean-mqtt-slim/addon/rootfs/app/eep/definitions")

def add_rssi_timestamp_sensors(profile_data):
    """Add RSSI and timestamp sensors to profile objects"""
    if "objects" not in profile_data:
        profile_data["objects"] = {}
    
    # Add RSSI sensor
    profile_data["objects"]["rssi"] = {
        "name": "RSSI",
        "component": "sensor",
        "device_class": "signal_strength",
        "unit": "dBm",
        "icon": "mdi:wifi",
        "description": "Signal strength"
    }
    
    # Add timestamp sensor
    profile_data["objects"]["last_seen"] = {
        "name": "Last Seen",
        "component": "sensor",
        "device_class": "timestamp",
        "icon": "mdi:clock-outline",
        "description": "Last telegram received"
    }
    
    return profile_data

def convert_profile(source_file, dest_file):
    """Convert a single profile file"""
    try:
        # Read source file
        with open(source_file, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        # Add RSSI and timestamp sensors
        profile_data = add_rssi_timestamp_sensors(profile_data)
        
        # Write to destination
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_file, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error converting {source_file}: {e}")
        return False

def main():
    """Main conversion function"""
    print("=" * 80)
    print("Converting ioBroker EEP profiles to Home Assistant format")
    print("=" * 80)
    
    if not SOURCE_DIR.exists():
        print(f"ERROR: Source directory not found: {SOURCE_DIR}")
        return
    
    # Count files
    source_files = list(SOURCE_DIR.rglob("*.json"))
    print(f"\nFound {len(source_files)} profile files to convert")
    
    # Convert each file
    converted = 0
    failed = 0
    
    for source_file in source_files:
        # Get relative path
        rel_path = source_file.relative_to(SOURCE_DIR)
        dest_file = DEST_DIR / rel_path
        
        print(f"Converting: {rel_path}...", end=" ")
        
        if convert_profile(source_file, dest_file):
            print("✓")
            converted += 1
        else:
            print("✗")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"Conversion complete!")
    print(f"  Converted: {converted}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(source_files)}")
    print("=" * 80)
    
    # List profile families
    families = set()
    for f in (DEST_DIR).rglob("*.json"):
        family = f.parent.name
        families.add(family)
    
    print(f"\nProfile families available: {len(families)}")
    for family in sorted(families):
        count = len(list((DEST_DIR / family).glob("*.json")))
        print(f"  {family}: {count} profiles")

if __name__ == "__main__":
    main()
