"""
Device Manager
Manages EnOcean devices and their configuration
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manage EnOcean devices"""
    
    def __init__(self, data_file: str = '/data/devices.json'):
        """
        Initialize device manager
        
        Args:
            data_file: Path to devices data file
        """
        self.data_file = Path(data_file)
        self.devices: Dict[str, dict] = {}
        self.load_devices()
    
    @staticmethod
    def normalize_device_id(device_id: str) -> str:
        """
        Normalize device ID to lowercase 8-char hex without prefix
        
        Args:
            device_id: Device ID in any format (0xABC123, ABC123, abc123)
            
        Returns:
            Normalized lowercase hex string without 0x prefix
        """
        # Remove 0x prefix if present
        if device_id.lower().startswith('0x'):
            device_id = device_id[2:]
        # Convert to lowercase
        return device_id.lower()
    
    def load_devices(self):
        """Load devices from file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    raw_devices = json.load(f)
                
                # Normalize all device IDs on load (handles legacy uppercase/0x prefixed IDs)
                self.devices = {}
                for device_id, device_data in raw_devices.items():
                    normalized_id = self.normalize_device_id(device_id)
                    device_data['id'] = normalized_id  # Update stored ID too
                    self.devices[normalized_id] = device_data
                
                logger.info(f"Loaded {len(self.devices)} devices from {self.data_file}")
            else:
                logger.info("No existing devices file, starting fresh")
                self.devices = {}
        except Exception as e:
            logger.error(f"Error loading devices: {e}")
            self.devices = {}
    
    def save_devices(self):
        """Save devices to file"""
        try:
            # Ensure data directory exists
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.data_file, 'w') as f:
                json.dump(self.devices, f, indent=2)
            logger.debug(f"Saved {len(self.devices)} devices to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving devices: {e}")
    
    def add_device(self, device_id: str, name: str, eep: str, manufacturer: str = "EnOcean") -> bool:
        """
        Add a new device
        
        Args:
            device_id: Device ID (sender ID)
            name: Device name
            eep: EEP profile code
            manufacturer: Manufacturer name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Normalize device ID to lowercase without 0x prefix
            device_id = self.normalize_device_id(device_id)
            self.devices[device_id] = {
                'id': device_id,
                'name': name,
                'eep': eep,
                'manufacturer': manufacturer,
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'last_seen': None,
                'rssi': None
            }
            self.save_devices()
            logger.info(f"Added device: {device_id} ({name})")
            return True
        except Exception as e:
            logger.error(f"Error adding device: {e}")
            return False
    
    def get_device(self, device_id: str) -> Optional[dict]:
        """
        Get device by ID
        
        Args:
            device_id: Device ID (accepts any format: 0xABC123, ABC123, abc123)
            
        Returns:
            Device dict if found, None otherwise
        """
        # Normalize device ID for lookup
        device_id = self.normalize_device_id(device_id)
        return self.devices.get(device_id)
    
    def list_devices(self) -> List[dict]:
        """
        List all devices
        
        Returns:
            List of device dicts
        """
        return list(self.devices.values())
    
    def update_last_seen(self, device_id: str, rssi: int = None):
        """
        Update device last seen timestamp
        
        Args:
            device_id: Device ID
            rssi: RSSI value (optional)
        """
        device_id = self.normalize_device_id(device_id)
        if device_id in self.devices:
            self.devices[device_id]['last_seen'] = datetime.now().isoformat()
            if rssi is not None:
                self.devices[device_id]['rssi'] = rssi
            self.save_devices()
    
    def remove_device(self, device_id: str) -> bool:
        """
        Remove a device
        
        Args:
            device_id: Device ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            device_id = self.normalize_device_id(device_id)
            if device_id in self.devices:
                del self.devices[device_id]
                self.save_devices()
                logger.info(f"Removed device: {device_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing device: {e}")
            return False
    
    def enable_device(self, device_id: str, enabled: bool = True) -> bool:
        """
        Enable or disable a device
        
        Args:
            device_id: Device ID
            enabled: True to enable, False to disable
            
        Returns:
            True if successful, False otherwise
        """
        try:
            device_id = self.normalize_device_id(device_id)
            if device_id in self.devices:
                self.devices[device_id]['enabled'] = enabled
                self.save_devices()
                logger.info(f"{'Enabled' if enabled else 'Disabled'} device: {device_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error enabling/disabling device: {e}")
            return False
    
    def is_device_enabled(self, device_id: str) -> bool:
        """
        Check if device is enabled
        
        Args:
            device_id: Device ID
            
        Returns:
            True if enabled, False otherwise
        """
        device = self.get_device(device_id)
        return device.get('enabled', False) if device else False
