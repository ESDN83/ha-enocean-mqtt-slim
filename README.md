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
  - Custom Devices (MV-01 for Kessel Staufix Control, etc.)

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

### Custom EEP Profiles

You can override built-in profiles or add completely new ones:

1. **Create directory** (if it doesn't exist):
   ```
   /config/enocean_custom_profiles/
   ```

2. **Add JSON file** with your custom profile:
   ```json
   {
     "eep": "MV-01-01",
     "rorg_number": "0xA5",
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
             "data": "db0",
             "bitoffs": "0",
             "bitsize": "1",
             "value": {
               "0": "Normal",
               "1": "Alarm"
             }
           }
         ]
       }
     ]
   }
   ```

3. **Restart addon** - Custom profile will override built-in version

### Example: Kessel Staufix Control

The Kessel Staufix Control uses a custom MV-01-01 profile. To customize it:

1. Copy the built-in profile:
   ```bash
   cp /addon_configs/.../eep/definitions/MV-01/MV-01-01.json /config/enocean_custom_profiles/MV-01-01.json
   ```

2. Edit the file to adjust datafield parsing

3. Restart the addon

### Configuration

The addon uses environment variables from Home Assistant:

- `SERIAL_PORT` - EnOcean USB gateway device
- `MQTT_HOST` - MQTT broker (auto-configured by HA)
- `MQTT_PORT` - MQTT port (default: 1883)
- `MQTT_USER` - MQTT username (auto-configured)
- `MQTT_PASSWORD` - MQTT password (auto-configured)
- `LOG_LEVEL` - Logging level (debug, info, warning, error)

## 🎓 How Teach-In Works

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

## 🔍 Troubleshooting

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

## 📝 Changelog

### v1.0.20 (Latest)
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

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on the original [enoceanmqtt](https://github.com/romor/enoceanmqtt) project
- EnOcean Alliance for EEP specifications
- Home Assistant community

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/ESDN83/ha-enocean-mqtt-slim/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ESDN83/ha-enocean-mqtt-slim/discussions)
- **Documentation**: [Wiki](https://github.com/ESDN83/ha-enocean-mqtt-slim/wiki)

---

Made with ❤️ for the Home Assistant community
