#!/usr/bin/env python3
"""
Quick fix script to update device 05834fa4 from wrong profile A5-38-08 to correct MV-01-01
"""
import json

# Path to devices.json in addon
DEVICES_FILE = "/data/devices.json"

# Read current devices
try:
    with open(DEVICES_FILE, 'r') as f:
        devices = json.load(f)
        print(f"✅ Loaded {len(devices)} devices")
except FileNotFoundError:
    print("❌ devices.json not found")
    exit(1)

# Find and update device 05834fa4
if '05834fa4' in devices:
    device = devices['05834fa4']
    old_eep = device.get('eep', 'unknown')
    print(f"\n📋 Found device: {device.get('name', 'Unknown')}")
    print(f"   Current EEP: {old_eep}")
    print(f"   Device ID: 05834fa4")
    
    # Update to correct profile
    device['eep'] = 'MV-01-01'
    device['name'] = 'Kessel Staufix Control'
    device['manufacturer'] = 'Kessel'
    
    print(f"\n✅ Updated to:")
    print(f"   New EEP: MV-01-01")
    print(f"   New Name: Kessel Staufix Control")
    print(f"   Manufacturer: Kessel")
    
    # Save updated devices
    with open(DEVICES_FILE, 'w') as f:
        json.dump(devices, f, indent=2)
    
    print(f"\n💾 Saved to {DEVICES_FILE}")
    print(f"\n⚠️  IMPORTANT: Restart the addon for changes to take effect!")
    print(f"   After restart, the device will use the correct MV-01-01 profile")
else:
    print(f"❌ Device 05834fa4 not found in devices.json")
    print(f"   Available devices: {list(devices.keys())}")
