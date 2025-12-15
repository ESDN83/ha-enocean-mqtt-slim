# Implementation Guide - EnOcean MQTT Slim

This document outlines the complete implementation plan for the EnOcean MQTT Slim addon.

## Project Status

### ✅ Completed
- [x] Repository structure created
- [x] Git repository initialized
- [x] MIT License added
- [x] README.md with full documentation
- [x] Home Assistant addon configuration (config.yaml)
- [x] Dockerfile for multi-arch builds
- [x] Build configuration (build.yaml)
- [x] Startup script (run.sh)
- [x] Python requirements.txt
- [x] MV-01-01 EEP profile for Kessel Staufix Control
- [x] Directory structure for all components

### 🚧 Next Steps

## Phase 1: Core ESP3 Protocol (Priority: HIGH)

### File: `addon/rootfs/app/core/esp3_protocol.py`

Implement ESP3 packet handling:

```python
class ESP3Packet:
    """ESP3 packet structure parser"""
    SYNC_BYTE = 0x55
    
    def __init__(self, raw_data: bytes):
        self.sync = raw_data[0]
        self.data_length = int.from_bytes(raw_data[1:3], 'big')
        self.optional_length = raw_data[3]
        self.packet_type = raw_data[4]
        self.header_crc = raw_data[5]
        # Extract data and optional data
        # Validate CRCs
        
    @staticmethod
    def calculate_crc8(data: bytes) -> int:
        """Calculate CRC8 checksum"""
        # Implement CRC8 algorithm
        pass
```

**Key Functions:**
- Sync byte detection (0x55)
- Header parsing (data length, optional length, packet type)
- CRC8 validation
- Data extraction
- Packet type identification (Type 1: RADIO_ERP1, Type 2: RESPONSE, Type 10: RADIO_ERP2)

### File: `addon/rootfs/app/core/serial_handler.py`

Serial port communication:

```python
class SerialHandler:
    def __init__(self, port: str, baudrate: int = 57600):
        self.port = port
        self.serial = serial.Serial(port, baudrate)
        
    async def read_packet(self) -> ESP3Packet:
        """Read and parse ESP3 packet"""
        pass
        
    async def write_packet(self, packet: ESP3Packet):
        """Send ESP3 packet"""
        pass
        
    async def get_base_id(self) -> str:
        """Query gateway base ID"""
        # Send CO_RD_IDBASE command (0x08)
        pass
```

## Phase 2: EEP System (Priority: HIGH)

### File: `addon/rootfs/app/eep/loader.py`

Load and manage EEP profiles:

```python
class EEPLoader:
    def __init__(self, definitions_path: str):
        self.profiles = {}
        self.load_all_profiles()
        
    def load_all_profiles(self):
        """Load all JSON EEP files"""
        for json_file in Path(definitions_path).rglob('*.json'):
            profile = EEPProfile(json_file)
            self.profiles[profile.eep] = profile
            
    def get_profile(self, eep: str) -> EEPProfile:
        """Get EEP profile by code"""
        return self.profiles.get(eep)
```

### File: `addon/rootfs/app/eep/parser.py`

Parse telegrams using EEP profiles:

```python
class EEPParser:
    @staticmethod
    def extract_bits(data: bytes, bitoffs: int, bitsize: int) -> int:
        """Extract bits from byte array"""
        pass
        
    def parse_telegram(self, data: bytes, eep_profile: EEPProfile) -> dict:
        """Parse telegram data using EEP profile"""
        result = {}
        for datafield in eep_profile.datafields:
            value = self.extract_bits(
                data, 
                datafield['bitoffs'], 
                datafield['bitsize']
            )
            if datafield.get('invert'):
                value = 1 - value
            result[datafield['shortcut']] = value
        return result
```

## Phase 3: Device Management (Priority: HIGH)

### File: `addon/rootfs/app/core/device_manager.py`

SQLite database for device storage:

