# Changelog

## [1.0.7] - 2025-12-12

### Added
- **Enhanced Logging** - Added detailed logging to all API endpoints for debugging
- Logs now show when each API endpoint is called
- Logs show service component availability (eep_loader, device_manager, mqtt_handler)
- Logs show actual data being returned from endpoints

### Fixed
- **Documentation** - Fixed misleading "150+ EEP profiles" claim
- Updated description to accurately reflect current MV-01-01 profile support
- Description now says "with more profiles coming soon"

### Debugging
- /api/status now logs service state and component availability
- /api/eep-profiles logs loader state and profile count
- /api/devices logs device manager state and device count
- All logs visible in addon logs for troubleshooting

## [1.0.6] - 2025-12-12

### Fixed
- **Critical: Service Initialization Order** - Fixed race condition causing 404 errors
- Service components now fully initialized BEFORE web UI starts accepting requests
- Moved `service_state.set_service()` call to AFTER `initialize()` completes
- This ensures eep_loader, device_manager, and mqtt_handler are available when API is called

### Technical Details
- Previously: service_state was set before initialization, causing components to be None
- Now: initialization completes first, then service is registered with state manager
- Web server still starts concurrently but components are guaranteed to exist
- Fixes 404 errors and JSON parsing issues caused by missing components

### Impact
- Resolves "Error loading devices" JSON parse errors
- Resolves 404 errors on /api/eep-profiles
- Resolves 404 errors on /api/status and /api/devices
- All API endpoints now work reliably on first load

## [1.0.5] - 2025-12-12

### Fixed
- **Complete JSON Response Fix** - Removed ALL JSONResponse wrappers
- Fixed POST/PUT/DELETE endpoints that were still using JSONResponse
- Removed unused JSONResponse import
- All endpoints now return plain Python dicts (FastAPI handles JSON conversion automatically)

### Technical Changes
- Removed JSONResponse from all API endpoints
- Simplified response handling throughout the application
- Better consistency across all endpoints

## [1.0.4] - 2025-12-12

### Fixed
- **JSON Parsing Errors** - Fixed "unexpected non-whitespace character" error
- Removed JSONResponse wrapper causing double JSON encoding
- All API endpoints now return plain dicts for proper JSON serialization
- Added comprehensive error handling to all endpoints
- Added logging for debugging API issues

### Improved
- Better error messages when service not initialized
- Graceful fallbacks for all API endpoints
- EEP profiles now load correctly in dropdown
- Gateway info displays properly
- Device list loads without errors

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
