# Custom EEP Profiles Guide

## Overview

EnOcean MQTT Slim includes 150+ built-in EEP profiles, but you can add your own custom profiles or override existing ones by placing JSON files in a special directory.

**Custom profiles allow you to:**
- ✅ Add support for new EnOcean devices
- ✅ Override built-in profiles with custom configurations
- ✅ Customize entity names, icons, and device classes
- ✅ Define custom data field mappings

---

## Quick Start

### 1. Create the Custom Profiles Directory

In Home Assistant, create this directory:
```
/config/enocean_custom_profiles/
```

**How to create it:**
- **File Editor addon:** Navigate to `/config` and create folder `enocean_custom_profiles`
- **SSH/Terminal:** `mkdir -p /config/enocean_custom_profiles`
- **Samba/SMB:** Browse to `\\homeassistant\config\` and create folder

### 2. Add Your Custom Profile

Create a JSON file in the directory:
```
/config/enocean_custom_profiles/MY-CUSTOM-PROFILE.json
```

### 3. Restart the Addon

The addon will automatically load your custom profiles on startup.

---

## Directory Structure

```
/config/
└── enocean_custom_profiles/
    ├── A5-30-05.json          # Override built-in profile
    ├── MY-CUSTOM-01.json      # New custom profile
    └── subdirectory/          # Subdirectories are supported
        └── ANOTHER-01.json
