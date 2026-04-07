# Configuration

This document explains how to configure the Silvia Pico firmware.

> **⚠️ Most important first step**  
> The **very first thing** you must do is set the **correct GPIO pins** in `config.py` to match your physical wiring. Incorrect pins can damage components or cause the system to behave unpredictably.

## 1. GPIO Pin Configuration (config.py) – Most Critical Settings

Open `config.py` and update the pin assignments **before** connecting any high-voltage parts.

```python
# ======================
# GPIO PIN CONFIGURATION
# ======================
# Change these to match your actual wiring!

HEATER_PIN = 15          # Solid State Relay for boiler heating element
PUMP_PIN = 14            # Relay for vibration pump
SOLENOID_PIN = 13        # Relay for brew solenoid valve
BACKFLUSH_VALVE_PIN = 12 # (Optional) Extra valve for backflush/cleaning

# Optional pins (uncomment and set if used)
# STATUS_LED_PIN = 25
# TEMPERATURE_SENSOR_PIN = 22   # Future real sensor support
