# Silvia Pico Documentation

**Welcome to the official documentation for the Rancilio Silvia Espresso Machine Control System.**

This project provides full microcontroller-based control for the Rancilio Silvia using a **Raspberry Pi Pico W**. The firmware delivers precise temperature regulation, pre-infusion, soft pressure release, automated backflush, Bluetooth connectivity, and persistent settings.

The system is designed to run completely asynchronously, allowing stable machine control while communicating with the companion iOS app.

### 📖 Table of Contents

- **[Hardware & Wiring](hardware.md)**  
  Physical connections, BOM, safety notes and installation into the Silvia.

- **[Installation on Pico W](installation.md)**  
  Flashing MicroPython, copying files, first boot.

- **[Configuration](configuration.md)**  
  How to set up `secrets.py`, `config.py`, `network_settings.py` and `settings.txt`.

- **[Usage Guide](usage.md)**  
  Daily operation, starting a brew, running backflush, using the iOS app.

- **[System Architecture](architecture.md)**  
  Code structure, main components, how the async system works.

- **[Features](features/)**  
  Detailed explanations of all major functions:
  - [Temperature Control](features/temperature-control.md) — custom two-stage system (heating cycle + predictive anticipation)
  - [Pre-infusion](features/pre-infusion.md)
  - [Soft Pressure Release](features/soft-pressure-release.md)
  - [Backflush](features/backflush.md)
  - [Bluetooth](features/bluetooth.md)
  - [API](features/api.md)

- **[Troubleshooting](troubleshooting.md)**  
  Common issues and solutions.

### Quick Links

- [GitHub Repository](https://github.com/Rolppe/silvia_pico)
- [iOS Companion App](https://github.com/Rolppe/silvia_pico_ui) (Swift)

---

**Next steps**  
Start with the **[Installation guide](installation.md)** if you are setting up the Pico for the first time.

---

*This documentation is a living document and will be updated as the project evolves.*
