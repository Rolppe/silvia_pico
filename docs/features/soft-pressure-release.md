# Soft Pressure Release

Soft pressure release is an automated post-brew phase that gently releases the pressure from the brew group after the shot is finished. It prevents the coffee puck from exploding and spraying grounds everywhere.

## Why Soft Pressure Release?

When brewing ends, the original Silvia immediately opens the solenoid valve while there is still high pressure in the group head. This causes the puck to “explode” — coffee grounds and water spray violently inside the group, creating a big mess and requiring extra cleaning.

The soft pressure release solves this by keeping the solenoid closed for a short, configurable time after the pump stops. This allows the remaining pressure to bleed off slowly and evenly through the coffee puck.

## How It Works in Silvia Pico

1. User stops the brew (via app or physical switch).
2. The pump is turned off immediately.
3. The solenoid valve **remains closed** for the configured release time.
4. After the delay, the solenoid opens and releases the remaining pressure gently.
5. The system returns to idle/ready state.

This entire sequence is fully automatic and runs in the main control loop.

## Configuration

The duration is adjustable in `config.py`:

```python
# Soft pressure release settings (seconds)
SOFT_PRESSURE_RELEASE_TIME_DEFAULT = 4     # Default: 4 seconds

# Minimum and maximum allowed values (for app validation)
SOFT_PRESSURE_RELEASE_MIN = 0
SOFT_PRESSURE_RELEASE_MAX = 10
