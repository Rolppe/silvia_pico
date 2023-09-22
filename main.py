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

    # Luo wifi yhteys # Create WiFi connection
    set_station(time, network, ssid, password, lock_printer)
    
    # Luo socket # Create Socket
    s = set_socket(socket, time, lock_printer)
    
# --- Pääsilmukka --- # --- MAIN LOOP --- 
    while True:
        
        # Hae kytkimien tilat # Get the state of the switches
        brew_switch_state, steam_switch_state, water_switch_state = brew_data.get_switches_state()
        
        # Luo ja aseta switch_chanced lippuun False # Set switches changed flag to False
        switch_changed = False
        
        # Hyväksy ja käsittele saapuvat yhteydet # Accept incoming communications
        try:
            conn, addr = s.accept()
            
        # Handle errors
        except Exception as e:
            # Tulosta virheilmoitus
            lock_printer("Virhe yhteyden käsittelyssä:", str(e))
            
        # Lue ja muuta stringiksi pyynnön sisältö # Read request and transform it to string
        request = conn.recv(1024)
        request = str(request)

        # Etsi pyynnöstä brew_temperature # From request search for brew_temperature for numeric values
        if 'GET /set_value?brew_temperature=' in request:
            
            # Parsi arvot requestistä # Parse numeric values from request string
            brew_temperature = request.split('GET /set_value?brew_temperature=')[1].split('&')[0]
            steam_temperature = request.split('GET /set_value?brew_temperature=')[1].split('&')[1].split('=')[1]
            pre_infusion_time = request.split('GET /set_value?brew_temperature=')[1].split('&')[2].split('=')[1]
            pre_heat_time = request.split('GET /set_value?brew_temperature=')[1].split('&')[3].split('=')[1]
            pressure_soft_release_time = request.split('GET /set_value?brew_temperature=')[1].split('&')[4].split('=')[1]

            # Muunna arvot kokonaisluvuksi # Transform values to integer
            brew_temperature = int(brew_temperature)
            pre_infusion_time = int(pre_infusion_time)
            steam_temperature = int(steam_temperature)
            pressure_soft_release_time = int(pressure_soft_release_time)
            pre_heat_time = int(pre_heat_time)
            
             # Tallenna arvot olioon # Store values to object
            brew_data.set_static_values(brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time)
            
            # Tallenna arvot tiedostoon # Store values to file
            save_settings(brew_data, json)
                    
        # Etsi pyynnöstä brew_switch = true # Check if brew switch is in the request
        if 'GET /set_value?brew_switch=true' in request:
            brew_switch_state = not brew_switch_state
            switch_changed = True

        # Etsi pyynnöstä steam_switch = true # Check if steam switch is in the request
        if 'GET /set_value?steam_switch=true' in request:
            steam_switch_state = not steam_switch_state
            switch_changed = True

        # Etsi pyynnöstä water_switch = true # Check if water switch is in the request
        if 'GET /set_value?water_switch=true' in request:
            water_switch_state = not water_switch_state
            switch_changed = True
        
        # Jos nappia on painettu niin tallenna olioon ja nollaa lippu # If button has pressed, store state of the switches toobject
        if switch_changed:
            brew_data.set_switches_state(brew_switch_state, steam_switch_state, water_switch_state)
            switch_changed = False
        
        # Luo vastaus # Create response
        response = response_HTML(brew_data, boiler) # (if not connected to hardware)
        # response = response_HTML(brew_data, sensor) # (if connected to hardware)
        
        # Lähetä vastaus # Send response
        conn.send(response)

        # Sulje yhteys # Close connection
        conn.close()

        # Nollaa conn-muuttuja # Nullify conn variable
        conn = None
            
        # Aseta pieni viive ennen seuraavan käsittelyn aloittamista # Set up small delay before next handling
        time.sleep(1)
        
###################################################################################


