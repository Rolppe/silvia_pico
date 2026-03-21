import utime
from machine import Pin, ADC
import adafruit_max31865 as max31865


# 9 bar 63.5g/min 30%
# 9bar 98.5g/min 42%

# Import functions, classes and data
from functions import print_values
from classes import BrewData, HeatingSpeedCalculator, Thermostat, Sensor, PressureMonitor

# Set the input pins for switches
switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN) 
switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)
switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)


# Set the output pins for relays
relay_heater = Pin(11, Pin.OUT, value = 0)
relay_solenoid = Pin(12, Pin.OUT, value = 0) 
relay_pump = Pin(13, Pin.OUT, value = 0)


pump_cycling_time_ms = 88 # 1Hz = 17ms
pump_on_time_ratio = 0.4
#include_pressure = False
include_heater = False
pressure_buildup_bar = 0
test_pressure = 9

pump_on_time = int(pump_cycling_time_ms * pump_on_time_ratio)



# Initialize max31865 (temperature sensort pt100)
sensor = Sensor(max31865, Pin)

# Create data and state store object 
brew_data = BrewData(switch_brew, switch_steam, switch_water)

# Create heat speed calculating object
heating_speed_calculator = HeatingSpeedCalculator(utime)

# Create class for pressure_barmonitoring
pressure_monitor = PressureMonitor(Pin, ADC, utime)

# Initialize thermostat
thermostat = Thermostat()




while True:
    # Read pt100 sensor temperature
    boiler_temperature = sensor.read_temperature()
    
    # Save temperature data
    brew_data.set_boiler_temperature(boiler_temperature)

    # Calculate heating speed
    heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
    
    # Save heating speed
    brew_data.set_heating_speed(heating_speed)
    
    ### THERMOSTAT ###     
    if include_heater:
        thermostat.run(brew_data, switch_steam, relay_heater)
    
    ### PRINT VALUES ###
    print_values(brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump)
    
    ### TEST ###
    if switch_brew.value():
        
#         # Build up pressure
#         relay_pump.value(1)
#         relay_solenoid.value(1)
#         while pressure_monitor.get_pressure() < pressure_buildup_bar:   
#             utime.sleep(0.1)
#         relay_pump.value(0)
        
        start_time = utime.ticks_ms()
        last_print_time = start_time
        relay_solenoid.value(1)
        pump_ratio_list = []
        pump_on_time_list = []
        pump_off_time_list = []
        pump_bypass_flag = False
        
        
        ## TEST LOOP ##
        # Run test as long as brew switch is on
        while(switch_brew.value()):
            
            cycle_start_time = utime.ticks_ms()
            total_elapsed_ms = utime.ticks_diff(utime.ticks_ms(), start_time)

            pressure_bar = pressure_monitor.get_pressure()
        
            # Print pressure_bar and pump on ratio
            if utime.ticks_diff(utime.ticks_ms(), last_print_time) >= 1000:
                pump_on_ratio = round((sum(pump_on_time_list) / (sum(pump_on_time_list) + sum(pump_off_time_list))*100))
                pump_on_time_list.clear()
                pump_off_time_list.clear()
                print("pump ratio: " + str(pump_on_ratio)+" %")
                print("pressure: " +str(pressure_bar) +" bar")
                last_print_time = utime.ticks_ms()
                
            # Maintain test pressure
            if pressure_bar < test_pressure:
                pump_bypass_flag = False
                pump_start_time = utime.ticks_ms()
                while pressure_monitor.get_pressure() < test_pressure and utime.ticks_diff(utime.ticks_ms(), pump_start_time) < 1000:
                    relay_pump.value(1)
                relay_pump.value(0)
            
                # Calculate pump on time
                pump_on_time = utime.ticks_diff(utime.ticks_ms(), pump_start_time)
                pump_on_time_list.append(pump_on_time)
            
            else:
                pump_bypass_flag = True
                pump_on_time_list.append(0.0)
                pump_on_time = 0.0
                
            if include_heater:
                # cycle heater off 100 ms, on 50 ms / 150 ms
                if (total_elapsed_ms % 150) < 100:
                    # Set heater relay off
                    relay_heater.value(0)
                else:
                    # Set heater relay on
                    relay_heater.value(1)
            
            utime.sleep_ms(1)
            cycle_time_ms = utime.ticks_diff(utime.ticks_ms(), cycle_start_time)
            pump_off_time = cycle_time_ms - pump_on_time
            pump_off_time_list.append(pump_off_time)

    # Set solenoid off
    relay_solenoid.value(0)
    utime.sleep_ms(1)
        
        
        
        
        
        
        