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

from functions import read_temperature, save_settings, load_settings, set_station, set_socket, set_sensor, response_HTML
from classes import LockPrinter, BrewSettings, VirtualBoiler, AccelerationCalculator
from secrets import ssid, password

def thread_ui():
    global lock_brew_temperature
    lock_printer = LockPrinter(_thread)
    #brew_settings = BrewSettings(utime, _thread)


    set_station(time, network, ssid, password)
    s = set_socket(socket, time)
    
    # Pääsilmukka
    while True:
        brew_button_state, steam_button_state, water_button_state = brew_settings.get_buttons_state()
        button_changed = False
        temperature_changed = False

        # Hyväksy ja käsittele saapuvat yhteydet
        try:
            conn, addr = s.accept()
        except Exception as e:
            # Tulosta virheilmoitus
            lock_printer("Virhe yhteyden käsittelyssä:", str(e))
            
        lock_printer.print("Yhteys pyynnöstä", addr)

        # Lue pyynnön sisältö
        request = conn.recv(1024)
        request = str(request)

        # Etsi pyynnöstä lämpötila arvo
        if 'GET /set_value?brew_temperature=' in request:
            # Parsi temperature arvo
            brew_temperature = request.split('GET /set_value?brew_temperature=')[1].split('&')[0]
            pre_infusion_time = request.split('GET /set_value?pre_infusion_time=')[0].split('&')[1].split('=')[1]
            # Muunna arvo kokonaisluvuksi
            brew_temperature = int(brew_temperature)
            pre_infusion_time = int(pre_infusion_time)
            
            brew_settings.set_brew_temperature(brew_temperature)
            brew_settings.set_pre_infusion_time(pre_infusion_time)
            # Tallenna lämpötila tiedostoon
            save_settings(brew_temperature, pre_infusion_time, json)
            # Printtaa asetettu lämpötila
            lock_printer.print('Vastaanotettu lämpötila:', brew_temperature)
            lock_printer.print('Vastaanotettu pre-infusio aika:', pre_infusion_time)
            temperature_changed = True
        
        
        if 'GET /set_value?brew_button=true' in request:
            brew_button_state = not brew_button_state
            #brew_settings.set_change_brew_state()
            button_changed = True
# 
#         if 'GET /set_value?steam=true' in request:
#             steam_button_state = not steam_button_state
#             button_changed = True
# 
#         if 'GET /set_value?water=true' in request:
#             water_button_state = not water_button_state
#             button_changed = True
        
        if button_changed:
                brew_settings.set_buttons_state(brew_button_state, steam_button_state, water_button_state)
                button_changed = False
        
        # Lähetä vastaus
        response = response_HTML(brew_settings)
        conn.send(response)

        # Sulje yhteys
        conn.close()

        # Nollaa conn-muuttuja
        conn = None


        

            
        # Aseta pieni viive ennen seuraavan käsittelyn aloittamista
        time.sleep(1)

# Käyttöliittymä säije
# def thread_ui():
#     global lock_brew_temperature
#     lock_printer = LockPrinter(_thread)
#     #brew_settings = BrewSettings(utime, _thread)
# 
#     # Määritä ulkoinen LED
#     led_pin = Pin("LED", Pin.OUT)
#     set_station(time, network)
#     s = set_socket(socket, time)
#     # Pääsilmukka
#     while True:
#         # Hyväksy ja käsittele saapuvat yhteydet
#         try:
#             conn, addr = s.accept()
#         except Exception as e:
#             # Tulosta virheilmoitus
#             print("Virhe yhteyden käsittelyssä:", str(e))
#             
#         print(4)
#         lock_printer.print("Yhteys pyynnöstä", addr)
# 
#         # Lue pyynnön sisältö
#         request = conn.recv(1024)
#         request = str(request)
# 
#         # Etsi pyynnöstä lämpötila arvo
#         if 'GET /set_value?temperature=' in request:
#             # Parsi temperature arvo
#             brew_temperature = request.split('GET /set_value?temperature=')[1].split(' ')[0]
# 
#             # Muunna arvo kokonaisluvuksi
#             brew_temperature = int(brew_temperature)
#             brew_settings.set_brew_temperature(brew_temperature)
#             # Tallenna lämpötila tiedostoon
#             save_settings(brew_temperature, json)
#             # Printtaa asetettu lämpötila
#             lock_printer.print('Vastaanotettu lämpötila:', brew_temperature)
#             # Aseta LEDin tila vastaanotetun lämpötilan mukaan
#             if brew_temperature > 105:
#                 led_pin.on()
#             else:
#                 led_pin.off()
# 
#         # Lähetä vastaus
#         response = response_HTML()
#         conn.send(response)
# 
#         # Sulje yhteys
#         conn.close()
# 
#         # Nollaa conn-muuttuja
#         conn = None
# 
#         # Aseta pieni viive ennen seuraavan käsittelyn aloittamista
#         time.sleep(1)

