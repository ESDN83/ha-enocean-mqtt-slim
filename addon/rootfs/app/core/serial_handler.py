"""
Serial Port Handler for EnOcean USB Gateway
Manages communication with EnOcean USB stick via serial port
"""
import asyncio
import logging
import serial
from typing import Optional, Callable
from .esp3_protocol import ESP3Packet

logger = logging.getLogger(__name__)


class SerialHandler:
    """Handle serial communication with EnOcean USB gateway"""
    
    def __init__(self, port: str, baudrate: int = 57600):
        """
        Initialize serial handler
        
        Args:
            port: Serial port path (e.g., /dev/ttyUSB0)
            baudrate: Baud rate (default: 57600 for EnOcean)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.running = False
        self.base_id = None
        self.version_info = None
        
    def open(self):
        """Open serial port connection"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )
            logger.info(f"Opened serial port {self.port} at {self.baudrate} baud")
            return True
        except Exception as e:
            logger.error(f"Failed to open serial port {self.port}: {e}")
            return False
    
    def close(self):
        """Close serial port connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info(f"Closed serial port {self.port}")
    
    def is_open(self) -> bool:
        """Check if serial port is open"""
        return self.serial is not None and self.serial.is_open
    
    async def read_packet(self) -> Optional[ESP3Packet]:
        """
        Read and parse one ESP3 packet from serial port
        
        Returns:
            ESP3Packet if successful, None otherwise
        """
        if not self.is_open():
            return None
        
        try:
            # Wait for sync byte
            bytes_read = 0
            timeout_count = 0
            logger.info("🔍 Waiting for sync byte (0x55)... Listening for EnOcean devices...")
            
            while True:
                byte = await asyncio.get_event_loop().run_in_executor(
                    None, self.serial.read, 1
                )
                
                # If no byte received (timeout)
                if not byte:
                    timeout_count += 1
                    if timeout_count % 10 == 0:  # Every 10 seconds
                        logger.info(f"   Still waiting... ({timeout_count} seconds elapsed, 0 bytes received)")
                    await asyncio.sleep(0.01)
                    continue
                
                # We got a byte!
                bytes_read += 1
                
                # Log every 100 non-sync bytes
                if bytes_read % 100 == 0:
                    logger.info(f"   Read {bytes_read} bytes so far, still looking for sync...")
                
                # Log individual bytes in debug mode
                logger.debug(f"   Read byte: 0x{byte[0]:02x}")
                
                # Check if it's the sync byte
                if byte[0] == ESP3Packet.SYNC_BYTE:
                    logger.info(f"✅ Found sync byte (0x55) after reading {bytes_read} bytes!")
                    break
            
            # Read header (4 bytes)
            header = await asyncio.get_event_loop().run_in_executor(
                None, self.serial.read, 4
            )
            if len(header) != 4:
                logger.warning("Incomplete header received")
                return None
            
            # Parse header to get lengths
            data_length = int.from_bytes(header[0:2], 'big')
            optional_length = header[2]
            
            # Read header CRC
            header_crc = await asyncio.get_event_loop().run_in_executor(
                None, self.serial.read, 1
            )
            if len(header_crc) != 1:
                logger.warning("Incomplete header CRC received")
                return None
            
            # Read data, optional data, and data CRC
            total_data_length = data_length + optional_length + 1
            data_block = await asyncio.get_event_loop().run_in_executor(
                None, self.serial.read, total_data_length
            )
            if len(data_block) != total_data_length:
                logger.warning(f"Incomplete data block received: {len(data_block)}/{total_data_length}")
                return None
            
            # Reconstruct full packet
            raw_packet = bytes([ESP3Packet.SYNC_BYTE]) + header + header_crc + data_block
            
            # Parse packet
            packet = ESP3Packet(raw_packet)
            logger.debug(f"Received packet: {packet}")
            return packet
            
        except Exception as e:
            logger.error(f"Error reading packet: {e}")
            return None
    
    async def write_packet(self, packet: ESP3Packet) -> bool:
        """
        Write ESP3 packet to serial port
        
        Args:
            packet: ESP3Packet to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_open():
            return False
        
        try:
            raw_data = packet.build()
            await asyncio.get_event_loop().run_in_executor(
                None, self.serial.write, raw_data
            )
            logger.debug(f"Sent packet: {packet}")
            return True
        except Exception as e:
            logger.error(f"Error writing packet: {e}")
            return False
    
    async def send_command_and_wait_response(self, command_packet: ESP3Packet, timeout: float = 2.0) -> Optional[ESP3Packet]:
        """
        Send command and wait for response
        
        Args:
            command_packet: Command packet to send
            timeout: Timeout in seconds
            
        Returns:
            Response packet if received, None otherwise
        """
        if not await self.write_packet(command_packet):
            return None
        
        # Wait for response
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            packet = await self.read_packet()
            if packet and packet.packet_type == ESP3Packet.PACKET_TYPE_RESPONSE:
                return packet
            await asyncio.sleep(0.01)
        
        logger.warning("Timeout waiting for response")
        return None
    
    async def get_base_id(self) -> Optional[str]:
        """
        Query gateway base ID
        
        Returns:
            Base ID as hex string, or None if failed
        """
        if self.base_id:
            return self.base_id
        
        logger.info("Querying gateway base ID...")
        command = ESP3Packet.create_read_base_id()
        response = await self.send_command_and_wait_response(command)
        
        if response and len(response.data) >= 5:
            # Response format: [return_code, base_id (4 bytes), ...]
            return_code = response.data[0]
            if return_code == 0:  # OK
                base_id_bytes = response.data[1:5]
                self.base_id = base_id_bytes.hex()
                logger.info(f"Gateway base ID: {self.base_id}")
                return self.base_id
            else:
                logger.error(f"Failed to read base ID: return code {return_code}")
        else:
            logger.error("Invalid response to base ID query")
        
        return None
    
    async def get_version_info(self) -> Optional[dict]:
        """
        Query gateway version information
        
        Returns:
            Dictionary with version info, or None if failed
        """
        if self.version_info:
            return self.version_info
        
        logger.info("Querying gateway version...")
        command = ESP3Packet.create_read_version()
        response = await self.send_command_and_wait_response(command)
        
        if response and len(response.data) >= 33:
            # Response format: [return_code, app_version (4), api_version (4), chip_id (4), chip_version (4), app_description (16)]
            return_code = response.data[0]
            if return_code == 0:  # OK
                self.version_info = {
                    'app_version': '.'.join(str(b) for b in response.data[1:5]),
                    'api_version': '.'.join(str(b) for b in response.data[5:9]),
                    'chip_id': response.data[9:13].hex(),
                    'chip_version': '.'.join(str(b) for b in response.data[13:17]),
                    'app_description': response.data[17:33].decode('ascii', errors='ignore').strip('\x00')
                }
                logger.info(f"Gateway version: {self.version_info}")
                return self.version_info
            else:
                logger.error(f"Failed to read version: return code {return_code}")
        else:
            logger.error("Invalid response to version query")
        
        return None
    
    async def start_reading(self, callback: Callable[[ESP3Packet], None]):
        """
        Start continuous reading of packets
        
        Args:
            callback: Function to call with each received packet
        """
        self.running = True
        logger.info("Started reading from serial port")
        logger.info("=" * 80)
        logger.info("🎧 LISTENING FOR ENOCEAN TELEGRAMS")
        logger.info("   Waiting for device transmissions...")
        logger.info("   Trigger your EnOcean devices now to see telegrams here")
        logger.info("=" * 80)
        
        packet_count = 0
        while self.running:
            try:
                packet = await self.read_packet()
                if packet:
                    packet_count += 1
                    logger.info(f"📦 RAW PACKET #{packet_count} RECEIVED")
                    logger.info(f"   Type: {hex(packet.packet_type)}")
                    logger.info(f"   Data length: {len(packet.data)}")
                    logger.info(f"   Raw data: {packet.data.hex()}")
                    
                    # Only process radio telegrams, not responses
                    if packet.packet_type == ESP3Packet.PACKET_TYPE_RADIO_ERP1:
                        logger.info(f"   ✅ This is a RADIO TELEGRAM - processing...")
                        await callback(packet)
                    else:
                        logger.info(f"   ⏭️  Not a radio telegram - skipping")
            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                await asyncio.sleep(1)
    
    def stop_reading(self):
        """Stop continuous reading"""
        self.running = False
        logger.info("Stopped reading from serial port")
    
    async def send_telegram(self, destination_id: str, rorg: int, data_bytes: bytes, status: int = 0x00) -> bool:
        """
        Send EnOcean telegram to a device
        
        Args:
            destination_id: Destination device ID as hex string (e.g., '05834fa4')
            rorg: RORG byte (0xA5 for 4BS, 0xF6 for RPS, 0xD2 for VLD)
            data_bytes: Data bytes (without RORG, sender ID, or status)
            status: Status byte (default 0x00)
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Get gateway base ID (sender ID)
        if not self.base_id:
            base_id = await self.get_base_id()
            if not base_id:
                logger.error("Cannot send telegram: gateway base ID not available")
                return False
        
        # Create radio packet
        packet = ESP3Packet.create_radio_packet(
            self.base_id,
            destination_id,
            rorg,
            data_bytes,
            status
        )
        
        # Send packet
        logger.info(f"📤 Sending telegram to {destination_id}: RORG={hex(rorg)}, data={data_bytes.hex()}")
        success = await self.write_packet(packet)
        
        if success:
            logger.info(f"✅ Telegram sent successfully")
        else:
            logger.error(f"❌ Failed to send telegram")
        
        return success
    
    async def send_rps_command(self, destination_id: str, button_code: int, press_duration: float = 0.1) -> bool:
        """
        Send RPS (rocker switch) command with press and release
        
        Args:
            destination_id: Destination device ID as hex string
            button_code: Button code (0x10=A0, 0x30=A1, 0x50=B0, 0x70=B1)
            press_duration: Duration to hold button in seconds (default 0.1)
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Get gateway base ID
        if not self.base_id:
            base_id = await self.get_base_id()
            if not base_id:
                logger.error("Cannot send RPS command: gateway base ID not available")
                return False
        
        logger.info(f"📤 Sending RPS command to {destination_id}: button={hex(button_code)}")
        
        # Send button press
        packet_press = ESP3Packet.create_rps_packet(self.base_id, destination_id, button_code, pressed=True)
        if not await self.write_packet(packet_press):
            logger.error("❌ Failed to send button press")
            return False
        
        logger.info(f"   ✅ Button press sent")
        
        # Wait for press duration
        await asyncio.sleep(press_duration)
        
        # Send button release
        packet_release = ESP3Packet.create_rps_packet(self.base_id, destination_id, button_code, pressed=False)
        if not await self.write_packet(packet_release):
            logger.error("❌ Failed to send button release")
            return False
        
        logger.info(f"   ✅ Button release sent")
        logger.info(f"✅ RPS command completed successfully")
        
        return True
    
    async def send_4bs_command(self, destination_id: str, db3: int, db2: int, db1: int, db0: int) -> bool:
        """
        Send 4BS (A5) command to actuator
        
        Args:
            destination_id: Destination device ID as hex string
            db3, db2, db1, db0: Data bytes
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Get gateway base ID
        if not self.base_id:
            base_id = await self.get_base_id()
            if not base_id:
                logger.error("Cannot send 4BS command: gateway base ID not available")
                return False
        
        logger.info(f"📤 Sending 4BS command to {destination_id}: DB3={hex(db3)}, DB2={hex(db2)}, DB1={hex(db1)}, DB0={hex(db0)}")
        
        # Create and send packet
        packet = ESP3Packet.create_4bs_packet(self.base_id, destination_id, db3, db2, db1, db0)
        success = await self.write_packet(packet)
        
        if success:
            logger.info(f"✅ 4BS command sent successfully")
        else:
            logger.error(f"❌ Failed to send 4BS command")
        
        return success
