# Changelog

## [1.0.12] - 2025-12-12

### Added
- **152 EEP Profiles!** - Massive expansion from 1 to 152 supported profiles
- Imported all profiles from ioBroker.enocean library
- RSSI and timestamp sensors added to ALL profiles automatically
- Support for 36 profile families

### Profile Families Included
- **A5-02**: 25 temperature sensor profiles
- **A5-04**: 3 humidity sensor profiles  
- **A5-05**: 1 barometric sensor profile
- **A5-06**: 3 light sensor profiles
- **A5-07**: 3 occupancy sensor profiles
- **A5-08**: 3 light/temp/occupancy profiles
- **A5-09**: 9 gas sensor profiles
- **A5-10**: 16 room control profiles
- **A5-11**: 2 controller status profiles
- **A5-12**: 3 automated meter reading profiles
- **A5-13**: 2 environmental sensor profiles
- **A5-14**: 4 multi-function sensor profiles
- **A5-20**: 3 HVAC profiles
- **A5-30**: 1 digital input profile
- **A5-38**: 1 gateway profile
- **D0-00**: 1 contact profile
- **D2-01**: 5 electronic switch profiles
- **D2-03**: 1 push button profile
- **D2-05**: 1 blinds control profile
- **D2-06**: 4 multisensor profiles
- **D2-10**: 1 room control profile
- **D2-14**: 1 multi-function profile
- **D2-50**: 1 heat recovery profile
- **D5-00**: 1 contact sensor profile
- **F6-01**: 1 push button profile
- **F6-02**: 2 rocker switch profiles
- **F6-04**: 1 key card profile
- **F6-05**: 2 wind sensor profiles
- **F6-10**: 1 window handle profile
- **I1-01**: 1 infrared message profile
- **MV-01**: 6 manufacturer-specific profiles (Kessel, etc.)
- **PE-01**: 2 manufacturer profiles
- **TF-01**: 3 manufacturer profiles
- **TF-13**: 28 manufacturer profiles
- **TF-14**: 7 manufacturer profiles
- **X1-01**: 3 manufacturer profiles

### Technical Details
- Created automated conversion script
- All profiles include rssi and last_seen sensors
- Profiles maintain compatibility with ioBroker format
- Ready for immediate use in Home Assistant

### Benefits
- Support for virtually all common EnOcean devices
- Temperature sensors, switches, actuators, and more
- No manual profile creation needed
- Comprehensive device ecosystem support

## [1.0.11] - 2025-12-12

### Added
- **RSSI Sensor** - Signal strength now available in Home Assistant
- **Last Seen Sensor** - Timestamp of last telegram received
- RSSI and timestamp included in all MQTT state messages
- New sensors automatically discovered in Home Assistant

### Improved
- State data now includes rssi and last_seen fields
- MV-01-01 profile updated with rssi and last_seen sensors
- Better device monitoring with signal strength tracking
- Timestamp tracking for device activity

### Technical Details
- RSSI added to parsed_data before MQTT publish
- Timestamp added using datetime.now().isoformat()
- Both sensors configured with appropriate device_class
- RSSI uses signal_strength device class with dBm unit
- Last Seen uses timestamp device class

### Home Assistant Integration
- RSSI sensor shows signal strength in dBm
- Last Seen sensor shows last telegram time
- Both sensors update with each telegram
- Useful for monitoring device connectivity

## [1.0.10] - 2025-12-12

### Added
- **Enhanced Telegram Logging** - Comprehensive logging for all received telegrams
- Visual telegram display with emojis (📡 for normal, 🎓 for teach-in, ⚠️ for unknown)
- Hex dump of all telegram data for debugging
- Detailed parsing logs showing data extraction step-by-step
- Instructions in logs for adding detected devices

### Improved
- Teach-in telegrams now logged at WARNING level (highly visible)
- Unknown devices logged at WARNING level with device details
- Each telegram shows: Sender ID, RORG, RSSI, and full data hex
- Parser logs show data bytes being extracted and parsed values
- Better visibility for troubleshooting device communication

### Debugging
- All telegrams logged with full details
- Parser shows which bytes are being used
- Easy to identify if device is sending data
- Easy to see if parsing is working correctly
- Helps diagnose MQTT "unknown" value issues

## [1.0.9] - 2025-12-12

### Fixed
- **Device Action Buttons** - Fixed Edit, Pause/Enable, and Delete buttons using absolute paths
- All device action buttons now use relative paths and work correctly through ingress
- Fixed fetch calls for: edit device, toggle enable/disable, delete device

### Added
- **Auto-Detect Feature** - Replaced yellow "Add Device" card with "Auto-Detect" functionality
- Click Auto-Detect card to start listening for EnOcean teach-in telegrams (60 seconds)
- Visual countdown timer shows remaining time
- Click again to stop early
- Detected devices appear in addon logs
- Keeps blue "Add Device" button in device list header

### Improved
- Cleaner UI with only one "Add Device" button (blue button in header)
- Auto-Detect card provides teach-in functionality like other integrations
- Better user experience for adding new devices

## [1.0.8] - 2025-12-12

### Fixed
- **CRITICAL: Ingress Path Issue** - Fixed 404 errors caused by absolute API paths
- Changed all fetch() calls from `/api/...` to `api/...` (relative paths)
- This fixes the issue where API calls were going to wrong URLs through Home Assistant ingress
- All API endpoints now work correctly through ingress proxy

### Technical Details
- Problem: JavaScript was calling `/api/status` which resolved to `http://192.168.1.130:8123/api/status`
- Should be: `api/status` which resolves to ingress path + `api/status`
- Fixed all fetch calls: status, devices, eep-profiles, gateway-info, and all POST/PUT/DELETE operations
- Relative paths work correctly with Home Assistant's ingress proxy system

### Impact
- ✅ Fixes all 404 errors on API endpoints
- ✅ Status, Gateway, EEP Profiles, and Devices now load correctly
- ✅ Add/Edit/Delete device operations now work
- ✅ All modals display correct data

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
