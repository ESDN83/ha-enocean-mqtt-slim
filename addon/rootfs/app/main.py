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
from eep.loader import EEPLoader
from eep.parser import EEPParser
from service_state import service_state
import uvicorn
# Import web app after service_state to ensure proper initialization
from web_ui.app import app as web_app

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
        self.eep_loader = None
        self.eep_parser = None
        self.running = False
        
        # Configuration from environment
        self.serial_port = os.getenv('SERIAL_PORT', '')
        self.mqtt_host = os.getenv('MQTT_HOST', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_PORT', 1883))
        self.mqtt_user = os.getenv('MQTT_USER', '')
        self.mqtt_password = os.getenv('MQTT_PASSWORD', '')
    
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
    
    async def publish_device_discovery(self, device: dict):
        """Publish MQTT discovery for a device"""
        try:
            # Get EEP profile
            profile = self.eep_loader.get_profile(device['eep'])
            if not profile:
                logger.warning(f"EEP profile {device['eep']} not found for device {device['id']}")
                return
            
            # Publish discovery for each entity
            entities = profile.get_entities()
            for entity in entities:
                self.mqtt_handler.publish_discovery(device, entity)
            
            # Publish initial availability
            self.mqtt_handler.publish_availability(device['id'], True)
            
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
            
            # Check if it's a teach-in telegram
            if packet.is_teach_in():
                logger.warning("=" * 80)
                logger.warning("🎓 TEACH-IN TELEGRAM DETECTED!")
                logger.warning(f"   Device ID: {sender_id}")
                logger.warning(f"   RORG: {hex(rorg)}")
                logger.warning(f"   RSSI: {rssi} dBm")
                logger.warning(f"   Data: {data_hex}")
                
                # Try to auto-detect EEP profile from teach-in telegram
                detected_eep = None
                device_name = f"Device {sender_id}"
                real_device_id = sender_id  # Default to sender ID
                
                # For 4BS (A5) teach-in telegrams with EEP
                if rorg == 0xA5 and len(packet.data) >= 9:
                    # 4BS teach-in telegram format:
                    # Byte 0: RORG (A5)
                    # Byte 1-4: DB3, DB2, DB1, DB0 (teach-in data)
                    # Byte 5-8: Real device ID (4 bytes)
                    # Byte 9: Status
                    
                    db3 = packet.data[1]
                    db2 = packet.data[2]
                    db1 = packet.data[3]
                    db0 = packet.data[4]
                    
                    # Extract real device ID from data payload
                    real_device_id = ''.join(f'{b:02x}' for b in packet.data[5:9])
                    logger.warning(f"   📱 Real Device ID (from data): {real_device_id}")
                    
                    # Check LRN bit (DB0.3) - 0 = teach-in
                    lrn_bit = (db0 >> 3) & 0x01
                    if lrn_bit == 0:
                        # Extract FUNC and TYPE from teach-in
                        func = (db3 >> 2) & 0x3F  # 6 bits
                        type_val = ((db3 & 0x03) << 5) | ((db2 >> 3) & 0x1F)  # 7 bits
                        
                        # Construct EEP code
                        detected_eep = f"A5-{func:02X}-{type_val:02X}"
                        logger.warning(f"   📋 Detected EEP: {detected_eep}")
                        
                        # Try to find matching profile
                        profile = self.eep_loader.get_profile(detected_eep)
                        if profile:
                            device_name = profile.type_title
                            logger.warning(f"   ✅ Found profile: {device_name}")
                        else:
                            logger.warning(f"   ⚠️  Profile {detected_eep} not in database")
                
                # Use real device ID for all operations
                sender_id = real_device_id
                device_name = f"Device {sender_id}" if not detected_eep else device_name
                
                # Check if device already exists
                existing_device = self.device_manager.get_device(sender_id)
                if existing_device:
                    logger.warning(f"   ℹ️  Device {sender_id} already configured as '{existing_device['name']}'")
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
                logger.warning("   This device is not in your configuration.")
                logger.warning("   Add it via Web UI if you want to use it.")
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
                from datetime import datetime
                parsed_data['rssi'] = rssi
                parsed_data['last_seen'] = datetime.now().isoformat()
                
                logger.info(f"  Parsed data: {parsed_data}")
                
                # Publish to MQTT
                if self.mqtt_handler and self.mqtt_handler.connected:
                    self.mqtt_handler.publish_state(sender_id, parsed_data)
                    self.mqtt_handler.publish_availability(sender_id, True)
                    logger.info(f"  → Published to MQTT")
                else:
                    logger.warning("  MQTT not connected, skipping publish")
            else:
                logger.warning("  Failed to parse telegram data")
            
        except Exception as e:
            logger.error(f"Error processing telegram: {e}", exc_info=True)
    
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
