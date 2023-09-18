import time
import _thread
import utime
import sys
import json
import uos
from machine import Pin
import adafruit_max31865 as max31865
import socket
import network

from functions import read_temperature, save_settings, load_settings, set_station, set_socket, set_sensor, response_HTML, print_metrics
from classes import LockPrinter, BrewSettings, VirtualBoiler, HeatingSpeedCalculator
from secrets import ssid, password


# --- Käyttöliittymä ---
def thread_ui():

    # Luo wifi yhteys
    set_station(time, network, ssid, password, lock_printer)
    
    # Luo socket
    s = set_socket(socket, time, lock_printer)
    
# --- Pääsilmukka ---
    while True:
        
        # Hae kytkimien tilat
        brew_switch_state, steam_switch_state, water_switch_state = brew_settings.get_switches_state()
        
        # Luo ja aseta switch_chanced lippuun False
        switch_changed = False
        
        # Hyväksy ja käsittele saapuvat yhteydet
        try:
            conn, addr = s.accept()
            
        except Exception as e:
            # Tulosta virheilmoitus
            lock_printer("Virhe yhteyden käsittelyssä:", str(e))
            
        # Lue ja muuta stringiksi pyynnön sisältö
        request = conn.recv(1024)
        request = str(request)

        # Etsi pyynnöstä brew_temperature
        if 'GET /set_value?brew_temperature=' in request:
            
            # Parsi arvot requestistä
            brew_temperature = request.split('GET /set_value?brew_temperature=')[1].split('&')[0]
            steam_temperature = request.split('GET /set_value?brew_temperature=')[1].split('&')[1].split('=')[1]
            pre_infusion_time = request.split('GET /set_value?brew_temperature=')[1].split('&')[2].split('=')[1]
            pre_heat_time = request.split('GET /set_value?brew_temperature=')[1].split('&')[3].split('=')[1]
            pressure_soft_release_time = request.split('GET /set_value?brew_temperature=')[1].split('&')[4].split('=')[1]

            # Muunna arvot kokonaisluvuksi
            brew_temperature = int(brew_temperature)
            pre_infusion_time = int(pre_infusion_time)
            steam_temperature = int(steam_temperature)
            pressure_soft_release_time = int(pressure_soft_release_time)
            pre_heat_time = int(pre_heat_time)
            
             # Tallenna arvot olioon 
            brew_settings.set_static_values(brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time)
            
            # Tallenna arvot tiedostoon
            save_settings(brew_settings, json)
            
        
                    
        # Etsi pyynnöstä brew_switch = true
        if 'GET /set_value?brew_switch=true' in request:
            brew_switch_state = not brew_switch_state
            switch_changed = True

        # Etsi pyynnöstä steam_switch = true
        if 'GET /set_value?steam_switch=true' in request:
            steam_switch_state = not steam_switch_state
            switch_changed = True

        # Etsi pyynnöstä water_switch = true
        if 'GET /set_value?water_switch=true' in request:
            water_switch_state = not water_switch_state
            switch_changed = True
        
        # Jos nappia on painettu niin tallenna olioon ja nollaa lippu
        if switch_changed:
            brew_settings.set_switches_state(brew_switch_state, steam_switch_state, water_switch_state)
            switch_changed = False
        
        # Lähetä vastaus
        response = response_HTML(brew_settings, boiler)
        conn.send(response)

        # Sulje yhteys
        conn.close()

        # Nollaa conn-muuttuja
        conn = None
            
        # Aseta pieni viive ennen seuraavan käsittelyn aloittamista
        time.sleep(1)
        
###################################################################################


# --- Hardware ---
def thread_harware():
    
    # Aseta heating_speed_multiplier. 
    heating_speed_multiplier = 1   
    
    # Luo HeatingSpeedCalculator olio
    heating_speed_calculator = HeatingSpeedCalculator(utime, heating_speed_multiplier)
    
    # Aseta releiden ulostulo pinnit
    relay_heater = Pin(16, Pin.OUT, value = 0)
    relay_solenoid = Pin(17, Pin.OUT, value = 0)
    relay_pump = Pin(18, Pin.OUT, value = 0)

    # Aseta kytkimet (# = sisääntulopinnit)
    switch_brew = False    # switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN)
    switch_steam = False   # switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)
    switch_water = False   # switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)
    
    # Aseta oletusarvot
    target_temperature = 0
    counter_brew_time = 0

    # Aseta lämpötilan biasointi
    bias = 0.75
    
    # Aseta aloitus mode
    brew_settings.set_mode("idle")

    # Lataa asetukset
    load_settings(json, brew_settings)
    
    # Aseta sensori
    sensor = set_sensor(max31865)
    
    # Hae lämpötila virtuaaliselta kattilalta
    boiler_temperature = boiler.get_temperature()# round(read_temperature(sensor), 2)
    
    switch_brew = False
    switch_steam = False
    switch_water = False

