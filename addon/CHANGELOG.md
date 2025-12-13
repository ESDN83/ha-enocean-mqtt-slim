# Changelog

## [1.0.27] - 2025-12-13

### Fixed
- **CRITICAL: Availability Payload Definitions** - Added payload_available and payload_not_available to MQTT discovery
- Prevents "unknown device" creation in Home Assistant
- Home Assistant now properly recognizes "online"/"offline" availability states

### Technical Details
- Added `"payload_available": "online"` to discovery config
- Added `"payload_not_available": "offline"` to discovery config
- Without these, HA doesn't know what values to expect on availability topic
- Fixes issue where HA creates unknown devices when seeing availability messages

## [1.0.26] - 2025-12-13

### Fixed
- **CRITICAL: Binary Sensor Template Syntax** - Fixed invalid Jinja2 template causing entity creation failure
- Changed from `{{{ 'ON' if ... }}}` (invalid triple braces) to `{% if ... %}ON{% else %}OFF{% endif %}`
- Binary sensors now appear correctly in Home Assistant
- Proper ON/OFF state conversion for binary sensors

### Technical Details
- Problem: Triple curly braces `{{{` are invalid Jinja2 syntax
- Solution: Use proper if/else block syntax `{% if %}...{% else %}...{% endif %}`
- Home Assistant can now parse the template correctly
- Binary sensor entities are created successfully

## [1.0.25] - 2025-12-13

### Fixed
- **Timestamp Format** - Changed to ISO 8601 with Z suffix for UTC
- Changed from `datetime.now().isoformat()` to `datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')`
- Matches Home Assistant's expected timestamp format
- Last Seen sensor now displays correctly

### Technical Details
- Old format: `2025-12-13T00:59:18.238571` (no timezone)
- New format: `2025-12-13T00:59:18Z` (UTC with Z suffix)
- Proper ISO 8601 format with timezone indicator
- Compatible with Home Assistant timestamp device class

## [1.0.24] - 2025-12-13

### Fixed
- **Binary Sensor Value Template** - Added ON/OFF conversion for binary sensors
- Binary sensors now convert 0/1 values to OFF/ON states
- Separate value_template logic for binary_sensor vs sensor components

### Technical Details
- Binary sensors use: `{% if value_json.AL == 1 %}ON{% else %}OFF{% endif %}`
- Regular sensors use: `{{ value_json.shortcut }}`
- Home Assistant binary sensors require ON/OFF, not 0/1

## [1.0.23] - 2025-12-13

### Fixed
- **Parser String to Int Conversion** - Fixed bitoffs and bitsize handling
- Parser now converts string values to integers before using as array indices
- Handles EEP profiles with string bitoffs/bitsize values (e.g., "29" instead of 29)

### Technical Details
- Problem: MV-01-01 profile has `"bitoffs": "29"` as string
- Python slice indices must be integers
- Added automatic conversion: `bitoffs = int(bitoffs)`
- Prevents "slice indices must be integers" error

## [1.0.22] - 2025-12-13

### Fixed
- **CRITICAL: Data Byte Extraction** - Fixed parser to use correct bytes for 4BS telegrams
- Changed from bytes 0-3 to bytes 1-4 (DB3-DB0)
- Alarm bit now extracted from correct position

### Technical Details
- 4BS telegram structure: `[RORG, DB3, DB2, DB1, DB0, ID, ID, ID, ID, STATUS]`
- Was using: bytes 0-3 (RORG + DB3 + DB2 + DB1) - WRONG!
- Now using: bytes 1-4 (DB3 + DB2 + DB1 + DB0) - CORRECT!
- Bit offset 29 now points to correct bit in DB0

## [1.0.21] - 2025-12-13

### Fixed
- **Device ID Detection** - Extract real device ID from data payload for non-standard devices
- Kessel Staufix Control sends real ID in bytes 5-8 of data payload
- Bypass teach-in detection for already configured devices

### Technical Details
- For 4BS telegrams, check bytes 5-8 for potential real device ID
- If ID matches configured device, use it instead of sender ID
- Configured devices treated as data even if LRN bit = 0
- Fixes issue where Staufix always looked like teach-in telegram

## [1.0.20] - 2025-12-12

### Added
- **UTE Teach-In Response** - Proper teach-in completion for devices
- Device exits teach-in mode automatically after receiving response
- Normal data telegrams start immediately
- Updated Web UI version display
- Added EnOcean icon
- **Custom EEP Profile Override Support** - Load custom profiles from `/config/enocean_custom_profiles/`

### Features
- Teach-in response sent back to device after auto-detection
- Device confirms successful learning
- Immediate transition to normal operation
- Custom profiles override built-in profiles
- Place JSON files in `/config/enocean_custom_profiles/` directory

## [1.0.14] - 2025-12-12

### Fixed
- **CRITICAL: AL (Alarm) entity not being published** - Fixed MV-01-01 profile
- AL entity was in "preDefined" array but not in "objects" dictionary
- get_entities() only reads from objects dictionary, so AL was never discovered
- Added AL entity definition to objects with proper binary_sensor configuration

### Technical Details
- Bug: AL was defined as `"preDefined": ["AL"]` but missing from `objects: {}`
- Fix: Added AL to objects dictionary with full entity definition
- Component: binary_sensor
- Device class: problem
- Icon: mdi:pipe-valve

### Impact
- AL (Alarm) entity now appears in Home Assistant
- All three entities now published correctly:
  - binary_sensor.staufix_control_alarm (AL)
  - sensor.staufix_control_rssi (rssi)
  - sensor.staufix_control_last_seen (last_seen)
- State data now includes AL value
- MQTT discovery works correctly

### What Was Broken
- Only rssi and last_seen entities were being created
- AL entity was completely missing
- State topic had no data
- Users saw empty/incomplete device

### What's Fixed Now
- All entities created correctly
- State data published to MQTT
- Complete device functionality
- Proper alarm monitoring

## [1.0.13] - 2025-12-12

### Added
- **EEP Profile Search** - Search through 152 profiles by code, title, or description
- **Profile Detail Viewer** - Click any profile to view complete details
- **Profile Browser** - Profiles grouped by family with expandable sections
- Real-time search filtering as you type
- Clear search button for quick reset

### Profile Viewer Features
- Complete profile information display
- Entity/sensor list with device classes and units
- Raw JSON view for technical details
- Profile metadata (RORG, telegram type, manufacturer)
- Bidirectional support indicator

### UI Improvements
- Extra-large modal for profile browsing
- Organized by profile families (A5-02, D2-01, etc.)
- Click-through navigation from list to details
- Responsive design for all screen sizes
- Search examples provided

### API
- New endpoint: GET /api/eep-profiles/{eep_code}
- Returns complete profile data including objects and datafields
- Proper error handling for missing profiles

### User Experience
- No more scrolling through 152 profiles manually
- Quick search: "temperature", "switch", "A5-02", etc.
- Instant results as you type
- Profile families show count of profiles
- Easy to find the right profile for your device

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