def thread_harware():
    lock_printer = LockPrinter(_thread)
    boiler = VirtualBoiler()
    acceleration_calculator = AccelerationCalculator(utime)
    
    relay_heater = Pin(16, Pin.OUT, value = 0)
    relay_solenoid = Pin(17, Pin.OUT, value = 0)
    relay_pump = Pin(18, Pin.OUT, value = 0)
#     switch_brew = Pin(7, Pin.IN, Pin.PULL_DOWN)
#     switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)
#     switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)
    switch_brew = False
    switch_steam = False
    switch_water = False
    target_temperature = 0
    steaming_temperature = 130
    counter_brewing_time = 0
    bias = -0.55

    if load_settings(json):
        brew_temperature, pre_infusion_time = load_settings(json)
        brew_settings.set_numeric_values(brew_temperature, pre_infusion_time)
    else:
        brew_settings.set_numeric_values(100,0)

    sensor = set_sensor(max31865)

    while True:
        brewing_temperature, pre_infusion_time = brew_settings.get_numeric_values()
        switch_brew, switch_steam, switch_water = brew_settings.get_buttons_state()
        #if (brew_settings.get_changed_state() == True):
        
        dummy_temperature = round(boiler.getTemperature(),2)
        acceleration = acceleration_calculator.get_acceleration(dummy_temperature)
        if acceleration > 100:
            acceleration = 0

        acceleration_positive = acceleration
        if acceleration_positive > 0:
            acceleration_posotive = abs(acceleration_positive)

        if not switch_steam: #.value() == 0:
            target_temperature = brewing_temperature
        else:
            target_temperature = steaming_temperature
        if (dummy_temperature < (target_temperature - acceleration_positive + bias)):
            relay_heater.value(1)
            boiler.heat()
        else:
            relay_heater.value(0)
            boiler.cooldown()
        if switch_brew: #.value():
            if pre_infusion_time:
                for x in range(pre_infusion_time):
                    print("preinfusion " + str(x))
                    time.sleep(1)

            while True:
                lock_printer.print("brewing time", counter_brewing_time)

                dummy_temperature = round(boiler.getTemperature(),2)
                lock_printer.print("Dummy temperature", dummy_temperature)
                
                acceleration = acceleration_calculator.get_acceleration(dummy_temperature)
                lock_printer.print("acceleration", acceleration)
                
                relay_heater.value(1)
                lock_printer.print("relay_heater: ", relay_heater.value())

                relay_solenoid.value(1)
                lock_printer.print("relay_solenoid: ", relay_solenoid.value())
                
                relay_pump.value(1)
                lock_printer.print("relay_pump: ", relay_pump.value())
                lock_printer.print("")
                
                boiler.cooldown()

    

                time.sleep(1)
                counter_brewing_time += 1
                switch_brew = brew_settings.get_brew_button_state()
                if not switch_brew: #.value() == 0:
                    counter_brewing_time = 0
                    relay_solenoid.value(0)
                    relay_pump.value(0)
                    break
        
        if switch_water: #.value():
            while True:
                relay_heater.value(1)
                relay_pump.value(1)

                lock_printer.print("Water")
                time.sleep(1)

                if not switch_water: #.value() == 0:
                    break
     
        lock_printer.print("Dummy temperature", dummy_temperature)
        lock_printer.print("acceleration", acceleration)
        lock_printer.print("Brew: ", switch_brew)#.value())
        lock_printer.print("Water: ", switch_water)#.value())
        lock_printer.print("Steam: ", switch_steam)#.value())
        
        lock_printer.print("relay_heater: ", relay_heater.value())
        lock_printer.print("relay_solenoid: ", relay_solenoid.value())
        lock_printer.print("relay_pump: ", relay_pump.value())
        lock_printer.print("","")
        #lock_printer.print("Sensor temperature: ", read_temperature(sensor))
        
        utime.sleep_ms(1000)

brew_settings = BrewSettings(utime, _thread)

# Käynnistä säikeet
_thread.start_new_thread(thread_harware, ())
thread_ui()