# --- HARDWARE ---
def _threadharware():
    
    # Aseta heating_speed_multiplier. # Set value for heating speed multiplier
    heating_speed_multiplier = 1   
    
    # Luo HeatingSpeedCalculator olio # Create heat speed calculating object
    heating_speed_calculator = HeatingSpeedCalculator(utime, heating_speed_multiplier)
    
    # Aseta releiden ulostulo pinnit # Set the output pin's for relays
    relay_heater = Pin(16, Pin.OUT, value = 0)
    relay_solenoid = Pin(17, Pin.OUT, value = 0)
    relay_pump = Pin(18, Pin.OUT, value = 0)

    # Aseta kytkimet (# = sisääntulopinnit) # Set the input switches (Pin's)
    switch_brew = False    # switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN)
    switch_steam = False   # switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)
    switch_water = False   # switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)
    
    # Luo target_temperature ja counter_brew_time # Set up the target temperature and counter for brewing time
    target_temperature = 0
    counter_brew_time = 0

    # Aseta lämpötilan haarukan biasointi # Set up bias for finetuning temperature
    bias = 0.75
    
    # Aseta aloitus mode # Set mode to idle
    brew_data.set_mode("idle")

    # Lataa asetukset # Load settings (to brew_data object)
    load_settings(json, brew_data)
    
    # Hae lämpötila  kattilalta # Get the boiler temperature
    boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
    # boiler_temperature = sensor.read_temperature (when connected on hardware)

# --- ESILÄMMITYS --- # --- PRE-HEATING ---

    # Jos Lämpötila käynnistäessä alle 80 celsius astetta # If temperature at the start is below 80 degrees celcius. Make start pre-heating
    if boiler_temperature < 80:
        
        # Tee luuppi joka lämmittää kattilaa kunnes lämpötila on 130 celsius astetta # Create loop that is going while temperature is less than 130 degrees celcius
        while boiler_temperature < 130:
            
            # Aseta mode arvoksi "Quick heat-up start" # Set the mode to "Quick heat-up start"
            brew_data.set_mode("Quick heat-up start")
            
            # Hae lämpötilan muutosnopeus # Calculate the heat up speed
            heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
            
            # Aseta lämmitys rele arvoon 1 # Start heating the boiler
            relay_heater.value(1)
                
            # Lämmitä virtuaalikattilaa # Heat the virtual boiler
            boiler.heat_up()
                        
            # Tulosta numero arvot # Print essential values
            print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
            # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
            
            # Aseta viive 1s. # Set up 1 second delay (to be reduced to 0.1 seconds when connected to hardware)
            time.sleep(1)
            
            # Hae kattilan lämpötila # Get the boiler temperature
            boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
            # boiler_temperature = sensor.read_temperature (when connected on hardware)
        
        # Aseta lämmitys rele arvoon 0 # Stop heating the boiler
        relay_heater.value(0)

