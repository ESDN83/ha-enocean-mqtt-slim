# Migration Guide from Old enoceanmqtt

## Issue: Duplicate Devices in Home Assistant

If you see duplicate devices or devices not updating, it's because the **old enoceanmqtt addon is still running** alongside the new EnOcean MQTT Slim addon.

### Symptoms

- Two devices with same name in Home Assistant
- One device shows values, the other is empty
- Values not updating properly
- MQTT browser shows two different topics:
  - `enocean/05834fa4/state` (NEW - EnOcean MQTT Slim)
  - `enoceanmqtt/staufix_control` (OLD - enoceanmqtt)

### Solution

#### Step 1: Stop Old enoceanmqtt Addon

1. Go to **Settings → Add-ons**
2. Find the **old enoceanmqtt addon** (NOT EnOcean MQTT Slim)
3. Click on it
4. Click **Stop**
5. **Disable "Start on boot"**
6. Optionally: **Uninstall** it completely

#### Step 2: Clean Up Old MQTT Discovery Messages

The old addon left discovery messages in MQTT. You need to remove them:

**Option A: Using MQTT Explorer (Recommended)**

1. Install MQTT Explorer on your computer
2. Connect to your MQTT broker
3. Navigate to `homeassistant/`
4. Delete all topics starting with `enoceanmqtt/`
5. Look for old device discovery topics and delete them

**Option B: Using Home Assistant MQTT Integration**

1. Go to **Settings → Devices & Services**
2. Click on **MQTT**
3. Click **Configure**
4. Go to **"Listen to a topic"**
5. Enter topic: `homeassistant/#`
6. Find old enoceanmqtt discovery messages
7. Publish empty message to each old topic to remove it

**Option C: Using Mosquitto CLI (Advanced)**

```bash
# Connect to your MQTT broker
mosquitto_pub -h YOUR_MQTT_HOST -u YOUR_USER -P YOUR_PASSWORD \
  -t "homeassistant/binary_sensor/enoceanmqtt_staufix_control_alarm/config" \
  -n -r

# Repeat for each old discovery topic
```

#### Step 3: Remove Old Devices from Home Assistant

1. Go to **Settings → Devices & Services → MQTT**
2. Find devices with "enoceanmqtt" in the name
3. Click on each device
4. Click **Delete**

#### Step 4: Restart Home Assistant

1. Go to **Settings → System**
2. Click **Restart**
3. Wait for restart to complete

#### Step 5: Verify New Addon is Working

1. Open **EnOcean MQTT Slim** Web UI
2. Check that your device is listed
3. Check MQTT browser - should only see:
   - `enocean/05834fa4/state` (state messages)
   - `homeassistant/binary_sensor/enocean_05834fa4_AL/config` (discovery)
   - `homeassistant/sensor/enocean_05834fa4_rssi/config` (RSSI sensor)
   - `homeassistant/sensor/enocean_05834fa4_last_seen/config` (timestamp sensor)

### Topic Comparison

| Old enoceanmqtt | New EnOcean MQTT Slim |
|-----------------|----------------------|
| `enoceanmqtt/staufix_control` | `enocean/05834fa4/state` |
| Custom device names in topic | Device ID in topic |
| `_RSSI_`, `_DATE_`, `_RAW_DATA_` | `rssi`, `last_seen` |
| No MQTT discovery | Full MQTT discovery |

### Expected Result

After cleanup, you should have:
- **ONE device** in Home Assistant: "Staufix Control"
- **THREE entities:**
  - `binary_sensor.staufix_control_alarm` (alarm status)
  - `sensor.staufix_control_rssi` (signal strength)
  - `sensor.staufix_control_last_seen` (last update time)
- All entities updating correctly
- Only `enocean/` topics in MQTT (no `enoceanmqtt/` topics)

### Troubleshooting

**Q: I still see duplicate devices**
- Make sure old addon is completely stopped
- Check MQTT broker for old discovery messages
- Delete old devices manually from HA

**Q: Values still not updating**
- Check EnOcean MQTT Slim logs for telegrams
- Verify device is enabled in Web UI
- Check MQTT connection status

**Q: Can I run both addons?**
- No! They will conflict
- Use only EnOcean MQTT Slim
- Old addon should be stopped/uninstalled

### Need Help?

1. Check addon logs: Settings → Add-ons → EnOcean MQTT Slim → Logs
2. Check MQTT messages in MQTT Explorer
3. Report issues on GitHub: https://github.com/ESDN83/ha-enocean-mqtt-slim/issues
