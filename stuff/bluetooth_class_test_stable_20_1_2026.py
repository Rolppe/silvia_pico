import bluetooth  # Bluetooth functions in MicroPython (built-in for Pico W).
from micropython import const  # Defines constants for memory efficiency.
import time  # Time delays, e.g., for data transmission interval.
import json  # Converts data to JSON format for transmission.
import machine  # Hardware control, e.g., pins and LED.
import random  # Random numbers for temperature simulation (replace with real sensor in production).


# BLE advertising constants: These are standard values for BLE advertising.
# They define how the device announces itself to other devices.
_ADV_TYPE_FLAGS = const(0x01)  # Flags, e.g., for general discoverability.
_ADV_TYPE_NAME = const(0x09)  # Device name in advertisement.
_ADV_TYPE_UUID16_COMPLETE = const(0x3)  # Complete 16-bit UUID list.
_ADV_TYPE_APPEARANCE = const(0x19)  # Device appearance (e.g., category like sensor).

# UUIDs for GATT service and characteristics: These are unique identifiers for BLE services and characteristics.
# Standard UUIDs are used for testing; use unique ones in production.
_CENTRAL_UUID = bluetooth.UUID('0000180a-0000-1000-8000-00805f9b34fb')  # Service UUID (e.g., Device Information Service).
_DATA_CHAR_UUID = bluetooth.UUID('00002a29-0000-1000-8000-00805f9b34fb')  # Data characteristic (notify and read).
_COMMAND_CHAR_UUID = bluetooth.UUID('00002a2a-0000-1000-8000-00805f9b34fb')  # Command characteristic (write).


# Main class BLECoffee: Handles all BLE operations.
class BLEHandler:
    def __init__(self, ble):
        # Print debug information during initialization.
        print("Initializing BLE...")
        self._ble = ble  # Store the Bluetooth object.
        self._ble.active(True)  # Activate the BLE module; without this, the device is not usable.
        print("BLE activated")
        self._ble.irq(self._irq)  # Set the IRQ handler (interrupt request): This is called when a BLE event occurs (e.g., connection).
        # Register GATT services: This defines what features the device offers.
        # _handle_tx and _handle_rx are handles for notify and write characteristics.
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((
            (_CENTRAL_UUID,
             (
                 (_DATA_CHAR_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,),  # Read and notify: Client can read and subscribe to updates.
                 (_COMMAND_CHAR_UUID, bluetooth.FLAG_WRITE,),  # Write: Client can send commands.
             ),
            ),
        ))
        print("Services registered")
        self._connections = set()  # Track active connections (conn_handles).
        # Create advertising packet: Contains name, services, etc., used to announce the device.
        self._payload = self._advertising_payload(name='EspressoPico', services=[_CENTRAL_UUID])
        self._advertise()  # Start advertising.
        self.temp = 92.0  # Initial value for temperature (updated later).


# IRQ handler: Called automatically on BLE events. This is the "event handler" for BLE.
    def _irq(self, event, data):
        print("IRQ event:", event, "data:", data)  # Debug: Shows all events.
        if event == 1:  # Connected: Client (e.g., app) has established a connection.
            print("Connection established:", data)
            led.value(1)  # Turn LED on to indicate connection.
            conn_handle, _, _ = data  # Unpack data: conn_handle is the connection identifier.
            self._connections.add(conn_handle)  # Add to connections.
        elif event == 2:  # Disconnected: Connection lost.
            print("Connection lost:", data)
            led.value(0)  # Turn LED off.
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)  # Remove connection.
            self._advertise()  # Restart advertising for discoverability.
        elif event == 3:  # Write: Client has written to a characteristic (e.g., command).
            print("Write received:", data)
            conn_handle, value_handle = data  # Unpack: value_handle is the handle of the written characteristic.
            value = self._ble.gatts_read(value_handle)  # Read the written value.
            command = value.decode('utf-8').strip()  # Convert to text.
            print("Command:", command)  # Debug: Shows the command (e.g., 'start_brew').
        else:
            print("Unknown IRQ event:", event, data)  # Other events (e.g., MTU exchange).

    
# Send data to client: Convert dict to JSON and notify connections.
    def send_data(self, data):
        json_data = json.dumps(data)  # Convert to JSON string.
        print("Sending data:", json_data)  # Debug.
        for conn_handle in self._connections:  # Send to each connection.
            self._ble.gatts_notify(conn_handle, self._handle_tx, json_data)  # Notify: Send data without request.

    
# Update temperature: Simulation here; replace with sensor reading (e.g., ADC or TSIC).
    def update_temp(self):
        self.temp = 92 + random.uniform(-1, 1)  # Simulate variation.

    
# Start advertising: Announces the device's availability to other devices.
    def _advertise(self, interval_us=500000):
        print("Advertising started")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)  # GAP advertise: Send packet every interval_us microseconds.

    
# Static method to create advertising payload: Builds a bytearray according to standards.
    @staticmethod
    def _advertising_payload(limited_disc=False, br_edr=False, name=None, services=None, appearance=0):
        payload = bytearray()  # Start empty.
        def _append(adv_type, value):
            nonlocal payload
            payload += bytearray([len(value) + 1, adv_type]) + value  # Add type and data.
        _append(_ADV_TYPE_FLAGS, bytearray([0x06 if limited_disc else 0x02, 0x00]))  # Flags: Discoverability.
        if name:
            _append(_ADV_TYPE_NAME, name.encode())  # Add name as UTF-8.
        if services:
            for uuid in services:
                b = bytes(uuid)
                if len(b) == 2:
                    _append(_ADV_TYPE_UUID16_COMPLETE, b)  # Add service UUIDs.
        if appearance:
            _append(_ADV_TYPE_APPEARANCE, bytearray([appearance & 0xFF, appearance >> 8]))  # Appearance (e.g., sensor).
        return payload


