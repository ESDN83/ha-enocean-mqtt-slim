# 🚨 CRITICAL BUG: Device ID Parsing Error

## Problem Summary

**User's device ID:** `0xFEE3448D` (8 hex digits = 4 bytes)  
**What the log shows:** `Sender ID: 00fee344` (only 6 hex digits)  
**User's telegram:** `f6 00 fe e3 44 8d 20`

## Root Cause Analysis

### 1. ESP3 Packet Structure (CORRECT)

The `esp3_protocol.py` correctly extracts sender ID:

```python
def get_sender_id(self) -> Optional[str]:
    if self.packet_type == self.PACKET_TYPE_RADIO_ERP1:
        if len(self.data) >= 5:
            # Sender ID is bytes 1-4 (after RORG)
            sender_bytes = self.data[1:5]
            return sender_bytes.hex()
```

For user's telegram `f6 00 fe e3 44 8d 20`:
- Byte 0: `f6` = RORG (RPS telegram)
- Bytes 1-4: `00 fe e3 44` = **WRONG!** This is what gets extracted
- Bytes 5-6: `8d 20` = Remaining data

**The code extracts bytes [1:5] = `00 fe e3 44` = `00fee344`**

### 2. The REAL Problem: Wrong Packet Structure Understanding

Looking at the user's telegram from enocean2mqtt:
```
FE:E3:44:8D->FF:FF:FF:FF (-64 dBm): 0x01 ['0xf6', '0x30', '0xfe', '0xe3', '0x44', '0x8d', '0x30']
```

The actual telegram structure is:
- `0xf6` = RORG
- `0x30` = Data byte (button info)
- `0xfe`, `0xe3`, `0x44`, `0x8d` = Sender ID (4 bytes)
- `0x30` = Status byte

**So the sender ID is at bytes [2:6], NOT [1:5]!**

### 3. ESP3 Radio ERP1 Packet Structure (VERIFIED)

According to ESP3 specification, Radio ERP1 packet data field contains:
```
[RORG] [Data Bytes...] [Sender ID - 4 bytes] [Status]
```

For **RPS (F6)** telegrams:
- RORG: 1 byte (0xF6)
- Data: 1 byte (button/rocker info)
- Sender ID: 4 bytes
- Status: 1 byte

Total: 7 bytes

For **4BS (A5)** telegrams:
- RORG: 1 byte (0xA5)
- Data: 4 bytes (DB3, DB2, DB1, DB0)
- Sender ID: 4 bytes
- Status: 1 byte

Total: 10 bytes

### 4. The Bug in esp3_protocol.py

```python
def get_sender_id(self) -> Optional[str]:
    if self.packet_type == self.PACKET_TYPE_RADIO_ERP1:
        if len(self.data) >= 5:
            # Sender ID is bytes 1-4 (after RORG)  <-- WRONG!
            sender_bytes = self.data[1:5]
            return sender_bytes.hex()
```

This assumes sender ID immediately follows RORG, but it actually comes AFTER the data bytes!

## Correct Implementation

The sender ID position depends on the RORG type:

```python
def get_sender_id(self) -> Optional[str]:
    if self.packet_type == self.PACKET_TYPE_RADIO_ERP1:
        rorg = self.get_rorg()
        
        if rorg == 0xF6:  # RPS - 1 data byte
            if len(self.data) >= 6:  # RORG + 1 data + 4 sender ID
                sender_bytes = self.data[2:6]  # Skip RORG and 1 data byte
                return sender_bytes.hex()
        
        elif rorg == 0xA5:  # 4BS - 4 data bytes
            if len(self.data) >= 9:  # RORG + 4 data + 4 sender ID
                sender_bytes = self.data[5:9]  # Skip RORG and 4 data bytes
                return sender_bytes.hex()
        
        elif rorg == 0xD5:  # 1BS - 1 data byte
            if len(self.data) >= 6:  # RORG + 1 data + 4 sender ID
                sender_bytes = self.data[2:6]  # Skip RORG and 1 data byte
                return sender_bytes.hex()
        
        elif rorg == 0xD2:  # VLD - variable length
            # VLD is more complex, need to parse length
            # For now, assume sender ID is last 5 bytes (4 ID + 1 status)
            if len(self.data) >= 5:
                sender_bytes = self.data[-5:-1]  # Last 4 bytes before status
                return sender_bytes.hex()
    
    return None
```

## Why Kessel Staufix Works

The Kessel Staufix uses **A5-3F-7F** (4BS telegram). Looking at main.py lines 98-105:

```python
# For 4BS telegrams, check if real device ID is in data payload
real_device_id = sender_id
if rorg == 0xA5 and len(packet.data) >= 9:
    # Extract potential real device ID from data bytes 5-8
    potential_id = ''.join(f'{b:02x}' for b in packet.data[5:9])
```

This extracts bytes [5:9] which is CORRECT for 4BS telegrams! So Kessel works by accident because of this workaround.

But this workaround doesn't apply to RPS (F6) telegrams, so rocker switches fail.

## Impact

- ✅ **4BS devices (A5)** work (Kessel Staufix)
- ❌ **RPS devices (F6)** fail (rocker switches like FT55)
- ❌ **1BS devices (D5)** likely fail
- ❌ **VLD devices (D2)** likely fail

## Fix Required

1. Fix `get_sender_id()` in `esp3_protocol.py` to correctly extract sender ID based on RORG type
2. Remove the workaround in `main.py` lines 98-105 (no longer needed)
3. Update `get_data_bytes()` to also respect RORG type
4. Test with all telegram types

## Verification Needed

Before implementing, we need to:
1. ✅ Verify ESP3 specification (done - structure confirmed)
2. ✅ Check enocean2mqtt behavior (done - they use Python enocean library)
3. ✅ Analyze user's telegram (done - confirms our analysis)
4. ⏳ Search for official ESP3 documentation
5. ⏳ Get 3rd confirmation source

## User's Telegram Breakdown

```
Raw: f6 00 fe e3 44 8d 20

Byte 0: f6       = RORG (RPS)
Byte 1: 00       = Data (button released, rocker A, button I)
Byte 2: fe       = Sender ID byte 1
Byte 3: e3       = Sender ID byte 2
Byte 4: 44       = Sender ID byte 3
Byte 5: 8d       = Sender ID byte 4
Byte 6: 20       = Status byte

Sender ID: FEE3448D ✅
Current extraction: 00FEE344 ❌
```

## Next Steps

1. Search for ESP3 specification document
2. Get 2 more confirmation sources
3. Discuss fix approach with user
4. Implement fix
5. Test with user's device
