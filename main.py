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
from functions          import save_settings, load_settings, print_values, fast_heatup, pre_infusion, get_IO
from classes            import BrewData, HeatingSpeedCalculator, Thermostat, TemperatureSensor, PressureMonitor, PumpRatioCalculator
from bluetooth_handler  import BLEHandler
from secrets            import ssid, password
from config             import FEATURES, PINS, MAX31865_CONFIG, TARGET_TEMPERATURES
from backflush          import run_backflush


# Turn off wifi for bluetooth stability
wlan = network.WLAN(network.STA_IF)
wlan.active(False)


# ============================================================================
# BLE COMMUNICATION
# ============================================================================

async def ble_communication(brew_data):
    
    ble = bluetooth.BLE()
    ble_handler = BLEHandler(ble)
    
    start_time = utime.ticks_ms()
    last_transmission_time = start_time
    
    
    # ============================================================================
    # BLE LOOP - BLE COMMUNICATION
    # ============================================================================
    
    while True:
        
        # Set transmission rate max 5 times in second
        if utime.ticks_diff(utime.ticks_ms(), last_transmission_time) >= 200:
            last_transmission_time = utime.ticks_ms()
        
            # Send data (boiler_temperature and pressure_bar) via BLE to the app if connected
            if ble_handler._connections:
                pressure_bar = brew_data.get_pressure()
                boiler_temperature = brew_data.get_boiler_temperature()
                mode = brew_data.get_mode()
                print(mode)
                data = {
                    'temp': boiler_temperature,
                    'pressure': pressure_bar,
                    'mode': mode
                }
                ble_handler.send_data(data)
            
        await asyncio.sleep_ms(50)
        
        
# ============================================================================
# MAIN LOOP ## RENAME!!!
# ============================================================================

async def main_loop(brew_data):
    
    # Set flag for indicating if settings are to be fetched
    new_settings_awailable = True
    
    # INITIALIZE SWITCHES AND RELAYS
    SWITCH_BREW, SWITCH_WATER, SWITCH_STEAM, RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER, LED_BREW_SWITCH, LED_WATER_SWITCH, LED_STEAM_SWITCH = get_IO(Pin, ADC, PINS)

    # INITIALIZE PT100 TEMPERATURE SENSOR WITH MAX31865
    temperature_sensor = TemperatureSensor(max31865, PINS, MAX31865_CONFIG)

    # INITIALIZE PRESSURE SENSOR HANDLER
    pressure_sensor = PressureMonitor(utime, asyncio, Pin, PINS, ADC)

    # INITIALIZE HEATING SPEED CALCULATOR
    heating_speed_calculator = HeatingSpeedCalculator(utime, asyncio)

    # LOAD SAVED SETTINGS
    load_settings(json, brew_data)

    # INITIALIZE THERMOSTAT
    thermostat = Thermostat(brew_data, TARGET_TEMPERATURES, RELAY_HEATER, temperature_sensor)

    # INITIALIZE PUMP RATIO CALCULATOR
    pump_ratio_calculator = PumpRatioCalculator(utime, asyncio)

    # INITIALIZE BREW VALUES
    pump_ratio = 0
    brew_cycle_counter = 0
    brew_pressure = FEATURES['brew_pressure_bar']
    soft_pressure_release_time = FEATURES['soft_pressure_release_time']
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
            SWITCH_BREW,
            SWITCH_WATER,
            SWITCH_STEAM,
            LED_BREW_SWITCH,
            LED_WATER_SWITCH,
            LED_STEAM_SWITCH,
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
#        brew_data.set_mode('fast_heatup')
        await fast_heatup(RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER, utime, temperature_sensor)
        
    while True:
            
        # Get brew settings from brew_data object
        if new_settings_awailable:
            brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
            new_settings_awailable = False
        
        # Read pt100 sensor temperature
        boiler_temperature = temperature_sensor.read_temperature()
                
        # Save temperature data
        brew_data.set_boiler_temperature(boiler_temperature)
        
        # Read pressure sensor
        pressure_bar = pressure_sensor.get_pressure()
        
        # Save pressure data
        brew_data.set_pressure(pressure_bar)
        
        # Calculate heating speed
        heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
        
        # Save heating speed
        brew_data.set_heating_speed(heating_speed)
            
        # RUN THERMOSTAT
        thermostat.run()
        
        # PRINT VALUES
        print_values(brew_data, temperature_sensor, heating_speed, RELAY_HEATER, RELAY_SOLENOID, RELAY_PUMP)
        
        # Set delay for resource sharing
        await asyncio.sleep_ms(50)
        
        
    # ============================================================================
    # BREW MODE - MAIN LOOP
    # ============================================================================
        
        # If brew swith is on start brewing 
        if SWITCH_BREW.value():
            
            # Set mode to brew
            brew_data.set_mode('BREW')## LATER!!! ADD MODE FOR NO PRESSURE RESISTANCE
            
            # Set heater of for safety
            RELAY_HEATER.value(0)
            
            
        # ============================================================================
        # PRE-INFUSION - BREW MODE - MAIN LOOP
        # ============================================================================
        
            if FEATURES['pre_infusion_mode_flag']:
            
                # Start pre-infusion program function
                await pre_infusion(RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER, SWITCH_BREW, utime, temperature_sensor, pressure_sensor, brew_data)#,ble_handler)
            
        
        # ============================================================================
        # BREW LOOP - BREW MODE - MAIN LOOP
        # ============================================================================
           
