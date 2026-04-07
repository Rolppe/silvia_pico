# Backflush

The automated backflush feature cleans the brew group, solenoid valve and shower screen of the Rancilio Silvia using a programmed cleaning cycle.

## Why Backflush?

Espresso machines accumulate coffee oils, grounds and residue in the brew group over time. Regular backflushing with a blind basket and cleaning detergent (e.g. Cafiza) is the most effective way to keep the machine clean and maintain great-tasting espresso.

The Silvia Pico automates this process completely, so you only need to insert the blind basket and start the cycle from the iOS app.

## How Backflush Works

The firmware runs a repeated on/off pump cycle:

1. Pump is turned **ON** for the configured time (typically 5 seconds).
2. Pump is turned **OFF** for the configured time (typically 5 seconds).
3. The cycle repeats for the programmed number of repetitions.
4. After the last cycle the pump and solenoid are turned off.

During the cycle the brew solenoid stays open so the cleaning solution is pushed back and forth through the group head.

## Configuration

All backflush parameters are defined in `config.py`:

```python
# Backflush / Cleaning cycle settings
BACKFLUSH_CYCLES = 10           # Number of on/off cycles (recommended 8-15)
BACKFLUSH_ON_TIME = 5           # seconds pump is ON
BACKFLUSH_OFF_TIME = 5          # seconds pump is OFF