```python
class DeviceManager:
    def __init__(self, db_path: str = '/data/devices.db'):
        self.db_path = db_path
        self.init_database()
        
    async def init_database(self):
        """Create database schema"""
        # CREATE TABLE devices
        # CREATE TABLE device_entities
        # CREATE TABLE telegrams
        
    async def add_device(self, device_id: str, name: str, eep: str, **kwargs):
        """Add new device"""
        pass
        
    async def get_device(self, device_id: str) -> dict:
        """Get device by ID"""
        pass
        
    async def list_devices(self) -> list:
        """List all devices"""
        pass
        
    async def update_last_seen(self, device_id: str, rssi: int):
        """Update device last seen timestamp"""
        pass
```

## Phase 4: MQTT Integration (Priority: HIGH)

### File: `addon/rootfs/app/core/mqtt_handler.py`

MQTT communication and HA discovery:

```python
class MQTTHandler:
    def __init__(self, host: str, port: int, user: str, password: str):
        self.client = mqtt.Client()
        self.client.username_pw_set(user, password)
        self.client.connect(host, port)
        
    async def publish_discovery(self, device: dict, entity: dict):
        """Publish HA MQTT discovery"""
        topic = f"homeassistant/{entity['component']}/{device['id']}_{entity['shortcut']}/config"
        payload = {
            "name": f"{device['name']} {entity['name']}",
            "unique_id": f"enocean_{device['id']}_{entity['shortcut']}",
            "state_topic": f"enocean/{device['id']}/state",
            "value_template": f"{{{{ value_json.{entity['shortcut']} }}}}",
            "device_class": entity.get('device_class'),
            "icon": entity.get('icon'),
            "device": {
                "identifiers": [f"enocean_{device['id']}"],
                "name": device['name'],
                "manufacturer": device.get('manufacturer', 'EnOcean'),
                "model": device['eep']
            }
        }
        self.client.publish(topic, json.dumps(payload), retain=True)
        
    async def publish_state(self, device_id: str, data: dict):
        """Publish device state"""
        topic = f"enocean/{device_id}/state"
        self.client.publish(topic, json.dumps(data))
```

## Phase 5: Web UI (Priority: MEDIUM)

### File: `addon/rootfs/app/web_ui/app.py`

FastAPI web application:

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def dashboard(request: Request):
    """Main dashboard"""
    devices = await device_manager.list_devices()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "devices": devices
    })

@app.get("/add")
async def add_device_page(request: Request):
    """Add device page"""
    eep_profiles = eep_loader.list_profiles()
    return templates.TemplateResponse("add_device.html", {
        "request": request,
        "profiles": eep_profiles
    })

@app.post("/api/devices")
async def create_device(device_data: dict):
    """API: Create new device"""
    await device_manager.add_device(**device_data)
    await mqtt_handler.publish_discovery(device_data)
    return {"status": "success"}

@app.post("/api/teachin/start")
async def start_teachin():
    """API: Start teach-in mode"""
    global teachin_mode
    teachin_mode = True
    return {"status": "started"}
```

### File: `addon/rootfs/app/web_ui/templates/dashboard.html`

Bootstrap-based UI:

```html
<!DOCTYPE html>
<html>
<head>
    <title>EnOcean Devices</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-primary">
        <div class="container-fluid">
            <span class="navbar-brand">EnOcean MQTT Slim</span>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>Devices</h2>
            <a href="/add" class="btn btn-success">Add Device</a>
        </div>
        
        <div class="row">
            {% for device in devices %}
            <div class="col-md-4 mb-3">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">{{ device.name }}</h5>
                        <p class="card-text">
                            <small class="text-muted">{{ device.eep }}</small><br>
                            ID: {{ device.id }}<br>
                            Status: <span class="badge bg-success">Online</span><br>
                            RSSI: {{ device.rssi }} dBm
                        </p>
                        <a href="/device/{{ device.id }}" class="btn btn-sm btn-primary">Details</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
```

## Phase 6: Main Application (Priority: HIGH)

### File: `addon/rootfs/app/main.py`

Application entry point:

```python
import asyncio
import os
import logging
from core.serial_handler import SerialHandler
from core.device_manager import DeviceManager
from core.mqtt_handler import MQTTHandler
from eep.loader import EEPLoader
from eep.parser import EEPParser
from web_ui.app import app
import uvicorn

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
serial_handler = None
device_manager = None
mqtt_handler = None
eep_loader = None
eep_parser = None
teachin_mode = False

