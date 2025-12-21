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
        self.command_callback = None
        self.event_loop = None
        
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
    
    def publish_discovery(self, device: Dict[str, Any], entity: Dict[str, Any], is_controllable: bool = False) -> bool:
        """
        Publish Home Assistant MQTT discovery message
        
        Args:
            device: Device information dict
            entity: Entity information dict
            is_controllable: Whether this entity supports commands
            
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
            elif component == 'switch':
                # For switches, convert 0/1 to OFF/ON to match state_on/state_off
                payload['value_template'] = f"{{% if value_json.{entity_shortcut} == 1 %}}ON{{% else %}}OFF{{% endif %}}"
            else:
                # For regular sensors, use value directly
                payload['value_template'] = f"{{{{ value_json.{entity_shortcut} }}}}"
            
            # Add command topic for controllable entities
            if is_controllable:
                command_topic = f"enocean/{device_id}/set/{entity_shortcut}"
                payload['command_topic'] = command_topic
                
                # Add component-specific command fields
                if component == 'switch':
                    payload['payload_on'] = '{"state": "ON"}'
                    payload['payload_off'] = '{"state": "OFF"}'
                    payload['state_on'] = "ON"
                    payload['state_off'] = "OFF"
                    payload['optimistic'] = False
                elif component == 'light':
                    payload['payload_on'] = '{"state": "ON"}'
                    payload['payload_off'] = '{"state": "OFF"}'
                    payload['state_on'] = 1
                    payload['state_off'] = 0
                    payload['optimistic'] = False
                    # Add brightness support if entity supports it
                    if 'brightness' in entity.get('name', '').lower() or 'dim' in entity.get('name', '').lower():
                        payload['brightness_command_topic'] = command_topic
                        payload['brightness_scale'] = 255
                        payload['brightness_state_topic'] = f"enocean/{device_id}/state"
                        payload['brightness_value_template'] = f"{{{{ value_json.{entity_shortcut} }}}}"
                    # Add RGB support for RGB lights
                    if 'rgb' in entity.get('name', '').lower() or 'color' in entity.get('name', '').lower():
                        payload['rgb_command_topic'] = command_topic
                        payload['rgb_state_topic'] = f"enocean/{device_id}/state"
                        payload['rgb_value_template'] = f"{{{{ value_json.rgb }}}}"
                        payload['color_mode'] = True
                        payload['supported_color_modes'] = ['rgb']
                elif component == 'cover':
                    payload['position_topic'] = f"enocean/{device_id}/state"
                    payload['set_position_topic'] = command_topic
                    payload['position_template'] = f"{{{{ value_json.{entity_shortcut} }}}}"
                    payload['optimistic'] = False
                
                logger.debug(f"Added command topic for controllable entity: {command_topic}")
            
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
                logger.info(f"Published discovery for {unique_id} (controllable={is_controllable})")
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
    
    def subscribe_commands(self, callback) -> bool:
        """
        Subscribe to command topics from Home Assistant
        
        Args:
            callback: Async function to call when command received
                     Signature: async def callback(device_id: str, entity: str, command: dict)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker, cannot subscribe to commands")
            return False
        
        try:
            self.command_callback = callback
            
            # Subscribe to all command topics: enocean/+/set/#
            topic = "enocean/+/set/#"
            self.client.subscribe(topic, qos=1)
            
            # Set message callback
            self.client.on_message = self._on_command_message
            
            logger.info(f"✓ Subscribed to command topic: {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to commands: {e}")
            return False
    
    def _on_command_message(self, client, userdata, msg):
        """
        Callback when command message received
        
        Topic format: enocean/{device_id}/set/{entity}
        Payload: JSON with command data
        """
        try:
            # Parse topic
            topic_parts = msg.topic.split('/')
            if len(topic_parts) < 4 or topic_parts[0] != 'enocean' or topic_parts[2] != 'set':
                logger.warning(f"Invalid command topic format: {msg.topic}")
                return
            
            device_id = topic_parts[1]
            entity = topic_parts[3]
            
            # Parse payload
            try:
                command = json.loads(msg.payload.decode('utf-8'))
            except json.JSONDecodeError:
                # Try simple string payload (ON/OFF)
                payload_str = msg.payload.decode('utf-8')
                command = {'state': payload_str}
            
            logger.info(f"📥 Command received: device={device_id}, entity={entity}, command={command}")
            
            # Call callback if set
            if self.command_callback:
                # Schedule async callback using asyncio.run_coroutine_threadsafe
                import asyncio
                try:
                    # Get the main event loop (we need to store it during init)
                    if hasattr(self, 'event_loop') and self.event_loop:
                        # Schedule coroutine in the main event loop from this thread
                        asyncio.run_coroutine_threadsafe(
                            self.command_callback(device_id, entity, command),
                            self.event_loop
                        )
                    else:
                        logger.error("Event loop not set, cannot process command")
                except Exception as e:
                    logger.error(f"Error calling command callback: {e}", exc_info=True)
            else:
                logger.warning("No command callback set, ignoring command")
                
        except Exception as e:
            logger.error(f"Error processing command message: {e}", exc_info=True)
