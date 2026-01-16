import utime
from machine import Pin, ADC
import adafruit_max31865 as max31865

# Import functions, classes and data
from classes import Sensor, PressureMonitor
from secrets import ssid, password

# Set the input pins for switches
switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN) # Pin(7, Pin.IN, Pin.PULL_DOWN)
switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN) # Pin(8, Pin.IN, Pin.PULL_DOWN)
switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN) # Pin(9, Pin.IN, Pin.PULL_DOWN


# Set the output pins for relays
relay_pump = Pin(11, Pin.OUT, value = 0) ## 11 12 13
relay_solenoid = Pin(12, Pin.OUT, value = 0) 
relay_heater = Pin(13, Pin.OUT, value = 0)

run_button_test = True
run_relay_test = False
run_pressure_test = True
run_temperature_test = True


if run_button_test:
    print("Button test")
    switch_brew_tested = False
    switch_water_tested = False
    switch_steam_tested = False
    while switch_brew_tested == False or switch_water_tested == False or switch_steam_tested == False:
        
        if switch_brew.value() and not switch_water.value() and not switch_steam.value(): # and not switch_brew_tested:
            switch_brew_tested = True
            print("Brew switch working")
            
        if switch_water.value() and not switch_brew.value() and not switch_steam.value():
            switch_water_tested = True
            print("Water switch working")
            
        if switch_steam.value() and not switch_water.value() and not switch_brew.value():
            switch_brew_tested = True
            print("Steam switch working")
        utime.sleep(0.1)
    print("button test complete")
    
if run_relay_test:
    print("relay test")
    relay_pump.value(0)
    relay_pump.value(1)
    utime.sleep(2)
    relay_pump.value(0)
    utime.sleep(2)
    
    relay_solenoid.value(0)
    relay_solenoid.value(1)
    utime.sleep(2)
    relay_solenoid.value(0)
    utime.sleep(2)
    
    relay_heater.value(0)
    relay_heater.value(1)
    utime.sleep(2)
    relay_heater.value(0)
    print("relay test complete")
    
        
        
        
        