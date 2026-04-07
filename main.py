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


# ============================================================================
# INITIALIZATION
# ============================================================================

# Turn off wifi for bluetooth stability
wlan = network.WLAN(network.STA_IF)
wlan.active(False)

# INITIALIZE PT100 TEMPERATURE SENSOR WITH MAX31865
temperature_sensor = TemperatureSensor(max31865, PINS, MAX31865_CONFIG)

# INITIALIZE PRESSURE SENSOR HANDLER
pressure_sensor = PressureSensor(utime, asyncio, Pin, PINS, ADC)

# INITIALIZE HEATING SPEED CALCULATOR
heating_speed_calculator = HeatingSpeedCalculator(utime, asyncio)
            
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

        await asyncio.sleep_ms(30)
        
        
# ============================================================================
# LOCAL PROGRAM
# ============================================================================

async def local_program(brew_data):
    
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
    pump_ratio_calculator.start(initial_pump_on=False)
    
    
    # INITIALIZE BREW VALUES
    brew_pressure_reached_flag = False
    
    
    # ============================================================================
    # BACKFLUSH -  LOCAL PROGRAM
    # ============================================================================

    # If brew Switch is on at boot start backflush cleaning program
    if SWITCH_BREW.value():
        await run_backflush(brew_data, thermostat)
        
        
    # ============================================================================
    # FAST HEATUP - LOCAL PROGRAM
    # ============================================================================
    
    # If fast heatup mode is on, start fast heatup program
    if brew_data.get_fast_heatup_mode() and brew_data.get_boiler_temperature() < 50:
        brew_data.set_mode('fast_heatup')
        await fast_heatup(utime, brew_data)
        
        
    # ============================================================================
    # MAIN LOOP - LOCAL PROGRAM
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
        await asyncio.sleep_ms(5)
        
        
        # ============================================================================
        # BREW MODE - LOCAL PROGRAM
        # ============================================================================
        
        # If brew swith is on start brewing 
        if SWITCH_BREW.value():
            
            # Set mode to brew
            brew_data.set_mode('BREW')
            await asyncio.sleep_ms(50)
            
            # Set heater of for safety
            RELAY_HEATER.value(0)
            
            # Initialize brew timer and pump ratio calculator
            #pump_ratio_calculator.start()
            #pump_ratio_calculator.set_pump_off()

            start_time = utime.ticks_ms()
            last_print_time = start_time
            
            
            # ============================================================================
            # PRE-INFUSION - BREW MODE - LOCAL PROGRAM
            # ============================================================================
        
            if brew_data.get_pre_infusion_mode():
            
                # Start pre-infusion program function
                await pre_infusion(brew_data, utime, asyncio, pump_ratio_calculator)
            
        
            # ============================================================================
            # BREW LOOP - BREW MODE - LOCAL PROGRAM
            # ============================================================================
           
           # Set mode to brewing
            brew_data.set_mode('brew loop initialization')
        
            last_pump_ratio_time = utime.ticks_ms()

            
            # Set solenoid an on for brewing
            RELAY_SOLENOID.value(1)
            
            # Set pump on for brewing
            RELAY_PUMP.value(1)
                
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
                
                
                # ===== PRESSURE + PUMP ===== #
                
                pressure = brew_data.get_pressure()
                brew_pressure = brew_data.get_brew_pressure()
                

                if pressure < brew_pressure - 1:
                    RELAY_PUMP.value(1)
                    pump_ratio_calculator.set_pump_on()
                    
                elif pressure < brew_pressure:
                    brew_pressure_reached_flag = True
                    RELAY_PUMP.value(1)
                    pump_ratio_calculator.set_pump_on()
                    await asyncio.sleep(0.035)
                    RELAY_PUMP.value(0)
                    pump_ratio_calculator.set_pump_off()
                        
                else:
                    RELAY_PUMP.value(0)
                    pump_ratio_calculator.set_pump_off()
        
 
                if utime.ticks_diff(utime.ticks_ms(), last_pump_ratio_time) >= 1000:
                    pump_ratio = pump_ratio_calculator.get_ratio()
                    brew_data.set_pump_ratio(pump_ratio)
                    last_pump_ratio_time = utime.ticks_ms()
                               

                # Add pause to share resources
                await asyncio.sleep_ms(50)
            
            
            # ============================================================================
            # PRESSURE SOFT RELEASE - BREW MODE - LOCAL PROGRAM
            # ============================================================================
                        
            # Set pump off
            RELAY_PUMP.value(0)
            brew_data.set_pump_ratio(0)
            
            if brew_data.get_pressure() >= brew_data.get_soft_pressure_release_arming_pressure() and brew_data.get_pressure_soft_release_mode():
                brew_data.set_mode('soft pressure release')
                soft_pressure_release_time = brew_data.get_pressure_soft_release_time()
                print("soft release time: " + str(soft_pressure_release_time))

                for x in range(soft_pressure_release_time):
                    await asyncio.sleep(1)
                
            
            # ============================================================================
            # PRESSURE DRAIN - BREW MODE - LOCAL PROGRAM
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
        # HOT WATER MODE - LOCAL PROGRAM
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
        # STEAM MODE - LOCAL PROGRAM
        # ============================================================================
    
        if SWITCH_STEAM.value():
            brew_data.set_mode('STEAM')
            
        else:
            brew_data.set_mode('IDLE')


# ============================================================================
# ASYNC HANDLING
# ============================================================================

async def async_main():
    await asyncio.gather(ble_communication(brew_data), local_program(brew_data))
asyncio.run(async_main())



