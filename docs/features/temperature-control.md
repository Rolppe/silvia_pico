# Temperature Control

The Silvia Pico uses a **custom two-stage temperature control system** instead of a traditional PID controller. This design was developed specifically for the Rancilio Silvia’s heavy brass boiler, which has slow thermal response and significant inertia.

## Why Not Traditional PID?

- The boiler is massive and reacts slowly.
- Simple on/off thermostats cause large temperature swings (~10 °C).
- A classic PID would require extensive tuning and still struggle with the boiler’s thermal mass and varying water flow during brewing.

The custom system achieves **±0.5 °C stability** by combining two independent logic layers.

## How the Two-Stage System Works

### 1. Heating Cycle Layer (Cycling)
- Continuously compares current boiler temperature to the target (brew or steam mode).
- Turns the heater relay **ON** when temperature is below target.
- Turns the heater relay **OFF** when temperature reaches or exceeds target + hysteresis.
- Runs in real time in the main control loop.

### 2. Predictive Anticipation Layer (Rate-of-Change)
- Calculates how fast the temperature is rising or falling (`heating_speed`).
- Uses this rate to **anticipate** when the heater should be turned off *before* the target is actually reached.
- Prevents overshoot caused by the boiler’s thermal inertia.
- The anticipation is stronger when the temperature is changing rapidly (e.g. during initial heat-up or when cold water flows through the boiler).

This predictive layer is based on a custom `HeatingSpeedCalculator` (or equivalent class in `classes.py` / `backflush.py`) that tracks temperature change over time.

## Key Settings in config.py

```python
# Temperature targets
BREW_TEMP_DEFAULT = 105.0      # °C
STEAM_TEMP_DEFAULT = 120.0     # °C

# How tightly the system holds the target
TEMP_HYSTERESIS = 0.5          # °C

# Sensitivity of the predictive layer
HEATING_SPEED_MULTIPLIER = 1.0 # Adjust if overshoot/undershoot occurs
