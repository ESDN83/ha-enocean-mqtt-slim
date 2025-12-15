# EnOcean Bidirectional Control - Implementation Plan

## 📋 Overview

Add support for **sending commands** to EnOcean actuators (switches, dimmers, plugs, etc.) from Home Assistant via MQTT.

---

## 🔍 Research Summary

### EnOcean Communication Patterns

1. **Unidirectional (Current):** Sensors → Gateway → HA (receive only)
2. **Bidirectional (Target):** HA → Gateway → Actuators (send commands)

### Key EnOcean Concepts

#### 1. **Teach-In Methods**
- **UTE (Universal Teach-In):** Modern, bidirectional, requires response
- **4BS Teach-In:** Traditional, includes EEP in telegram
- **RPS:** Simple, no teach-in data

#### 2. **Command Telegrams**
- **RORG Types:**
  - `0xA5` (4BS) - 4-byte data (temperature, humidity, etc.)
  - `0xD2` (VLD) - Variable length (actuators, dimmers)
  - `0xF6` (RPS) - Rocker switches (1 byte)
  
#### 3. **Actuator EEP Profiles**
Common controllable devices:
- **A5-38-08** - Central Command (dimming, switching)
- **D2-01-xx** - Electronic switches and dimmers
- **D2-05-xx** - Blinds/shutters control
- **A5-20-01** - HVAC actuators

---

## 🎯 Implementation Plan

### Phase 1: MQTT Command Subscription ✅

**Goal:** Listen for commands from Home Assistant

**Components:**
1. **MQTT Command Topics:**
   ```
   enocean/{device_id}/set/{entity}
   Example: enocean/05834fa4/set/switch
   ```

2. **Command Payloads:**
   ```json
   {"state": "ON"}
   {"state": "OFF"}
   {"brightness": 255}
   {"position": 50}
   ```

3. **Implementation:**
   - Add MQTT subscription in `mqtt_handler.py`
   - Parse command payloads
   - Route to command handler

---

### Phase 2: Command Translation ✅

**Goal:** Translate MQTT commands to EnOcean telegrams

**Components:**
1. **Command Translator** (`core/command_translator.py`):
   - Map HA commands to EEP-specific telegrams
   - Handle different RORG types
   - Support common actuator profiles

2. **EEP Command Definitions:**
   - Extend EEP JSON files with `commands` section
   - Define command structure per profile
   
   **Example:**
   ```json
   {
     "eep": "A5-38-08",
     "commands": {
       "switch": {
         "on": {"db3": 0x02, "db2": 0x00, "db1": 0x64, "db0": 0x09},
         "off": {"db3": 0x02, "db2": 0x00, "db1": 0x00, "db0": 0x08}
       },
       "dim": {
         "range": [0, 100],
         "formula": "db1 = value * 255 / 100"
       }
     }
   }
   ```

---

### Phase 3: Telegram Sending ✅

**Goal:** Send EnOcean telegrams via serial port

**Components:**
1. **Extend `serial_handler.py`:**
   - Add `send_telegram()` method
   - Build ESP3 packets for commands
   - Handle CRC calculation
   - Queue management for multiple commands

2. **ESP3 Packet Builder:**
   - Create command packets with correct structure
   - Set sender ID (gateway base ID)
   - Set destination ID (actuator ID)
   - Calculate checksums

---

### Phase 4: MQTT Discovery for Controllable Entities ✅

**Goal:** Expose switches/lights/covers in Home Assistant

**Components:**
1. **Update `mqtt_handler.py`:**
   - Add `command_topic` to discovery payloads
   - Set correct `device_class` for actuators
   - Add `optimistic: false` for state feedback

2. **Discovery Payload Example:**
   ```json
   {
     "name": "Smart Plug",
     "unique_id": "enocean_05834fa4_switch",
     "state_topic": "enocean/05834fa4/state",
     "command_topic": "enocean/05834fa4/set/switch",
     "payload_on": "{\"state\": \"ON\"}",
     "payload_off": "{\"state\": \"OFF\"}",
     "state_on": "ON",
     "state_off": "OFF",
     "optimistic": false,
     "device_class": "outlet"
   }
   ```

---

### Phase 5: State Feedback ✅

**Goal:** Update HA when device state changes

**Components:**
1. **Listen for Response Telegrams:**
   - Actuators send confirmation telegrams
   - Parse response and update MQTT state
   - Handle timeout (no response)

2. **Optimistic Updates:**
   - Immediately publish expected state
   - Update with actual state when received
   - Revert if command fails

---

## 📁 File Structure

```
addon/rootfs/app/
├── core/
│   ├── command_translator.py      # NEW: Translate MQTT → EnOcean
│   ├── command_handler.py         # NEW: Handle incoming commands
│   ├── serial_handler.py          # MODIFY: Add send_telegram()
│   ├── mqtt_handler.py            # MODIFY: Add command subscription
│   └── esp3_protocol.py           # MODIFY: Add command packet builder
├── eep/
│   ├── definitions/
│   │   ├── A5-38/
│   │   │   └── A5-38-08.json     # MODIFY: Add commands section
│   │   ├── D2-01/
│   │   │   └── D2-01-xx.json     # MODIFY: Add commands section
│   └── command_profiles.py        # NEW: Command profile loader
└── main.py                         # MODIFY: Initialize command handling
```

---

## 🔧 Implementation Steps

