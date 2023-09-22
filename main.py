import time
import _thread
import utime
import json
from machine import Pin
import adafruit_max31865 as max31865
import socket
import network

from functions import save_settings, load_settings, set_station, set_socket,  response_HTML, print_values
from classes import LockPrinter, BrewData, VirtualBoiler, HeatingSpeedCalculator, Sensor
from secrets import ssid, password


# --- UI ---
def _threadui():

    # Create WiFi connection
    set_station(time, network, ssid, password, lock_printer)
    
    # Create Socket
    s = set_socket(socket, time, lock_printer)
    
# --- MAIN LOOP --- 
    while True:
        
        # Get the state of the switches
        brew_switch_state, steam_switch_state, water_switch_state = brew_data.get_switches_state()
        
        Set switches changed flag to False
        switch_changed = False
        
        # Accept incoming communications
        try:
            conn, addr = s.accept()
            
        # Handle errors
        except Exception as e:
            # Print an error message
            lock_printer("Virhe yhteyden käsittelyssä:", str(e))
            
        # Read request and transform it to string
        request = conn.recv(1024)
        request = str(request)

        # From request: search for brew_temperature for numeric values
        if 'GET /set_value?brew_temperature=' in request:
            
            # Parse numeric values from request string
            brew_temperature = request.split('GET /set_value?brew_temperature=')[1].split('&')[0]
            steam_temperature = request.split('GET /set_value?brew_temperature=')[1].split('&')[1].split('=')[1]
            pre_infusion_time = request.split('GET /set_value?brew_temperature=')[1].split('&')[2].split('=')[1]
            pre_heat_time = request.split('GET /set_value?brew_temperature=')[1].split('&')[3].split('=')[1]
            pressure_soft_release_time = request.split('GET /set_value?brew_temperature=')[1].split('&')[4].split('=')[1]

            # Transform values to integer
            brew_temperature = int(brew_temperature)
            pre_infusion_time = int(pre_infusion_time)
            steam_temperature = int(steam_temperature)
            pressure_soft_release_time = int(pressure_soft_release_time)
            pre_heat_time = int(pre_heat_time)
            
            # Store values to brew_data object
            brew_data.set_settings(brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time)
            
            # Store values to file
            save_settings(brew_data, json)
                    
        # Check if brew switch is treu in the request
        if 'GET /set_value?brew_switch=true' in request:
            brew_switch_state = not brew_switch_state
            switch_changed = True

        # Check if steam switch is true in the request
        if 'GET /set_value?steam_switch=true' in request:
            steam_switch_state = not steam_switch_state
            switch_changed = True

        # Check if water switch is true in the request
        if 'GET /set_value?water_switch=true' in request:
            water_switch_state = not water_switch_state
            switch_changed = True
        
        # If button has pressed, store state of the switches to brew_data object
        if switch_changed:
            brew_data.set_switches_state(brew_switch_state, steam_switch_state, water_switch_state)
            switch_changed = False
        
        #Create response
        response = response_HTML(brew_data)

        
        # Send response
        conn.send(response)

        # Close connection
        conn.close()

        # Nullify conn variable
        conn = None
            
        # Set up small delay before next handling
        time.sleep(1)
        
###################################################################################


# --- HARDWARE ---
def _threadharware():
    
    # Set value for heating speed multiplier for thermostat response
    heating_speed_multiplier = 0.8
    
    # Set up bias for finetuning temperature
    bias = 0.40
    
    # Create heat speed calculating object
    heating_speed_calculator = HeatingSpeedCalculator(utime, heating_speed_multiplier)
    
    # Set the output pin's for relays
    relay_heater = Pin(16, Pin.OUT, value = 0)
    relay_solenoid = Pin(17, Pin.OUT, value = 0)
    relay_pump = Pin(18, Pin.OUT, value = 0)

    # Set the input switches (Pin's)
    switch_brew = False    # switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN)
    switch_steam = False   # switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)
    switch_water = False   # switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)
    
    # Set up the target temperature and counter for brewing time
    target_temperature = 0
    counter_brew_time = 0

    
    # Set mode to idle
    brew_data.set_mode("idle")

    # Load settings (to brew_data object)
    load_settings(json, brew_data)
    
    # Get the boiler temperature
    boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
    # boiler_temperature = sensor.read_temperature (when connected on hardware)

