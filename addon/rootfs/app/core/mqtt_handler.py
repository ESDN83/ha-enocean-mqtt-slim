"""
MQTT Handler
Manages MQTT communication and Home Assistant discovery
"""
import json
import logging
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTHandler:
    """Handle MQTT communication and Home Assistant discovery"""
    
    def __init__(self, host: str, port: int, username: str = None, password: str = None):
        """
        Initialize MQTT handler
        
        Args:
            host: MQTT broker host
            port: MQTT broker port
            username: MQTT username (optional)
            password: MQTT password (optional)
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            self.client = mqtt.Client(client_id="enocean-mqtt-slim")
            
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
            
            logger.info(f"Connecting to MQTT broker at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            logger.info("✓ Connected to MQTT broker")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def publish_discovery(self, device: Dict[str, Any], entity: Dict[str, Any]) -> bool:
        """
        Publish Home Assistant MQTT discovery message
        
        Args:
            device: Device information dict
            entity: Entity information dict
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        try:
            component = entity.get('component', 'sensor')
            device_id = device['id']
            entity_shortcut = entity['shortcut']
            
            # Create unique ID
            unique_id = f"enocean_{device_id}_{entity_shortcut}"
            
            # Discovery topic
            topic = f"homeassistant/{component}/{unique_id}/config"
            
            # Build discovery payload
            payload = {
                "name": f"{device['name']} {entity['name']}",
                "unique_id": unique_id,
                "state_topic": f"enocean/{device_id}/state",
                "availability_topic": f"enocean/{device_id}/availability",
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": {
                    "identifiers": [f"enocean_{device_id}"],
                    "name": device['name'],
                    "manufacturer": device.get('manufacturer', 'EnOcean'),
                    "model": device.get('eep', 'Unknown'),
                    "via_device": "enocean_gateway"
                }
            }
            
            # Set value_template based on component type
            if component == 'binary_sensor':
                # For binary sensors, convert 0/1 to OFF/ON
                payload['value_template'] = f"{{% if value_json.{entity_shortcut} == 1 %}}ON{{% else %}}OFF{{% endif %}}"
            else:
                # For regular sensors, use value directly
                payload['value_template'] = f"{{{{ value_json.{entity_shortcut} }}}}"
            
            # Add optional fields
            if entity.get('device_class'):
                payload['device_class'] = entity['device_class']
            if entity.get('icon'):
                payload['icon'] = entity['icon']
            if entity.get('unit'):
                payload['unit_of_measurement'] = entity['unit']
            
            # Publish discovery message
            result = self.client.publish(topic, json.dumps(payload), qos=1, retain=True)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published discovery for {unique_id}")
                return True
            else:
                logger.error(f"Failed to publish discovery for {unique_id}: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing discovery: {e}")
            return False
    
    def publish_state(self, device_id: str, data: Dict[str, Any], retain: bool = True) -> bool:
        """
        Publish device state
        
        Args:
            device_id: Device ID
            data: State data dictionary
            retain: Whether to retain the message (default: True for state persistence)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        try:
            topic = f"enocean/{device_id}/state"
            payload = json.dumps(data)
            
            # Use retain flag to persist state in MQTT broker
            result = self.client.publish(topic, payload, qos=1, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published state for {device_id}: {data} (retain={retain})")
                return True
            else:
                logger.error(f"Failed to publish state for {device_id}: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing state: {e}")
            return False
    
    def publish_availability(self, device_id: str, available: bool) -> bool:
        """
        Publish device availability
        
        Args:
            device_id: Device ID
            available: True if online, False if offline
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            topic = f"enocean/{device_id}/availability"
            payload = "online" if available else "offline"
            
            result = self.client.publish(topic, payload, qos=1, retain=True)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published availability for {device_id}: {payload}")
                return True
            else:
                logger.error(f"Failed to publish availability for {device_id}: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing availability: {e}")
            return False
    
    def remove_device(self, device_id: str, entities: list) -> bool:
        """
        Remove device from Home Assistant (delete discovery configs)
        
        Args:
            device_id: Device ID
            entities: List of entity dicts
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            for entity in entities:
                component = entity.get('component', 'sensor')
                entity_shortcut = entity['shortcut']
                unique_id = f"enocean_{device_id}_{entity_shortcut}"
                
                topic = f"homeassistant/{component}/{unique_id}/config"
                
                # Publish empty payload to remove
                self.client.publish(topic, "", qos=1, retain=True)
                logger.info(f"Removed discovery for {unique_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing device: {e}")
            return False
