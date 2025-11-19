import _thread
import utime
import json
from machine import Pin
import adafruit_max31865 as max31865
import socket
import network

from api_functions import set_station, set_socket,  response_HTML, parse_request
from functions import save_settings, load_settings, print_values
from modes import brew_mode, water_mode
from classes import LockPrinter, BrewData, HeatingSpeedCalculator, Thermostat, Sensor
from secrets import ssid, password


sensor = Sensor(max31865, _thread, Pin)

# Set the input switches (Pin's)
switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN)
switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)
switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)

# Create and define lock printer for printing with both threads without the risk of collision
lock_printer = LockPrinter(_thread)

# Create data store object for threads to share data
brew_data = BrewData(_thread, switch_brew, switch_steam, switch_water)

        
# Run thermostat cycle
thermostat = Thermostat()

# Set value for heating speed multiplier for thermostat response
heating_speed_multiplier = 0.8

# Create heat speed calculating object
heating_speed_calculator = HeatingSpeedCalculator(utime)

# Set the output pin's for relays
relay_heater = Pin(11, Pin.OUT, value = 0)
relay_solenoid = Pin(12, Pin.OUT, value = 0)
relay_pump = Pin(13, Pin.OUT, value = 0)

# Set mode to idle
brew_data.set_mode("idle")

# Load settings (to brew_data object)
load_settings(json, brew_data)

# Connect to Wifi
set_station(utime, network, ssid, password, lock_printer)

# Create Socket
s = set_socket(socket, utime, lock_printer)


def network_settings_api():
    
    while (switch_steam.value() and switch_water.value()):
        
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
    



# Fast heatup setting on/off

if switch_steam.value():
    fast_heatup = False
else:
    fast_heatup = True

# steam_water_purge = True

if fast_heatup:
    top_temp = 0
        
#     # Fill the boiler
    relay_pump.value(1)
    relay_solenoid.value(1)
    utime.sleep(2)
    relay_pump.value(0)
    relay_solenoid.value(0)
    
   
    relay_heater.value(1)
    while sensor.read_temperature() < 85:
        utime.sleep(1)
    relay_heater.value(0)
    
    while sensor.read_temperature() < 110:
        relay_heater.value(1)
        utime.sleep(1)
        relay_heater.value(0)
        utime.sleep(1)
    while sensor.read_temperature() < 120:
        relay_heater.value(1)
        utime.sleep(1)
        relay_heater.value(0)
        utime.sleep(2)
    while sensor.read_temperature() < 125:
        relay_heater.value(1)
        utime.sleep(1)
        relay_heater.value(0)
        utime.sleep(3)
            
        

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
            
    boiler_temperature = sensor.read_temperature()


    if switch_brew.value():
        brew_counter = 0
        relay_solenoid.value(1)
        relay_pump.value(1)
        relay_heater.value(0)
        
        # Set solenoid to brewing (pressure) mode
        while(switch_brew.value()):
            print(1)
            while(switch_brew.value()):
                print(2)

                print(str(brew_counter))
                
                brew_counter += 1

                if brew_counter < 2000:
                    print("ali")
                    relay_heater.value(0)
                    
                elif brew_counter < 3000:
                    print("yli")
                    relay_heater.value(1)
                
                else:
                    relay_heater.value(0)
                    brew_counter = 0
        
    # If water switch is on
    if switch_water.value():
        
        # If also steam switch is on then turn on network setup
        if switch_steam.value():
            relay_pump.value(0)
            relay_solenoid.value(0)
            relay_heater.value(0)
            network_settings_api()
        
        else:
            # Water loop
            while (switch_water.value()):
                 
                # Start heating the boiler
                relay_heater.value(1)
            
                # Start the pump
                relay_pump.value(1)
            
    # Set relays to default when not brewing or hot watering
    relay_pump.value(0)
    relay_solenoid.value(0)

    
    # --- THERMOSTAT ---      
    thermostat.run(brew_data, switch_steam, relay_heater)
    
    # --- Print essential values
    print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # Hardware setup
        
###################################################################################


        