# --- PRE-HEATING ---

    # If temperature at the start is below 80 degrees celcius. Make start pre-heating
    if boiler_temperature < 80:
        
        # Create loop that is going while temperature is less than 130 degrees celcius
        while boiler_temperature < 130:
            
            # Set the mode to "Quick heat-up start"
            brew_data.set_mode("Quick heat-up start")
            
            # Calculate the heat up speed
            heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
            
            # Start heating the boiler
            relay_heater.value(1)
                
            # Heat the virtual boiler
            boiler.heat_up()
                        
            ## Print essential values
            print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
            # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
            
            # Aseta viive 1s. # Set up 1 second delay (to be reduced to 0.1 seconds when connected to hardware)
            time.sleep(1)
            
            # Get the boiler temperature
            boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
            # boiler_temperature = sensor.read_temperature (when connected on hardware)
        
        # Stop heating the boiler
        relay_heater.value(0)


# --- MAIN LOOP ---    
    while True:
        
        # Get brew settings from brew_data object
        brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
        
        # Get the state of the switches
        switch_brew, switch_steam, switch_water = brew_data.get_switches_state()
        
        # Get temperature from the boiler
        boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
        
        # Get calculation of temperature change speed
        heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature) 
        
        # Set brewing time counter to 0
        counter_brewing_time = 0
        
    
    # --- BREW MODE ---
        if switch_brew: # (when not connected to harware)
        # if switch_brew.value(): (when connected to hardware)
            
            # Set solenoid to brewing (pressure) mode
            relay_solenoid.value(1)
            
            # Calulate pre-heat time before pre-infusion
            pre_heat_time_before_pre_infusion = pre_heat_time - pre_infusion_time
            
            # If pre-heat time before preinfusion is negative: set it zero
            if pre_heat_time_before_pre_infusion < 0:
                pre_heat_time_before_pre_infusion = 0
            
            # Calculate pre-heating time for pre-infusion
            pre_heat_time_on_pre_infusion = pre_heat_time - pre_heat_time_before_pre_infusion #
                        
                        
        # --- Pre-heat ---
        
            # If pre-heat time exceeds pre-infusion time: Pre-heat before pre-infusion
            if pre_heat_time_before_pre_infusion > 0:
                
                # Start heating the boiler
                relay_heater.value(1)
                
                # Create for loop for pre-heat time before pre-infusion 
                for x in range(pre_heat_time_before_pre_infusion):
                    
                    # Set mode to pre-heat
                    brew_data.set_mode("Pre-heat " + str(x + 1) + "s.")
                    
                    # Heat up virtual boiler
                    boiler.heat_up()
                    
                    # Get boiler temperature
                    boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
                    # boiler_temperature = sensor.read_temperature (when connected on hardware)
                    
                    # Print essential values
                    print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
                    # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
                
                    # Set delay 1 second
                    time.sleep(1)
            
            # Else stop heating the boiler
            else:
                relay_heater.value(0)

        
        # --- PRE-INFUSION ---
        
            # Create loop for the time of the preinfusion
            for x in range(pre_infusion_time):
                
                # Start the pump
                relay_pump.value(1)
                
                # If there is pre heat before (optional) pre-infusion and brew
                if (pre_heat_time_on_pre_infusion == pre_infusion_time - x):
                    
                    # Start pre-heating the boiler
                    relay_heater.value(1)
                    
                # If boiler is not heating set mode to "Pre-infusion"
                if relay_heater.value() == 0:
                    brew_data.set_mode("Pre-infusion "+ str(x + 1) +"s.")
                    
                    # Cood down the virtual boiler
                    boiler.cooldown()
                
                # Else set mode to "Pre-infusion + Pre-heat"
                else:
                    brew_data.set_mode( "Pre-heat "+ str(x + 1 + pre_heat_time_before_pre_infusion) +"s. Pre-infusion " + str(x + 1)+ "s.")
                    
                    # Cool down the virtual boiler
                    boiler.cooldown(0.5)
                
                # Get the boiler temperature 
                boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
                #boiler_temperature  = sensor.read_temperature() (when connected on hardware)
                
                # Print essential values 
                print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
                # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
                
                # Set delay 0.5 seconds. this needs to be adjusted for suitable pressure when connected to hardware
                time.sleep(0.5)
                
                # Stop the pump
                relay_pump.value(0)
                
                # Print essential values
                print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
                # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
                                
                ## Set delay 0.5 seconds. this needs to be adjusted for suitable pressure when connected to hardware
                time.sleep(0.5)
            
            # Start heating the boiler for brewing
            relay_heater.value(1)
            
            # Start the pump for brewing
            relay_pump.value(1)

        # --- Brew loop ---
        
            while True:

                # Get the boiler temperature
                boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
                # boiler_temperature = sensor.read_temperature() (when connected on hardware)
                
                # Get calculated heating speed
                heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
                
                # Set mode to "Brew"
                brew_data.set_mode("Brew " + str(counter_brewing_time) + "s.")
                
                # Print essential values
                print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
                # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
        
                # Cool down virtual boiler
                boiler.cooldown()
                
                 # Set delay 1 second (decrease as fit when connected to hardware)
                time.sleep(1)
                
                # Add 1 to brewing time counter
                counter_brewing_time += 1
                
                # Get the state of the switches
                switch_brew = brew_data.get_brew_switch_state()
                
                # If brewing switch is turned off brake loop and make (optional) Pressure soft release
                if not switch_brew: # (when not connected to harware)
                # if switch_brew.value() == 0: # (when connected to harware)
                    
                    # Reset brewing time counter
                    counter_brewing_time = 0
                    
                    # Stop heating the boiler
                    relay_heater.value(0)
                    
                    # Stop the pump
                    relay_pump.value(0)
                    
                # --- Pressure soft release ---
                    
                    # Create loop for the time of pressure release
                    for x in range(pressure_soft_release_time):
                        
                        # Set mode to "Soft pressure release"
                        brew_data.set_mode("Soft pressure release " + str(x + 1) +" s.")
                        
                        # Print essential values 
                        print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
                        # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
                        
                         # Set delay for 1 second
                        time.sleep(1)
                    
                    # Release brewing pressure
                    relay_solenoid.value(0)
                    
                    # Break the brewing loop
                    break
        

    # --- WATER ---

        # If water switch is on
        if switch_water: # (when not connected to hardware)
        # if switch_water.value(): # (when connected to harware)
            
            # Set mode to water
            brew_data.set_mode("Water")
            
            # Print essential values
            print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
            # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
            
            # Water loop
            while True:
                
                # Get the boiler temperature
                boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
                # boiler_temperature = sensor.read_temperature (when connected on hardware)
                
                # Get calculated heating speed
                heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
                
                # Cool down the virtual boiler
                boiler.cooldown(3)
                
                # Get brew switch state from the brew_data object
                switch_water = brew_data.get_water_switch_state()
                
                # Start heating the boiler
                relay_heater.value(1)
                
                # Start the pump
                relay_pump.value(1)
                
                # Set delay for 1 second
                time.sleep(1)
                
                # If water switch is off
                if not switch_water: # (when hardware is not connected)
                # if switch_water.value() == 0: (use when connected to hardware)
                    
                    # Stop heating the boiler
                    relay_heater.value(0)
                    
                    # Stop the pump
                    relay_pump.value(0)
                    
                    # Break the loop
                    break
        

    # --- TEMPERATURE MODE ---
        
        # If steam switch is off: set brewing temperature as a target temperature
        if not switch_steam: # (when hardware is not connected)
        #if switch_steam.value() == 0: # (when hardware is connected)
            target_temperature = brew_temperature     
        
        # Otherwise set steam temperature as a target temperature
        else:
            target_temperature = steam_temperature
        
        # If boiler is at least 1 degree celsius lower than target temperature
        if boiler_temperature < target_temperature -1:
                
                # Set mode to "Heating"
                brew_data.set_mode("Heating")
        
        # Otherwise if target temperature is at leas 1 degree celsius warmer than target temperature
        elif boiler_temperature >  target_temperature +1:
            
            # Set mode to "Cooling down"
            brew_data.set_mode("Cooling down")
        
        # Otherwise
        else:
            
            # If target temperature is same as brewing temperature set mode to "Brew standby"
            if target_temperature == brew_temperature:
                brew_data.set_mode("Brew standby")
            
            # Otherwise set mode to "Steam standby"
            else:
                brew_data.set_mode("Steam standby")
                 
        
    # --- THERMOSTAT ---
        
        # If boiler temperature is lower than target temperature - heating speed + bias
        if (boiler_temperature < (target_temperature - heating_speed - bias)):
            
            # Start heating the boiler
            relay_heater.value(1)
            
            ## Heat the virtual boiler
            boiler.heat_up()
            
        # Otherwise
        else:
            
            # Stop heating the boiler
            relay_heater.value(0)
            
            # Cool down the virtual boiler
            boiler.cooldown()
        
        # Print essential values
        print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
        # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
        
        # Set up delay 1 second (reduced to 0.1 when connected to hardware)
        time.sleep(1)


# Create and define temperature sensor
sensor = Sensor(max31865, _thread, Pin)

# Create and define lock printer for printing with both threads without the risk of collision
lock_printer = LockPrinter(_thread)

# Create virtual boiler for demostrating purposes
boiler = VirtualBoiler(_thread)

# Create data store object for threads to share data
brew_data = BrewData(_thread)

# Start the threads
_thread.start_new_thread(_threadharware, ())
_threadui()


