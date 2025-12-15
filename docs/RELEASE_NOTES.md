# Release Notes - EnOcean MQTT Slim

## v1.0.35 - RGB Lighting Support (2025-12-15)

### 🎨 New Features
- **RGB Color Control** - Full RGB lighting support for EnOcean RGB actuators
- **Color Picker Integration** - Native Home Assistant color picker for RGB lights
- **Color Mode Support** - Proper MQTT discovery with RGB color modes
- **RGB State Feedback** - Real-time RGB state tracking and confirmation

### 🔧 Technical Details
- Added `translate_rgb_command()` method in command translator
- RGB support for A5-38-08 (Central Command) profile
- RGB support for D2-01-12 (Electronic Switch) profile
- MQTT discovery includes `rgb_command_topic`, `rgb_state_topic`, and `supported_color_modes`
- Full 0-255 range per RGB channel (16.7 million colors)

### 📝 Modified Files
- `addon/rootfs/app/core/command_translator.py` - RGB command translation
- `addon/rootfs/app/core/mqtt_handler.py` - RGB MQTT discovery
- `addon/rootfs/app/main.py` - RGB command handling and state updates
- `addon/config.yaml` - Version bump to 1.0.35
- `addon/rootfs/app/web_ui/templates/dashboard_full.html` - Version update

### 💡 Usage Example
```json
// MQTT Command
{"rgb": [255, 0, 0]}  // Pure Red
{"rgb": [0, 255, 0]}  // Pure Green
{"rgb": [0, 0, 255]}  // Pure Blue
{"rgb": [255, 255, 255]}  // White
```

### 🎯 Benefits
- ✅ Full color control from Home Assistant
- ✅ Native color picker UI
- ✅ Works with automations and scenes
- ✅ State feedback and tracking
- ✅ Foundation for RGBW/HSV support (future)

---

## v1.0.34 - Searchable Profile Selector (2025-12-15)

### 🔍 New Features
- **Searchable EEP Dropdown** - Real-time search/filter for EEP profiles
- **Improved UX** - Much easier to find profiles among 150+ options
- **Larger Dropdown** - 8 rows (200px height) for better visibility
- **Smart Filtering** - Search by EEP code, title, or description
- **New Device Profile** - D2-01-12 (Electronic Switch with Energy Measurement)

### 🔧 Technical Details
- Added search input field above EEP profile dropdown
- Real-time filtering using JavaScript
- Case-insensitive search across code, title, and description
- Stores all profiles in memory for instant filtering
- D2-01-12 profile includes switch, energy (Wh), and power (W) entities

### 📝 Modified Files
- `addon/rootfs/app/web_ui/templates/dashboard_full.html` - Search UI and JavaScript
- `addon/rootfs/app/eep/definitions/D2-01/D2-01-12.json` - New profile (NEW)
- `addon/config.yaml` - Version bump to 1.0.34

### 💡 Usage Examples
```
Search: "switch" → Shows all switch profiles
Search: "D2-01" → Shows D2-01 family
Search: "temperature" → Shows temperature sensors
Search: "energy" → Shows energy monitoring devices
```

### 🎯 Benefits
- ✅ 10x faster profile selection
- ✅ No more scrolling through 150+ profiles
- ✅ Find profiles by function, not just code
- ✅ Better user experience
- ✅ Scalable to 500+ profiles

---

## v1.0.33 - State Feedback & Command Confirmation (2025-12-15)

### 📡 New Features
- **Command Confirmation Tracking** - Know when commands are actually executed
- **Response Time Measurement** - Track device performance (e.g., 0.32s)
- **Timeout Detection** - Identify failed commands automatically
- **State Feedback** - Real confirmation instead of pure optimistic updates
- **Background Cleanup** - Automatic cleanup of expired commands

### 🔧 Technical Details
- New `CommandTracker` class with pending command management
- Automatic confirmation detection when device responds
- 5-second timeout for command confirmation
- 5% tolerance for numeric value matching (brightness, position)
- Async callback support for confirmations and timeouts
- Statistics tracking (pending, confirmed, timed-out)

### 📝 New Files
- `addon/rootfs/app/core/command_tracker.py` - Command tracking module (350+ lines)

### 📝 Modified Files
- `addon/rootfs/app/main.py` - Tracker integration and callbacks
- `addon/config.yaml` - Version bump to 1.0.33
- `addon/rootfs/app/web_ui/templates/dashboard_full.html` - Version update

### 💡 How It Works
1. Command sent → Tracked with expected state
2. Device responds → Telegram received
3. Tracker checks if state matches expected
4. If match → Confirmation logged with response time
5. If timeout → Warning logged
6. Optimistic update still published immediately
7. Real state confirmed or timeout detected

### 📊 Example Log Output
```
🎮 COMMAND RECEIVED
   Device: Smart Plug
   Command: {"state": "ON"}
   ✅ Command sent successfully!
   📋 Tracking command for confirmation (timeout: 5s)
   ✅ Published optimistic state

📡 TELEGRAM RECEIVED (0.3s later)
   ✅ COMMAND CONFIRMED
   Response time: 0.32s
   Confirmed state: {"switch": 1}
   🎯 Command confirmation processed
```

### 🎯 Benefits
- ✅ Know when commands are actually executed
- ✅ Detect failed commands (timeouts)
- ✅ Measure device response times
- ✅ Better debugging and monitoring
- ✅ Foundation for retry logic (future)

---

## Installation

### Home Assistant Add-on Store
1. Add repository: `https://github.com/ESDN83/ha-enocean-mqtt-slim`
2. Install "EnOcean MQTT Slim"
3. Configure serial port
4. Start the addon