# --- PÄÄSILMUKKA --- # --- MAIN LOOP ---
    while True:
        
        # Hae brew_data oliosta uutto asetukset # Get brew settings from object
        brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
        
        # Hae oliosta kytkimien asennot # Get the state of the switches # 
        switch_brew, switch_steam, switch_water = brew_data.get_switches_state()
        
        # Hae lämpötila virtuaaliselta kattilalta # Get temperature from the boiler
        boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
        
        # Hae lämpötilan muutosnopeus # Get calculation of temperature change speed
        heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature) 
        
        # Aseta counter_brewing_time" # Set brewing time counter to 0
        counter_brewing_time = 0
        
        # Create flag for indicatin 
        #flag_pre_infusion_full_heat = False
    
    # --- UUTTOTILA --- # --- BREW MODE ---
        if switch_brew: # (when not connected to harware)
        # if switch_brew.value(): (when connected to hardware)
            
            # Aseta solenoidi rele arvoon 1 # Set solenoid to brewing (pressure) mode
            relay_solenoid.value(1)
            
            # Laske pre-heat aika ennen pre-infuusiota # Calulate pre-heat time before pre-infusion
            pre_heat_time_before_pre_infusion = pre_heat_time - pre_infusion_time
            
            # If pre-heat time before preinfusion is negative: set it zero
            if pre_heat_time_before_pre_infusion < 0:
                pre_heat_time_before_pre_infusion = 0
            
            # Vähennä pre-heat ajasta ennen preinfusionia lämmitys aika #  Calculate pre-heating time for pre-infusion
            pre_heat_time_on_pre_infusion = pre_heat_time - pre_heat_time_before_pre_infusion #
                        
                        
        # --- Pre-heat ---
        
            # Jos pre-heat ennen pre-infuusio # If pre-heat time exceeds pre-infusion time: Pre-heat before pre-infusion
            if pre_heat_time_before_pre_infusion > 0:
                
                # Aseta lämmitys rele arvoon 1 # Start heating the boiler
                relay_heater.value(1)
                
                # Viivytä pre_heat_before_preingusion ajan # Create for loop for pre-heat time before pre-infusion 
                for x in range(pre_heat_time_before_pre_infusion):
                    
                    # Aseta modeksi Pre_heat # Set mode to pre-heat
                    brew_data.set_mode("Pre-heat " + str(x + 1) + "s.")
                    
                    # Lämmitä virtuaali kattilaa # Heat up virtual boiler
                    boiler.heat_up()
                    
                    # Hae kattilan lämpötila # Get boiler temperature
                    boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
                    # boiler_temperature = sensor.read_temperature (when connected on hardware)
                    
                    # Tulosta numeriset arvot # Print essential metrics
                    print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
                    # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
                
                    # Aseta viive: 1 sekunti # Set delay 1 second
                    time.sleep(1)
            
            # Muussa tapauksessa aseta lämmitysrele arvoon 0 # Else stop heating the boiler
            else:
                relay_heater.value(0)

        
        # --- PRE-INFUSION ---
        
            # Create loop for the time of the preinfusion
            for x in range(pre_infusion_time):
                
                # Aseta pumppu rele arvoon 1 # Start the pump
                relay_pump.value(1)
                
                # Jos pre_heat_time on yhtäsuuri tai suurempi kun jäljellä oleva pre_infusion_time # If there is pre heat before (optional) pre-infusion and brew
                if (pre_heat_time_on_pre_infusion == pre_infusion_time - x):
                    
                    # Aseta lämmitysrele arvoon 1 # Start pre-heating the boiler
                    relay_heater.value(1)
                    
                # Jos lämmitys rele on arvossa: 0, aseta modeksi Pre-infusion # If boiler is not heating set mode to "Pre-infusion"
                if relay_heater.value() == 0:
                    brew_data.set_mode("Pre-infusion "+ str(x + 1) +"s.")
                    
                    # Jäähdytä virtuaaliboileria # Cood down the virtual boiler
                    boiler.cooldown()
                
                # Muussa tapauksessa aseta modeksi Pre-infusion + Pre-heat # Else set mode to "Pre-infusion + Pre-heat"
                else:
                    brew_data.set_mode( "Pre-heat "+ str(x + 1 + pre_heat_time_before_pre_infusion) +"s. Pre-infusion" + str(x + 1)+ "s. ")
                    
                    # Jäähdytä virtuaaliboileria # Cool down the virtual boiler
                    boiler.cooldown(0.5)
                
                # Hae kattilan lämpötila # Get the boiler temperature 
                boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
                #boiler_temperature  = sensor.read_temperature() (when connected on hardware)
                
                # Tulosta numeriset arvot # Print essential values 
                print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
                # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
                
                # Aseta viive 0.5s. # Set delay 0.5 seconds. this needs to be adjusted for suitable pressure when connected to hardware
                time.sleep(0.5)
                
                # Aseta pumppu rele arvoon 0 # Stop the pump
                relay_pump.value(0)
                
                # Tulosta numeriset arvot # Print essential values
                print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
                # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
                                
                # Aseta viive 0.5 s. # Set delay 0.5 seconds. this needs to be adjusted for suitable pressure when connected to hardware
                time.sleep(0.5)
            
            # Uuttoluuppia ennakoide:
            # Aseta relay_heater arvoon 1 # Start heating the boiler for brewing
            relay_heater.value(1)
            
            # Aseta relay_pump arvoon 1 # Start the pump for brewing
            relay_pump.value(1)

        # --- Uuttoluuppi ---
        
            while True:

                # Hae lämpötila virtuaaliselta kattilalta # Get the boiler temperature
                boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
                # boiler_temperature = sensor.read_temperature() (when connected on hardware)
                
                # Laske kattilan lämmitysnopeus # Get calculated heating speed
                heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
                
                # Aseta modeksi Brew # Set mode to "Brew"
                brew_data.set_mode("Brew " + str(counter_brewing_time) + " s.")
                
                # Tulosta numeriset arvot # Print essential values
                print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
                # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
        
                # Simuloi virtuaaliboilerin jäähtymistä # Cool down virtual boiler
                boiler.cooldown()
                
                # aseta viive: 1s. # Set delay 1 second (decrease as fit when connected to hardware)
                time.sleep(1)
                
                # Lisää counter_brewing_time arvoa yhdellä # Add 1 to brewing time counter
                counter_brewing_time += 1
                
                # Hae kytkimien asennot # Get the state of the switches
                switch_brew = brew_data.get_brew_switch_state()
                
                # Jos switch_brew on kytketty asentoon arvoon 0 # If brewing switch is turned off brake loop and make (optional) Pressure soft release
                if not switch_brew:
                # if switch_brew.value() == 0:
                    
                    # Nollaa counter_brewing_time # Reset brewing time counter
                    counter_brewing_time = 0
                    
                    # Aseta relay_heater arvoon 0 # Stop heating the boiler
                    relay_heater.value(0)
                    
                    # Asetas relay_pump arvoon 0 # Stop the pump
                    relay_pump.value(0)
                    
                # --- Pressure soft release ---
                    
                    # Luo luuppi joka viivyttää annetun ajan relay_solenoid arvon muuttumista 0:aan # Create loop for the time of pressure release
                    for x in range(pressure_soft_release_time):
                        
                        # Aseta mode Soft pressure release # Set mode to "Soft pressure release"
                        brew_data.set_mode("Soft pressure release " + str(x + 1) +"s.")
                        
                        # Tulosta numeriset arvot # Print essential values 
                        print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
                        # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
                        
                        # Aseta viive: 1s. # Set delay for 1 second
                        time.sleep(1)
                    
                    # Aseta relay_solenoid arvoon 0 # Release brewing pressure
                    relay_solenoid.value(0)
                    
                    # Riko uuttoluuppi # Break the brewing loop
                    break
        

    # --- VESITILA --- # --- WATER ---

        # Jos switch_water on arvossa 0 # If water switch is on
        if switch_water:
        # if switch_water.value():
            
            # Aseta modeksi: Water # Set mode to water
            brew_data.set_mode("Water")
            
            # Tulosta numeeriset arvot # Print essential values
            print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
            # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
            
            # Vesiluuppi # Water loop
            while True:
                
                # Hae lämpötila virtuaaliselta kattilalta # Get the boiler temperature
                boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
                # boiler_temperature = sensor.read_temperature (when connected on hardware)
                
                # Laske kattilan lämmitysnopeus # Get calculated heating speed
                heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
                
                # Simuloi boilerin jäähtyminen # Cool down the virtual boiler
                boiler.cooldown(3)
                
                # Hae switch_water arvo oliosta # Get brew switch state from the object
                switch_water = brew_data.get_water_switch_state()
                
                # Aseta releet relay_heater arvoon 1 # Start heating the boiler
                relay_heater.value(1)
                
                #Aseta releet relay_pump arvoon 1 # Start the pump
                relay_pump.value(1)
                
                # Aseta viive: 1s. # Set delay for 1 second
                time.sleep(1)
                
                # Jos switch_water arvo on 0 # If water switch is off
                if not switch_water:
                # if switch_water.value() == 0: (use when connected to hardware)
                    
                    # Aseta releet relay_heater arvoon 1 # Stop heating the boiler
                    relay_heater.value(0)
                    
                    #Aseta releet relay_pump arvoon 1 # Stop the pump
                    relay_pump.value(0)
                    
                    # Break the loop
                    break
        

    # --- STEAM JA BREW LÄMPÖTILAT # --- TEMPERATURE MODE ---
        
        # Jos steam_switch on arvossa 1 aseta target_temperature aroksi steam_temperature # If steam switch is off: set brewing temperature as a target temperature
        if not switch_steam:
        #if switch_steam.value() == 0: # (to be used when connected to hardware)
            target_temperature = brew_temperature     
        
        # Muussa tapauksessa aseta target_temperature arvoon brewing_temperature # Otherwise set steam temperature as a target temperature
        else:
            target_temperature = steam_temperature
        
        # Jos kattila on yli asteen kylmempi kuin tavoite lämpötila aseta mode arvoksi "Heating" # If boiler is at least 1 degree celsius lower than target temperature
        if boiler_temperature < target_temperature -1:
                
                # Set mode to "Heating"
                brew_data.set_mode("Heating")
        
        # Jos kattila on yli asteen kuumempi kuin tavoitelämpotila aseta mode arvoksi "Cooling" # Otherwise if target temperature is at leas 1 degree celsius warmer than target temperature
        elif boiler_temperature >  target_temperature +1:
            
            # Set mode to "Cooling down"
            brew_data.set_mode("Cooling down")
        
        # Jos kattilan lämpötila arvossa target_temperature # Otherwise
        else:
            
            # Jos target_temperature on sama kuin brew_temperature aseta mode arvoksi "Brew standby" # If target temperature is same as brewing temperature set mode to "Brew standby"
            if target_temperature == brew_temperature:
                brew_data.set_mode("Brew standby")
            
            # Muussa tapauksessa aseta mode arvoksi "Steam standby" # Otherwise set mode to "Steam standby"
            else:
                brew_data.set_mode("Steam standby")
                 
        
    # --- LÄMMÖNSÄÄTELY --- # --- THERMOSTAT ---
        
        # Jos lämpötiola on pienempi kuin tavoitelämpötila - lämpenemisnopeus + asetettu bias # If boiler temperature is lower than target temperature - heating speed + bias
        if (boiler_temperature < (target_temperature - abs(heating_speed) + bias)):
            
            # Aseta relay_heater arvoon 1 # Start heating the boiler
            relay_heater.value(1)
            
            # Lämmitä virtuaalikattilaa # Heat the virtual boiler
            boiler.heat_up()
            
        # Muussa tapauksessa # Otherwise
        else:
            
            # Aseta relay_heater arvoon 0 # Stop heating the boiler
            relay_heater.value(0)
            
            # Jäähdytä virtuaalikattilaa # Cool down the virtual boiler
            boiler.cooldown()
        
        # Tulosta numeriset arvot # Print essential values
        print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when not connected to harware)
        # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # (when connected to hardware)
        
        # Tee viive # Set up delay 1 second
        time.sleep(1)


# Luo sensori # Create and define temperature sensor
sensor = Sensor(max31865, _thread, Pin)

# Luo lock_printer # Create and define lock printer for printing with both threads without the risk of collision
lock_printer = LockPrinter(_thread)

# Luo VirtualBoiler olio # Create virtual boiler for demostrating purposes
boiler = VirtualBoiler(_thread)

# Luo brew_data olio # Create data store object for threads to share data
brew_data = BrewData(_thread)

# Käynnistä säikeet # Start the threads
_thread.start_new_thread(_threadharware, ())
_threadui()


