# Rancilio Silvia Espresso Machine Control System (Pico)

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![MicroPython](https://img.shields.io/badge/MicroPython-v1.22+-orange)](https://micropython.org)
[![Raspberry Pi Pico W](https://img.shields.io/badge/Hardware-Pico_W-green)](https://www.raspberrypi.com/products/raspberry-pi-pico/)

**Full microcontroller control for the Rancilio Silvia espresso machine using Raspberry Pi Pico W.**

A modern, open-source firmware that replaces the original thermostat and manual controls with advanced temperature regulation, pre-infusion, soft pressure release, automated backflush, and Bluetooth connectivity.

> Next-generation Silvia mod — improved temperature stability, better extraction, and automatic cleaning.

### ✨ Key Features

- **Advanced Temperature Control** (custom two-stage system: heating cycle + predictive anticipation)
- **Pre-infusion** (low-pressure pre-wetting)
- **Soft pressure release** (prevents puck explosion)
- **Automated backflush program**
- **Bluetooth connectivity** (easy mobile pairing)
- **iOS Companion App** (Swift) — [silvia_pico_ui](https://github.com/Rolppe/silvia_pico_ui)
- **Persistent settings** (survive reboots)
- **Async operation** (app communication and machine control run in parallel)

### 🚀 Quick Start (3 minutes)

1. Flash MicroPython to your Pico W
2. Copy all files to the Pico (use `ugit.py` for convenience)
3. Rename `secrets_TEMPLATE.py` → `secrets.py` and fill in your Wi-Fi SSID, password, Bluetooth device name and other credentials
4. Review and adjust `config.py` according to your hardware/setup
5. Power on → connect via Bluetooth or the iOS companion app


**IN PROGRESS ->**
**Full installation guide → [Installation](docs/installation.md)**

### 📖 Full Documentation

- [Hardware & Wiring](docs/hardware.md)
- [Installation on Pico W](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Usage Guide](docs/usage.md)
- [System Architecture](docs/architecture.md)
- [Features](docs/features/)
  - [Temperature Control](docs/features/temperature-control.md)
  - [Pre-infusion](docs/features/pre-infusion.md)
  - [Soft Pressure Release](docs/features/soft-pressure-release.md)
  - [Backflush](docs/features/backflush.md)
  - [Bluetooth](docs/features/bluetooth.md)
  - [API](docs/features/api.md)
- [Troubleshooting](docs/troubleshooting.md)

### Tech Stack

- **Hardware**: Raspberry Pi Pico W
- **Language**: MicroPython
- **Connectivity**: Wi-Fi + Bluetooth
- **License**: MIT
