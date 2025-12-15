# F6-02-01 Rocker Switch - Automation Guide

## 🎉 Great! Your FT55 is Working!

You've successfully added your FT55 rocker switch and the addon is receiving telegrams. Now let's set up automations.

---

## 📱 Understanding F6-02-01 Buttons

The F6-02-01 profile creates **binary sensors** (not button entities) for each rocker position:

### Your FT55 Entities in Home Assistant:

After adding your FT55, you should see these entities:

1. **binary_sensor.ft55_rocker_a_up** (AI)
2. **binary_sensor.ft55_rocker_a_down** (AO)
3. **binary_sensor.ft55_rocker_b_up** (BI)
4. **binary_sensor.ft55_rocker_b_down** (BO)
5. **sensor.ft55_rssi** (Signal strength)
6. **sensor.ft55_last_seen** (Timestamp)

> **Note:** The exact entity names depend on what you named your device in the addon.

---

## 🔍 Finding Your Entities

### Method 1: Developer Tools
1. Go to **Settings** → **Devices & Services**
2. Click **MQTT** integration
3. Find your **FT55** device
4. Click on it to see all entities

### Method 2: States Page
1. Go to **Developer Tools** → **States**
2. Search for your device name (e.g., "ft55")
3. You'll see all binary_sensor and sensor entities

---

## 🤖 Creating Automations

### Example 1: Toggle Light with Rocker A

**Rocker A Up = Turn Light ON**
**Rocker A Down = Turn Light OFF**

```yaml
# Automation 1: Rocker A Up - Turn Light ON
alias: "FT55 - Rocker A Up - Light ON"
description: "Turn on living room light when pressing rocker A up"
trigger:
  - platform: state
    entity_id: binary_sensor.ft55_rocker_a_up
    to: "on"
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
mode: single

---

# Automation 2: Rocker A Down - Turn Light OFF
alias: "FT55 - Rocker A Down - Light OFF"
description: "Turn off living room light when pressing rocker A down"
trigger:
  - platform: state
    entity_id: binary_sensor.ft55_rocker_a_down
    to: "on"
action:
  - service: light.turn_off
    target:
      entity_id: light.living_room
mode: single
```

### Example 2: Toggle Light (Single Automation)

```yaml
alias: "FT55 - Rocker A - Toggle Light"
description: "Toggle light with rocker A (up or down)"
trigger:
  - platform: state
    entity_id: binary_sensor.ft55_rocker_a_up
    to: "on"
  - platform: state
    entity_id: binary_sensor.ft55_rocker_a_down
    to: "on"
action:
  - service: light.toggle
    target:
      entity_id: light.living_room
mode: single
```

### Example 3: Dim Light with Long Press

```yaml
alias: "FT55 - Rocker A Up - Dim Up"
description: "Increase brightness while holding rocker A up"
trigger:
  - platform: state
    entity_id: binary_sensor.ft55_rocker_a_up
    to: "on"
action:
  - repeat:
      while:
        - condition: state
          entity_id: binary_sensor.ft55_rocker_a_up
          state: "on"
      sequence:
        - service: light.turn_on
          target:
            entity_id: light.living_room
          data:
            brightness_step_pct: 10
        - delay:
            milliseconds: 300
mode: restart
```

### Example 4: Control Blinds with Rocker B

```yaml
# Rocker B Up = Open Blinds
alias: "FT55 - Rocker B Up - Open Blinds"
description: "Open blinds when pressing rocker B up"
trigger:
  - platform: state
    entity_id: binary_sensor.ft55_rocker_b_up
    to: "on"
action:
  - service: cover.open_cover
    target:
      entity_id: cover.living_room_blinds
mode: single

---

# Rocker B Down = Close Blinds
alias: "FT55 - Rocker B Down - Close Blinds"
description: "Close blinds when pressing rocker B down"
trigger:
  - platform: state
    entity_id: binary_sensor.ft55_rocker_b_down
    to: "on"
action:
  - service: cover.close_cover
    target:
      entity_id: cover.living_room_blinds
mode: single
```

### Example 5: Scene Control

```yaml
alias: "FT55 - Rocker Scenes"
description: "Control different scenes with each rocker"
trigger:
  - platform: state
    entity_id: binary_sensor.ft55_rocker_a_up
    to: "on"
    id: "scene_bright"
  - platform: state
    entity_id: binary_sensor.ft55_rocker_a_down
    to: "on"
    id: "scene_dim"
  - platform: state
    entity_id: binary_sensor.ft55_rocker_b_up
    to: "on"
    id: "scene_movie"
  - platform: state
    entity_id: binary_sensor.ft55_rocker_b_down
    to: "on"
    id: "scene_off"
action:
  - choose:
      - conditions:
          - condition: trigger
            id: "scene_bright"
        sequence:
          - service: scene.turn_on
            target:
              entity_id: scene.living_room_bright
      - conditions:
          - condition: trigger
            id: "scene_dim"
        sequence:
          - service: scene.turn_on
            target:
              entity_id: scene.living_room_dim
      - conditions:
          - condition: trigger
            id: "scene_movie"
        sequence:
          - service: scene.turn_on
            target:
              entity_id: scene.living_room_movie
      - conditions:
          - condition: trigger
            id: "scene_off"
        sequence:
          - service: scene.turn_on
            target:
              entity_id: scene.living_room_off
mode: single
```

