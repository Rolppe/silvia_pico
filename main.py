# IMPORT LIBRARIES
import utime
import json
import socket
import network
import select
import bluetooth
import time
import adafruit_max31865  as max31865
import asyncio

# IMPORT FUNCTIONS, CLASSES AND CONFIGURATIONS
from machine            import Pin, ADC
from micropython        import const
from functions          import save_settings, load_settings, print_values, fast_heatup, pre_infusion
from classes            import BrewData, HeatingSpeedCalculator, Thermostat, TemperatureSensor, PressureSensor, PumpRatioCalculator
from bluetooth_handler  import BLEHandler
from secrets            import ssid, password
from preset             import FEATURES, PINS, MAX31865_CONFIG, TARGET_TEMPERATURES
from backflush          import run_backflush


# Turn off wifi for bluetooth stability
wlan = network.WLAN(network.STA_IF)
wlan.active(False)


# ============================================================================
# BLE COMMUNICATION
# ============================================================================
async def ble_communication(brew_data):
    ble = bluetooth.BLE()
    ble_handler = BLEHandler(ble, brew_data)

    last_transmission_time = utime.ticks_ms()

    while True:
        # Lähetetään data max 5 kertaa sekunnissa
        if utime.ticks_diff(utime.ticks_ms(), last_transmission_time) >= 200:
            last_transmission_time = utime.ticks_ms()
            ble_handler.run_transmission()

        # Mainostus disconnectin jälkeen
        ble_handler.advertise_if_needed()

        await asyncio.sleep_ms(100)
        
# async def ble_communication(brew_data):
#     
#     ble         = bluetooth.BLE()
#     ble_handler = BLEHandler(ble, brew_data)
#     
#     start_time  = utime.ticks_ms()
#     last_transmission_time = start_time
    
    
    # ============================================================================
    # BLE LOOP - BLE COMMUNICATION
    # ============================================================================
#     
#     while True:
#          # Set transmission rate max 5 times in second
#         if utime.ticks_diff(utime.ticks_ms(), last_transmission_time) >= 200:
#             last_transmission_time = utime.ticks_ms()
#             ble_handler.run_transmission()
#         await asyncio.sleep_ms(50)
        
        
# ============================================================================
# MAIN LOOP ## RENAME!!!
# ============================================================================

