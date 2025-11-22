# Settings
fast_heatup_setting = False
pre_infusion_setting = True

pre_infusion_pressure_buildup_time = 1
pre_infusion_time = 5 



# Import libraries
import utime
import json
from machine import Pin
import adafruit_max31865 as max31865
import socket
import network

# Import functions, classes and data
from api_functions import set_station, set_socket,  response_HTML, parse_request
from functions import save_settings, load_settings, print_values, fast_heatup, pre_infusion
from classes import BrewData, HeatingSpeedCalculator, Thermostat, Sensor
from secrets import ssid, password

# Initialize max31865 (temperature sensort pt100)
sensor = Sensor(max31865, Pin)

# Set the input pins for switches
switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN)
switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)
switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)

# Set the output pins for relays
relay_heater = Pin(11, Pin.OUT, value = 0)
relay_solenoid = Pin(12, Pin.OUT, value = 0)
relay_pump = Pin(13, Pin.OUT, value = 0)

# Create data and state store object 
brew_data = BrewData(switch_brew, switch_steam, switch_water)

# Create heat speed calculating object
heating_speed_calculator = HeatingSpeedCalculator(utime)

# Load settings (to brew_data object)
load_settings(json, brew_data)

# Connect to Wifi
set_station(utime, network, ssid, password)

# Set Socket
s = set_socket(socket, utime)

# Set flag for indicating if settings are to be fetched
api_flag = True

# Function to api through wifi
def network_settings_api():
    
    # If steam and water switches are on, then start broadcasting api
    while (switch_steam.value() and switch_water.value()):

        # Accept incoming communications
        try:
            conn, addr = s.accept()

        # If error print it
        except Exception as e:
            
            # Print an error message
            print('an error occured while establishing connection:' + str(e))

        # Read request and format it to string
        request = conn.recv(1024)
        request = str(request)

        # Parse request and save it to brew data
        parse_request(brew_data, request, save_settings, json)

        # Create HTML response
        response = response_HTML(brew_data)

        # Broadcast HTML response
        conn.send(response)

        # Close connection
        conn.close()

        # Nullify conn variable
        conn = None

        # Set up small delay before next handling
        utime.sleep(1)
    

# If steam switch is off, set mode for fast heatup and fill boiler
if not switch_steam.value() and fast_heatup_setting:
    brew_data.set_mode('fast_heatup')
    fast_heatup(relay_pump, relay_solenoid, relay_heater, utime, sensor, pressure_buildup_time, pre_infusion_time)

# Run thermostat cycle
thermostat = Thermostat()

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
        
        if pre_infusion_setting:
            print(0)
            brew_data.set_mode('pre-infusion')
            pre_infusion(relay_pump, relay_solenoid, relay_heater, utime, sensor, pre_infusion_pressure_buildup_time, pre_infusion_time)
        
        # Set mode to brewing
        brew_data.set_mode('brew')
        
        # Initialize counter for brewing cycles
        brew_cycle_counter = 0
        
        # Set solenoid an on for brewing
        relay_solenoid.value(1)
        
        # Set pump on for brewing
        relay_pump.value(1)
        
        ## BREW LOOP ##
        # Run brew cycle with heat cycling as long as brew switch is on
        while(switch_brew.value()):
            
            # If under 1500 cycles, set heater off and increment counter
            if brew_cycle_counter < 1500:
                relay_heater.value(0)
                brew_cycle_counter += 1
            
            # If 1500 between 3000 cycles, set heater on and increment counter
            elif brew_cycle_counter < 3000:
                relay_heater.value(1)
                brew_cycle_counter += 1
            
            # At the 3000 cycles reset counter
            else:
                brew_cycle_counter = 0
            
        # Set heater off after brewing for security reason
        relay_heater.value(0)
        
        # Set pump off
        relay_pump.value(0)
        
        # Set soleinoid off
        relay_solenoid.value(0)


    ### HOT WATER MODE AND API MODE ###       
    
    # If water switch is on 
    if switch_water.value():
        
        ## API MODE ##
        # If steam switch is turned on before, then start api
        if switch_steam.value():
            
            # Set mode 'api'
            brew_data.set_mode('api')
            
            # Turn of relays for safety reason
            relay_pump.value(0)
            relay_solenoid.value(0)
            relay_heater.value(0)
            
            # turn on api
            network_settings_api()
            
            # Set api flag true for setting refresh
            api_flag = True
        
        ## HOT WATER MODE ##
        # If steam swith is not on, set heater and pump on and start water loop
        else:
            
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
    


