# Import libraries
import utime
import json
from machine import Pin, ADC
import adafruit_max31865 as max31865
import socket
import network
import uasyncio as asyncio

# Import functions, classes and data
from api_functions import set_station,  response_HTML, response_complete_HTML, parse_request
from functions import save_settings, load_settings, print_values, fast_heatup, pre_infusion
from classes import BrewData, HeatingSpeedCalculator, Thermostat, Sensor, PressureMonitor
from secrets import ssid, password

# Set the input pins for switches
switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN)
switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)
switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)

# Set the output pins for relays
relay_pump = Pin(11, Pin.OUT, value=0)
relay_solenoid = Pin(12, Pin.OUT, value=0)
relay_heater = Pin(13, Pin.OUT, value=0)

######## Developement Settings ###########################

fast_heatup_mode = False
pre_infusion_mode = True
after_brew_pressure_drain = False

pre_infusion_pressure_buildup_time = 0
pre_infusion_time = 5
soft_pressure_release_time = 0

brew_pressure = 8

##########################################################

# Initialize max31865 (temperature sensort pt100)
sensor = Sensor(max31865, Pin)

# Create data and state store object
brew_data = BrewData(switch_brew, switch_steam, switch_water)

# Create heat speed calculating object
heating_speed_calculator = HeatingSpeedCalculator(utime)

# Load settings (to brew_data object)
load_settings(json, brew_data)

# Create class for pressure_barmonitoring
pressure_monitor = PressureMonitor(Pin, ADC, utime)

# Connect to Wifi
set_station(utime, network, ssid, password)

# Set flag for indicating if settings are to be fetched
api_flag = True

async def handle_client(reader, writer):
    try:
        request = await reader.read(1024)
        request_str = str(request)

        if 'POST' in request_str:
            parse_request(brew_data, request_str, save_settings, json)
            response = response_complete_HTML()
        else:
            response = response_HTML(brew_data)

        writer.write(response.encode())
        await writer.drain()
    except Exception as e:
        print('Error in API handler:', e)
    finally:
        writer.close()
        await writer.wait_closed()

async def api_server():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 80)
    await server.serve_forever()

# If steam switch is off and fast heatup mode is on, set mode for fast heatup and fill boiler
if switch_steam.value() and fast_heatup_mode:
    brew_data.set_mode('fast_heatup')
    fast_heatup(relay_pump, relay_solenoid, relay_heater, utime, sensor)

# Initialize thermostat
thermostat = Thermostat()

async def main_loop():
    global api_flag
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

            ## Pre-infusion ##
            if pre_infusion_mode:

                # Set heater of for safety
                relay_heater.value(0)

                #If brew switch is being put of within half second, push water and skip preinfusion
                await asyncio.sleep(0.5)

                if not switch_brew.value():
                    relay_solenoid.value(1)
                    relay_pump.value(1)
                    await asyncio.sleep(1)
                    relay_pump.value(0)
                    relay_solenoid.value(0)

                else:
                    # Set mode to pre-infusion
                    brew_data.set_mode('pre-infusion')

                    # Start pre-infusion program function
                    pre_infusion(relay_pump, relay_solenoid, relay_heater, switch_brew, utime, sensor, pressure_monitor)

            # Set mode to brewing
            brew_data.set_mode('brew')

            # Initialize counter for brewing cycles
            brew_cycle_counter = 0

            # Set solenoid an on for brewing
            relay_solenoid.value(1)

            # Set pump on for brewing
            relay_pump.value(1)

            start_time = utime.ticks_ms()
            last_print_time = start_time

            ## BREW LOOP ##
            # Run brew cycle with heat cycling as long as brew switch is on
            while switch_brew.value():

                elapsed_ms = utime.ticks_diff(utime.ticks_ms(), start_time)
                current_seconds = elapsed_ms // 1000

                # cycle heater of for 0.5ms and on 0.1s
                if (elapsed_ms % 150) < 100:
                    # Set heater relay off
                    relay_heater.value(0)
                else:
                    # Set heater relay on
                    relay_heater.value(1)

                # Get pressure
                pressure_bar = pressure_monitor.get_pressure()


    #           # Get flow
    #            flow_ml_min =  -4.03 * pressure_bar **2 + 14.15 * pressure_bar + 658.81



                # Print pressure_bar4 times in second
                if utime.ticks_diff(utime.ticks_ms(), last_print_time) >= 250:
                    print("pressure: " +str(pressure_bar) +" bar")
                    last_print_time = utime.ticks_ms()


                if pressure_bar < brew_pressure -1:
                    relay_pump.value(1)
                elif pressure_bar < brew_pressure:
                    relay_pump.value(1)
                    await asyncio.sleep(0.005)
                    relay_pump.value(0)
                else:
                    relay_pump.value(0)

                await asyncio.sleep(0.01)  # Allow other tasks to run

            # Set pump off
            relay_pump.value(0)

            ## SLOW pressure_barRELEASE ##
            await asyncio.sleep(soft_pressure_release_time)

            # Set soleinoid off
            relay_solenoid.value(0)

            if after_brew_pressure_drain:
                pressure_bar = pressure_monitor.get_pressure()
                while pressure_bar > 1.5:
                    print("Pressure: " + str(pressure_bar) + " bar")
                    await asyncio.sleep(0.5)
                    relay_solenoid.value(1)
                    await asyncio.sleep(0.5)
                    relay_solenoid.value(0)
                    pressure_bar = pressure_monitor.get_pressure()


        ### HOT WATER MODE ###

        # If water switch is on
        if switch_water.value():

            ## HOT WATER MODE ##
            # Set mode to 'water'
            brew_data.set_mode('water')

            # Set on boiler heater
            relay_heater.value(1)

            # set on water
            relay_pump.value(1)

            # Run cycle for hot water as long as hot water switch is on
            while switch_water.value():
                await asyncio.sleep(0.1)

            # Set heater and pump relays off after hot water loop
            relay_pump.value(0)
            relay_heater.value(0)

        await asyncio.sleep(0.01)  # Allow API task to run

async def main():
    asyncio.create_task(api_server())
    await main_loop()

asyncio.run(main())