async def main_loop(brew_data):
    
    # Set flag for indicating if settings are to be fetched
    brew_data.set_setting_changed()
    
    # Initialize switches, leds and relays
    LED_SWITCH_BREW, LED_SWITCH_WATER, LED_SWITCH_STEAM = brew_data.get_leds()
    SWITCH_BREW, SWITCH_WATER, SWITCH_STEAM             = brew_data.get_switches()
    RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER            = brew_data.get_relays()
    

    # LOAD SAVED SETTINGS
    load_settings(json, brew_data)

    # INITIALIZE THERMOSTAT
    thermostat = Thermostat(brew_data, TARGET_TEMPERATURES, RELAY_HEATER, temperature_sensor)

    # INITIALIZE PUMP RATIO CALCULATOR
    pump_ratio_calculator = PumpRatioCalculator(utime, asyncio)

    # INITIALIZE BREW VALUES
    pump_ratio                 = 0
    brew_cycle_counter         = 0
    brew_pressure_reached_flag = False
    
    
    # ============================================================================
    # BACKFLUSH -  MAIN LOOP
    # ============================================================================

    # If brew Switch is on at boot start backflush cleaning program
    if SWITCH_BREW.value():
        await run_backflush(
            RELAY_PUMP,   
            RELAY_SOLENOID,
            RELAY_HEATER,
            temperature_sensor,
            pressure_sensor,
            brew_data,
            thermostat
        )
        
        
    # ============================================================================
    # FAST HEATUP - MAIN LOOP
    # ============================================================================
    
    # If fast heatup mode is on, start fast heatup program
    if FEATURES['fast_heatup_mode_flag']:
        brew_data.set_mode('fast_heatup')
        await fast_heatup(RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER, utime, temperature_sensor)
        
    # ============================================================================
    # MAIN LOOP - MAIN LOOP
    # ============================================================================
        
    while True:

        
        # Get brew settings from brew_data object
        if brew_data.get_setting_changed():
            save_settings(brew_data, json)
            
        # Get boiler  temperature
        boiler_temperature = brew_data.get_boiler_temperature()
        
        # Read pressure sensor
        pressure = brew_data.get_pressure()
        
        # Save heating speed
        heating_speed = brew_data.get_heating_speed()
            
        # RUN THERMOSTAT
        thermostat.run()
         
        # PRINT VALUES
        if FEATURES['print_values_flag']:
            print_values(brew_data)
        
        # Set delay for resource sharing
        await asyncio.sleep_ms(50)
        
        
    # ============================================================================
    # BREW MODE - MAIN LOOP
    # ============================================================================
        
        # If brew swith is on start brewing 
        if SWITCH_BREW.value():
            
            # Set mode to brew
            brew_data.set_mode('BREW')
            
            # Set heater of for safety
            RELAY_HEATER.value(0)
            
            
        # ============================================================================
        # PRE-INFUSION - BREW MODE - MAIN LOOP
        # ============================================================================
        
            if brew_data.get_pre_infusion_mode():
            
                # Start pre-infusion program function
                await pre_infusion(brew_data, utime, asyncio)
            
        
        # ============================================================================
        # BREW LOOP - BREW MODE - MAIN LOOP
        # ============================================================================
           
           # Set mode to brewing
            brew_data.set_mode('brew loop initialization')
            
            # Initialize brew
            pump_ratio_calculator.start()
            
            # Set solenoid an on for brewing
            RELAY_SOLENOID.value(1)
            
            # Set pump on for brewing
            RELAY_PUMP.value(1)
            
            start_time = utime.ticks_ms()
            last_print_time = start_time
            last_pump_ratio_time = start_time
                
            # Set mode for brew loop
            brew_data.set_mode('brew loop')

            # Run brew cycle with heat cycling as long as brew switch is on
            while(SWITCH_BREW.value()):

                
                # Initialize timer
                elapsed_ms = utime.ticks_diff(utime.ticks_ms(), start_time)
                
                
                # ===== HEATER ===== #
                
                # Read pt100 sensor temperature
                boiler_temperature = brew_data.get_boiler_temperature()
                
                # Cycle heater of for 0.5ms and on 0.1s
                if (elapsed_ms % 150) < 100:
                    
                    # Set heater relay off
                    RELAY_HEATER.value(0)
                
                else:
                    # Set heater relay on
                    RELAY_HEATER.value(1)
                
                
                # ===== PRESSURE ===== #
                
                # Get pressure
                pressure = brew_data.get_pressure()
                
                brew_pressure = brew_data.get_brew_pressure()
                
                # If pressure is under brew pressure cycling range, keep pump on
                if pressure < brew_pressure -1:
                    RELAY_PUMP.value(1)
                    pump_ratio_calculator.set_pump_on()
                
                # If pressure is on target cycling range, use short pulses to minimize pressure spikes
                elif pressure < brew_pressure:
                    brew_pressure_reached_flag = True
                    RELAY_PUMP.value(1)
                    pump_ratio_calculator.set_pump_on()
                    await asyncio.sleep(0.035)        #utime.sleep(0.035)
                    RELAY_PUMP.value(0)
                    pump_ratio_calculator.set_pump_off()
                
                else:
                    RELAY_PUMP.value(0)
                    pump_ratio_calculator.set_pump_off()
                    
                if utime.ticks_diff(utime.ticks_ms(), last_pump_ratio_time) >= 2000:
                    pump_ratio = round(pump_ratio_calculator.get_ratio(), 2)
                    last_pump_ratio_time = utime.ticks_ms()
                               
                
                # Add pause to share resources
                await asyncio.sleep_ms(50)
            
            
        # ============================================================================
        # PRESSURE SOFT RELEASE - BREW MODE - MAIN LOOP
        # ============================================================================
                        
            # Set pump off
            RELAY_PUMP.value(0)
            
            # Check pressure
            if brew_data.get_pressure() >= 2: # LATER: >= FEATURES['min_soft_pressure_release_trigger_pressure']
                brew_data.set_mode('soft pressure release')
                soft_pressure_release_time = brew_data.get_pressure_soft_release_time()
                for x in range(soft_pressure_release_time): # LATER ADD BETTER TIMING
                    for y in range(5):
                        await asyncio.sleep(0.2)
                
            
        # ============================================================================
        # PRESSURE DRAIN - BREW MODE - MAIN LOOP
        # ============================================================================

            # Set soleinoid off
            RELAY_SOLENOID.value(0)
            if FEATURES['after_brew_pressure_drain_flag']:
                brew_data.set_mode('after brew pressure drain')
                pressure = brew_data.get_pressure()
                
                # Cycle solenoid for pressure to release 
                while pressure > 1.5:
                    await asyncio.sleep(0.5)
                    RELAY_SOLENOID.value(1)
                    await asyncio.sleep(0.5)
                    RELAY_SOLENOID.value(0)
                    pressure = brew_data.get_pressure()
                    
                    
    # ============================================================================
    # HOT WATER MODE - MAIN LOOP
    # ============================================================================

        # If water switch is on
        if SWITCH_WATER.value():
            
            # Set mode to 'water'
            brew_data.set_mode('WATER')
            
            # Set on boiler heater
            RELAY_HEATER.value(1)
            
            # set on water
            RELAY_PUMP.value(1)
            
            # Run cycle for hot water as long as hot water switch is on
            while (SWITCH_WATER.value()):
                await asyncio.sleep_ms(50)
                
            # Set heater and pump relays off after hot water kloop
            RELAY_PUMP.value(0)
            RELAY_HEATER.value(0)
           
    # ============================================================================
    # STEAM MODE - MAIN LOOP
    # ============================================================================
    
        if SWITCH_STEAM.value():
            
            # Set mode to steam
            brew_data.set_mode('STEAM')
        
        else:
    
            # Set mode to IDLE
            brew_data.set_mode('IDLE')
            

# INITIALIZE PT100 TEMPERATURE SENSOR WITH MAX31865
temperature_sensor = TemperatureSensor(max31865, PINS, MAX31865_CONFIG)

# INITIALIZE PRESSURE SENSOR HANDLER
pressure_sensor = PressureSensor(utime, asyncio, Pin, PINS, ADC)

# INITIALIZE HEATING SPEED CALCULATOR
heating_speed_calculator = HeatingSpeedCalculator(utime, asyncio)
            
# ============================================================================
# ASYNC HANDLING
# ============================================================================


# INITIALIZE MAIN DATA HANDLER
brew_data = BrewData(
    Pin,
    ADC,
    PINS,
    TARGET_TEMPERATURES,
    FEATURES,
    heating_speed_calculator,
    temperature_sensor,
    pressure_sensor
)
async def async_main():
    await asyncio.gather(ble_communication(brew_data), main_loop(brew_data))
asyncio.run(async_main())