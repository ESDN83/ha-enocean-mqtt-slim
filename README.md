# EnOcean MQTT Slim

[![GitHub Release](https://img.shields.io/github/v/release/ESDN83/ha-enocean-mqtt-slim)](https://github.com/ESDN83/ha-enocean-mqtt-slim/releases)
[![License](https://img.shields.io/github/license/ESDN83/ha-enocean-mqtt-slim)](LICENSE)

A lightweight, modern EnOcean to MQTT bridge for Home Assistant with automatic device detection and a beautiful web UI.

## ✨ Features

### 🎯 Zero Configuration
- **Automatic Device Detection** - Just press the teach-in button on your device!
- **Auto-EEP Detection** - Automatically detects EEP profile from teach-in telegrams
- **MQTT Discovery** - Devices appear in Home Assistant automatically
- **UTE Teach-In Response** - Proper teach-in completion for immediate device operation

### 🎨 Modern Web UI
- **Device Management** - Add, edit, enable/disable, and delete devices
- **Live Status** - Real-time gateway and MQTT connection status
- **EEP Profile Browser** - Search and view all 152 supported profiles
- **Profile Details** - View entities, datafields, and raw JSON for each profile

<img width="2071" height="949" alt="grafik" src="https://github.com/user-attachments/assets/3de488a6-a8b0-4305-80e4-033d65c770ba" />


### 🔧 Advanced Features
- **Custom EEP Profiles** - Override or add custom profiles via `/config/enocean_custom_profiles/`
- **Profile Overrides** - Tweak existing profiles without modifying built-in definitions
- **Device Editing** - Change EEP profile, name, manufacturer after adding
- **RSSI Monitoring** - Track signal strength for each device
- **Last Seen** - Monitor device activity and connectivity

### 📡 Supported Devices
- **152 EEP Profiles** including:
  - Temperature & Humidity Sensors (A5-02, A5-04)
  - Door/Window Contacts (D5-00)
  - Motion Sensors (A5-07, A5-08)
  - Light Switches (F6-02, F6-03)
  - Actuators (A5-38)
  - **Custom Devices** (MV-01 for Kessel Staufix Control, etc.)

## 🚀 Quick Start

### Installation

1. **Add Repository** to Home Assistant:
   ```
   https://github.com/ESDN83/ha-enocean-mqtt-slim
   ```

2. **Install** the addon from the Add-on Store

3. **Configure** your serial port:
   - Go to Settings → Add-ons → EnOcean MQTT Slim
   - Select your EnOcean USB gateway (e.g., `/dev/ttyUSB0`)
   - Start the addon

4. **Open Web UI** and start adding devices!

### Adding Devices

#### Method 1: Automatic (Recommended)
1. Open the Web UI
2. Put your EnOcean device in teach-in mode (press learn button)
3. Device is automatically detected and added!
4. Check Home Assistant for new entities

#### Method 2: Manual
1. Open the Web UI
2. Click "Add Device"
3. Enter Device ID (8-character hex, e.g., `05834fa4`)
4. Enter Device Name
5. Select EEP Profile
6. Click "Save Device"

## 📖 Documentation

### Table of Contents
- [Custom EEP Profiles](#custom-eep-profiles)
- [Kessel Staufix Control Setup](#kessel-staufix-control-setup)
- [Creating Custom EEP Profiles](#creating-custom-eep-profiles)
- [Configuration](#configuration)
- [How Teach-In Works](#how-teach-in-works)
- [Troubleshooting](#troubleshooting)

---

## Custom EEP Profiles

You can override built-in profiles or add completely new ones by placing JSON files in `/config/enocean_custom_profiles/`.

### Quick Start

1. **Create directory** (if it doesn't exist):
   ```bash
   mkdir -p /config/enocean_custom_profiles/
   ```

2. **Add JSON file** with your custom profile (e.g., `MV-01-01.json`)

3. **Restart addon** - Custom profile will override built-in version

### Profile Structure

```json
{
  "eep": "MV-01-01",
  "rorg_number": "0xA5",
  "telegram": "4BS",
  "func_number": "0x01",
  "type_number": "0x01",
  "type_title": "My Custom Device",
  "manufacturer": "Custom",
  "description": "Custom device profile",
  "objects": {
    "AL": {
      "name": "Alarm",
      "component": "binary_sensor",
      "device_class": "problem",
      "icon": "mdi:alert"
    }
  },
  "case": [
    {
      "datafield": [
        {
          "shortcut": "AL",
          "bitoffs": "29",
          "bitsize": "1",
          "value": {
            "==": [
              {"var": "value"},
              1
            ]
          }
        }
      ]
    }
  ]
}
```

---

## Kessel Staufix Control Setup

The Kessel Staufix Control is a special device that uses a custom MV-01-01 profile. This section provides complete setup instructions.

### Overview

**Device:** Kessel Staufix Control  
**EEP Profile:** MV-01-01 (Custom)  
**Manufacturer:** Kessel  
**Function:** Wastewater backflow prevention alarm

### Features

- **Alarm Status** - Binary sensor showing problem/normal state
- **Signal Strength** - RSSI sensor for monitoring connection quality
- **Last Seen** - Timestamp of last communication

### Setup Instructions

#### 1. Add Device

**Option A: Manual (Recommended for Staufix)**
1. Open Web UI
2. Click "Add Device"
3. Enter:
   - **Device ID:** Your 8-character hex ID (e.g., `05834fa4`)
   - **Name:** `Staufix` (or your preferred name)
   - **EEP Profile:** Select `MV-01-01 - Kessel Staufix Control`
   - **Manufacturer:** `Kessel`
4. Click "Save Device"

**Option B: Automatic**
1. Press the Alert or OK button on your Staufix device
2. Device should be auto-detected (may require multiple button presses)

#### 2. Verify in Home Assistant

After adding, you should see:

**Device:** Staufix  
**Entities:**
- `binary_sensor.staufix_alarm` - Alarm status (ON = problem, OFF = normal)
- `sensor.staufix_rssi` - Signal strength in dBm
- `sensor.staufix_last_seen` - Last update timestamp

#### 3. Test Functionality

- **Press Alert button** → Alarm should show ON (problem)
- **Press OK button** → Alarm should show OFF (normal)

### Understanding the Data

The Staufix sends non-standard EnOcean telegrams:

```
Telegram: a5 01 00 00 0d 05 83 4f a4 80
          ↑  ↑---------↑  ↑---------↑  ↑
        RORG  DB3-DB0     Device ID   Status
              (data)      (real ID)
```

**Key Points:**
- Always sends with LRN bit = 0 (looks like teach-in, but it's data!)
- Real device ID is in data bytes 5-8
- Alarm bit is at bit offset 29 (DB0, bit 5)

### Customizing the Profile

If you need to adjust the Staufix profile:

1. **Create custom profile:**
   ```bash
   mkdir -p /config/enocean_custom_profiles/
   ```

2. **Copy and edit:**
   ```bash
   # Copy built-in profile as template
   cat > /config/enocean_custom_profiles/MV-01-01.json << 'EOF'
   {
     "eep": "MV-01-01",
     "rorg_number": "0xA5",
     "telegram": "4BS",
     "func_number": "0x01",
     "type_number": "0x01",
     "type_title": "Kessel Staufix Control",
     "manufacturer": "Kessel",
     "description": "Wastewater backflow prevention alarm",
     "objects": {
       "AL": {
         "name": "Alarm",
         "component": "binary_sensor",
         "device_class": "problem",
         "icon": "mdi:pipe-valve",
         "description": "Staufix alarm status"
       },
       "rssi": {
         "name": "RSSI",
         "component": "sensor",
         "device_class": "signal_strength",
         "unit": "dBm",
         "icon": "mdi:wifi"
       },
       "last_seen": {
         "name": "Last Seen",
         "component": "sensor",
         "device_class": "timestamp",
         "icon": "mdi:clock-outline"
       }
     },
     "case": [
       {
         "datafield": [
           {
             "shortcut": "AL",
             "bitoffs": "29",
             "bitsize": "1",
             "value": {
               "==": [
                 {"var": "value"},
                 1
               ]
             }
           }
         ]
       }
     ]
   }
   EOF
   ```

3. **Restart addon** to load custom profile

### Troubleshooting Staufix

**Problem: Device not detected**
- Press Alert or OK button multiple times
- Check addon logs for "TELEGRAM RECEIVED"
- Verify device ID in logs matches your device

**Problem: Alarm sensor not showing**
- Delete device in Web UI
- Delete MQTT discovery topics in MQTT Explorer
- Restart addon
- Re-add device

**Problem: Alarm always shows same state**
- Press both Alert and OK buttons to test
- Check MQTT Explorer for state changes
- Verify `{"AL": 0}` or `{"AL": 1}` in state topic

---

## Creating Custom EEP Profiles

This guide explains how to create custom EEP profiles for devices not in the standard database.

### Step 1: Understand Your Device

You need to know:
1. **Device ID** - 8-character hex (e.g., `05834fa4`)
2. **RORG** - Radio telegram type (e.g., `0xA5` for 4BS)
3. **Data structure** - Which bits represent which values
4. **Entity types** - What sensors/binary sensors to create

### Step 2: Capture Raw Telegrams

1. Enable debug logging in addon
2. Trigger your device (press button, etc.)
3. Check logs for telegram data:
   ```
   📡 TELEGRAM RECEIVED
   Data: a5 01 00 00 0d 05 83 4f a4 80
   ```

### Step 3: Analyze Data Structure

For 4BS (RORG 0xA5) telegrams:
```
Byte 0: RORG (0xA5)
Byte 1: DB3 (data byte 3)
Byte 2: DB2 (data byte 2)
Byte 3: DB1 (data byte 1)
Byte 4: DB0 (data byte 0)
Byte 5-8: Sender ID or additional data
Byte 9: Status
```

**Bit numbering:**
- Bit 0 = MSB of DB3
- Bit 31 = LSB of DB0

### Step 4: Create Profile JSON

```json
{
  "eep": "XX-YY-ZZ",
  "rorg_number": "0xA5",
  "telegram": "4BS",
  "func_number": "0xYY",
  "type_number": "0xZZ",
  "type_title": "Your Device Name",
  "manufacturer": "Manufacturer Name",
  "description": "Device description",
  "objects": {
    "SHORTCUT1": {
      "name": "Entity Name",
      "component": "sensor",
      "device_class": "temperature",
      "unit": "°C",
      "icon": "mdi:thermometer"
    },
    "SHORTCUT2": {
      "name": "Switch State",
      "component": "binary_sensor",
      "device_class": "opening",
      "icon": "mdi:door"
    }
  },
  "case": [
    {
      "datafield": [
        {
          "shortcut": "SHORTCUT1",
          "bitoffs": "8",
          "bitsize": "8",
          "value": {
            "*": [
              {"var": "value"},
              0.1
            ]
          }
        },
        {
          "shortcut": "SHORTCUT2",
          "bitoffs": "31",
          "bitsize": "1"
        }
      ]
    }
  ]
}
```

### Step 5: Define Datafields

Each datafield extracts a value from the telegram:

```json
{
  "shortcut": "TEMP",        // Must match key in "objects"
  "bitoffs": "8",            // Bit offset (0-31 for 4BS)
  "bitsize": "8",            // Number of bits to extract
  "value": {                 // Optional: transform value
    "*": [                   // Multiply
      {"var": "value"},      // Raw extracted value
      0.1                    // Factor
    ]
  }
}
```

**Common transformations:**

**Multiply:**
```json
"value": {
  "*": [{"var": "value"}, 0.1]
}
```

**Add offset:**
```json
"value": {
  "+": [{"var": "value"}, -40]
}
```

**Scale and offset:**
```json
"value": {
  "+": [
    {"*": [{"var": "value"}, 0.1]},
    -40
  ]
}
```

**Boolean (equals):**
```json
"value": {
  "==": [{"var": "value"}, 1]
}
```

### Step 6: Component Types

**Sensor (numeric values):**
```json
{
  "component": "sensor",
  "device_class": "temperature",  // temperature, humidity, pressure, etc.
  "unit": "°C"
}
```

**Binary Sensor (on/off):**
```json
{
  "component": "binary_sensor",
  "device_class": "opening",  // opening, motion, problem, etc.
  "icon": "mdi:door"
}
```

### Step 7: Test Your Profile

1. Save profile to `/config/enocean_custom_profiles/XX-YY-ZZ.json`
2. Restart addon
3. Check logs for: `🔄 Overriding EEP profile: XX-YY-ZZ`
4. Add device with your custom profile
5. Trigger device and check if entities update

### Example: Temperature Sensor

```json
{
  "eep": "A5-02-05",
  "rorg_number": "0xA5",
  "telegram": "4BS",
  "func_number": "0x02",
  "type_number": "0x05",
  "type_title": "Temperature Sensor 0°C to +40°C",
  "manufacturer": "Generic",
  "description": "Temperature sensor with 0-40°C range",
  "objects": {
    "TMP": {
      "name": "Temperature",
      "component": "sensor",
      "device_class": "temperature",
      "unit": "°C",
      "icon": "mdi:thermometer"
    }
  },
  "case": [
    {
      "datafield": [
        {
          "shortcut": "TMP",
          "bitoffs": "16",
          "bitsize": "8",
          "value": {
            "*": [
              {"var": "value"},
              0.15686
            ]
          }
        }
      ]
    }
  ]
}
```

### Example: Door/Window Contact

```json
{
  "eep": "D5-00-01",
  "rorg_number": "0xD5",
  "telegram": "1BS",
  "func_number": "0x00",
  "type_number": "0x01",
  "type_title": "Door/Window Contact",
  "manufacturer": "Generic",
  "description": "Single contact",
  "objects": {
    "CO": {
      "name": "Contact",
      "component": "binary_sensor",
      "device_class": "opening",
      "icon": "mdi:door"
    }
  },
  "case": [
    {
      "datafield": [
        {
          "shortcut": "CO",
          "bitoffs": "0",
          "bitsize": "1",
          "invert": true
        }
      ]
    }
  ]
}
```

---

## Configuration

The addon uses environment variables from Home Assistant:

- `SERIAL_PORT` - EnOcean USB gateway device
- `MQTT_HOST` - MQTT broker (auto-configured by HA)
- `MQTT_PORT` - MQTT port (default: 1883)
- `MQTT_USER` - MQTT username (auto-configured)
- `MQTT_PASSWORD` - MQTT password (auto-configured)
- `LOG_LEVEL` - Logging level (debug, info, warning, error)

---

## How Teach-In Works

### UTE (Universal Teach-In) Process

1. **Device sends teach-in telegram**
   - Contains EEP profile information
   - Contains real device ID in data payload
   - LRN bit = 0 (teach-in mode)

2. **Addon detects and parses**
   - Extracts FUNC and TYPE from telegram
   - Constructs EEP code (e.g., A5-30-03)
   - Extracts real device ID from data bytes 5-8
   - Looks up profile in database

3. **Addon adds device**
   - Creates device with detected EEP
   - Publishes MQTT discovery
   - Sends teach-in response back to device

4. **Device receives response**
   - Confirms successful learning
   - Exits teach-in mode
   - Starts sending normal data telegrams

5. **Data flows to Home Assistant**
   - Device sends data telegrams
   - Addon parses using EEP profile
   - Publishes to MQTT
   - Entities update in Home Assistant

---

## Troubleshooting

### Device Not Detected

**Check logs** for teach-in telegrams:
```
🎓 TEACH-IN TELEGRAM DETECTED!
   Device ID: c0206880
   📱 Real Device ID (from data): 05834fa4
   📋 Detected EEP: A5-30-03
```

If you see this, the device was detected. If not:
- Ensure device is in teach-in mode
- Check serial port connection
- Verify gateway is working

### Device Added But No Data

**Check if teach-in response was sent**:
```
📤 Sending teach-in response to device...
✅ Teach-in response sent! Device should exit learn mode.
```

If not sent:
- Device may need manual teach-in completion
- Try pressing learn button again
- Check if device supports UTE

### Wrong EEP Profile

**Edit device** in Web UI:
1. Click pencil icon next to device
2. Change EEP Profile dropdown
3. Click "Save Device"
4. Device will use new profile immediately

### Custom Profile Not Loading

**Check logs** for:
```
🔄 Overriding EEP profile: MV-01-01 with custom version
```

If not shown:
- Verify file is in `/config/enocean_custom_profiles/`
- Check JSON syntax is valid
- Restart addon

### Entities Not Appearing in HA

1. **Check MQTT Explorer** for discovery topics under `homeassistant/`
2. **Delete old discovery** topics if they exist
3. **Restart addon** to republish
4. **Check HA logs** for MQTT integration errors

---

## 📊 Web UI Features

### Dashboard
- Gateway status and information
- MQTT connection status
- Device count
- EEP profile browser
- Auto-detect mode

### Device Management
- List all devices with status
- Edit device properties
- Enable/disable devices
- Delete devices
- View last seen and RSSI

### EEP Profiles
- Browse 152 built-in profiles
- Search by EEP code, name, or description
- View profile details
- See entities and datafields
- View raw JSON

---

## 🛠️ Development

### Project Structure
```
addon/
├── config.yaml              # Addon configuration
├── icon.png                 # Addon icon
├── rootfs/
│   └── app/
│       ├── main.py          # Main application
│       ├── core/            # Core functionality
│       │   ├── serial_handler.py
│       │   ├── esp3_protocol.py
│       │   ├── mqtt_handler.py
│       │   └── device_manager.py
│       ├── eep/             # EEP handling
│       │   ├── loader.py
│       │   ├── parser.py
│       │   └── definitions/ # 152 EEP profiles
│       └── web_ui/          # Web interface
│           ├── app.py
│           └── templates/
```

### Building

```bash
# Build for all architectures
docker buildx build --platform linux/amd64,linux/arm64,linux/armv7 -t enocean-mqtt-slim .

# Build for local testing
docker build -t enocean-mqtt-slim .
```

---

## 📝 Changelog

### v1.0.27 (Latest)
- ✅ Added availability payload definitions to MQTT discovery
- ✅ Prevents "unknown device" creation in Home Assistant
- ✅ Complete Kessel Staufix Control support

### v1.0.26
- ✅ Fixed binary_sensor Jinja2 template syntax
- ✅ Proper ON/OFF conversion for binary sensors

### v1.0.25
- ✅ Fixed timestamp format to ISO 8601 with Z suffix
- ✅ UTC timezone support

### v1.0.24
- ✅ Fixed binary_sensor value template for ON/OFF states

### v1.0.23
- ✅ Fixed parser string to int conversion for bitoffs/bitsize

### v1.0.22
- ✅ Fixed parser to use correct data bytes (1-4) for 4BS telegrams

### v1.0.21
- ✅ Fixed device ID detection for non-standard devices
- ✅ Bypass teach-in detection for configured devices

### v1.0.20
- ✅ Added UTE teach-in response for proper device learning
- ✅ Device exits teach-in mode automatically
- ✅ Normal data telegrams start immediately
- ✅ Updated Web UI version display
- ✅ Added EnOcean icon
- ✅ Added custom EEP profile override support

### v1.0.19
- ✅ Extract real device ID from teach-in data payload
- ✅ Fixed device matching for normal telegrams
- ✅ Proper device ID handling

### v1.0.18
- ✅ Automatic device detection from teach-in telegrams
- ✅ Auto-detect EEP profile (FUNC + TYPE extraction)
- ✅ Auto-add devices with correct profile
- ✅ MQTT discovery published automatically

### v1.0.14
- ✅ Initial release
- ✅ Web UI for device management
- ✅ 152 EEP profiles
- ✅ MQTT integration
- ✅ Home Assistant discovery

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Based on the original [enoceanmqtt](https://github.com/romor/enoceanmqtt) project
- EnOcean Alliance for EEP specifications
- Home Assistant community
- Special thanks to all contributors and testers

---

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/ESDN83/ha-enocean-mqtt-slim/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ESDN83/ha-enocean-mqtt-slim/discussions)
- **Documentation**: [Wiki](https://github.com/ESDN83/ha-enocean-mqtt-slim/wiki)

---

Made with ❤️ for the Home Assistant community