#            # Set mode to brewing
#             brew_data.set_mode('brew loop initialization')
            
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
                boiler_temperature = temperature_sensor.read_temperature()
                
                # Save temperature value for sharing
                brew_data.set_boiler_temperature(boiler_temperature)
                
                
                # Cycle heater of for 0.5ms and on 0.1s
                if (elapsed_ms % 150) < 100:
                    
                    # Set heater relay off
                    RELAY_HEATER.value(0)
                
                else:
                    # Set heater relay on
                    RELAY_HEATER.value(1)
                
                
                # ===== PRESSURE ===== #
                
                # Get pressure
                pressure_bar = pressure_sensor.get_pressure()
                
                # Save pressure value for sharing
                brew_data.set_pressure(pressure_bar)
                
                # If pressure is under brew pressure cycling range, keep pump on
                if pressure_bar < brew_pressure -1:
                    RELAY_PUMP.value(1)
                    pump_ratio_calculator.set_pump_on()
                
                # If pressure is on target cycling range, use short pulses to minimize pressure spikes
                elif pressure_bar < brew_pressure:
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
            if pressure_sensor.get_pressure() >= 2: # LATER: >= FEATURES['min_soft_pressure_release_trigger_pressure']
#                brew_data.set_mode('soft pressure release')
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
                pressure_bar = pressure_sensor.get_pressure()
                brew_data.set_pressure(pressure_bar)
                
                # Cycle solenoid for pressure to release 
                while pressure_bar > 1.5:
                    print("Pressure: " + str(pressure_bar) + " bar")
                    await asyncio.sleep(0.5)
                    RELAY_SOLENOID.value(1)
                    await asyncio.sleep(0.5)
                    RELAY_SOLENOID.value(0)
                    pressure_bar = pressure_sensor.get_pressure()
                    
                    
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
            
# ============================================================================
# ASYNC HANDLING
# ============================================================================

# MUUTETAAN SIISTIMMÄKSI !!!!!!!!
SWITCH_BREW, SWITCH_WATER, SWITCH_STEAM, RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER, LED_BREW_SWITCH, LED_WATER_SWITCH, LED_STEAM_SWITCH = get_IO(Pin, ADC, PINS)

# INITIALIZE MAIN DATA HANDLER
brew_data = BrewData(SWITCH_BREW, SWITCH_STEAM, SWITCH_WATER)

async def async_main():
    await asyncio.gather(ble_communication(brew_data), main_loop(brew_data))
asyncio.run(async_main())