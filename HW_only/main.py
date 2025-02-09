import _thread
import utime
import json
from machine import Pin
import adafruit_max31865 as max31865

from functions import save_settings, load_settings, print_values
from modes import brew_mode, water_mode
from classes import LockPrinter, BrewData, HeatingSpeedCalculator, Thermostat, Sensor

sensor = Sensor(max31865, _thread, Pin)
# = max31865.MAX31865(
#             wires = 2, rtd_nominal = 100, ref_resistor = 430,
#             pin_sck = 6, pin_mosi = 3, pin_miso = 4, pin_cs = 5
#             )

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
    
#     # --- BREW MODE ---
#     if switch_brew.value() == 1:
#         brew_mode(brew_data, switch_brew, relay_pump, relay_solenoid, relay_heater, print_values, lock_printer, sensor, heating_speed_calculator)
# 
#     # --- WATER ---
#     if switch_water.value() == 1:
#         water_mode(brew_data, switch_water, relay_pump, relay_heater, relay_solenoid, print_values, lock_printer, sensor, heating_speed_calculator)




    if switch_brew.value(): 
        
        # Set solenoid to brewing (pressure) mode
        while(switch_brew.value()):
            relay_heater.value(1)
            relay_solenoid.value(1)
            relay_pump.value(1)

    # If water switch is on
    if switch_water.value():
     
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


        



