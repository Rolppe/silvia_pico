# IMPORT LIBRARIES
import utime
import json
import socket
import network
import select
import bluetooth
import time
import adafruit_max31865  as max31865


# IMPORT FUNCTIONS, CLASSES AND CONFIGURATIONS
from machine            import Pin, ADC
from micropython        import const
from functions          import save_settings, load_settings, print_values, fast_heatup, pre_infusion, get_IO
from classes            import BrewData, HeatingSpeedCalculator, Thermostat, TemperatureSensor, PressureMonitor
from bluetooth_handler  import BLEHandler
from secrets            import ssid, password
from config             import FEATURES, PINS, MAX31865_CONFIG

# Turn off wifi for bluetooth stability
wlan = network.WLAN(network.STA_IF)
wlan.active(False)

# INITIALIZE SWITCHES AND RELAYS
SWITCH_BREW, SWITCH_WATER, SWITCH_STEAM, RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER = get_IO(Pin, ADC, PINS)

# INITIALIZE PT100 TEMPERATURE SENSOR WITH MAX31865
temperature_sensor = TemperatureSensor(max31865, PINS, MAX31865_CONFIG)

# INITIALIZE PRESSURE SENSOR HANDLER
pressure_sensor = PressureMonitor(utime, Pin, PINS, ADC)

# INITIALIZE MAIN DATA HANDLER
brew_data = BrewData(SWITCH_BREW, SWITCH_STEAM, SWITCH_WATER)

# INITIALIZE HEATING SPEED CALCULATOR
heating_speed_calculator = HeatingSpeedCalculator(utime)

# LOAD SAVED SETTINGS
load_settings(json, brew_data)

# INITIALIZE THERMOSTAT
thermostat = Thermostat()

# INITIALIZE BLE
ble = bluetooth.BLE()
ble_handler = BLEHandler(ble)

# Set flag for indicating if settings are to be fetched
api_flag = True

# If steam switch is off and fast heatup mode is on, set mode for fast heatup and fill boiler
if FEATURES['fast_heatup_mode_flag']:
    brew_data.set_mode('fast_heatup')
    fast_heatup(RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER, utime, sensor)


# ============================================================================
# MAIN LOOP
# ============================================================================

while True:
    
    # Get brew settings from brew_data object
    if api_flag:
        brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
        api_flag = False
        
    # Read pt100 sensor temperature
    boiler_temperature = temperature_sensor.read_temperature()
    
    # Save temperature data
    brew_data.set_boiler_temperature(boiler_temperature)
    
    # Calculate heating speed
    heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
    
    # Save heating speed
    brew_data.set_heating_speed(heating_speed)
        
    # RUN THERMOSTAT
    thermostat.run(brew_data, SWITCH_STEAM, RELAY_HEATER)
    
    # PRINT VALUES
    print_values(brew_data, temperature_sensor, heating_speed, RELAY_HEATER, RELAY_SOLENOID, RELAY_PUMP)
    
    
# ============================================================================
# BREW MODE
# ============================================================================
    
    # If brew swith is on start brewing
    if SWITCH_BREW.value():
        
        ## Pre-infusion ##
        if FEATURES['pre_infusion_mode_flag']:
            
            # Set heater of for safety
            RELAY_HEATER.value(0)
            
            #If brew switch is being put of within half second, push water and skip preinfusion
            utime.sleep(0.5)
            if not SWITCH_BREW.value():
                RELAY_SOLENOID.value(1)
                RELAY_PUMP.value(1)
                utime.sleep(1)
                RELAY_PUMP.value(0)
                RELAY_SOLENOID.value(0)
                
            else:
                # Set mode to pre-infusion
                brew_data.set_mode('pre-infusion')
                
                # Start pre-infusion program function
                pre_infusion(RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER, SWITCH_BREW, utime, temperature_sensor, pressure_sensor,ble_handler)
        
        # Set mode to brewing
        brew_data.set_mode('brew')
        
        # Initialize counter for brewing cycles
        brew_cycle_counter = 0
        
        # Set solenoid an on for brewing
        RELAY_SOLENOID.value(1)
        
        # Set pump on for brewing
        RELAY_PUMP.value(1)
        start_time = utime.ticks_ms()
        last_print_time = start_time
        
        
