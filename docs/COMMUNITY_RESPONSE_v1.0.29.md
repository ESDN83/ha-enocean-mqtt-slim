# Response to Community Feedback - v1.0.29

## Thank You for Your Feedback! 🙏

Thank you for testing the addon and providing valuable feedback! I've addressed both issues you mentioned in version **1.0.29**.

---

## ✅ Issue 1: Missing F6-02-01 Profile - FIXED!

You were absolutely right! The F6-02-01 profile was missing, which is one of the most common wall button profiles (like Eltako FT55).

### What I Added:

**New F6-02-01 Profile** - "Rocker Switch, 2 Rocker"
- ✅ Supports 4 buttons: AI (Rocker A Up), AO (Rocker A Down), BI (Rocker B Up), BO (Rocker B Down)
- ✅ Perfect for light and blind control
- ✅ Works with Eltako FT55 and similar 2-rocker switches
- ✅ All 4 buttons are now properly detected and mapped

The profile is now available in the EEP selection dropdown when adding devices!

---

## ✅ Issue 2: Device ID Format Confusion - FIXED!

You mentioned having `0xFEE50F9C` but the system expected `FEE50F9C`. This was confusing!

### What I Improved:

**Smart Device ID Input**
- ✅ **Automatically removes `0x` prefix** - Just paste your device ID as-is!
- ✅ **Real-time validation** - Shows you if the format is correct
- ✅ **Helpful feedback messages**:
  - ✅ "Removed '0x' prefix automatically" (green)
  - ⚠️ "Device ID must be 8 characters (currently X)" (yellow)
  - ✅ "✓ Valid device ID format" (green)
  - ❌ "Device ID must contain only hex characters" (red)
- ✅ **Accepts both formats**: `FEE50F9C` or `0xFEE50F9C`

### How It Works Now:

1. **Go to Web UI** → Click "Add Device"
2. **Paste your device ID** - Either format works:
   - `0xFEE50F9C` → Automatically cleaned to `FEE50F9C`
   - `FEE50F9C` → Works as-is
3. **Select F6-02-01** from the EEP dropdown
4. **Save** - All 4 buttons will be detected!

---

## 📋 Step-by-Step Guide for Your Device

Based on your feedback, here's exactly how to set up your device:

### 1. Update to v1.0.29
```
Settings → Add-ons → EnOcean MQTT Slim → Update
```

### 2. Add Your Device
1. Open the addon Web UI (via Home Assistant ingress)
2. Click **"Add Device"**
3. **Device ID**: Paste `0xFEE50F9C` (or `FEE50F9C`)
   - The system will automatically clean it to `FEE50F9C`
   - You'll see: ✅ "Removed '0x' prefix automatically"
4. **Device Name**: Enter a friendly name (e.g., "Wall Switch Living Room")
5. **EEP Profile**: Select **F6-02-01 - Rocker Switch, 2 Rocker**
6. **Manufacturer**: Enter "Eltako" (or your manufacturer)
7. Click **"Save Device"**

### 3. Test Your Buttons
Press each button on your switch:
- **Rocker A Up** (AI) → Should trigger
- **Rocker A Down** (AO) → Should trigger
- **Rocker B Up** (BI) → Should trigger
- **Rocker B Down** (BO) → Should trigger

All 4 buttons will appear as binary sensors in Home Assistant!

---

## 🎯 What You'll See in Home Assistant

After adding the device, you'll get these entities:

1. **binary_sensor.wall_switch_living_room_rocker_a_up** (AI)
2. **binary_sensor.wall_switch_living_room_rocker_a_down** (AO)
3. **binary_sensor.wall_switch_living_room_rocker_b_up** (BI)
4. **binary_sensor.wall_switch_living_room_rocker_b_down** (BO)
5. **sensor.wall_switch_living_room_rssi** (Signal strength)
6. **sensor.wall_switch_living_room_last_seen** (Timestamp)

---

## 🔍 About EEP Profiles

The addon now includes **153 EEP profiles** (was 152, added F6-02-01):

- **F6-02-01**: 2-rocker switch (4 buttons) - **NEW!**
- **F6-02-02**: 2-rocker switch (alternative mapping)
- **F6-02-03**: 2-rocker switch with energy bow
- And 150 more profiles for various sensors and actuators

You can browse all profiles in the Web UI by clicking the **"EEP Profiles"** card.

---

## 📚 Configuration Location

You asked about configuration location:

**Device Configuration**: `/addon_configs/enocean-mqtt-slim/devices.json`
- This is where your devices are stored
- Managed through the Web UI (no manual editing needed)
- Automatically backed up

**EEP Definitions**: Built into the addon at `/app/eep/definitions/`
- 153 profiles included
- No configuration needed

---

## 🐛 Troubleshooting

If you still have issues:

### Check the Logs
```
Settings → Add-ons → EnOcean MQTT Slim → Log
```

Look for:
- ✅ "Published discovery for device..." - Device added successfully
- ⚠️ "UNKNOWN DEVICE" - Device not configured yet
- 🎓 "TEACH-IN TELEGRAM DETECTED" - Device in learn mode

### Common Issues

**Issue**: Device ID not working
- **Solution**: Use the Web UI - it now handles format automatically!

**Issue**: Buttons not detected
- **Solution**: Make sure you selected **F6-02-01** (not F6-02-02 or F6-02-03)

**Issue**: Only 2 buttons work
- **Solution**: Wrong EEP profile - change to F6-02-01

---

## 🎉 Summary

**Version 1.0.29 fixes both your issues:**

1. ✅ **F6-02-01 profile added** - Your 4-button switch now fully supported
2. ✅ **Device ID input improved** - Accepts `0x` prefix automatically
3. ✅ **Better user experience** - Real-time validation and helpful messages

**Update now and your device should work perfectly!**

---

## 📞 Need More Help?

If you still have issues after updating to v1.0.29:

1. **Check the addon logs** - They show exactly what's happening
2. **Reply in the community thread** - I'm monitoring it
3. **Open a GitHub issue** - https://github.com/ESDN83/ha-enocean-mqtt-slim/issues

---

## 🙏 Thank You!

Your feedback helped improve the addon for everyone. The F6-02-01 profile is one of the most common, and the device ID confusion was a real usability issue.

**Please update to v1.0.29 and let me know if it works for you!**

---

**Release**: v1.0.29  
**GitHub**: https://github.com/ESDN83/ha-enocean-mqtt-slim  
**Release Notes**: https://github.com/ESDN83/ha-enocean-mqtt-slim/releases/tag/v1.0.29
