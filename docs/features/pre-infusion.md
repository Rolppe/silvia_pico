# Pre-infusion

Pre-infusion is a low-pressure pre-wetting phase that occurs **before** the full-pressure brewing stage. It is one of the most important features for improving espresso quality on the Rancilio Silvia.

## Why Pre-infusion?

When high-pressure water hits a dry coffee puck, it creates channels (pathways of least resistance). This leads to uneven extraction: some parts of the puck become over-extracted while others remain under-extracted.

Pre-infusion solves this by gently saturating the entire coffee puck at low pressure first. Once the puck is evenly wet, the full brewing pressure is applied, resulting in much more uniform extraction and better flavour.

## How Pre-infusion Works in Silvia Pico

The system uses a **pulsed pump** technique:

1. The brew solenoid opens to build initial pressure.
2. The pump is turned **on for 0.5 seconds**, then **off for 0.5 seconds**.
3. This cycle repeats for the configured pre-infusion time.
4. During the off periods, pressure drops slightly, allowing water to soak evenly through the puck.
5. After the pre-infusion phase ends, the system immediately switches to full-pressure brewing.

This pulsing is fully automatic and runs in the main control loop.

## Configuration

All timing is adjustable in `config.py`:

```python
# Pre-infusion settings (seconds)
PRE_INFUSION_TIME_DEFAULT = 4     # Default: 4 seconds

# These values affect the pulsing behaviour
PUMP_ON_TIME_PRE_INFUSION = 0.5   # seconds
PUMP_OFF_TIME_PRE_INFUSION = 0.5  # seconds