async def process_telegram(packet):
    """Process received EnOcean telegram"""
    global teachin_mode
    
    # Extract sender ID
    sender_id = packet.get_sender_id()
    
    # Check if device exists
    device = await device_manager.get_device(sender_id)
    
    if not device and not teachin_mode:
        logger.debug(f"Unknown device {sender_id}, ignoring")
        return
        
    if teachin_mode and not device:
        # Auto-detect EEP from teach-in telegram
        eep = detect_eep_from_telegram(packet)
        logger.info(f"Teach-in: Device {sender_id} detected with EEP {eep}")
        # Notify web UI
        return
        
    # Parse telegram using EEP profile
    eep_profile = eep_loader.get_profile(device['eep'])
    data = eep_parser.parse_telegram(packet.data, eep_profile)
    
    # Add metadata
    data['_RSSI_'] = packet.rssi
    data['_DATE_'] = datetime.now().isoformat()
    
    # Publish to MQTT
    await mqtt_handler.publish_state(sender_id, data)
    
    # Update last seen
    await device_manager.update_last_seen(sender_id, packet.rssi)

async def serial_reader():
    """Read telegrams from serial port"""
    while True:
        try:
            packet = await serial_handler.read_packet()
            await process_telegram(packet)
        except Exception as e:
            logger.error(f"Error reading packet: {e}")
            await asyncio.sleep(1)

async def main():
    """Main application"""
    global serial_handler, device_manager, mqtt_handler, eep_loader, eep_parser
    
    logger.info("Starting EnOcean MQTT Slim...")
    
    # Initialize components
    serial_port = os.getenv('SERIAL_PORT')
    mqtt_host = os.getenv('MQTT_HOST')
    mqtt_port = int(os.getenv('MQTT_PORT', 1883))
    mqtt_user = os.getenv('MQTT_USER')
    mqtt_password = os.getenv('MQTT_PASSWORD')
    
    # Load EEP profiles
    eep_loader = EEPLoader('/app/eep/definitions')
    eep_parser = EEPParser()
    logger.info(f"Loaded {len(eep_loader.profiles)} EEP profiles")
    
    # Initialize device manager
    device_manager = DeviceManager()
    await device_manager.init_database()
    
    # Initialize MQTT
    mqtt_handler = MQTTHandler(mqtt_host, mqtt_port, mqtt_user, mqtt_password)
    logger.info(f"Connected to MQTT broker at {mqtt_host}:{mqtt_port}")
    
    # Initialize serial port
    if serial_port:
        serial_handler = SerialHandler(serial_port)
        base_id = await serial_handler.get_base_id()
        logger.info(f"Gateway Base ID: {base_id}")
        
        # Start serial reader task
        asyncio.create_task(serial_reader())
    else:
        logger.warning("No serial port configured")
    
    # Start web UI
    config = uvicorn.Config(app, host="0.0.0.0", port=8099, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
```

## Implementation Priority

1. **ESP3 Protocol** - Core communication
2. **EEP System** - Profile loading and parsing
3. **Device Manager** - Database and storage
4. **MQTT Handler** - HA integration
5. **Main Application** - Tie everything together
6. **Web UI** - User interface

## Testing Plan

1. **Unit Tests**
   - ESP3 packet parsing
   - CRC8 calculation
   - Bit extraction
   - EEP profile loading

2. **Integration Tests**
   - Serial communication
   - MQTT publishing
   - Database operations

3. **End-to-End Tests**
   - Kessel Staufix Control device
   - Teach-in flow
   - HA entity creation

## Next Actions

1. Implement `esp3_protocol.py`
2. Implement `serial_handler.py`
3. Implement `eep/loader.py` and `eep/parser.py`
4. Test with Kessel Staufix Control
5. Implement web UI
6. Create GitHub repository
7. Publish to GitHub Container Registry

## Notes

- All configuration via UI (no YAML files)
- SQLite for persistence
- FastAPI for modern web framework
- Bootstrap for responsive UI
- MIT license for maximum compatibility
