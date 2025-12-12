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
                logger.warning("")
                logger.warning("   To add this device:")
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
