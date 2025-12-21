"""
Service State Manager
Provides access to service state for web UI
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ServiceState:
    """Singleton to hold service state accessible from web UI"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceState, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.service = None
        self.gateway_info = {}
        self.detected_profiles = {}  # Cache: device_id -> list of detected profile EEPs
        self._initialized = True
    
    def set_service(self, service):
        """Set the main service instance"""
        self.service = service
        logger.info("Service state manager initialized")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        if not self.service:
            return {
                "status": "initializing",
                "eep_profiles": 0,
                "devices": 0,
                "gateway_connected": False,
                "mqtt_connected": False
            }
        
        return {
            "status": "running" if self.service.running else "stopped",
            "eep_profiles": len(self.service.eep_loader.profiles) if self.service.eep_loader else 0,
            "devices": len(self.service.device_manager.list_devices()) if self.service.device_manager else 0,
            "gateway_connected": self.service.serial_handler is not None and self.service.serial_handler.is_open if self.service.serial_handler else False,
            "mqtt_connected": self.service.mqtt_handler.connected if self.service.mqtt_handler else False
        }
    
    def get_gateway_info(self) -> Dict[str, Any]:
        """Get gateway information"""
        return self.gateway_info
    
    def set_gateway_info(self, info: Dict[str, Any]):
        """Set gateway information"""
        self.gateway_info = info
    
    def get_device_manager(self):
        """Get device manager instance"""
        if self.service and self.service.device_manager:
            return self.service.device_manager
        return None
    
    def get_eep_loader(self):
        """Get EEP loader instance"""
        if self.service and self.service.eep_loader:
            return self.service.eep_loader
        return None
    
    def get_mqtt_handler(self):
        """Get MQTT handler instance"""
        if self.service and self.service.mqtt_handler:
            return self.service.mqtt_handler
        return None
    
    def get_state_persistence(self):
        """Get state persistence instance"""
        if self.service and self.service.state_persistence:
            return self.service.state_persistence
        return None
    
    def set_detected_profiles(self, device_id: str, profile_eeps: list):
        """Cache detected profiles for a device"""
        self.detected_profiles[device_id] = profile_eeps
        logger.info(f"Cached {len(profile_eeps)} detected profiles for device {device_id}")
    
    def get_detected_profiles(self, device_id: str) -> list:
        """Get cached detected profiles for a device"""
        return self.detected_profiles.get(device_id, [])


# Global instance
service_state = ServiceState()
