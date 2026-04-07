# Hardware & Wiring

This document describes the physical hardware setup and electrical connections for the **Rancilio Silvia Espresso Machine Control System** using the Raspberry Pi Pico W.

> **⚠️ Important Safety Warning**  
> This project involves controlling 230 V AC high-power components (heating element, pump, solenoid). Incorrect wiring can cause fire, electric shock, or permanent damage to the machine and Pico. Proceed only if you understand the risks and follow proper electrical safety practices. Use fuses, proper grounding, and isolated relays.

## System Overview

The Pico W replaces the original mechanical thermostat and manual controls of the Rancilio Silvia. It manages:
- Boiler temperature regulation (custom two-stage control)
- Vibration pump
- Brew solenoid valve
- Backflush and cleaning cycles
- Pre-infusion and soft pressure release timing

The system was initially developed with a **virtual boiler** for software testing. The code is designed so that real hardware integration requires only small changes (mainly enabling real relay control and sensor reading).

## Recommended Bill of Materials (BOM)

| Item                          | Quantity | Notes / Recommendation                          |
|-------------------------------|----------|-------------------------------------------------|
| Raspberry Pi Pico W           | 1        | Main controller                                 |
| Solid State Relay (SSR) 25–40 A | 1        | For boiler heating element                      |
| Solid State Relay (SSR) 5–10 A | 2–3      | For pump, solenoid, and optional backflush valve|
| 5 V DC power supply           | 1        | Stable, at least 500 mA for Pico                |
| Enclosure / mounting box      | 1        | Heat-resistant, moisture protected              |
| Wiring & connectors           | –        | High-temperature wire, heat shrink, ferrules    |
| Fuses & fuse holders          | –        | 10 A + 2 A recommended                          |
| Optional: Temperature sensor  | 1        | DS18B20 or similar (for real boiler feedback)   |

## Pico Pin Connections

Exact pin assignments are defined in `config.py`. Update the table below with your final wiring:

| Function                   | Pico GPIO Pin            | Description                              | Notes                     |
|----------------------------|--------------------------|--------------------------------|---------------------------|
| Heater Relay               | (configure in config.py) | Controls boiler heating element     | High-current SSR          |
| Pump Relay                 | (configure in config.py) | Controls vibration pump             | –                         |
| Solenoid / Brew Valve      | (configure in config.py) | Controls brew solenoid              | –                         |
| Backflush Valve (optional) | (configure in config.py) | Extra valve for cleaning cycle      | –                         |
| Status LED (optional)      | (configure in config.py) | Visual feedback                     | –                         |
| Temperature Sensor (future)| (configure in config.py) | OneWire / DS18B20                   | Planned real hardware     |

> **Tip**: Use `boot.py` or `config.py` to define your final pin mapping. All relay controls are handled through the `Relay` class in the codebase.

## Mechanical Installation

- Choose a mounting location for the Pico (inside the Silvia base, external waterproof box, or custom 3D-printed enclosure).
- Ensure good airflow and protection from heat, steam, and coffee grounds.
- Use strain relief on all cables.
- Keep high-voltage AC wiring physically separated from the Pico’s low-voltage side.

## Power Supply

- The Pico W must be powered with a stable **5 V DC** supply (micro-USB or direct 5 V pin).
- It is strongly recommended to power the Pico from a separate supply, not directly from the machine’s internal transformer, to avoid noise and ground issues.

## Current Hardware Status

The firmware is fully functional with the virtual boiler. Real hardware integration is the next major milestone. The code architecture already supports switching between virtual and real hardware with minimal changes.

**Next steps for real hardware:**
1. Wire the relays safely.
2. Update pin definitions in `config.py`.
3. Test temperature control in real conditions.
4. (Optional) Add a real temperature sensor for closed-loop feedback.
