# Usage Guide

This guide explains how to operate the Rancilio Silvia with the Silvia Pico control system on a daily basis.

## 1. Powering On the System

1. Plug in the Pico W (5 V power supply).
2. The system boots automatically.
3. Wait for the Bluetooth LED (if connected) or check the serial console — the system will print:
   - "Silvia Pico started"
   - Loaded settings from `config.py` and `secrets.py`
   - Bluetooth advertising status

The machine is now ready. The iOS companion app can connect via Bluetooth.

## 2. Connecting with the iOS App

- Open the **silvia_pico_ui** app on your iPhone.
- The app will automatically scan for "Silvia-Pico" (or the name you set in `secrets.py`).
- Tap to connect (pairing code is the one defined in `secrets.py`).
- Once connected, you can:
  - Set brew temperature
  - Set steam temperature
  - Adjust pre-infusion time, pre-heat time, and soft pressure release time
  - Start/stop brew, water, or steam mode
  - Run backflush program

## 3. Starting a Normal Espresso Brew

1. Make sure the group head is locked with a portafilter and coffee puck.
2. In the iOS app, set desired **Brew Temperature**.
3. Tap **Brew** button in the app (or use the physical brew switch if wired).
4. The system will automatically:
   - Run pre-heat (if configured)
   - Perform pre-infusion (low pressure pre-wetting)
   - Start full-pressure brewing
   - When you stop the brew, it will perform soft pressure release (prevents mess)

The current mode and temperature are shown live in the app.

## 4. Steam Mode (for milk frothing)

1. In the app, set **Steam Temperature** (usually ~120 °C).
2. Tap **Steam** mode.
3. The system switches the target temperature to steam mode.
4. Open the steam wand — the system will maintain the higher temperature.
5. When finished, tap **Brew** mode again to return to normal temperature.

## 5. Hot Water Mode

Tap **Water** in the app to dispense hot water from the steam wand (useful for Americanos).

## 6. Running the Automated Backflush / Cleaning Cycle

1. Install the blind filter basket (no coffee).
2. Fill the group head with cleaning detergent (Cafiza or similar) if desired.
3. In the iOS app, go to the Backflush section and tap **Start Backflush**.
4. The system will run the programmed number of cycles (defined in `config.py`):
   - Pump on for X seconds
   - Pump off for X seconds
   - Repeated for the set number of cycles
5. When finished, rinse thoroughly with clean water.

## 7. Monitoring & Status

The iOS app shows live:
- Current boiler temperature
- Target temperature
- Active mode (Brew / Steam / Pre-infusion / Backflush etc.)
- Relay states (heater, pump, solenoid)

You can also monitor via serial console in Thonny for detailed debug output.

## 8. Shutting Down

Simply unplug the Pico or turn off the power supply. All user settings are saved automatically to `settings.txt` and will be restored on next boot.

---

**Next recommended reading:**
- [Configuration](configuration.md) — how to change defaults
- [Troubleshooting](troubleshooting.md) — if something doesn’t work

---
