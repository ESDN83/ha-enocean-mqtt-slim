# Changelog

## [1.0.3] - 2025-12-12

### Added
- **Complete Device Management UI** - Full web-based device management
- Interactive device list table with real-time updates
- Add device modal with form validation
- Edit device functionality
- Delete device with confirmation
- Enable/Disable toggle buttons
- EEP profile selector dropdown
- Gateway information modal with real data
- EEP profiles viewer modal
- Real-time status updates (auto-refresh every 30 seconds)
- Visual feedback for all actions
- Responsive Bootstrap 5 design

### Features
- ✅ Add devices via web UI (no manual JSON editing!)
- ✅ Edit device name, EEP, manufacturer
- ✅ Enable/disable devices with one click
- ✅ Delete devices (removes from HA automatically)
- ✅ View gateway information (Base ID, version, chip ID)
- ✅ Browse available EEP profiles
- ✅ Real-time device status (last seen, RSSI)
- ✅ Status indicators for Gateway and MQTT
- ✅ Device count badges
- ✅ Hover effects and smooth animations

### API
- Complete REST API for device management
- Service state manager for real-time data
- All endpoints return actual service data (no fake data)

### UI Improvements
- Professional table layout for devices
- Action buttons (Edit, Enable/Disable, Delete)
- Modal dialogs for forms
- Success/error messages
- Loading states
- Empty state with call-to-action

## [1.0.2] - 2025-12-12

### Added
- MQTT handler with Home Assistant auto-discovery
- Device manager with JSON-based storage (/data/devices.json)
- Complete telegram processing pipeline
- Automatic device state publishing to MQTT
- Device availability tracking
- Last seen tracking with RSSI
- Device enable/disable functionality

### Features
- Parse EnOcean telegrams using EEP profiles
- Publish parsed data to MQTT (enocean/{device_id}/state)
- Home Assistant MQTT discovery for automatic entity creation
- Availability topics (enocean/{device_id}/availability)
- Teach-in detection (logged but not yet interactive)

### Integration
- Devices stored in /data/devices.json
- MQTT topics: enocean/{device_id}/state
- HA discovery topics: homeassistant/{component}/{unique_id}/config
- Full support for Kessel Staufix Control (MV-01-01)

## [1.0.1] - 2025-12-12

### Fixed
- Removed Docker image reference (addon builds locally now)
- Added comprehensive description for HA addon store
- Fixed configuration to work with local builds

### Added
- Detailed description in config.yaml
- CHANGELOG.md for version tracking

## [1.0.0] - 2025-12-12

### Added
- Initial release
- MIT License
- Complete project structure
- MV-01-01 EEP profile for Kessel Staufix Control
- FastAPI web UI framework
- SQLite database structure
- MQTT integration architecture
- Comprehensive documentation