---

## 🎨 Creating Automations via UI

### Step-by-Step:

1. **Go to Settings** → **Automations & Scenes**
2. **Click "+ CREATE AUTOMATION"**
3. **Click "Create new automation"**
4. **Add Trigger:**
   - Trigger type: **State**
   - Entity: Select your **binary_sensor.ft55_rocker_a_up**
   - To: **on**
5. **Add Action:**
   - Action type: **Call service**
   - Service: **light.turn_on** (or whatever you want to control)
   - Target: Select your light/device
6. **Save** with a descriptive name

---

## 🐛 Troubleshooting

### Issue: "No entities showing up"

**Check:**
1. Device is enabled in addon Web UI
2. MQTT integration is working
3. Check addon logs for telegram reception
4. Wait a few seconds after adding device
5. Press a button on the FT55 to trigger discovery

### Issue: "Entities show as unavailable"

**Solutions:**
1. Press any button on the FT55 to send a telegram
2. Check MQTT broker is running
3. Restart Home Assistant
4. Check addon logs for errors

### Issue: "Buttons don't trigger automations"

**Check:**
1. Entity names in automation match actual entity names
2. Trigger is set to state change **to: "on"**
3. Test by manually changing entity state in Developer Tools
4. Check automation is enabled
5. Check automation logs for errors

### Issue: "502 Bad Gateway when opening Web UI"

**Solutions:**
1. Wait 10-20 seconds after addon start
2. Refresh browser page
3. Clear browser cache
4. Check addon is fully started (check logs)
5. Restart addon if needed

---

## 💡 Pro Tips

### Tip 1: Use Descriptive Names
When adding your FT55 in the addon, use descriptive names like:
- "Living Room Wall Switch"
- "Bedroom Light Switch"
- "Kitchen Rocker"

This makes entities easier to find and automations easier to understand.

### Tip 2: Test Each Button
After adding the device, press each button and check the addon logs to verify all 4 buttons are detected.

### Tip 3: Use Helpers for Complex Logic
For advanced scenarios, create **input_boolean** or **input_select** helpers to manage state between button presses.

### Tip 4: Group Related Automations
Use automation folders or naming conventions:
- "FT55 Living Room - Rocker A Up"
- "FT55 Living Room - Rocker A Down"
- etc.

---

## 📚 Understanding Binary Sensors vs Buttons

### Why Binary Sensors?

EnOcean rocker switches send **press** and **release** telegrams:
- **Press** = binary_sensor changes to **"on"**
- **Release** = binary_sensor changes to **"off"**

This allows for:
- ✅ Simple press detection (trigger on "on")
- ✅ Long press detection (check duration in "on" state)
- ✅ Double press detection (two "on" states quickly)
- ✅ Hold and repeat actions (while "on")

### Button Entities
Home Assistant **button** entities are for one-time actions (like pressing a doorbell). EnOcean rockers need **binary sensors** because they have press AND release states.

---

## 🎯 Quick Start Automation

**Copy this to get started quickly:**

```yaml
alias: "FT55 - Quick Test"
description: "Test your FT55 - shows notification when any button pressed"
trigger:
  - platform: state
    entity_id:
      - binary_sensor.ft55_rocker_a_up
      - binary_sensor.ft55_rocker_a_down
      - binary_sensor.ft55_rocker_b_up
      - binary_sensor.ft55_rocker_b_down
    to: "on"
action:
  - service: notify.persistent_notification
    data:
      title: "FT55 Button Pressed"
      message: "Button {{ trigger.to_state.name }} was pressed!"
mode: queued
```

This will show a notification every time you press any button, helping you verify everything works!

---

## 📞 Need More Help?

1. **Check addon logs** - Shows telegram reception
2. **Check MQTT integration** - Verify entities are created
3. **Test in Developer Tools** - Manually trigger automations
4. **Community forum** - Ask for help with specific use cases
5. **GitHub issues** - Report bugs or request features

---

## ✅ Summary

**Your FT55 is working!** The addon receives telegrams correctly. Now:

1. ✅ Find your binary_sensor entities in Home Assistant
2. ✅ Create automations using state triggers (to: "on")
3. ✅ Test each button to verify it works
4. ✅ Build your smart home automations!

**The entities ARE there - they're just binary sensors, not button entities!** 🎉

---

**Version:** 1.0.29  
**Profile:** F6-02-01 - Rocker Switch, 2 Rocker  
**Device:** Eltako FT55 (and similar)