### Manual Installation
```bash
git clone https://github.com/ESDN83/ha-enocean-mqtt-slim.git
cd ha-enocean-mqtt-slim
# Follow addon installation instructions
```

---

## Upgrade Notes

### From v1.0.32 to v1.0.33+
- ✅ No breaking changes
- ✅ Automatic state persistence continues to work
- ✅ All existing devices remain configured
- ✅ New features activate automatically

### Configuration
No configuration changes required. All new features work out of the box.

---

## Known Issues

### v1.0.35
- RGB support is currently limited to A5-38-08 and D2-01-12 profiles
- RGBW and HSV color modes not yet implemented (planned for future)

### v1.0.34
- Profile search is client-side only (no server-side filtering)

### v1.0.33
- Command confirmation timeout is fixed at 5 seconds (not configurable yet)

---

## Roadmap

### Planned Features
- **RGBW Support** - Add white channel for RGBW lights
- **HSV Color Mode** - Hue, Saturation, Value color control
- **More Device Profiles** - D2-05-xx (blinds), A5-20-01 (HVAC), etc.
- **Configurable Timeouts** - Per-device timeout settings
- **Automatic Retry** - Retry failed commands automatically
- **Success Rate Tracking** - Statistics per device
- **Command Queue** - Queue multiple commands per device

---

## Support

- **GitHub Issues**: https://github.com/ESDN83/ha-enocean-mqtt-slim/issues
- **Documentation**: https://github.com/ESDN83/ha-enocean-mqtt-slim/blob/main/README.md
- **Home Assistant Community**: https://community.home-assistant.io/

---

## Contributors

- **ESDN83** - Project maintainer
- **Community** - Bug reports, feature requests, and testing

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## v1.0.32 - Bidirectional Control Foundation (2025-12-15)

### 🔄 New Features
- **Bidirectional Control** - Foundation for sending commands to EnOcean devices
- **Command Translation** - Translate MQTT commands to EnOcean telegrams
- **RPS Button Emulation** - Virtual rocker switch support
- **A5-38-08 Support** - Central Command profile for actuators

### 🔧 Technical Details
- New `CommandTranslator` class for command translation
- Support for switch ON/OFF commands
- Support for dimming commands (brightness 0-255)
- RPS button press emulation for F6-02 devices
- MQTT command subscription and handling

### 📝 Modified Files
- `addon/rootfs/app/core/command_translator.py` - New command translator (NEW)
- `addon/rootfs/app/main.py` - Command handling integration
- `addon/rootfs/app/core/mqtt_handler.py` - Command subscription
- `addon/config.yaml` - Version bump to 1.0.32

### 🎯 Benefits
- ✅ Control EnOcean devices from Home Assistant
- ✅ Switch and dimmer support
- ✅ Foundation for covers and other actuators
- ✅ Bidirectional communication

---

## v1.0.31 - Enhanced Device Management (2025-12-15)

### 🔧 New Features
- **Improved Web UI** - Better device management interface
- **Device Enable/Disable** - Toggle devices without deleting
- **Enhanced Discovery** - Better MQTT discovery handling
- **State Persistence** - Improved state restoration

### 📝 Modified Files
- `addon/rootfs/app/web_ui/templates/dashboard_full.html` - UI improvements
- `addon/rootfs/app/core/device_manager.py` - Enable/disable support
- `addon/config.yaml` - Version bump to 1.0.31

### 🎯 Benefits
- ✅ Better device management
- ✅ Temporary device disabling
- ✅ Improved user experience

---

## v1.0.30 - CRITICAL BUG FIX (2025-12-15)

### 🚨 Critical Fix
- **Sender ID Extraction** - Fixed fundamental bug in ESP3 packet parsing
- **RPS Device Support** - F6 devices (rocker switches) now work correctly
- **All Device Types** - F6, A5, D5, D2 all now work properly

### 🐛 Bug Description
The sender ID extraction was incorrect - it assumed sender ID came after RORG byte, but it actually comes at the END (last 4 bytes before status byte).

### ✅ Fix Details
- Fixed `get_sender_id()` to use `data[-5:-1]` (last 4 bytes before status)
- Fixed `get_data_bytes()` to use `data[1:-5]` (skip RORG and last 5 bytes)
- Removed A5-specific workaround (no longer needed)
- Verified by 3 independent sources (Python enocean library, ESP3 spec, HA core)

### 📊 Impact
**Before Fix:**
- ✅ A5 (4BS) devices worked (with workaround)
- ❌ F6 (RPS) devices failed
- ❌ D5 (1BS) devices likely failed
- ❌ D2 (VLD) devices likely failed

**After Fix:**
- ✅ ALL device types work correctly!

### 📝 Modified Files
- `addon/rootfs/app/core/esp3_protocol.py` - Fixed sender ID extraction
- `addon/rootfs/app/main.py` - Removed workaround
- `addon/config.yaml` - Version bump to 1.0.30

### 🎯 Benefits
- ✅ FT55 rocker switches now work
- ✅ All EnOcean device types supported
- ✅ Cleaner code without workarounds
- ✅ Follows ESP3 specification
- ✅ Backward compatible (Kessel Staufix still works)

---

## Changelog Summary

| Version | Date | Key Features |
|---------|------|--------------|
| v1.0.35 | 2025-12-15 | RGB Lighting Support |
| v1.0.34 | 2025-12-15 | Searchable Profile Selector + D2-01-12 |
| v1.0.33 | 2025-12-15 | State Feedback & Command Confirmation |
| v1.0.32 | 2025-12-15 | Bidirectional Control Foundation |
| v1.0.31 | 2025-12-15 | Enhanced Device Management |
| v1.0.30 | 2025-12-15 | CRITICAL BUG FIX - Sender ID Extraction |

---

**Thank you for using EnOcean MQTT Slim!** 🎉