```

**Notes:**
- ✅ Subdirectories are supported (profiles are loaded recursively)
- ✅ File names don't matter (EEP code is read from JSON content)
- ✅ Custom profiles override built-in profiles with the same EEP code
- ✅ Changes require addon restart to take effect

---

## EEP Profile JSON Format

### Basic Structure

```json
{
  "eep": "A5-30-05",
  "rorg_number": "0xa5",
  "func_number": "0x30",
  "type_number": "0x05",
  "type_title": "My Custom Temperature Sensor",
  "manufacturer": "Custom Manufacturer",
  "description": "Custom temperature sensor with extended range",
  "bidirectional": false,
  "objects": {
    "temperature": {
      "name": "Temperature",
      "component": "sensor",
      "device_class": "temperature",
      "unit": "°C",
      "icon": "mdi:thermometer"
    }
  },
  "case": [
    {
      "condition": {},
      "datafield": [
        {
          "data": "DB1",
          "shortcut": "temperature",
          "description": "Temperature value",
          "bitoffs": "0",
          "bitsize": "8",
          "range": {
            "min": -40,
            "max": 80
          },
          "scale": {
            "min": 0,
            "max": 255
          }
        }
      ]
    }
  ]
}
```

### Field Descriptions

#### Top-Level Fields

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `eep` | ✅ Yes | EEP code identifier | `"A5-30-05"` |
| `rorg_number` | ✅ Yes | RORG value (hex string) | `"0xa5"` |
| `func_number` | ✅ Yes | FUNC value (hex string) | `"0x30"` |
| `type_number` | ✅ Yes | TYPE value (hex string) | `"0x05"` |
| `type_title` | ✅ Yes | Human-readable name | `"Temperature Sensor"` |
| `manufacturer` | ❌ No | Manufacturer name | `"EnOcean"` |
| `description` | ❌ No | Profile description | `"Digital temperature sensor"` |
| `bidirectional` | ❌ No | Supports bidirectional communication | `false` |
| `objects` | ✅ Yes | Home Assistant entity definitions | See below |
| `case` | ✅ Yes | Data field definitions | See below |

#### Objects (Home Assistant Entities)

Each object becomes a Home Assistant entity:

```json
"objects": {
  "temperature": {
    "name": "Temperature",
    "component": "sensor",
    "device_class": "temperature",
    "unit": "°C",
    "icon": "mdi:thermometer"
  },
  "humidity": {
    "name": "Humidity",
    "component": "sensor",
    "device_class": "humidity",
    "unit": "%",
    "icon": "mdi:water-percent"
  }
}
```

**Object Fields:**

| Field | Required | Description | Examples |
|-------|----------|-------------|----------|
| `name` | ✅ Yes | Entity display name | `"Temperature"`, `"Button A"` |
| `component` | ✅ Yes | HA component type | `"sensor"`, `"binary_sensor"`, `"switch"` |
| `device_class` | ❌ No | HA device class | `"temperature"`, `"motion"`, `"door"` |
| `unit` | ❌ No | Unit of measurement | `"°C"`, `"%"`, `"lx"` |
| `icon` | ❌ No | MDI icon | `"mdi:thermometer"`, `"mdi:lightbulb"` |

**Common Component Types:**
- `sensor` - Numeric values (temperature, humidity, etc.)
- `binary_sensor` - On/off states (motion, door, etc.)
- `switch` - Controllable on/off
- `cover` - Blinds, shutters
- `light` - Lights, dimmers

**Common Device Classes:**
- **Sensor:** `temperature`, `humidity`, `illuminance`, `power`, `energy`, `voltage`, `current`
- **Binary Sensor:** `motion`, `door`, `window`, `moisture`, `problem`, `safety`

#### Datafields (Data Parsing)

Datafields define how to extract values from telegram data bytes:

```json
"datafield": [
  {
    "data": "DB1",
    "shortcut": "temperature",
    "description": "Temperature value",
    "bitoffs": "0",
    "bitsize": "8",
    "range": {
      "min": -40,
      "max": 80
    },
    "scale": {
      "min": 0,
      "max": 255
    }
  }
]
```

**Datafield Fields:**

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `data` | ✅ Yes | Data byte identifier | `"DB0"`, `"DB1"`, `"DB2"`, `"DB3"` |
| `shortcut` | ✅ Yes | Links to object key | `"temperature"` |
| `description` | ❌ No | Field description | `"Temperature value"` |
| `bitoffs` | ✅ Yes | Bit offset (0-7) | `"0"`, `"4"` |
| `bitsize` | ✅ Yes | Number of bits (1-8) | `"8"`, `"1"` |
| `range` | ✅ Yes | Physical value range | `{"min": -40, "max": 80}` |
| `scale` | ✅ Yes | Raw value range | `{"min": 0, "max": 255}` |

**Data Byte Naming:**
- **4BS (A5):** `DB3`, `DB2`, `DB1`, `DB0` (4 data bytes)
- **RPS (F6):** `DB0` (1 data byte)
- **1BS (D5):** `DB0` (1 data byte)

**Bit Offset Examples:**
- `bitoffs: "0"`, `bitsize: "8"` = Full byte (bits 0-7)
- `bitoffs: "0"`, `bitsize: "1"` = Bit 0 only
- `bitoffs: "4"`, `bitsize: "4"` = Upper nibble (bits 4-7)

---

## Complete Examples

### Example 1: Simple Temperature Sensor (A5-02-05)

```json
{
  "eep": "A5-02-05",
  "rorg_number": "0xa5",
  "func_number": "0x02",
  "type_number": "0x05",
  "type_title": "Temperature Sensor 0°C to +40°C",
  "manufacturer": "EnOcean",
  "description": "Temperature sensor with 0-40°C range",
  "bidirectional": false,
  "objects": {
    "temperature": {
      "name": "Temperature",
      "component": "sensor",
      "device_class": "temperature",
      "unit": "°C",
      "icon": "mdi:thermometer"
    }
  },
  "case": [
    {
      "condition": {},
      "datafield": [
        {
          "data": "DB1",
          "shortcut": "temperature",
          "description": "Temperature 0°C to +40°C",
          "bitoffs": "0",
          "bitsize": "8",
          "range": {
            "min": 0,
            "max": 40
          },
          "scale": {
            "min": 255,
            "max": 0
          }
        }
      ]
    }
  ]
}
```

### Example 2: Rocker Switch (F6-02-01)

```json
{
  "eep": "F6-02-01",
  "rorg_number": "0xf6",
  "func_number": "0x02",
  "type_number": "0x01",
  "type_title": "Rocker Switch, 2 Rocker",
  "manufacturer": "EnOcean",
  "description": "2-button rocker switch",
  "bidirectional": false,
  "objects": {
    "button_a0": {
      "name": "Button A0",
      "component": "binary_sensor",
      "device_class": null,
      "icon": "mdi:gesture-tap-button"
    },
    "button_a1": {
      "name": "Button A1",
      "component": "binary_sensor",
      "device_class": null,
      "icon": "mdi:gesture-tap-button"
    },
    "button_b0": {
      "name": "Button B0",
      "component": "binary_sensor",
      "device_class": null,
      "icon": "mdi:gesture-tap-button"
    },
    "button_b1": {
      "name": "Button B1",
      "component": "binary_sensor",
      "device_class": null,
      "icon": "mdi:gesture-tap-button"
    }
  },
  "case": [
    {
      "condition": {},
      "datafield": [
        {
          "data": "DB0",
          "shortcut": "button_a0",
          "description": "Rocker A, Button 0",
          "bitoffs": "0",
          "bitsize": "1",
          "range": {
            "min": 0,
            "max": 1
          },
          "scale": {
            "min": 0,
            "max": 1
          }
        },
        {
          "data": "DB0",
          "shortcut": "button_a1",
          "description": "Rocker A, Button 1",
          "bitoffs": "1",
          "bitsize": "1",
          "range": {
            "min": 0,
            "max": 1
          },
          "scale": {
            "min": 0,
            "max": 1
          }
        },
        {
          "data": "DB0",
          "shortcut": "button_b0",
          "description": "Rocker B, Button 0",
          "bitoffs": "2",
          "bitsize": "1",
          "range": {
            "min": 0,
            "max": 1
          },
          "scale": {
            "min": 0,
            "max": 1
          }
        },
        {
          "data": "DB0",
          "shortcut": "button_b1",
          "description": "Rocker B, Button 1",
          "bitoffs": "3",
          "bitsize": "1",
          "range": {
            "min": 0,
            "max": 1
          },
          "scale": {
            "min": 0,
            "max": 1
          }
        }
      ]
    }
  ]
}
```

### Example 3: Multi-Sensor (A5-04-01)

```json
{
  "eep": "A5-04-01",
  "rorg_number": "0xa5",
  "func_number": "0x04",
  "type_number": "0x01",
  "type_title": "Temperature and Humidity Sensor",
  "manufacturer": "EnOcean",
  "description": "Combined temperature and humidity sensor",
  "bidirectional": false,
  "objects": {
    "temperature": {
      "name": "Temperature",
      "component": "sensor",
      "device_class": "temperature",
      "unit": "°C",
      "icon": "mdi:thermometer"
    },
    "humidity": {
      "name": "Humidity",
      "component": "sensor",
      "device_class": "humidity",
      "unit": "%",
      "icon": "mdi:water-percent"
    }
  },
  "case": [
    {
      "condition": {},
      "datafield": [
        {
          "data": "DB1",
          "shortcut": "humidity",
          "description": "Relative Humidity",
          "bitoffs": "0",
          "bitsize": "8",
          "range": {
            "min": 0,
            "max": 100
          },
          "scale": {
            "min": 0,
            "max": 250
          }
        },
        {
          "data": "DB2",
          "shortcut": "temperature",
          "description": "Temperature",
          "bitoffs": "0",
          "bitsize": "8",
          "range": {
            "min": -20,
            "max": 60
          },
          "scale": {
            "min": 0,
            "max": 250
          }
        }
      ]
    }
  ]
}
```

---

## Finding More Examples

### Built-in EEP Profiles

All 150+ built-in profiles are available in the GitHub repository:

**📁 Browse EEP Profiles:**
https://github.com/ESDN83/ha-enocean-mqtt-slim/tree/main/addon/rootfs/app/eep/definitions

**Directory Structure:**
```
eep/definitions/
├── A5-02/          # Temperature sensors
├── A5-04/          # Humidity sensors
├── A5-07/          # Occupancy sensors
├── A5-30/          # Digital input
├── D2-01/          # Electronic switches
├── D5-00/          # Contacts and switches
├── F6-02/          # Rocker switches
├── MV-01/          # Kessel Staufix
└── ...
```

**Popular Examples:**
- [A5-02-05.json](https://github.com/ESDN83/ha-enocean-mqtt-slim/blob/main/addon/rootfs/app/eep/definitions/A5-02/A5-02-05.json) - Temperature sensor
- [F6-02-01.json](https://github.com/ESDN83/ha-enocean-mqtt-slim/blob/main/addon/rootfs/app/eep/definitions/F6-02/F6-02-01.json) - Rocker switch
- [D5-00-01.json](https://github.com/ESDN83/ha-enocean-mqtt-slim/blob/main/addon/rootfs/app/eep/definitions/D5-00/D5-00-01.json) - Window contact
- [MV-01-01.json](https://github.com/ESDN83/ha-enocean-mqtt-slim/blob/main/addon/rootfs/app/eep/definitions/MV-01/MV-01-01.json) - Kessel Staufix

### Official EnOcean Documentation

- **EEP Specification:** https://www.enocean-alliance.org/eep/
- **EnOcean Alliance:** https://www.enocean-alliance.org/

---

## Testing Your Custom Profile

### 1. Create the Profile

Save your JSON file to `/config/enocean_custom_profiles/`

### 2. Restart the Addon

Go to **Settings → Add-ons → EnOcean MQTT Slim → Restart**

### 3. Check the Logs

Look for these messages:
```
INFO - Loaded 150 built-in EEP profiles
INFO - ➕ Adding custom EEP profile: MY-CUSTOM-01
INFO - Loaded 1 custom profiles (0 overrides, 1 new)
```

Or if overriding:
```
INFO - 🔄 Overriding EEP profile: A5-30-05 with custom version
INFO - Loaded 1 custom profiles (1 overrides, 0 new)
```

### 4. Add a Device

1. Open Web UI
2. Click "Add Device"
3. Your custom profile should appear in the EEP dropdown
4. Add the device and test!

---

## Troubleshooting

### Profile Not Loading

**Check the logs for errors:**
```
ERROR - Failed to load custom EEP profile from /config/enocean_custom_profiles/MY-PROFILE.json: ...
```

**Common issues:**
- ❌ Invalid JSON syntax (use a JSON validator)
- ❌ Missing required fields (`eep`, `rorg_number`, etc.)
- ❌ Incorrect file permissions
- ❌ File not in `/config/enocean_custom_profiles/`

### Profile Loads But Device Doesn't Work

1. **Check datafield mappings:**
   - Verify `data` byte names (DB0, DB1, etc.)
   - Check `bitoffs` and `bitsize` values
   - Ensure `shortcut` matches object key

2. **Check value ranges:**
   - `range` = physical values (e.g., -40 to 80°C)
   - `scale` = raw telegram values (e.g., 0 to 255)

3. **Enable debug logging:**
   - Set log level to `debug` in addon configuration
   - Check telegram parsing in logs

### Custom Profile Not Overriding Built-in

- ✅ Ensure `eep` field matches exactly (case-sensitive)
- ✅ Restart addon after adding profile
- ✅ Check logs for "Overriding EEP profile" message

---

## Best Practices

### 1. Start with an Existing Profile

Copy a similar built-in profile and modify it:
```bash
# In Home Assistant terminal
cp /app/eep/definitions/A5-02/A5-02-05.json /config/enocean_custom_profiles/MY-SENSOR.json
```

### 2. Use Descriptive Names

```json
{
  "eep": "MY-CUSTOM-01",
  "type_title": "My Company Temperature Sensor Model XYZ",
  "manufacturer": "My Company"
}
```

### 3. Document Your Profile

Add detailed descriptions:
```json
{
  "description": "Custom profile for XYZ sensor. Temperature range -40 to +80°C, humidity 0-100%.",
  "datafield": [
    {
      "description": "Temperature value in °C, transmitted as 8-bit value"
    }
  ]
}
```

### 4. Test Thoroughly

- ✅ Test all data fields
- ✅ Verify value ranges
- ✅ Check entity creation in Home Assistant
- ✅ Test with actual device telegrams

### 5. Share Your Profiles

If you create a useful custom profile, consider contributing it back to the project!

---

## Advanced Topics

### Conditional Cases

Some profiles have multiple cases based on conditions:

```json
"case": [
  {
    "condition": {
      "statusfield": {
        "bitoffs": "4",
        "bitsize": "1",
        "value": "0"
      }
    },
    "datafield": [...]
  },
  {
    "condition": {
      "statusfield": {
        "bitoffs": "4",
        "bitsize": "1",
        "value": "1"
      }
    },
    "datafield": [...]
  }
]
```

### Bidirectional Communication

For devices that can receive commands:

```json
{
  "bidirectional": true,
  "objects": {
    "switch": {
      "component": "switch",
      "name": "Output"
    }
  }
}
```

---

## Summary

**Key Points:**
- ✅ Custom profiles go in `/config/enocean_custom_profiles/`
- ✅ Use JSON format matching built-in profiles
- ✅ Custom profiles can override built-in profiles
- ✅ Restart addon after adding/modifying profiles
- ✅ Check logs for loading confirmation
- ✅ Browse GitHub for 150+ examples

**Need Help?**
- 📚 Check built-in profiles for examples
- 🐛 Enable debug logging
- 💬 Ask in GitHub Issues or HA Community Forum

Happy customizing! 🎉
