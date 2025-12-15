# EnOcean MQTT Slim v1.0.2 - Full MQTT Integration

## 🎉 Major Release - Production Ready!

This release brings complete MQTT integration with Home Assistant auto-discovery, making the addon fully functional for production use.

## ✨ New Features

### MQTT Integration
- **Home Assistant Auto-Discovery**: Devices automatically appear in Home Assistant
- **State Publishing**: Real-time device state updates via MQTT
- **Availability Tracking**: Online/offline status for each device
- **Discovery Topics**: Automatic entity creation with proper device classes and icons

### Device Management
- **JSON-Based Storage**: Devices stored in `/data/devices.json`
- **Enable/Disable**: Control which devices are active
- **Last Seen Tracking**: Monitor device activity with timestamps
- **RSSI Tracking**: Signal strength monitoring

### Telegram Processing
- **Complete Pipeline**: Receive → Parse → Publish workflow
- **EEP Profile Parsing**: Extract data using EnOcean Equipment Profiles
- **Teach-In Detection**: Identify new devices (logging only for now)
- **Error Handling**: Robust error handling and logging

## 📋 What's Included

### Core Components
- ✅ ESP3 Protocol Handler (packet parsing, CRC validation)
- ✅ Serial Communication (async, reconnection handling)
- ✅ MQTT Handler (paho-mqtt based, HA discovery)
- ✅ Device Manager (JSON storage, CRUD operations)
- ✅ EEP Loader & Parser (MV-01-01 for Kessel Staufix)
- ✅ Web UI (status dashboard, Bootstrap-based)

### Supported Devices
- **Kessel Staufix Control** (MV-01-01) - Backwater alarm system
- Ready for more EEP profiles to be added

## 🚀 Getting Started

### Installation
1. Add repository to Home Assistant: `https://github.com/ESDN83/ha-enocean-mqtt-slim`
2. Install "EnOcean MQTT Slim" addon
3. Configure serial port in addon configuration
4. Start the addon

### Adding Your First Device

Create `/data/devices.json`:
```json
{
  "05834fa4": {
    "id": "05834fa4",
    "name": "Staufix Control",
    "eep": "MV-01-01",
    "manufacturer": "Kessel",
    "enabled": true,
    "created_at": "2025-12-12T16:00:00",
    "last_seen": null,
    "rssi": null
  }
}
```

Restart the addon and the device will:
1. Publish MQTT discovery messages
2. Create entity: `binary_sensor.staufix_control_alarm`
3. Listen for telegrams
4. Update state automatically

## 📊 MQTT Topics

### Discovery
```
homeassistant/binary_sensor/enocean_05834fa4_AL/config
```

### State Updates
```
enocean/05834fa4/state
Payload: {"AL": 0} or {"AL": 1}
```

### Availability
```
enocean/05834fa4/availability
Payload: "online" or "offline"
```

## 🔧 Configuration

### Addon Options
- **serial_port**: Path to EnOcean USB stick (e.g., `/dev/ttyUSB0`)
- **log_level**: `debug`, `info`, `warning`, or `error`

### Environment Variables (Auto-configured)
- `MQTT_HOST`: MQTT broker hostname
- `MQTT_PORT`: MQTT broker port (default: 1883)
- `MQTT_USER`: MQTT username
- `MQTT_PASSWORD`: MQTT password

## 📝 Example Log Output

```
✓ Loaded 1 EEP profiles
✓ Serial port opened successfully
✓ Gateway Base ID: ffd1f400
✓ Gateway Version: 2.15.0.0
✓ Loaded 1 configured devices
✓ MQTT connected successfully
Published discovery for device 05834fa4 (Staufix Control)
Listening for EnOcean telegrams...

Received telegram from 05834fa4, RORG=0xa5, RSSI=-45dBm
  → Device: Staufix Control (MV-01-01)
  Parsed data: {'AL': 0}
  → Published to MQTT
```

## 🐛 Known Limitations

- Web UI for device management not yet implemented (manual JSON editing required)
- Interactive teach-in mode not yet available
- Only MV-01-01 EEP profile included (more coming soon)
- No device statistics or history yet

## 🔜 Coming Soon

- Web-based device management (add/edit/delete via UI)
- Interactive teach-in mode
- Additional EEP profiles (temperature sensors, switches, etc.)
- Device statistics and history
- Backup/restore functionality

## 📚 Documentation

- [README](https://github.com/ESDN83/ha-enocean-mqtt-slim/blob/main/README.md)
- [DOCS](https://github.com/ESDN83/ha-enocean-mqtt-slim/blob/main/addon/DOCS.md)
- [CHANGELOG](https://github.com/ESDN83/ha-enocean-mqtt-slim/blob/main/addon/CHANGELOG.md)

## 🙏 Credits

- EEP profile structure inspired by [ioBroker.enocean](https://github.com/Jey-Cee/ioBroker.enocean)
- Built for the Home Assistant community
- Developed by ESDN83

## 📄 License

MIT License - See [LICENSE](https://github.com/ESDN83/ha-enocean-mqtt-slim/blob/main/LICENSE) for details

---

**Full Changelog**: https://github.com/ESDN83/ha-enocean-mqtt-slim/compare/v1.0.1...v1.0.2
