"""
ESP3 Protocol Implementation for EnOcean
Handles packet parsing and creation according to ESP3 specification
"""
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ESP3Packet:
    """ESP3 packet structure parser and builder"""
    
    SYNC_BYTE = 0x55
    
    # Packet types
    PACKET_TYPE_RADIO_ERP1 = 0x01
    PACKET_TYPE_RESPONSE = 0x02
    PACKET_TYPE_RADIO_SUB_TEL = 0x03
    PACKET_TYPE_EVENT = 0x04
    PACKET_TYPE_COMMON_COMMAND = 0x05
    PACKET_TYPE_SMART_ACK_COMMAND = 0x06
    PACKET_TYPE_REMOTE_MAN_COMMAND = 0x07
    PACKET_TYPE_RADIO_MESSAGE = 0x09
    PACKET_TYPE_RADIO_ERP2 = 0x0A
    
    # Common commands
    CO_WR_SLEEP = 0x01
    CO_WR_RESET = 0x02
    CO_RD_VERSION = 0x03
    CO_RD_SYS_LOG = 0x04
    CO_WR_SYS_LOG = 0x05
    CO_WR_BIST = 0x06
    CO_WR_IDBASE = 0x07
    CO_RD_IDBASE = 0x08
    CO_WR_REPEATER = 0x09
    CO_RD_REPEATER = 0x0A
    
    def __init__(self, raw_data: Optional[bytes] = None):
        """Initialize ESP3 packet from raw data or create empty packet"""
        if raw_data:
            self.parse(raw_data)
        else:
            self.sync = self.SYNC_BYTE
            self.data_length = 0
            self.optional_length = 0
            self.packet_type = 0
            self.data = b''
            self.optional_data = b''
    
    def parse(self, raw_data: bytes):
        """Parse raw ESP3 packet data"""
        if len(raw_data) < 6:
            raise ValueError("Packet too short")
        
        # Parse header
        self.sync = raw_data[0]
        if self.sync != self.SYNC_BYTE:
            raise ValueError(f"Invalid sync byte: {hex(self.sync)}")
        
        self.data_length = int.from_bytes(raw_data[1:3], 'big')
        self.optional_length = raw_data[3]
        self.packet_type = raw_data[4]
        header_crc = raw_data[5]
        
        # Validate header CRC
        calculated_header_crc = self.calculate_crc8(raw_data[1:5])
        if header_crc != calculated_header_crc:
            raise ValueError(f"Header CRC mismatch: {hex(header_crc)} != {hex(calculated_header_crc)}")
        
        # Extract data and optional data
        data_start = 6
        data_end = data_start + self.data_length
        optional_end = data_end + self.optional_length
        
        if len(raw_data) < optional_end + 1:
            raise ValueError("Packet data incomplete")
        
        self.data = raw_data[data_start:data_end]
        self.optional_data = raw_data[data_end:optional_end]
        data_crc = raw_data[optional_end]
        
        # Validate data CRC
        calculated_data_crc = self.calculate_crc8(self.data + self.optional_data)
        if data_crc != calculated_data_crc:
            raise ValueError(f"Data CRC mismatch: {hex(data_crc)} != {hex(calculated_data_crc)}")
        
        logger.debug(f"Parsed ESP3 packet: type={hex(self.packet_type)}, data_len={self.data_length}, opt_len={self.optional_length}")
    
    @staticmethod
    def calculate_crc8(data: bytes) -> int:
        """Calculate CRC8 checksum using EnOcean polynomial"""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc = crc << 1
                crc &= 0xFF
        return crc
    
    def build(self) -> bytes:
        """Build raw ESP3 packet from components"""
        # Build header
        header = bytes([
            (self.data_length >> 8) & 0xFF,
            self.data_length & 0xFF,
            self.optional_length,
            self.packet_type
        ])
        header_crc = self.calculate_crc8(header)
        
        # Build data CRC
        data_crc = self.calculate_crc8(self.data + self.optional_data)
        
        # Assemble packet
        packet = bytes([self.SYNC_BYTE]) + header + bytes([header_crc]) + self.data + self.optional_data + bytes([data_crc])
        return packet
    
    def get_sender_id(self) -> Optional[str]:
        """Extract sender ID from radio telegram"""
        if self.packet_type == self.PACKET_TYPE_RADIO_ERP1:
            # Sender ID is always the last 4 bytes before status byte
            # Structure: [RORG] [Data...] [Sender ID - 4 bytes] [Status - 1 byte]
            if len(self.data) >= 6:  # Minimum: RORG + 1 data + 4 sender + 1 status
                sender_bytes = self.data[-5:-1]  # Last 4 bytes before status
                return sender_bytes.hex()
        return None
    
    def get_rorg(self) -> Optional[int]:
        """Extract RORG (R-ORG) from radio telegram"""
        if self.packet_type == self.PACKET_TYPE_RADIO_ERP1:
            if len(self.data) >= 1:
                return self.data[0]
        return None
    
    def get_rssi(self) -> Optional[int]:
        """Extract RSSI from optional data"""
        if len(self.optional_data) >= 6:
            # RSSI is at byte 5 of optional data
            rssi_raw = self.optional_data[5]
            # Convert to dBm (negative value)
            return -rssi_raw
        return None
    
    def get_data_bytes(self) -> bytes:
        """Get data bytes (without RORG, sender ID, and status)"""
        if self.packet_type == self.PACKET_TYPE_RADIO_ERP1:
            if len(self.data) >= 6:
                # Data is between RORG and sender ID
                # Structure: [RORG] [Data...] [Sender ID - 4 bytes] [Status - 1 byte]
                return self.data[1:-5]  # Skip RORG, skip last 5 bytes (4 ID + 1 status)
        return b''
    
    def get_status_byte(self) -> Optional[int]:
        """Get status byte from telegram"""
        if self.packet_type == self.PACKET_TYPE_RADIO_ERP1:
            if len(self.data) >= 1:
                return self.data[-1]
        return None
    
    def is_teach_in(self) -> bool:
        """Check if this is a teach-in telegram"""
        rorg = self.get_rorg()
        status = self.get_status_byte()
        
        if rorg == 0xA5:  # 4BS telegram
            # Check LRN bit (bit 3 of status byte)
            if status is not None:
                return (status & 0x08) == 0
        elif rorg == 0xF6:  # RPS telegram
            # RPS teach-in detection is more complex
            # Usually indicated by specific button combinations
            pass
        elif rorg == 0xD5:  # 1BS telegram
            # Check LRN bit
            if status is not None:
                return (status & 0x08) == 0
        
        return False
    
    @classmethod
    def create_common_command(cls, command: int, data: bytes = b'') -> 'ESP3Packet':
        """Create a common command packet"""
        packet = cls()
        packet.packet_type = cls.PACKET_TYPE_COMMON_COMMAND
        packet.data = bytes([command]) + data
        packet.data_length = len(packet.data)
        packet.optional_length = 0
        packet.optional_data = b''
        return packet
    
    @classmethod
    def create_read_base_id(cls) -> 'ESP3Packet':
        """Create packet to read base ID"""
        return cls.create_common_command(cls.CO_RD_IDBASE)
    
    @classmethod
    def create_read_version(cls) -> 'ESP3Packet':
        """Create packet to read version info"""
        return cls.create_common_command(cls.CO_RD_VERSION)
    
    @classmethod
    def create_teach_in_response(cls, device_id: str, eep_func: int, eep_type: int, manufacturer_id: int = 0x7FF) -> 'ESP3Packet':
        """
        Create a UTE teach-in response packet
        
        Args:
            device_id: Device ID as hex string (e.g., '05834fa4')
            eep_func: EEP FUNC value (6 bits)
            eep_type: EEP TYPE value (7 bits)
            manufacturer_id: Manufacturer ID (11 bits, default 0x7FF = not specified)
        
        Returns:
            ESP3Packet with teach-in response
        """
        packet = cls()
        packet.packet_type = cls.PACKET_TYPE_RADIO_ERP1
        
        # Convert device ID to bytes
        device_id_bytes = bytes.fromhex(device_id)
        
        # Build teach-in response data (4BS format)
        # DB3: FUNC (6 bits) + TYPE high (2 bits)
        db3 = (eep_func << 2) | ((eep_type >> 5) & 0x03)
        
        # DB2: TYPE low (5 bits) + MANUF high (3 bits)
        db2 = ((eep_type & 0x1F) << 3) | ((manufacturer_id >> 8) & 0x07)
        
        # DB1: MANUF low (8 bits)
        db1 = manufacturer_id & 0xFF
        
        # DB0: Response bits
        # Bit 7: EEP teach-in response (1)
        # Bit 6-4: Response code (0 = teach-in accepted)
        # Bit 3: LRN bit (1 = data telegram)
        # Bit 2-0: Reserved
        db0 = 0x88  # 10001000 = Response accepted, LRN=1
        
        # Build data: RORG + DB3 + DB2 + DB1 + DB0 + Sender ID + Status
        rorg = 0xA5  # 4BS
        status = 0x00  # No special status
        
        packet.data = bytes([rorg, db3, db2, db1, db0]) + device_id_bytes + bytes([status])
        packet.data_length = len(packet.data)
        
        # Optional data (empty for now)
        packet.optional_length = 0
        packet.optional_data = b''
        
        return packet
    
    @classmethod
    def create_radio_packet(cls, sender_id: str, destination_id: str, rorg: int, data_bytes: bytes, status: int = 0x00) -> 'ESP3Packet':
        """
        Create a radio telegram packet for sending commands to devices
        
        Args:
            sender_id: Sender ID (gateway base ID) as hex string (e.g., 'ff800000')
            destination_id: Destination device ID as hex string (e.g., '05834fa4')
            rorg: RORG byte (0xA5 for 4BS, 0xF6 for RPS, 0xD2 for VLD)
            data_bytes: Data bytes (without RORG, sender ID, or status)
            status: Status byte (default 0x00)
        
        Returns:
            ESP3Packet ready to send
        """
        packet = cls()
        packet.packet_type = cls.PACKET_TYPE_RADIO_ERP1
        
        # Convert IDs to bytes
        sender_id_bytes = bytes.fromhex(sender_id)
        destination_id_bytes = bytes.fromhex(destination_id)
        
        # Build packet data: RORG + Data + Sender ID + Status
        packet.data = bytes([rorg]) + data_bytes + sender_id_bytes + bytes([status])
        packet.data_length = len(packet.data)
        
        # Build optional data: SubTelNum + Destination ID + dBm + Security Level
        # SubTelNum: 3 (number of subtelegrams)
        # Destination ID: 4 bytes
        # dBm: 0xFF (not used for sending)
        # Security Level: 0 (no encryption)
        packet.optional_data = bytes([0x03]) + destination_id_bytes + bytes([0xFF, 0x00])
        packet.optional_length = len(packet.optional_data)
        
        logger.debug(f"Created radio packet: RORG={hex(rorg)}, sender={sender_id}, dest={destination_id}, data={data_bytes.hex()}")
        
        return packet
    
    @classmethod
    def create_rps_packet(cls, sender_id: str, destination_id: str, button_code: int, pressed: bool = True) -> 'ESP3Packet':
        """
        Create an RPS (F6) telegram for rocker switch emulation
        
        Args:
            sender_id: Sender ID (gateway base ID) as hex string
            destination_id: Destination device ID as hex string (ignored for RPS - uses broadcast)
            button_code: Button code (0x10=A0, 0x30=A1, 0x50=B0, 0x70=B1)
            pressed: True for button pressed, False for released
        
        Returns:
            ESP3Packet for RPS telegram
        """
        # RPS telegrams are BROADCAST - destination is always FFFFFFFF
        # Eltako actuators learn the SENDER ID and respond to broadcasts from that ID
        broadcast_id = "FFFFFFFF"
        
        # RPS data byte:
        # Bits 7-5: R1 (rocker first action)
        # Bit 4: EB (energy bow - 1=pressed, 0=released)
        # Bits 3-1: R2 (rocker second action)
        # Bit 0: SA (second action valid)
        
        if pressed:
            data_byte = button_code | 0x10  # Set EB bit (pressed)
        else:
            data_byte = 0x00  # All bits 0 (released)
        
        # Status byte for RPS: T21=1, NU=1 for pressed, NU=0 for released
        status = 0x30 if pressed else 0x20
        
        logger.info(f"Creating RPS packet: sender={sender_id}, broadcast={broadcast_id}, button={hex(button_code)}, pressed={pressed}, data={hex(data_byte)}, status={hex(status)}")
        
        return cls.create_radio_packet(sender_id, broadcast_id, 0xF6, bytes([data_byte]), status)
    
    @classmethod
    def create_4bs_packet(cls, sender_id: str, destination_id: str, db3: int, db2: int, db1: int, db0: int) -> 'ESP3Packet':
        """
        Create a 4BS (A5) telegram for actuator control
        
        Args:
            sender_id: Sender ID (gateway base ID) as hex string
            destination_id: Destination device ID as hex string
            db3, db2, db1, db0: Data bytes
        
        Returns:
            ESP3Packet for 4BS telegram
        """
        data_bytes = bytes([db3, db2, db1, db0])
        return cls.create_radio_packet(sender_id, destination_id, 0xA5, data_bytes, 0x00)
    
    def __repr__(self) -> str:
        return (f"ESP3Packet(type={hex(self.packet_type)}, "
                f"data_len={self.data_length}, "
                f"opt_len={self.optional_length}, "
                f"sender={self.get_sender_id()}, "
                f"rorg={hex(self.get_rorg()) if self.get_rorg() else None})")
