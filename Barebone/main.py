import utime
import json
from machine import Pin
import adafruit_max31865 as max31865

from classes import Sensor



def _hardware():

# Set the output pin's for relays
    relay_heater = Pin(16, Pin.OUT, value = 0)
    relay_solenoid = Pin(17, Pin.OUT, value = 0)
    relay_pump = Pin(18, Pin.OUT, value = 0)

    # Set the input switches (Pin's)
    switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN)
    switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)
    switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)
    
    # Set up the target temperature and counter for brewing time
    target_temperature = 0
    counter_brew_time = 0
    brew_temperature = 30
    steam_temperature = 32
    # Get the boiler temperature
    boiler_temperature = sensor.read_temperature() #(when connected on hardware)

# --- MAIN LOOP ---    
    while True:
        
        # Get temperature from the boiler
        boiler_temperature = sensor.read_temperature() # (when connected to hardware)
        
        # Set brewing time counter to 0
        counter_brewing_time = 0
        
    
        if switch_brew.value(): 
            
            # Set solenoid to brewing (pressure) mode
            while(switch_brew.value()):
                relay_solenoid.value(1)
                relay_pump.value(1)
                print("brewing")
                utime.sleep(1)
    
        # If water switch is on
        if switch_water.value():
         
            # Water loop
            while (switch_water.value()):
                 
                # Start heating the boiler
                relay_heater.value(1)
            
                # Start the pump
                relay_pump.value(1)
                
                print("Water mode")
                
                utime.sleep(1)
                
        # Set relays to default when not brewing or hot watering
        relay_pump.value(0)
        relay_solenoid.value(0)

    # --- TEMPERATURE MODE ---
        
        # If steam switch is off: set brewing temperature as a target temperature
        if switch_steam.value() == 0: 
            target_temperature = brew_temperature
                  
        # Otherwise set steam temperature as a target temperature
        else:
            target_temperature = steam_temperature
        
                         
    # --- THERMOSTAT ---
        
        # If boiler temperature is lower than target temperature
        if (boiler_temperature < target_temperature):
            
            # Start heating the boiler
            relay_heater.value(1)
            print("Heating")
            
        # Otherwise
        else:  
            # Stop heating the boiler
            relay_heater.value(0)
            print("cooling")


        print("relay_heater" + str(relay_heater.value()))
        print("relay_solenoid" + str(relay_solenoid.value()))
        print("relay_pump" + str(relay_pump.value()))
        print("switch_brew" + str(switch_brew.value()))
        print("switch_steam" + str(switch_steam.value()))
        print("switch_water" + str(switch_water.value()))
        print("Boiler temperature" + str(boiler_temperature))
    
    
sensor = Sensor(max31865, Pin)

_hardware()

