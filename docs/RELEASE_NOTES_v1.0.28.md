# Release v1.0.28 - State Persistence and Restoration

## 🎉 Major Feature: State Persistence After Restart

This release adds automatic state persistence and restoration to prevent entities from showing as "unavailable" after Home Assistant or addon restarts.

## ✨ New Features

### State Persistence Manager
- **Automatic State Saving** - Device states are automatically saved to `/data/device_states.json`
- **State Restoration on Startup** - Last known states are republished after restart
- **Configurable Delay** - Set delay before restoration (1-60 seconds, default: 5)
- **Easy to Disable** - Can be turned off via configuration if not wanted

### MQTT Improvements
- **Retain Flag** - MQTT messages now use `retain=true` for persistence
- **QoS 1** - Improved message delivery reliability
- **Broker-Level Persistence** - MQTT broker stores last state for each device

## 🔧 Configuration Options

Two new configuration options added:

```yaml
restore_state: true          # Enable/disable state restoration (default: true)
restore_delay: 5             # Delay in seconds before restoration (default: 5)
```

## 📊 How It Works

### Normal Operation
1. Device sends telegram
2. Data is parsed and saved to file
3. State published to MQTT with retain flag
4. Home Assistant receives update

### After Restart
1. Addon starts and initializes
2. Waits configured delay (default: 5s)
3. Loads saved states from file
4. Republishes each state to MQTT
5. Entities show last known values immediately

## ✅ Benefits

**Before:**
- ❌ Entities show "unavailable" after restart
- ❌ Must wait for device to send new telegram
- ❌ Could take hours for battery-powered devices
- ❌ Automations may fail during unavailable period

**After:**
- ✅ Entities show last known state immediately
- ✅ No waiting for new telegrams
- ✅ Works for all devices (battery or mains-powered)
- ✅ Automations work immediately after restart
- ✅ Can be disabled if not wanted

## 🎯 Use Cases

This feature is especially useful for:
- **Battery-powered devices** that transmit infrequently
- **Critical automations** that need immediate state availability
- **Status monitoring** where "unavailable" is confusing
- **Kessel Staufix Control** and similar alarm devices

## 🚀 Upgrade Instructions

1. Update addon to v1.0.28 in Home Assistant
2. Restart addon (state restoration is enabled by default)
3. Test by restarting Home Assistant - entities should maintain their state!

## 🎛️ Disabling State Restoration

If you prefer the old behavior:
1. Go to Settings → Add-ons → EnOcean MQTT Slim → Configuration
2. Set `restore_state: false`
3. Restart addon

## 📝 Technical Details

### Files Added
- `addon/rootfs/app/core/state_persistence.py` - State persistence manager

### Files Modified
- `addon/rootfs/app/main.py` - Added state persistence integration
- `addon/rootfs/app/core/mqtt_handler.py` - Added retain flag support
- `addon/config.yaml` - Added new configuration options

### State Storage
States are stored in `/data/device_states.json` with format:
```json
{
  "device_id": {
    "state": {
      "AL": 0,
      "rssi": -83,
      "last_seen": "2025-12-13T00:59:18Z"
    },
    "saved_at": "2025-12-13T00:59:18Z"
  }
}
```

## 🐛 Bug Fixes

None in this release - pure feature addition.

## 📚 Documentation

- Updated README with state persistence information
- Added configuration examples
- Documented disable procedure

## 🙏 Acknowledgments

Thanks to all users who requested this feature and provided feedback on the Kessel Staufix Control integration!

## 📦 Full Changelog

See [CHANGELOG.md](addon/CHANGELOG.md) for complete version history.

---

**Previous Release:** [v1.0.27](https://github.com/ESDN83/ha-enocean-mqtt-slim/releases/tag/v1.0.27)  
**Repository:** https://github.com/ESDN83/ha-enocean-mqtt-slim  
**Issues:** https://github.com/ESDN83/ha-enocean-mqtt-slim/issues