### Step 1: Extend ESP3 Protocol for Sending
```python
# esp3_protocol.py
class ESP3Packet:
    @staticmethod
    def create_command_packet(destination_id: str, rorg: int, data: bytes) -> bytes:
        """Create ESP3 packet for sending command"""
        # Build packet structure
        # Calculate CRC
        # Return complete packet
```

### Step 2: Add Command Sending to Serial Handler
```python
# serial_handler.py
async def send_telegram(self, destination_id: str, rorg: int, data: bytes):
    """Send EnOcean telegram to device"""
    packet = ESP3Packet.create_command_packet(destination_id, rorg, data)
    await self.write_packet(packet)
```

### Step 3: Create Command Translator
```python
# command_translator.py
class CommandTranslator:
    def translate_command(self, device: dict, entity: str, command: dict) -> tuple:
        """Translate MQTT command to EnOcean telegram"""
        profile = self.eep_loader.get_profile(device['eep'])
        # Get command definition from profile
        # Build data bytes
        return (rorg, data_bytes)
```

### Step 4: Add MQTT Command Subscription
```python
# mqtt_handler.py
def subscribe_commands(self, callback):
    """Subscribe to command topics"""
    self.client.subscribe("enocean/+/set/#")
    self.client.message_callback_add("enocean/+/set/#", callback)
```

### Step 5: Integrate in Main Service
```python
# main.py
async def handle_command(self, device_id: str, entity: str, command: dict):
    """Handle command from MQTT"""
    device = self.device_manager.get_device(device_id)
    rorg, data = self.command_translator.translate_command(device, entity, command)
    await self.serial_handler.send_telegram(device_id, rorg, data)
    # Publish optimistic state
    self.mqtt_handler.publish_state(device_id, {entity: command['state']})
```

---

## 🎯 Supported Devices (Initial)

### Priority 1: Common Actuators
1. **Switches/Plugs** (A5-38-08, D2-01-xx)
   - ON/OFF control
   - State feedback

2. **Dimmers** (A5-38-08, D2-01-xx)
   - Brightness control (0-100%)
   - Smooth dimming

3. **Blinds/Shutters** (D2-05-xx)
   - Position control (0-100%)
   - Tilt control

### Priority 2: Advanced
4. **HVAC** (A5-20-01)
   - Temperature setpoint
   - Mode control

5. **RGB Lights** (D2-01-xx)
   - Color control
   - Brightness

---

## 🧪 Testing Plan

### Test Cases:
1. ✅ Send ON command → Device turns on
2. ✅ Send OFF command → Device turns off
3. ✅ Send DIM 50% → Device dims to 50%
4. ✅ Receive state feedback → HA updates
5. ✅ Command timeout → Revert optimistic state
6. ✅ Multiple commands → Queue properly
7. ✅ Invalid device → Error handling

---

## 📚 References

### EnOcean Specifications:
- **ESP3 Specification:** Already in repo (`ESP3_spec.pdf`)
- **EEP Specification 2.6.8:** [EnOcean Alliance](https://www.enocean-alliance.org/eep/)
- **A5-38-08 Profile:** Central Command (Gateway)
- **D2-01-xx Profile:** Electronic Switches and Dimmers

### Similar Implementations:
- **enoceanmqtt:** Has bidirectional support (reference)
- **Home Assistant EnOcean:** Core integration (reference)
- **Python enocean library:** Has command sending

---

## ⚠️ Important Considerations

### 1. **Gateway Base ID**
- Commands must be sent FROM gateway's base ID
- Already queried during initialization ✅

### 2. **Teach-In for Actuators**
- Actuators must be taught-in to gateway
- May require UTE teach-in response
- Already implemented for sensors ✅

### 3. **Security**
- EnOcean uses rolling code for security
- Some devices require encryption
- Phase 2 feature

### 4. **Timing**
- Commands may need delays between sends
- Queue management important
- Implement retry logic

---

## 🚀 Rollout Plan

### v1.0.32 (Next Release):
- ✅ Bug fixes (already done)
- ✅ Basic switch control (A5-38-08)
- ✅ MQTT command subscription
- ✅ Command translation
- ✅ State feedback

### v1.0.33:
- ✅ Dimmer support
- ✅ Cover/blind control
- ✅ Advanced command profiles

### v1.0.34:
- ✅ HVAC control
- ✅ RGB lighting
- ✅ Security/encryption

---

## 💡 Quick Win: Virtual Rocker Switch

**Easiest implementation:** Create virtual rocker switch that sends F6-02-01 telegrams

**Use Case:** HA button → Virtual rocker → Control actuator

**Implementation:**
```python
# Send F6-02-01 telegram (rocker press)
data = bytes([0xF6, 0x30])  # Button A0 pressed
await serial_handler.send_telegram(actuator_id, 0xF6, data)
await asyncio.sleep(0.1)
data = bytes([0xF6, 0x00])  # Button released
await serial_handler.send_telegram(actuator_id, 0xF6, data)
```

---

## ✅ Next Steps

1. **Review this plan** - Confirm approach
2. **Start with Phase 1** - MQTT command subscription
3. **Implement Quick Win** - Virtual rocker switch
4. **Test with real device** - Verify commands work
5. **Expand to more profiles** - Add dimming, covers, etc.

---

**Ready to implement?** Let me know which phase to start with, or if you want to begin with the "Quick Win" virtual rocker switch feature!
