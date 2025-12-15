# EnOcean MQTT Slim

[![GitHub Release](https://img.shields.io/github/v/release/ESDN83/ha-enocean-mqtt-slim)](https://github.com/ESDN83/ha-enocean-mqtt-slim/releases)
[![License](https://img.shields.io/github/license/ESDN83/ha-enocean-mqtt-slim)](LICENSE)

A lightweight, modern EnOcean to MQTT bridge for Home Assistant with automatic device detection and a beautiful web UI.

![Web UI Screenshot](https://github.com/user-attachments/assets/3de488a6-a8b0-4305-80e4-033d65c770ba)

---

## ✨ Key Features

- 🎯 **Zero Configuration** - Automatic device detection via teach-in
- 🎨 **Modern Web UI** - Manage devices, browse 150+ EEP profiles with search
- 🔧 **Custom EEP Profiles** - Add or override profiles via `/config/enocean_custom_profiles/`
- 📡 **152 EEP Profiles** - Temperature, humidity, switches, contacts, and more
- 🏠 **MQTT Auto-Discovery** - Devices appear in Home Assistant automatically
- 🔄 **UTE Teach-In** - Proper teach-in completion for immediate operation
- 🔀 **Bidirectional Control** - Send commands to EnOcean actuators (switches, dimmers, RGB lights)
- 📊 **State Feedback** - Command confirmation tracking with response times
- 🎨 **RGB Lighting** - Full RGB color control with Home Assistant color picker
- 🔍 **Searchable Profiles** - Real-time search/filter for EEP profiles

---

## 🚀 Quick Start

### Installation

1. Add this repository to Home Assistant Add-on Store
2. Install "EnOcean MQTT Slim"
3. Configure your serial port (e.g., `/dev/ttyUSB0`)
4. Start the addon
5. Open Web UI and add devices!

### Adding Devices

**Automatic (Recommended):**
1. Open Web UI
2. Put device in teach-in mode (press learn button)
3. Device auto-detected and added!

**Manual:**
1. Open Web UI → Add Device
2. Enter Device ID, Name, and select EEP Profile
3. Save

---

## 📚 Documentation

### User Guides
- **[Installation & Setup](docs/IMPLEMENTATION_GUIDE.md)** - Complete installation guide
- **[Custom EEP Profiles](docs/CUSTOM_EEP_PROFILES_GUIDE.md)** - Create and override EEP profiles
- **[F6-02-01 Automation](docs/F6-02-01_AUTOMATION_GUIDE.md)** - Rocker switch automation examples
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Migrate from enoceanmqtt

### Technical Documentation
- **[Bug Analysis](docs/BUG_ANALYSIS_DEVICE_ID.md)** - Sender ID extraction fix details
- **[3-Source Verification](docs/VERIFICATION_3_SOURCES.md)** - Fix verification proof
- **[Kessel Staufix Analysis](docs/KESSEL_STAUFIX_ANALYSIS.md)** - Compatibility analysis

### Release Notes
- **[v1.0.30 (Latest)](docs/RELEASE_NOTES_v1.0.30_CRITICAL_FIX.md)** - Critical sender ID fix
- **[v1.0.29](docs/COMMUNITY_RESPONSE_v1.0.29.md)** - Community response
- **[v1.0.28](docs/RELEASE_NOTES_v1.0.28.md)** - Previous release
- **[v1.0.2](docs/RELEASE_NOTES_v1.0.2.md)** - Initial release

---

## 🔧 Configuration

### Serial Port
Select your EnOcean USB gateway:
- `/dev/ttyUSB0`
- `/dev/ttyAMA0`
- `/dev/serial/by-id/usb-EnOcean_...`

### Custom EEP Profiles
Place JSON files in `/config/enocean_custom_profiles/` to add or override profiles.

**Example:**
```json
{
  "eep": "MY-CUSTOM-01",
  "rorg_number": "0xa5",
  "type_title": "My Custom Sensor",
  "objects": {
    "temperature": {
      "name": "Temperature",
      "component": "sensor",
      "device_class": "temperature",
      "unit": "°C"
    }
  }
}
```

See **[Custom EEP Profiles Guide](docs/CUSTOM_EEP_PROFILES_GUIDE.md)** for complete documentation.

---

## 📡 Supported Devices

### 152 Built-in EEP Profiles

| Category | EEP Codes | Examples |
|----------|-----------|----------|
| **Temperature** | A5-02-xx | Temperature sensors (0-40°C, -40-80°C, etc.) |
| **Humidity** | A5-04-xx | Temperature + Humidity sensors |
| **Contacts** | D5-00-xx | Door/Window contacts |
| **Switches** | F6-02-xx, F6-03-xx | Rocker switches, push buttons |
| **Motion** | A5-07-xx, A5-08-xx | Occupancy sensors, motion detectors |
| **Actuators** | A5-38-xx | Dimming, switching actuators |
| **Custom** | MV-01-xx | Kessel Staufix Control, etc. |

**Browse all profiles:** [EEP Definitions on GitHub](https://github.com/ESDN83/ha-enocean-mqtt-slim/tree/main/addon/rootfs/app/eep/definitions)

---

## 🛠️ Development

### Project Structure
```
addon/
├── config.yaml              # Addon configuration
├── rootfs/app/
│   ├── main.py             # Main application
│   ├── core/               # Core functionality
│   ├── eep/                # EEP handling
│   │   └── definitions/    # 152 EEP profiles
│   └── web_ui/             # Web interface
docs/                        # Documentation
```

### Building
```bash
docker buildx build --platform linux/amd64,linux/arm64,linux/armv7 -t enocean-mqtt-slim .
```

---

## 🐛 Troubleshooting

### Device Not Detected
- Check serial port connection
- Enable debug logging
- Press teach-in button multiple times
- Check addon logs for "TELEGRAM RECEIVED"

### Entities Not Appearing
- Verify MQTT broker is running
- Check MQTT integration is configured
- Restart Home Assistant
- Check Web UI shows device as online

### Custom Profile Not Loading
- Verify file is in `/config/enocean_custom_profiles/`
- Check JSON syntax is valid
- Restart addon
- Check logs for "Overriding EEP profile" message

---

## 📝 Changelog

### v1.0.35 (Latest) - RGB Lighting Support
- 🎨 **RGB Color Control** - Full RGB lighting support for EnOcean RGB actuators
- 🎨 **Color Picker Integration** - Native Home Assistant color picker
- 🎨 **16.7 Million Colors** - Full 0-255 range per RGB channel

### v1.0.34 - Searchable Profile Selector
- 🔍 **Searchable EEP Dropdown** - Real-time search/filter for profiles
- 🔍 **10x Faster Selection** - Find profiles by code, title, or description
- 📦 **D2-01-12 Profile** - Electronic switch with energy measurement

### v1.0.33 - State Feedback & Command Confirmation
- 📊 **Command Confirmation** - Know when commands are actually executed
- ⏱️ **Response Time Measurement** - Track device performance
- ⚠️ **Timeout Detection** - Identify failed commands automatically

### v1.0.32 - Bidirectional Control
- 🔀 **Send Commands** - Control EnOcean actuators from Home Assistant
- 💡 **Switch & Dimmer Support** - ON/OFF and brightness control
- 🎮 **Command Translation** - MQTT to EnOcean telegram conversion

### v1.0.31 - Enhanced Device Management
- 🔧 **Improved Web UI** - Better device management interface
- ⏸️ **Enable/Disable Devices** - Toggle without deleting

### v1.0.30 - CRITICAL BUG FIX
- 🐛 **Fixed sender ID extraction** for ALL device types (F6, A5, D5, D2)
- ✅ FT55 rocker switches and RPS devices now work
- ✅ Verified by 3 independent sources

See **[Full Release Notes](docs/RELEASE_NOTES.md)** for complete details.

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test thoroughly
4. Submit a pull request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Based on [enoceanmqtt](https://github.com/romor/enoceanmqtt)
- EnOcean Alliance for EEP specifications
- Home Assistant community
- All contributors and testers

---

## 📧 Support

- **Issues:** [GitHub Issues](https://github.com/ESDN83/ha-enocean-mqtt-slim/issues)
- **Discussions:** [GitHub Discussions](https://github.com/ESDN83/ha-enocean-mqtt-slim/discussions)
- **Documentation:** [docs/](docs/)

---

Made with ❤️ for the Home Assistant community