# ============================================================================
# BREW LOOP
# ============================================================================
        brew_pressure = FEATURES['brew_pressure_bar']
        soft_pressure_release_time = FEATURES['soft_pressure_release_time']
        
        # Run brew cycle with heat cycling as long as brew switch is on
        while(SWITCH_BREW.value()):
            elapsed_ms = utime.ticks_diff(utime.ticks_ms(), start_time)
            current_seconds = elapsed_ms // 1000
            
            # ===== HEATER =====
            # Read pt100 sensor temperature
            boiler_temperature = temperature_sensor.read_temperature()
            
            # cycle heater of for 0.5ms and on 0.1s
            if (elapsed_ms % 150) < 100:
                # Set heater relay off
                RELAY_HEATER.value(0)
            
            else:
                # Set heater relay on
                RELAY_HEATER.value(1)
            
            # ===== PRESSURE =====
            # Get pressure
            pressure_bar = pressure_sensor.get_pressure()
            
            # If pressure is is low and and not in range keep pump on
            if pressure_bar < brew_pressure -1:
                RELAY_PUMP.value(1)
            
            # if pressure is close to target use short pulses to minimize pressure spikes
            elif pressure_bar < brew_pressure:
                RELAY_PUMP.value(1)
                utime.sleep(0.005)
                RELAY_PUMP.value(0)
            
            else:
                RELAY_PUMP.value(0)
                
            # ===== BLUETOOTH =====
            if ble_handler._connections:
                data = {
                    'temp': boiler_temperature,
                    'pressure': pressure_bar
                }
                ble_handler.send_data(data)
            
            # Print pressure_bar4 times in second
            if utime.ticks_diff(utime.ticks_ms(), last_print_time) >= 250:
                print("pressure: " +str(pressure_bar) +" bar")
                last_print_time = utime.ticks_ms()
        
        
        # ===== END PROCEDURES =====
        # Set pump off
        RELAY_PUMP.value(0)
        
        # ===== PRESSURE SOFT RELEASE =====
        ## slow pressure release ##
        utime.sleep(soft_pressure_release_time)
        
        # ===== PRESSURE DRAIN =====
        # Set soleinoid off
        RELAY_SOLENOID.value(0)
        if FEATURES['after_brew_pressure_drain_flag']:
            pressure_bar = pressure_sensor.get_pressure()
            while pressure_bar > 1.5:
                print("Pressure: " + str(pressure_bar) + " bar")
                utime.sleep(0.5)
                RELAY_SOLENOID.value(1)
                utime.sleep(0.5)
                RELAY_SOLENOID.value(0)
                pressure_bar = pressure_sensor.get_pressure()
                
                
# ============================================================================
# HOT WATER MODE
# ============================================================================

    # If water switch is on
    if SWITCH_WATER.value():
        # Set mode to 'water'
        brew_data.set_mode('water')
        # Set on boiler heater
        RELAY_HEATER.value(1)
        # set on water
        RELAY_PUMP.value(1)
        # Run cycle for hot water as long as hot water switch is on
        while (SWITCH_WATER.value()):
            utime.sleep(0.1)
        # Set heater and pump relays off after hot water kloop
        RELAY_PUMP.value(0)
        RELAY_HEATER.value(0)
       
# ============================================================================
# MAIN LOOP BLE COMMUNICATION
# ============================================================================
    
    # Send data (boiler_temperature and pressure_bar) via BLE to the app if connected
    if ble_handler._connections:
        pressure_bar = pressure_sensor.get_pressure()  # Read pressure again if needed
        data = {
            'temp': boiler_temperature,
            'pressure': pressure_bar
        }
        ble_handler.send_data(data)
    time.sleep(0.1)  # Short delay in the loop to save resources