# --- Pika-esilämmitys ---

    # Jos Lämpötila käynnistäessä alle 80 celsius astetta
    if boiler_temperature < 80:
        
        # Tee luuppi joka lämmittää kattilaa kunnes lämpötila on 130 celsius astetta
        while boiler_temperature < 130:
            brew_settings.set_mode("Quick heat-up start")
            
            # Hae lämpötilan muutosnopeus
            heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
            
            # Aseta lämmitys rele arvoon 1
            relay_heater.value(1)
                
            # Lämmitä virtuaalikattilaa
            boiler.heat_up()
                        
            # Tulosta metriikat
            print_metrics(lock_printer, brew_settings, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump)
            
            time.sleep(1)
        
            boiler_temperature = boiler.get_temperature()
        
        # Aseta lämmitys rele arvoon 0
        relay_heater.value(0)

# --- Pääslmukka ---
    while True:
        
        # Hae brew_settings oliosta uutto asetukset
        brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_settings.get_static_values()
        switch_brew, switch_steam, switch_water = brew_settings.get_switches_state()
        
        # Hae lämpötila virtuaaliselta kattilalta
        boiler_temperature = boiler.get_temperature() # round(read_temperature(sensor), 2)
        
        # Hae lämpötilan muutosnopeus
        heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature) 
        
        # Aseta counter_brewing_time"
        counter_brewing_time = 0
            
    
    # --- Uutto tila ---   
        if switch_brew: #.value():
            
            # Aseta solenoidi rele arvoon 1
            relay_solenoid.value(1)
                        
        # --- Pre-heat ---
        
            # Jos pre-heat ennen pre-infuusio
            if pre_heat_time > pre_infusion_time:
                
                # Laske pre-heat aika ennen pre-infuusiota
                pre_heat_before_pre_infusion = pre_heat_time - pre_infusion_time
                
                # Vähennä pre-heat ajasta ennen preinfusionia lämmitys aika
                pre_heat_time = pre_heat_time - pre_infusion_time
                
                # Aseta lämmitys rele arvoon 1
                relay_heater.value(1)
                
                # Viivytä pre_heat_before_preingusion ajan
                for x in range(pre_heat_before_pre_infusion):
                    
                    # Aseta modeksi Pre_heat
                    brew_settings.set_mode("Pre-heat " + str(x + 1) + "s.")
                    
                    # Lämmitä virtuaali kattilaa
                    boiler.heat_up()
                    
                    # Hae kattilan lämpötila
                    boiler_temperature = boiler.get_temperature()
                    
                    # Tulosta metriikat
                    print_metrics(lock_printer, brew_settings, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump)
                
                    # Aseta viive: 1 sekunti
                    time.sleep(1)
            
            # Muussa tapauksessa aseta lämmitysrele arvoon 0
            else:
                relay_heater.value(0)

        # --- Pre-infusion ---
        
            # Toteuta for loop pre-infusionin pituiseksi siten että pumppu
            # on puolet ajasta päällä ja pre-heat pre_heat_time:n mukaisesti
            for x in range(pre_infusion_time):
                
                
                
                # Aseta pumppu rele arvoon 1
                relay_pump.value(1)
                
                # Jos pre_heat_time on yhtäsuuri tai suurempi kun jäljellä oleva pre_infusion_time
                if (pre_infusion_time - x <= pre_heat_time):
                    
                    # Aseta lämmitysrele arvoon 1
                    relay_heater.value(1)
                    
                    
                # Jos lämmitys rele on arvossa: 0, aseta modeksi Pre-infusion
                if relay_heater.value() == 0:
                    brew_settings.set_mode("Pre-infusion "+ str(x + 1) +"s.")
                    
                    # Jäähdytä virtuaaliboileria
                    boiler.cooldown()
                
                # Muussa tapauksessa aseta modeksi Pre-infusion + Pre-heat
                else:
                    brew_settings.set_mode("Pre-infusion + Pre-heat "+ str(x + 1) +"s.")
                    # Jäähdytä virtuaaliboileria
                    boiler.cooldown(0.5)
                
                # Hae kattilan lämpötila
                boiler_temperature = boiler.get_temperature()
                
                # Tulosta metriikat
                print_metrics(lock_printer, brew_settings, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump)
                
                # Aseta viive 0.5 s.
                time.sleep(0.5)
                
                # Aseta pumppu rele arvoon 0
                relay_pump.value(0)
                
                # Tulosta metriikat
                print_metrics(lock_printer, brew_settings, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump)
                                
                # Aseta viive 0.5 s.
                time.sleep(0.5)
            
            # Aseta lämmitysrele arvoon 1
            relay_heater.value(1)
            
            # Aseta pumppu rele arvoon 1
            relay_pump.value(1)

        # --- Uuttoluuppi ---
        
            while True:

                # Hae lämpötila virtuaaliselta kattilalta
                boiler_temperature = boiler.get_temperature()
                
                # Laske kattilan lämmitysnopeus
                heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
                
                # Aseta modeksi Brew
                brew_settings.set_mode("Brew " + str(counter_brewing_time) + " s.")
                
                # Tulosta metriikat
                print_metrics(lock_printer, brew_settings, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump)
        
                # Simuloi virtuaaliboilerin jäähtymistä
                boiler.cooldown()
                
                # aseta viive: 1s.
                time.sleep(1)
                
                # Lisää counter_brewing_time arvoa yhdellä
                counter_brewing_time += 1
                
                # Hae kytkimien asennot
                switch_brew = brew_settings.get_brew_switch_state()
                
                # Jos switch_brew on kytketty pois nollaa counter,
                # suorita pehmeä paineen lasku, aseta relay_heater
                # ja relay_pump arvoihin 0 sekä riko luuppi
                if not switch_brew: #.value() == 0:
                    counter_brewing_time = 0
                    relay_heater.value(0)
                    relay_pump.value(0)
                    
                # --- Pressure soft release ---
                    
                    # Luo luuppi joka viivyttää annetun ajan relay_solenoid arvon muuttumista 0:aan
                    for x in range(pressure_soft_release_time):
                        
                        # Aseta mode Soft pressure release
                        brew_settings.set_mode("Soft pressure release " + str(x + 1) +"s.")
                        
                        # Tulosta metriikat
                        print_metrics(lock_printer, brew_settings, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump)
                        
                        # Aseta viive: 1s.
                        time.sleep(1)
                    
                    # Aseta relay_solenoid arvoon 0
                    relay_solenoid.value(0)
                    
                    # Riko uuttoluuppi
                    break
        

    # --- Vesitila ---

        if switch_water: #.value():
            
            # Aseta modeksi: Water
            brew_settings.set_mode("Water")
            
            # Tulosta metriikat
            print_metrics(lock_printer, brew_settings, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump)
            
            # Vesiluuppi
            while True:
                
                # Hae lämpötila virtuaaliselta kattilalta
                boiler_temperature = boiler.get_temperature()
                
                # Laske kattilan lämmitysnopeus
                heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
                
                # Simuloi boilerin jäähtyminen
                boiler.cool_down(3)
                
                # Hae switch_water arvo oliosta
                switch_water = brew_settings.get_water_switch_state()
                
                # Aseta releet relay_heater ja relay_pump arvoon 1
                relay_heater.value(1)
                relay_pump.value(1)
                
                # Aseta viive: 1s.
                time.sleep(1)
                
                # Jos switch_water arvo on 0: aseta relay_pump ja relay_heater arvoon 0 ja riko vesiluuppi
                if not switch_water: #.value() == 0:
                    relay_pump.value(0)
                    relay_heater.value(0)
                    break
        

    # --- Höyrystystila --- #######################################korjausta nimeämiseen
        
        # Jos switch_steam arvo on 0, aseta target_temperature arvoon
        # brew_temperature muussa tapauksessa arvoon steam_temperature

        
        if not switch_steam: #.value() == 0:
            target_temperature = brew_temperature           
            #brew_settings.set_mode("Idle")
        else:
            target_temperature = steam_temperature
            #brew_settings.set_mode("Steam")
        
        if target_temperature > boiler_temperature +1 #################################### TÄSSÄ ;EMMÄÄ
        
    # --- Lämmitysreleen ja virtuaali kattilan säätely ---
        
        # Jos lämpötiola on pienempi kuin tavoitelämpötila - lämpenemisnopeus + asetettu bias
        if (boiler_temperature < (target_temperature - abs(heating_speed) + bias)):
            
            # Aseta relay_heater arvoon 1
            relay_heater.value(1)
            
            # Lämmitä virtuaalikattilaa
            boiler.heat_up()
            
        # Muussa tapauksessa
        else:
            
            # Aseta relay_heater arvoon 0
            relay_heater.value(0)
            
            # Jäähdytä virtuaalikattilaa
            boiler.cooldown()
        
        # Tulosta metriikat
        print_metrics(lock_printer, brew_settings, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump)
        
        # Tee viive
        utime.sleep_ms(1000)


# Luo lock_printer
lock_printer = LockPrinter(_thread)

# Luo VirtualBoiler olio
boiler = VirtualBoiler(_thread)

# Luo brew_settings olio
brew_settings = BrewSettings(utime, _thread)

# Käynnistä säikeet
_thread.start_new_thread(thread_harware, ())
thread_ui()


