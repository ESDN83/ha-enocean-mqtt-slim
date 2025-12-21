"""
EnOcean MQTT Slim - Main Application
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

from core.serial_handler import SerialHandler
from core.esp3_protocol import ESP3Packet
from core.mqtt_handler import MQTTHandler
from core.device_manager import DeviceManager
from core.state_persistence import StatePersistence
from core.command_translator import CommandTranslator
from core.command_tracker import CommandTracker
from eep.loader import EEPLoader
from eep.parser import EEPParser
from service_state import service_state
import uvicorn
# Import web app after service_state to ensure proper initialization
from web_ui.app import app as web_app

# Import at module level for use in teach-in handling
import sys
sys.path.insert(0, '/app')

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


class EnOceanMQTTService:
    """Main service for EnOcean MQTT bridge"""
    
    def __init__(self):
        self.serial_handler = None
        self.mqtt_handler = None
        self.device_manager = None
        self.state_persistence = None
        self.eep_loader = None
        self.eep_parser = None
        self.command_translator = None
        self.command_tracker = None
        self.running = False
        
        # Configuration from environment
        self.serial_port = os.getenv('SERIAL_PORT', '')
        self.mqtt_host = os.getenv('MQTT_HOST', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_PORT', 1883))
        self.mqtt_user = os.getenv('MQTT_USER', '')
        self.mqtt_password = os.getenv('MQTT_PASSWORD', '')
        self.restore_state = os.getenv('RESTORE_STATE', 'true').lower() == 'true'
        self.restore_delay = int(os.getenv('RESTORE_DELAY', 5))
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("=" * 60)
        logger.info("EnOcean MQTT Slim - Starting...")
        logger.info("=" * 60)
        
        # Load EEP profiles
        logger.info("Loading EEP profiles...")
        self.eep_loader = EEPLoader('/app/eep/definitions')
        self.eep_parser = EEPParser()
        
        if len(self.eep_loader.profiles) == 0:
            logger.error("No EEP profiles loaded! Check definitions directory.")
            return False
        
        logger.info(f"✓ Loaded {len(self.eep_loader.profiles)} EEP profiles")
        
        # List some profiles
        profiles = self.eep_loader.list_profiles()
        logger.info("Available EEP profiles:")
        for profile in profiles[:5]:  # Show first 5
            logger.info(f"  - {profile['eep']}: {profile['title']}")
        if len(profiles) > 5:
            logger.info(f"  ... and {len(profiles) - 5} more")
        
        # Initialize serial port if configured
        if self.serial_port:
            logger.info(f"Opening serial port: {self.serial_port}")
            self.serial_handler = SerialHandler(self.serial_port)
            
            if not self.serial_handler.open():
                logger.error(f"Failed to open serial port: {self.serial_port}")
                logger.warning("Continuing without serial port (web UI only mode)")
                self.serial_handler = None
            else:
                logger.info("✓ Serial port opened successfully")
                
                # Query gateway info
                try:
                    base_id = await self.serial_handler.get_base_id()
                    if base_id:
                        logger.info(f"✓ Gateway Base ID: {base_id}")
                    
                    version_info = await self.serial_handler.get_version_info()
                    if version_info:
                        logger.info(f"✓ Gateway Version: {version_info['app_version']}")
                        logger.info(f"  Chip ID: {version_info['chip_id']}")
                        logger.info(f"  Description: {version_info['app_description']}")
                except Exception as e:
                    logger.error(f"Error querying gateway info: {e}")
        else:
            logger.warning("No serial port configured")
            logger.info("Running in web UI only mode")
        
        # Initialize device manager
        logger.info("Initializing device manager...")
        self.device_manager = DeviceManager()
        logger.info(f"✓ Loaded {len(self.device_manager.list_devices())} configured devices")
        
        # Initialize state persistence
        logger.info("Initializing state persistence...")
        self.state_persistence = StatePersistence()
        if self.restore_state:
            logger.info(f"✓ State restoration enabled (delay: {self.restore_delay}s)")
        else:
            logger.info("State restoration disabled")
        
        # Initialize command translator
        logger.info("Initializing command translator...")
        self.command_translator = CommandTranslator(self.eep_loader)
        logger.info("✓ Command translator initialized")
        
        # Initialize command tracker
        logger.info("Initializing command tracker...")
        self.command_tracker = CommandTracker()
        self.command_tracker.set_confirmation_callback(self.on_command_confirmed)
        self.command_tracker.set_timeout_callback(self.on_command_timeout)
        self.command_tracker.start()
        logger.info("✓ Command tracker initialized")
        
        # Initialize MQTT
        logger.info(f"Connecting to MQTT broker: {self.mqtt_host}:{self.mqtt_port}")
        if self.mqtt_user:
            logger.info(f"  MQTT User: {self.mqtt_user}")
        
        self.mqtt_handler = MQTTHandler(
            self.mqtt_host,
            self.mqtt_port,
            self.mqtt_user,
            self.mqtt_password
        )
        
        if self.mqtt_handler.connect():
            # Wait a moment for connection
            await asyncio.sleep(1)
            if self.mqtt_handler.connected:
                logger.info("✓ MQTT connected successfully")
                
                # Subscribe to command topics
                # Set the event loop for MQTT command callbacks
                self.mqtt_handler.event_loop = asyncio.get_event_loop()
                
                if self.mqtt_handler.subscribe_commands(self.handle_command):
                    logger.info("✓ Subscribed to MQTT command topics")
                else:
                    logger.warning("Failed to subscribe to MQTT command topics")
                
                # Publish discovery for all configured devices
                for device in self.device_manager.list_devices():
                    if device.get('enabled'):
                        await self.publish_device_discovery(device)
            else:
                logger.warning("MQTT connection pending...")
        else:
            logger.error("Failed to connect to MQTT broker")
        
        logger.info("=" * 60)
        logger.info("Initialization complete!")
        logger.info("=" * 60)
        
        return True
    
    async def on_command_confirmed(self, device_id: str, entity: str, command: dict, state_data: dict):
        """
        Callback when command is confirmed by device
        
        Args:
            device_id: Device ID
            entity: Entity name
            command: Original command
            state_data: Confirmed state data from device
        """
        # State is already published by process_telegram, no need to republish
        logger.info(f"   🎯 Command confirmation processed for {device_id}/{entity}")
    
    async def on_command_timeout(self, device_id: str, entity: str, command: dict):
        """
        Callback when command times out without confirmation
        
        Args:
            device_id: Device ID
            entity: Entity name
            command: Original command that timed out
        """
        # Optionally could revert to last known state or mark as unavailable
        logger.warning(f"   ⚠️  Command timeout - device may not have responded")
    
    async def publish_device_discovery(self, device: dict):
        """Publish MQTT discovery for a device"""
        try:
            # Get EEP profile
            profile = self.eep_loader.get_profile(device['eep'])
            if not profile:
                logger.warning(f"EEP profile {device['eep']} not found for device {device['id']}")
                return
            
            # Check if device is controllable
            is_controllable = self.command_translator.is_controllable(device['eep'])
            
            # Publish discovery for each entity
            entities = profile.get_entities()
            for entity in entities:
                # Determine if this specific entity is controllable
                # For now, mark all entities of controllable devices as controllable
                # In future, could be more granular (e.g., only switches, not sensors)
                entity_controllable = is_controllable
                
                # Override: sensors are never controllable, only switches/lights/covers
                component = entity.get('component', 'sensor')
                if component in ['sensor', 'binary_sensor']:
                    entity_controllable = False
                
                self.mqtt_handler.publish_discovery(device, entity, entity_controllable)
            
            # Publish initial availability
            self.mqtt_handler.publish_availability(device['id'], True)
            
            if is_controllable:
                logger.info(f"Published discovery for device {device['id']} ({device['name']}) - CONTROLLABLE ✅")
            else:
                logger.info(f"Published discovery for device {device['id']} ({device['name']})")
            
        except Exception as e:
            logger.error(f"Error publishing device discovery: {e}")
    
    async def process_telegram(self, packet: ESP3Packet):
        """Process received EnOcean telegram"""
        try:
            sender_id = packet.get_sender_id()
            rorg = packet.get_rorg()
            rssi = packet.get_rssi()
            
            # Log raw data for debugging
            data_hex = ' '.join(f'{b:02x}' for b in packet.data)
            
            logger.info("=" * 80)
            logger.info(f"📡 TELEGRAM RECEIVED")
            logger.info(f"   Sender ID: {sender_id}")
            logger.info(f"   RORG: {hex(rorg) if rorg else 'N/A'}")
            logger.info(f"   RSSI: {rssi} dBm")
            logger.info(f"   Data: {data_hex}")
            
            # Sender ID is now correctly extracted by get_sender_id() in esp3_protocol.py
            # No workaround needed!
            
            # Check if device is already configured - if so, treat as data even if LRN=0
            device = self.device_manager.get_device(sender_id)
            
            # Check if it's a teach-in telegram (but not for already configured devices)
            if packet.is_teach_in() and not device:
                logger.warning("=" * 80)
                logger.warning("🎓 TEACH-IN TELEGRAM DETECTED!")
                logger.warning(f"   Device ID: {sender_id}")
                logger.warning(f"   RORG: {hex(rorg)}")
                logger.warning(f"   RSSI: {rssi} dBm")
                logger.warning(f"   Data: {data_hex}")
                
                # Try to auto-detect EEP profile from telegram
                detected_eep = None
                detected_func = None
                detected_type = None
                device_name = f"Device {sender_id}"
                matching_profiles = []
                
                # For 4BS (A5) teach-in telegrams with EEP information
                if rorg == 0xA5 and len(packet.data) >= 9:
                    # 4BS teach-in telegram format:
                    # Byte 0: RORG (A5)
                    # Byte 1-4: DB3, DB2, DB1, DB0 (teach-in data)
                    # Byte 5-8: Sender ID (4 bytes) - already correctly extracted by get_sender_id()
                    # Byte 9: Status
                    
                    db3 = packet.data[1]
                    db2 = packet.data[2]
                    db1 = packet.data[3]
                    db0 = packet.data[4]
                    
                    # Check LRN bit (DB0.3) - 0 = teach-in
                    lrn_bit = (db0 >> 3) & 0x01
                    if lrn_bit == 0:
                        # Extract FUNC and TYPE from teach-in
                        func = (db3 >> 2) & 0x3F  # 6 bits
                        type_val = ((db3 & 0x03) << 5) | ((db2 >> 3) & 0x1F)  # 7 bits
                        
                        # Store FUNC and TYPE
                        detected_func = func
                        detected_type = type_val
                        
                        # Find matching profiles
                        matching_profiles = self.eep_loader.find_profiles_by_telegram(rorg, func, type_val)
                        
                        if len(matching_profiles) == 1:
                            # Exact match found
                            detected_eep = matching_profiles[0].eep
                            device_name = matching_profiles[0].type_title
                            logger.warning(f"   ✅ Exact match: {detected_eep} - {device_name}")
                        elif len(matching_profiles) > 1:
                            # Multiple matches - require manual selection
                            logger.warning(f"   ⚠️  Multiple profiles match (FUNC={func:02X}, TYPE={type_val:02X}):")
                            for idx, prof in enumerate(matching_profiles, 1):
                                logger.warning(f"      {idx}. {prof.eep} - {prof.type_title}")
                            logger.warning("")
                            logger.warning("   ⚠️  MANUAL SELECTION REQUIRED:")
                            logger.warning(f"      1. Go to Web UI")
                            logger.warning(f"      2. Click 'Add Device'")
                            logger.warning(f"      3. Enter Device ID: {sender_id}")
                            logger.warning(f"      4. Select one of the {len(matching_profiles)} profiles listed above")
                            logger.warning("")
                            
                            # Cache detected profiles for Web UI
                            profile_eeps = [prof.eep for prof in matching_profiles]
                            service_state.set_detected_profiles(sender_id, profile_eeps)
                            logger.info(f"   📝 Cached {len(profile_eeps)} profiles for device {sender_id}: {profile_eeps}")
                            
                            # Don't auto-add - require manual selection
                            detected_eep = None
                        else:
                            # No match found
                            detected_eep = f"A5-{func:02X}-{type_val:02X}"
                            logger.warning(f"   ⚠️  EEP {detected_eep} not in database")
                
                # For RPS (F6), D5, and other telegrams WITHOUT embedded teach-in info
                elif rorg in [0xF6, 0xD5, 0xD2]:
                    logger.warning(f"   📋 RORG {hex(rorg)} telegram detected")
                    
                    # Find all profiles matching this RORG
                    matching_profiles = self.eep_loader.find_profiles_by_telegram(rorg)
                    
                    if len(matching_profiles) == 0:
                        logger.warning(f"   ⚠️  No profiles found for RORG {hex(rorg)}")
                    elif len(matching_profiles) == 1:
                        # Only one profile for this RORG
                        detected_eep = matching_profiles[0].eep
                        device_name = matching_profiles[0].type_title
                        logger.warning(f"   ✅ Auto-selected: {detected_eep} - {device_name}")
                    else:
                        # Multiple profiles available - user must choose
                        logger.warning(f"   📋 {len(matching_profiles)} possible profiles for RORG {hex(rorg)}:")
                        for idx, prof in enumerate(matching_profiles, 1):
                            logger.warning(f"      {idx}. {prof.eep} - {prof.type_title}")
                        logger.warning("")
                        logger.warning("   ⚠️  MANUAL SELECTION REQUIRED:")
                        logger.warning(f"      1. Go to Web UI")
                        logger.warning(f"      2. Click 'Add Device'")
                        logger.warning(f"      3. Enter Device ID: {sender_id}")
                        logger.warning(f"      4. Select one of the {len(matching_profiles)} profiles listed above")
                        logger.warning("")
                        # Don't auto-add - require manual selection
                        logger.warning("=" * 80)
                        return
                
                # If no EEP detected at all
                if not detected_eep:
                    device_name = f"Device {sender_id}"
                
                # Check if device already exists
                existing_device = self.device_manager.get_device(sender_id)
                if existing_device:
                    logger.warning(f"   ℹ️  Device {sender_id} already configured as '{existing_device['name']}'")
                    
                    # Send teach-in response to confirm and exit teach-in mode
                    if detected_eep and rorg == 0xA5:
                        logger.warning(f"   📤 Sending teach-in response to device...")
                        try:
                            # Extract FUNC and TYPE from detected EEP
                            eep_parts = detected_eep.split('-')
                            if len(eep_parts) == 3:
                                func = int(eep_parts[1], 16)
                                type_val = int(eep_parts[2], 16)
                                
                                # Create and send teach-in response
                                response = ESP3Packet.create_teach_in_response(sender_id, func, type_val)
                                if self.serial_handler:
                                    await self.serial_handler.write_packet(response)
                                    logger.warning(f"   ✅ Teach-in response sent! Device should exit learn mode.")
                        except Exception as e:
                            logger.error(f"   ❌ Failed to send teach-in response: {e}")
                    
                    logger.warning("=" * 80)
                    return
                
                # Auto-add device if EEP detected
                if detected_eep:
                    logger.warning("")
                    logger.warning(f"   🤖 AUTO-ADDING DEVICE...")
                    logger.warning(f"   Device ID: {sender_id}")
                    logger.warning(f"   Name: {device_name}")
                    logger.warning(f"   EEP: {detected_eep}")
                    
                    # Add device
                    success = self.device_manager.add_device(
                        sender_id,
                        device_name,
                        detected_eep,
                        "EnOcean"
                    )
                    
                    if success:
                        logger.warning(f"   ✅ Device added successfully!")
                        
                        # Publish MQTT discovery
                        device = self.device_manager.get_device(sender_id)
                        if device:
                            await self.publish_device_discovery(device)
                            logger.warning(f"   ✅ MQTT discovery published!")
                        
                        # Send teach-in response to confirm and exit teach-in mode
                        if rorg == 0xA5:
                            logger.warning(f"   📤 Sending teach-in response to device...")
                            try:
                                # Extract FUNC and TYPE from detected EEP
                                eep_parts = detected_eep.split('-')
                                if len(eep_parts) == 3:
                                    func = int(eep_parts[1], 16)
                                    type_val = int(eep_parts[2], 16)
                                    
                                    # Create and send teach-in response
                                    response = ESP3Packet.create_teach_in_response(sender_id, func, type_val)
                                    if self.serial_handler:
                                        await self.serial_handler.write_packet(response)
                                        logger.warning(f"   ✅ Teach-in response sent! Device should exit learn mode.")
                            except Exception as e:
                                logger.error(f"   ❌ Failed to send teach-in response: {e}")
                        
                        logger.warning("")
                        logger.warning(f"   🎉 Device '{device_name}' is now ready to use!")
                        logger.warning(f"   Check Home Assistant for new entities.")
                    else:
                        logger.warning(f"   ❌ Failed to add device")
                else:
                    logger.warning("")
                    logger.warning("   ⚠️  Could not auto-detect EEP profile")
                    logger.warning("   Manual configuration required:")
                    logger.warning(f"   1. Go to Web UI")
                    logger.warning(f"   2. Click 'Add Device'")
                    logger.warning(f"   3. Enter Device ID: {sender_id}")
                    logger.warning(f"   4. Select appropriate EEP profile")
                
                logger.warning("=" * 80)
                return
            
            # Look up device
            device = self.device_manager.get_device(sender_id)
            if not device:
                logger.warning("⚠️  UNKNOWN DEVICE (not configured)")
                logger.warning(f"   Device ID: {sender_id}")
                logger.warning(f"   RORG: {hex(rorg)}")
                logger.warning(f"   RSSI: {rssi} dBm")
                logger.warning(f"   Data: {data_hex}")
                logger.warning("")
                
                # Try to suggest possible profiles based on RORG
                matching_profiles = self.eep_loader.find_profiles_by_telegram(rorg)
                if len(matching_profiles) > 0:
                    logger.warning(f"   📋 Found {len(matching_profiles)} possible profiles for RORG {hex(rorg)}:")
                    # Show first 10 matches
                    for idx, prof in enumerate(matching_profiles[:10], 1):
                        logger.warning(f"      {idx}. {prof.eep} - {prof.type_title}")
                    if len(matching_profiles) > 10:
                        logger.warning(f"      ... and {len(matching_profiles) - 10} more")
                    logger.warning("")
                
                logger.warning("   ⚠️  MANUAL CONFIGURATION REQUIRED:")
                logger.warning("      1. Go to Web UI")
                logger.warning("      2. Click 'Add Device'")
                logger.warning(f"      3. Enter Device ID: {sender_id}")
                logger.warning("      4. Select the appropriate EEP profile")
                if len(matching_profiles) > 0:
                    logger.warning(f"      5. Choose from the {len(matching_profiles)} profiles listed above")
                logger.warning("")
                logger.info("=" * 80)
                return
            
            if not device.get('enabled'):
                logger.info(f"   ⏸️  Device {sender_id} is DISABLED")
                logger.info("=" * 80)
                return
            
            logger.info(f"   ✅ Known Device: {device['name']} ({device['eep']})")
            
            # Update last seen
            self.device_manager.update_last_seen(sender_id, rssi)
            
            # Get EEP profile
            profile = self.eep_loader.get_profile(device['eep'])
            if not profile:
                logger.warning(f"  EEP profile {device['eep']} not found")
                return
            
            # Parse telegram
            parsed_data = self.eep_parser.parse_telegram_with_full_data(packet.data, profile)

            if parsed_data:
                # Add RSSI and timestamp to parsed data
                from datetime import datetime, timezone
                parsed_data['rssi'] = rssi
                parsed_data['last_seen'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

                logger.info(f"  Parsed data: {parsed_data}")
                
                # Check for command confirmation
                if self.command_tracker:
                    await self.command_tracker.check_telegram(sender_id, parsed_data)

                # Save state for persistence
                if self.state_persistence:
                    self.state_persistence.save_state(sender_id, parsed_data)

                # IMPORTANT: Ensure MQTT discovery is published BEFORE state data
                # This prevents HA from creating "unknown" devices
                if self.mqtt_handler and self.mqtt_handler.connected:
                    # Check if this is the first telegram from this device (no discovery published yet)
                    # We track this by checking if device has 'discovery_published' flag
                    if not device.get('discovery_published', False):
                        logger.info(f"  📢 First telegram from {sender_id}, publishing discovery first...")
                        await self.publish_device_discovery(device)
                        # Mark discovery as published
                        device['discovery_published'] = True
                        self.device_manager.devices[sender_id] = device
                    
                    # Now publish state data (discovery is guaranteed to exist)
                    self.mqtt_handler.publish_state(sender_id, parsed_data, retain=True)
                    self.mqtt_handler.publish_availability(sender_id, True)
                    logger.info(f"  → Published to MQTT (retained)")
                else:
                    logger.warning("  MQTT not connected, skipping publish")
            else:
                logger.warning("  Failed to parse telegram data")
            
        except Exception as e:
            logger.error(f"Error processing telegram: {e}", exc_info=True)
    
    async def handle_command(self, device_id: str, entity: str, command: dict):
        """
        Handle command from MQTT (Home Assistant)
        
        Args:
            device_id: Device ID
            entity: Entity name (e.g., "switch", "light")
            command: Command dictionary (e.g., {"state": "ON"})
        """
        try:
            logger.info("=" * 80)
            logger.info(f"🎮 COMMAND RECEIVED")
            logger.info(f"   Device ID: {device_id}")
            logger.info(f"   Entity: {entity}")
            logger.info(f"   Command: {command}")
            
            # Check if serial handler available
            if not self.serial_handler:
                logger.error("   ❌ Serial handler not available, cannot send commands")
                return
            
            # Get device
            device = self.device_manager.get_device(device_id)
            if not device:
                logger.error(f"   ❌ Device {device_id} not found")
                return
            
            if not device.get('enabled'):
                logger.warning(f"   ⚠️  Device {device_id} is disabled")
                return
            
            logger.info(f"   ✅ Device: {device['name']} ({device['eep']})")
            
            # Translate command to EnOcean telegram
            result = self.command_translator.translate_command(device, entity, command)
            if not result:
                logger.error(f"   ❌ Could not translate command for {device['eep']}")
                return
            
            command_type, rorg_or_button, data_bytes = result
            
            # Send command based on type
            if command_type == 'rps':
                # RPS button press
                button_code = rorg_or_button
                logger.info(f"   📤 Sending RPS command: button={hex(button_code)}")
                success = await self.serial_handler.send_rps_command(device_id, button_code)
            elif command_type == 'telegram':
                # Generic telegram
                rorg = rorg_or_button
                logger.info(f"   📤 Sending telegram: RORG={hex(rorg)}, data={data_bytes.hex()}")
                success = await self.serial_handler.send_telegram(device_id, rorg, data_bytes)
            else:
                logger.error(f"   ❌ Unknown command type: {command_type}")
                return
            
            if success:
                logger.info(f"   ✅ Command sent successfully!")
                
                # Track command for confirmation
                if self.command_tracker:
                    # Create expected state from command
                    expected_state = {}
                    if 'state' in command:
                        expected_state[entity] = 1 if command['state'].upper() == 'ON' else 0
                    elif 'brightness' in command:
                        expected_state[entity] = command['brightness']
                    elif 'position' in command:
                        expected_state[entity] = command['position']
                    
                    if expected_state:
                        self.command_tracker.add_pending_command(
                            device_id, 
                            entity, 
                            command, 
                            expected_state,
                            timeout=5.0
                        )
                        logger.info(f"   📋 Tracking command for confirmation (timeout: 5s)")
                
                # Publish optimistic state update
                if self.mqtt_handler and self.mqtt_handler.connected:
                    # Create state update from command
                    state_update = {}
                    if 'state' in command:
                        state_update[entity] = 1 if command['state'].upper() == 'ON' else 0
                    elif 'brightness' in command:
                        state_update[entity] = command['brightness']
                    elif 'position' in command:
                        state_update[entity] = command['position']
                    elif 'rgb' in command:
                        # RGB color command
                        rgb = command['rgb']
                        state_update['rgb'] = rgb
                        logger.info(f"   🎨 RGB color: {rgb}")
                    
                    if state_update:
                        self.mqtt_handler.publish_state(device_id, state_update, retain=True)
                        logger.info(f"   ✅ Published optimistic state: {state_update}")
            else:
                logger.error(f"   ❌ Failed to send command")
            
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error handling command: {e}", exc_info=True)
    
    async def run_serial_reader(self):
        """Run serial reader task"""
        if self.serial_handler:
            logger.info("Listening for EnOcean telegrams...")
            try:
                await self.serial_handler.start_reading(self.process_telegram)
            except Exception as e:
                logger.error(f"Error in serial reader: {e}")
    
    async def run_web_server(self):
        """Run web server task"""
        logger.info("Starting web UI on port 8099...")
        config = uvicorn.Config(
            web_app,
            host="0.0.0.0",
            port=8099,
            log_level="warning",
            access_log=False
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def run(self):
        """Main run loop"""
        self.running = True
        
        # Initialize first, THEN register with state manager
        if not await self.initialize():
            logger.error("Initialization failed, exiting")
            return
        
        # NOW register service with state manager (after initialization complete)
        service_state.set_service(self)
        logger.info("✓ Service registered with state manager")
        
        # Store gateway info if available
        if self.serial_handler:
            try:
                base_id = await self.serial_handler.get_base_id()
                version_info = await self.serial_handler.get_version_info()
                if base_id and version_info:
                    service_state.set_gateway_info({
                        "base_id": base_id,
                        "version": version_info.get('app_version', 'Unknown'),
                        "chip_id": version_info.get('chip_id', 'Unknown'),
                        "description": version_info.get('app_description', 'Unknown')
                    })
            except Exception as e:
                logger.error(f"Error storing gateway info: {e}")
        
        # Restore last known states if enabled
        if self.restore_state and self.state_persistence and self.mqtt_handler and self.mqtt_handler.connected:
            logger.info("=" * 60)
            logger.info(f"⏳ Waiting {self.restore_delay}s before restoring states...")
            logger.info("=" * 60)
            await asyncio.sleep(self.restore_delay)
            
            logger.info("=" * 60)
            logger.info("🔄 Restoring last known device states...")
            logger.info("=" * 60)
            
            restored_count = 0
            all_states = self.state_persistence.get_all_states()
            
            for device_id, state_data in all_states.items():
                device = self.device_manager.get_device(device_id)
                if device and device.get('enabled') and state_data:
                    try:
                        # Republish last known state
                        self.mqtt_handler.publish_state(device_id, state_data, retain=True)
                        self.mqtt_handler.publish_availability(device_id, True)
                        logger.info(f"  ✓ Restored state for {device['name']} ({device_id})")
                        restored_count += 1
                    except Exception as e:
                        logger.error(f"  ✗ Failed to restore state for {device_id}: {e}")
            
            if restored_count > 0:
                logger.info(f"✓ Restored {restored_count} device state(s)")
            else:
                logger.info("No states to restore")
            logger.info("=" * 60)
        
        logger.info("=" * 60)
        logger.info("Service is running!")
        logger.info("Web UI available via Home Assistant ingress")
        logger.info("=" * 60)
        
        # Run web server and serial reader concurrently
        tasks = [
            asyncio.create_task(self.run_web_server()),
        ]
        
        if self.serial_handler:
            tasks.append(asyncio.create_task(self.run_serial_reader()))
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown service"""
        logger.info("Shutting down...")
        self.running = False
        
        if self.command_tracker:
            self.command_tracker.stop()
        
        if self.serial_handler:
            self.serial_handler.stop_reading()
            self.serial_handler.close()
        
        logger.info("Shutdown complete")


async def main():
    """Main entry point"""
    service = EnOceanMQTTService()
    await service.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
