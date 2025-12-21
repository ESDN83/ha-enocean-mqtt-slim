"""
Command Translator
Translates MQTT commands to EnOcean telegrams based on EEP profiles
"""
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class CommandTranslator:
    """Translate MQTT commands to EnOcean telegrams"""
    
    def __init__(self, eep_loader):
        """
        Initialize command translator
        
        Args:
            eep_loader: EEP profile loader instance
        """
        self.eep_loader = eep_loader
    
    def translate_switch_command(self, device: Dict[str, Any], state: str) -> Optional[Tuple[int, bytes]]:
        """
        Translate switch ON/OFF command to EnOcean telegram
        
        Args:
            device: Device dictionary with 'eep' key
            state: "ON" or "OFF"
            
        Returns:
            Tuple of (rorg, data_bytes) or None if not supported
        """
        eep = device.get('eep', '')
        
        # A5-38-08: Central Command (Gateway)
        if eep == 'A5-38-08':
            # DB3: Command ID (0x02 = Switching)
            # DB2: Not used (0x00)
            # DB1: Dimming value (0x00 = OFF, 0x64 = 100% = ON)
            # DB0: Switching command (0x09 = ON, 0x08 = OFF)
            if state.upper() == 'ON':
                data_bytes = bytes([0x02, 0x00, 0x64, 0x09])
            else:
                data_bytes = bytes([0x02, 0x00, 0x00, 0x08])
            return (0xA5, data_bytes)
        
        # D2-01-xx: Electronic switches and dimmers
        elif eep.startswith('D2-01'):
            # VLD telegram for D2-01 actuators
            # CMD 0x01 = Actuator Set Output
            # DB_0 bits 7-1: Output value (0-100, 0=OFF, 100=ON)
            # DB_0 bit 0: I/O channel (0)
            if state.upper() == 'ON':
                data_bytes = bytes([0x01, 0x01, 0x64, 0x00])  # CMD, Channel, Value 100%, reserved
            else:
                data_bytes = bytes([0x01, 0x01, 0x00, 0x00])  # CMD, Channel, Value 0%, reserved
            return (0xD2, data_bytes)
        
        # Eltako actuator control (F6-02-01-actuator)
        elif eep == 'F6-02-01-actuator':
            # Return None to use RPS command instead
            logger.info(f"F6-02-01-actuator: using RPS command for {state}")
            return None
        
        # Virtual rocker switch (F6-02-01) - sensors, not actuators
        elif eep == 'F6-02-01' or eep.startswith('F6-02'):
            # Use RPS button press to toggle
            # This will be handled separately by send_rps_command
            return None
        
        logger.warning(f"Switch command not supported for EEP {eep}")
        return None
    
    def translate_dim_command(self, device: Dict[str, Any], brightness: int) -> Optional[Tuple[int, bytes]]:
        """
        Translate dimming command to EnOcean telegram
        
        Args:
            device: Device dictionary with 'eep' key
            brightness: Brightness value 0-255
            
        Returns:
            Tuple of (rorg, data_bytes) or None if not supported
        """
        eep = device.get('eep', '')
        
        # A5-38-08: Central Command (Gateway)
        if eep == 'A5-38-08':
            # DB3: Command ID (0x02 = Dimming)
            # DB2: Dimming range (0x00 = absolute)
            # DB1: Dimming value (0-100, scaled from 0-255)
            # DB0: Dimming command (0x09 = execute)
            dim_value = int((brightness / 255.0) * 100)
            data_bytes = bytes([0x02, 0x00, dim_value, 0x09])
            return (0xA5, data_bytes)
        
        logger.warning(f"Dim command not supported for EEP {eep}")
        return None
    
    def translate_rgb_command(self, device: Dict[str, Any], red: int, green: int, blue: int) -> Optional[Tuple[int, bytes]]:
        """
        Translate RGB color command to EnOcean telegram
        
        Args:
            device: Device dictionary with 'eep' key
            red: Red value 0-255
            green: Green value 0-255
            blue: Blue value 0-255
            
        Returns:
            Tuple of (rorg, data_bytes) or None if not supported
        """
        eep = device.get('eep', '')
        
        # A5-38-08: Central Command (Gateway) - RGB extension
        if eep == 'A5-38-08':
            # DB3: Command ID (0x07 = RGB Color)
            # DB2: Red (0-255)
            # DB1: Green (0-255)
            # DB0: Blue (0-255)
            data_bytes = bytes([0x07, red, green, blue])
            return (0xA5, data_bytes)
        
        # D2-01-12: Electronic switch with RGB support
        elif eep == 'D2-01-12':
            # VLD telegram for RGB
            # This is a simplified implementation
            logger.warning(f"RGB command for {eep} using simplified format")
            data_bytes = bytes([0x07, red, green, blue])
            return (0xD2, data_bytes)
        
        logger.warning(f"RGB command not supported for EEP {eep}")
        return None
    
    def translate_cover_command(self, device: Dict[str, Any], position: int) -> Optional[Tuple[int, bytes]]:
        """
        Translate cover position command to EnOcean telegram
        
        Args:
            device: Device dictionary with 'eep' key
            position: Position value 0-100 (0=closed, 100=open)
            
        Returns:
            Tuple of (rorg, data_bytes) or None if not supported
        """
        eep = device.get('eep', '')
        
        # D2-05-xx: Blinds/shutters control
        if eep.startswith('D2-05'):
            # VLD telegram for blind control
            # This is complex and device-specific
            logger.warning(f"Cover command for {eep} not yet implemented")
            return None
        
        logger.warning(f"Cover command not supported for EEP {eep}")
        return None
    
    def translate_rps_button(self, button: str) -> Optional[int]:
        """
        Translate button name to RPS button code
        
        Args:
            button: Button name ("A0", "A1", "B0", "B1")
            
        Returns:
            Button code or None if invalid
        """
        button_map = {
            'A0': 0x10,
            'AI': 0x10,  # Alternative naming
            'A1': 0x30,
            'AO': 0x30,  # Alternative naming
            'B0': 0x50,
            'BI': 0x50,  # Alternative naming
            'B1': 0x70,
            'BO': 0x70,  # Alternative naming
        }
        return button_map.get(button.upper())
    
    def translate_command(self, device: Dict[str, Any], entity: str, command: Dict[str, Any]) -> Optional[Tuple[str, int, bytes]]:
        """
        Translate generic MQTT command to EnOcean telegram
        
        Args:
            device: Device dictionary
            entity: Entity name (e.g., "switch", "light", "cover")
            command: Command dictionary (e.g., {"state": "ON"}, {"brightness": 255})
            
        Returns:
            Tuple of (command_type, rorg, data_bytes) or None if not supported
            command_type can be "telegram" or "rps"
        """
        eep = device.get('eep', '')
        
        logger.info(f"Translating command for {device['id']} ({eep}): entity={entity}, command={command}")
        
        # Handle switch commands
        if 'state' in command:
            state = command['state']
            result = self.translate_switch_command(device, state)
            if result:
                rorg, data_bytes = result
                return ('telegram', rorg, data_bytes)
            
            # Fallback to RPS for actuators and switches
            if eep == 'F6-02-01-actuator' or eep.startswith('F6-02'):
                # Use rocker A0 for ON, A1 for OFF (Eltako convention)
                if state.upper() == 'ON':
                    button_code = 0x10  # A0 (rocker up) = ON
                else:
                    button_code = 0x30  # A1 (rocker down) = OFF
                logger.info(f"RPS command: state={state} -> button_code={hex(button_code)}")
                return ('rps', button_code, bytes())
        
        # Handle brightness commands
        if 'brightness' in command:
            brightness = command['brightness']
            result = self.translate_dim_command(device, brightness)
            if result:
                rorg, data_bytes = result
                return ('telegram', rorg, data_bytes)
        
        # Handle position commands (covers)
        if 'position' in command:
            position = command['position']
            result = self.translate_cover_command(device, position)
            if result:
                rorg, data_bytes = result
                return ('telegram', rorg, data_bytes)
        
        # Handle RPS button commands
        if 'button' in command:
            button = command['button']
            button_code = self.translate_rps_button(button)
            if button_code:
                return ('rps', button_code, bytes())
        
        logger.warning(f"Could not translate command for {eep}: {command}")
        return None
    
    def get_supported_commands(self, eep: str) -> Dict[str, list]:
        """
        Get list of supported commands for an EEP profile
        
        Args:
            eep: EEP profile code
            
        Returns:
            Dictionary of supported commands by entity type
        """
        commands = {}
        
        # A5-38-08: Central Command
        if eep == 'A5-38-08':
            commands['switch'] = ['state']
            commands['light'] = ['state', 'brightness']
        
        # F6-02-xx: Rocker switches
        elif eep.startswith('F6-02'):
            commands['button'] = ['button']
        
        # D2-01-xx: Electronic switches
        elif eep.startswith('D2-01'):
            commands['switch'] = ['state']
            commands['light'] = ['state', 'brightness']
        
        # D2-05-xx: Blinds/shutters
        elif eep.startswith('D2-05'):
            commands['cover'] = ['position']
        
        return commands
    
    def is_controllable(self, eep: str) -> bool:
        """
        Check if an EEP profile supports sending commands
        
        Args:
            eep: EEP profile code
            
        Returns:
            True if controllable, False otherwise
        """
        controllable_profiles = [
            'A5-38-08',  # Central Command
            'D2-01',     # Electronic switches (prefix)
            'D2-05',     # Blinds/shutters (prefix)
            'F6-02',     # Virtual rocker (prefix)
        ]
        
        for profile in controllable_profiles:
            if eep == profile or eep.startswith(profile):
                return True
        
        return False
