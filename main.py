import _thread
import utime
import json
from machine import Pin
import adafruit_max31865 as max31865
import socket
import network

from functions import save_settings, load_settings, print_values
from api_functions import set_station, set_socket,  response_HTML, parse_request
from modes import brew_mode, water_mode
from classes import LockPrinter, BrewData, HeatingSpeedCalculator, Sensor, Thermostat
from secrets import ssid, password


# --- UI ---
def _threadui():

    # Create WiFi connection
    set_station(utime, network, ssid, password, lock_printer)
    
    # Create Socket
    s = set_socket(socket, utime, lock_printer)
    
# --- MAIN LOOP --- 
    while True:
        
        # Set switches changed flag to False
        switch_changed = False
        
        # Accept incoming communications
        try:
            conn, addr = s.accept()
            
        # Handle errors
        except Exception as e:
            # Print an error message
            lock_printer("an error occured while establishing connection:", str(e))
            
        # Read request and transform it to string
        request = conn.recv(1024)
        request = str(request)
        
        # Parse request to brew data
        parse_request(brew_data, request, save_settings, json)
        
        # Create response
        response = response_HTML(brew_data)

        # Send response
        conn.send(response)

        # Close connection
        conn.close()

        # Nullify conn variable
        conn = None
            
        # Set up small delay before next handling
        utime.sleep(1)
        
###################################################################################


# --- HARDWARE ---
def _threadharware():
        
    # Run thermostat cycle
    thermostat = Thermostat()
    
    # Set value for heating speed multiplier for thermostat response
    heating_speed_multiplier = 0.8
    
    # Create heat speed calculating object
    heating_speed_calculator = HeatingSpeedCalculator(utime)
    
    # Set the output pin's for relays
    relay_heater = Pin(16, Pin.OUT, value = 0)
    relay_solenoid = Pin(17, Pin.OUT, value = 0)
    relay_pump = Pin(18, Pin.OUT, value = 0)
    
    # Set mode to idle
    brew_data.set_mode("idle")

    # Load settings (to brew_data object)
    load_settings(json, brew_data)


# --- MAIN LOOP ---    
    while True:
        
        # Get brew settings from brew_data object
        brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
        
        # Get temperature from the boiler
        boiler_temperature = sensor.read_temperature()
        brew_data.set_boiler_temperature(boiler_temperature)

        # Get calculation of temperature change speed
        heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
        brew_data.set_heating_speed(heating_speed)
        
        # --- BREW MODE ---
        if switch_brew.value() == 1:
            brew_mode(brew_data, switch_brew, relay_pump, relay_solenoid, relay_heater, print_values, lock_printer, sensor, heating_speed_calculator)

        # --- WATER ---
        if switch_water.value() == 1:
            water_mode(brew_data, switch_water, relay_pump, relay_heater, relay_solenoid, print_values, lock_printer, sensor, heating_speed_calculator)

        
        # --- THERMOSTAT ---      
        thermostat.run(brew_data, switch_steam, relay_heater)
        
        # --- Print essential values
        print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # Hardware setup
        
###################################################################################


# --- GLOBAL ---
        
# Set the input switches (Pin's)
switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN)
switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)
switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)

# Create and define temperature sensor
sensor = Sensor(max31865, _thread, Pin)

# Create and define lock printer for printing with both threads without the risk of collision
lock_printer = LockPrinter(_thread)

# Create data store object for threads to share data
brew_data = BrewData(_thread, switch_brew, switch_steam, switch_water)

# Start the threads
_thread.start_new_thread(_threadharware, ())
_threadui()

