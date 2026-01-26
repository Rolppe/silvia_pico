# This code implements a Bluetooth Low Energy (BLE) service for the Raspberry Pi Pico 2 W using MicroPython.
# It allows establishing a connection with a device (e.g., a smartphone or computer) and sending temperature data in real time.
# The code is designed to be modular: the BLECoffee class handles BLE operations, and the main program initializes it and sends data.
# Debug prints help with troubleshooting, showing what BLE functions are happening in real time.

# Import necessary modules:
import bluetooth  # Bluetooth functions in MicroPython (built-in for Pico W).
from micropython import const  # Defines constants for memory efficiency.
import time  # Time delays, e.g., for data transmission interval.
import json  # Converts data to JSON format for transmission.
import machine  # Hardware control, e.g., pins and LED.
import random  # Random numbers for temperature simulation (replace with real sensor in production).
import utime
import adafruit_max31865 as max31865
from machine import Pin, ADC
from functions import save_settings, load_settings, print_values, fast_heatup, pre_infusion
from classes import BrewData, HeatingSpeedCalculator, Thermostat, Sensor, PressureMonitor
from secrets import ssid, password
from bluetooth_class_test import BLEHandler

# Set the input pins for switches
switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN)
switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)
switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)
# Set the output pins for relays
relay_pump = Pin(11, Pin.OUT, value = 0)
relay_solenoid = Pin(12, Pin.OUT, value = 0)
relay_heater = Pin(13, Pin.OUT, value = 0)
# Set advertising constants
_ADV_TYPE_FLAGS = const(0x01) # Flags, e.g., for general discoverability.
_ADV_TYPE_NAME = const(0x09) # Device name in advertisement.
_ADV_TYPE_UUID16_COMPLETE = const(0x3) # Complete 16-bit UUID list.
_ADV_TYPE_APPEARANCE = const(0x19) # Device appearance (e.g., category like sensor).
# Set UUIDs for GATT service and characteristics
_CENTRAL_UUID = bluetooth.UUID('0000180a-0000-1000-8000-00805f9b34fb') # Service UUID (e.g., Device Information Service).
_DATA_CHAR_UUID = bluetooth.UUID('00002a29-0000-1000-8000-00805f9b34fb') # Data characteristic (notify and read).
_COMMAND_CHAR_UUID = bluetooth.UUID('00002a2a-0000-1000-8000-00805f9b34fb') # Command characteristic (write).
######## Developement Settings ###########################
fast_heatup_mode = False
pre_infusion_mode = True
after_brew_pressure_drain = False
pre_infusion_pressure_buildup_time = 0
pre_infusion_time = 5
soft_pressure_release_time = 0
brew_pressure = 9
##########################################################
# Initialize max31865 (temperature sensort pt100)
sensor = Sensor(max31865, Pin)
# Create data and state store object
brew_data = BrewData(switch_brew, switch_steam, switch_water)
# Create heat speed calculating object
heating_speed_calculator = HeatingSpeedCalculator(utime)
# Load settings (to brew_data object)
load_settings(json, brew_data)
# Create class for pressure_barmonitoring
pressure_monitor = PressureMonitor(Pin, ADC, utime)
# Set flag for indicating if settings are to be fetched
api_flag = True
# If steam switch is off and fast heatup mode is on, set mode for fast heatup and fill boiler
if switch_steam.value() and fast_heatup_mode:
    brew_data.set_mode('fast_heatup')
    fast_heatup(relay_pump, relay_solenoid, relay_heater, utime, sensor)
# Initialize thermostat
thermostat = Thermostat()
# Initialize BLE
ble = bluetooth.BLE()
ble_handler = BLEHandler(ble)

