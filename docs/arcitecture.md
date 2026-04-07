# System Architecture

This document describes the overall software architecture of the Silvia Pico firmware.

## High-Level Overview

The firmware is built for the **Raspberry Pi Pico W** running **MicroPython**. It is designed to run two major subsystems in parallel:

- **Machine Control** (temperature regulation, brewing logic, relays)
- **Communication** (Bluetooth + iOS app interaction)

These subsystems run concurrently so that the machine control remains stable and responsive even while the app is connected or sending commands.

## File Structure

silvia_pico/
├── boot.py                 # Startup script (runs first on boot)
├── main.py                 # Main entry point – launches both subsystems
├── classes.py              # Core classes (BrewData, TemperatureManager, etc.)
├── functions.py            # Shared utility functions
├── api_functions.py        # API / command handling between app and firmware
├── bluetooth_handler.py    # Bluetooth server and communication
├── backflush.py            # Backflush logic
├── preset.py               # Preset / saved profile handling
├── config.py               # Hardware pins & default settings
├── secrets_TEMPLATE.py     # Wi-Fi & Bluetooth credentials (renamed to secrets.py)
├── ugit.py                 # Helper for easy file upload
├── lib/                    # Additional MicroPython libraries
└── docs/                   # Documentation (this folder)


## Core Components

### 1. Boot Process (`boot.py`)
- Runs automatically when the Pico starts.
- Loads configuration and persistent settings.
- Initializes hardware pins and Bluetooth.
- Starts the main application.

### 2. Main Application (`main.py`)
- Launches the two main tasks:
  - Machine control loop (temperature, relays, brewing states)
  - Bluetooth communication handler
- Uses MicroPython’s `_thread` module (or uasyncio) for concurrency.

### 3. Core Classes (`classes.py`)
Contains the central data structures and logic:
- `BrewData` – global state holder (temperature, mode, settings, relay states). Shared safely between threads.
- `TemperatureManager` – the custom two-stage temperature control (heating cycle + predictive anticipation).
- Other helper classes for relays, virtual boiler, etc.

### 4. Feature Modules
- `bluetooth_handler.py` – Handles Bluetooth advertising, connections, and command parsing from the iOS app.
- `backflush.py` – Automated cleaning cycle logic.
- `api_functions.py` – Processes commands coming from the app (set temperature, start brew, start backflush, etc.).
- `functions.py` – Reusable utilities (printing, timing, etc.).

### 5. Configuration & Persistence
- `config.py` – Hardware pins, default values, system behaviour.
- `secrets.py` – Wi-Fi / Bluetooth credentials (never committed to Git).
- Persistent storage (`settings.txt`) – user changes are saved automatically and restored on reboot.

## Data Flow

1. iOS app connects via Bluetooth → sends command.
2. `bluetooth_handler` receives and forwards command to `api_functions`.
3. `BrewData` object is updated.
4. Main control loop in `main.py` reads the updated state and acts (heater, pump, solenoid).
5. Live status is sent back to the app continuously.

All shared data access is protected to prevent race conditions.

## Design Principles

- **Separation of concerns** – machine control and communication are isolated.
- **Persistent settings** – user preferences survive reboots.
- **Virtual boiler support** – easy testing without real hardware (`USE_VIRTUAL_BOILER` flag).
- **Extensibility** – new features (e.g. real temperature sensor, brewing profiles) can be added with minimal changes to core files.

This architecture makes the system reliable, maintainable, and ready for future hardware integration.

---