#### MAIN LOOP ####
while True:
    # Get brew settings from brew_data object
    if api_flag:
        brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
        api_flag = False
    # Read pt100 sensor temperature
    boiler_temperature = sensor.read_temperature()
    # Save temperature data
    brew_data.set_boiler_temperature(boiler_temperature)
    # Calculate heating speed
    heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
    # Save heating speed
    brew_data.set_heating_speed(heating_speed)
    ### THERMOSTAT ###
   
    thermostat.run(brew_data, switch_steam, relay_heater)
    ### PRINT VALUES ###
   
    print_values(brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump)
    ### BREWING MODE ###
    # If brew swith is on start brewing
    if switch_brew.value():
        ## Pre-infusion ##
        if pre_infusion_mode:
            # Set heater of for safety
            relay_heater.value(0)
            #If brew switch is being put of within half second, push water and skip preinfusion
            utime.sleep(0.5)
            if not switch_brew.value():
                relay_solenoid.value(1)
                relay_pump.value(1)
                utime.sleep(1)
                relay_pump.value(0)
                relay_solenoid.value(0)
            else:
                # Set mode to pre-infusion
                brew_data.set_mode('pre-infusion')
                # Start pre-infusion program function
                pre_infusion(relay_pump, relay_solenoid, relay_heater, switch_brew, utime, sensor, pressure_monitor)
        # Set mode to brewing
        brew_data.set_mode('brew')
        # Initialize counter for brewing cycles
        brew_cycle_counter = 0
        # Set solenoid an on for brewing
        relay_solenoid.value(1)
        # Set pump on for brewing
        relay_pump.value(1)
        start_time = utime.ticks_ms()
        last_print_time = start_time
        ## BREW LOOP ##
       
        # Run brew cycle with heat cycling as long as brew switch is on
        while(switch_brew.value()):
            elapsed_ms = utime.ticks_diff(utime.ticks_ms(), start_time)
            current_seconds = elapsed_ms // 1000
            # cycle heater of for 0.5ms and on 0.1s
            if (elapsed_ms % 150) < 100:
                # Set heater relay off
                relay_heater.value(0)
            else:
                # Set heater relay on
                relay_heater.value(1)
            # Get pressure
            pressure_bar = pressure_monitor.get_pressure()
            # Print pressure_bar4 times in second
            if utime.ticks_diff(utime.ticks_ms(), last_print_time) >= 250:
                print("pressure: " +str(pressure_bar) +" bar")
                last_print_time = utime.ticks_ms()
            if pressure_bar < brew_pressure -1:
                relay_pump.value(1)
            elif pressure_bar < brew_pressure:
                relay_pump.value(1)
                utime.sleep(0.005)
                relay_pump.value(0)
            else:
                relay_pump.value(0)
        # Set pump off
        relay_pump.value(0)
        ## SLOW pressure_barRELEASE ##
        utime.sleep(soft_pressure_release_time)
        # Set soleinoid off
        relay_solenoid.value(0)
        if after_brew_pressure_drain:
            pressure_bar = pressure_monitor.get_pressure()
            while pressure_bar > 1.5:
                print("Pressure: " + str(pressure_bar) + " bar")
                utime.sleep(0.5)
                relay_solenoid.value(1)
                utime.sleep(0.5)
                relay_solenoid.value(0)
                pressure_bar = pressure_monitor.get_pressure()
    ### HOT WATER MODE AND API MODE ###
    # If water switch is on
    if switch_water.value():
        # Set mode to 'water'
        brew_data.set_mode('water')
        # Set on boiler heater
        relay_heater.value(1)
        # set on water
        relay_pump.value(1)
        # Run cycle for hot water as long as hot water switch is on
        while (switch_water.value()):
            utime.sleep(0.1)
        # Set heater and pump relays off after hot water kloop
        relay_pump.value(0)
        relay_heater.value(0)
       
    # Lähetä data (boiler_temperature ja pressure_bar) BLE:n kautta appiin, jos yhteys on
    if ble_handler._connections:
        pressure_bar = pressure_monitor.get_pressure()  # Lue paine uudelleen, jos tarvitaan
        data = {
            'temp': boiler_temperature,
            'pressure': pressure_bar
        }
        ble_handler.send_data(data)
    time.sleep(0.1)  # Lyhyt viive loopissa resurssien säästämiseksi