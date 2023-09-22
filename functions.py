# Funktio metriikoiden tulostamiseen käyttäen LockPrinteriä # Function for printing information
def print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump): # (when not connected to harware)
# def print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump): # (when connected to harware)

    
    # Hae kattilan lämpötila # Get boiler temperature
    boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
    # boiler_temperature = sensor.get_temperature() # (when connected to hardware)
    
    # Hae mode brew_data oliosta # Get mode from object
    mode = brew_data.get_mode()
    
    # Hae asetusarvot brew_data:sta # Get settings from brew_data object
    brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
    
    # Hae kytkinten asennot brew_data:stä # Get the values of the switches from brew_data object
    switch_brew, switch_steam, switch_water = brew_data.get_switches_state()
    
    # Tulosta arvot # Print values
    lock_printer.print("Mode: ", mode)
    lock_printer.print("Boiler temperature: ", boiler_temperature)
    lock_printer.print("heating_speed", heating_speed)
    lock_printer.print("switch_brew: ", switch_brew)#.value())
    lock_printer.print("switch_water: ", switch_water)#.value())
    lock_printer.print("switch_steam: ", switch_steam)#.value())
    lock_printer.print("relay_heater: ", relay_heater.value())
    lock_printer.print("relay_solenoid: ", relay_solenoid.value())
    lock_printer.print("relay_pump: ", relay_pump.value())
    lock_printer.print("","")


# Funktio asetusten tallentamiseen # Funktion for saving settings to file
def save_settings(brew_data, json_module):
    
    # Hae tiedot brew_data oliosta # Get settings from brew_data object
    brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
    
    # Luo data # Form the data
    data = {
        "brew_temperature": brew_temperature,
        "steam_temperature": steam_temperature,
        "pre_infusion_time": pre_infusion_time,
        "pressure_soft_release_time": pressure_soft_release_time,
        "pre_heat_time": pre_heat_time
    }
    
    # Tallena json muodossa tiedostoon # Save data to file in json format
    with open('settings.txt', 'w') as file:
        json_module.dump(data, file)


# Funktio tiedostosta lataamiseen # Function for loading settings from file
def load_settings(json_module, brew_data):
    
    # Hae data tiedostosta muuttujiin # Get values from file to variables
    try:
        with open('settings.txt', 'r') as file:
            data = json_module.load(file)
            brew_temperature = data.get("brew_temperature")
            steam_temperature = data.get("steam_temperature")
            pre_infusion_time = data.get("pre_infusion_time")
            pressure_soft_release_time = data.get("pressure_soft_release_time")
            pre_heat_time = data.get("pre_heat_time")
        
    # Jos data ei ole saatavilla: Palauta False # If data is not available: return False
    except OSError:
        return False
    
    # Muussa tapauksessa aseta asetukset brew_data:iin # Set settings to brew_data object
    brew_data.set_static_values(brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time)
    
    # Palauta True # Return True
    return True

# Wifi yhteyden luonti # Funktion for WiFi connection creation
def set_station(time_module, network_module, ssid, password, lock_printer):
    
    # Luo station moduuli # Create station module
    station = network_module.WLAN(network_module.STA_IF)
    station.active(True)
    
    # Aseta ssid ja password # Set wifi SSID and Password
    station.connect(ssid, password)
    
    # Määritä staattinen IP-osoite # Define static ip address
    station.ifconfig(('192.168.0.99', '255.255.255.0', '192.168.0.10', '8.0.8.0'))
    
    # Hae ja tulosta Raspberry Pi Picon IP-osoite # Create object for ip address
    ip_address = station.ifconfig()[0]
    
    # Asetetaan maksimi odotusaika 5s. # Set maxium wait time for 5 seconds 
    max_wait = 5
    
    # Luo odotusluuppi # Create connection wait loop
    while max_wait > 0:
        
        # Jos yhteys onnistui tai epäonnistui riko luuppi # If connectiod succeed or failed: brake the loop
        if station.status() < 0 or station.status() >= 3:
            break
        
        # Vähennä maksimi jonotusajasta 1 sekunti # Decrease 1 second from waiting time
        max_wait -= 1
        
        # Tulosta odotusilmoitus # Print waiting status
        lock_printer.print('waiting for connection...')
        
        # Aseta viive 1 sekunti # Set delay for one second
        time_module.sleep(1)
        
    # Jos yhteydessä on virhe # If there's a error in connection: return False and inform from error
    if station.isconnected == False:
        raise RuntimeError('network connection failed')
        return False
    
    #  muussa tapauksessa ilmoita onnistuneesta yhteydestä ja tulosta käyttöliittymän paikallinen url osoite # Otherwise inform from succesful connection and show link to ip in browser and return True
    else:
        lock_printer.print('Connected')
        lock_printer.print('Käynnistetty. Mene selaimella <a href="http://{0}" target="_blank">{0}</a>'.format(ip_address))
        status = station.ifconfig()
        lock_printer.print('ip = ' , status[0])
        return True

# Kaksisuuntaisen liikenteen avaus # Function for two ways connection
def set_socket(socket,time_module, lock_printer):
    
    # Luo socket # Create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Aseta portiksi 80 # Set port to 80
    port = 80

    # Sitomisluuppi # Create loop for binding
    while True:
        try:
            # Bind port to socket
            s.bind(('', port))
            s.listen(5)
            
            # Portti sidottiin onnistuneesti, poistu silmukasta # Break the loop
            break
        
        # Jos tulee virhe kirjoita viesti # If there's an error. Inform about it
        except OSError as e:
            if e.errno == 98:
                lock_printer.print(f"Port {port} is already in use. Waiting for it to become available...")
            
            # Odota 1 sekunti ja yritä uudelleen # Wait for one second
            time_module.sleep(1)  
    
    # Palauta socket # Return socket
    return s


# HTML responsen luominen # Function for creating HTML response
def response_HTML(brew_data, boiler): # (if not connected to hardware
# def response_HTML(brew_data, sensor): (if connected to hardware)
    
    # Haetaan mode olioista # Get the state of the mode from brew_data object
    mode = brew_data.get_mode()
    
    # Haetaan virtuaalikattilan lämpötila brew_data olioista # 
    boiler_temperature = boiler.get_temperature() # (if not connected to hardware)
    # boiler_temperature = sensor.get_temperature() # (if connected to hardware
    
    # Haetaan staattiset tiedot brew_data oliosta # Get settings from brew_data object
    brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
    
    # # Haetaan kytkimien asento brew_data olioista # Get the states of the switches from brew_data object
    brew_switch_state, steam_switch_state, water_switch_state = brew_data.get_switches_state()

    # Jos Quick heat-up start niin aseta nappien väriksi harmaa # If boiler is on quick heat-up mode, color buttons as grey
    if mode == "Quick heat-up start":
        brew_switch_color = "gray"
        steam_switch_color = "gray"
        water_switch_color = "gray"
    
    # Muussa tapauksessa tilan mukaan punaionen tai vihreä # Otherwise as green if off and red if on
    else:
        brew_switch_color = 'red' if brew_switch_state else 'green'
        steam_switch_color = 'red' if steam_switch_state else 'green'
        water_switch_color = 'red' if water_switch_state else 'green'
    
    # Palauta HTML # Return HTML
    return f"""HTTP/1.1 200 OK
Content-type:text/html

<html>
  <head>
    <title>Silvia Pico</title>
  </head>
  <body>
    <h1>Brewing setup</h1>
    <form action="/set_value" method="get">
      Brewing temperature (&#8451;): <input type="text" name="brew_temperature" value = "{brew_temperature}">
      <br><br>
      Steam temperature (&#8451;): <input type="text" name="steam_temperature" value = "{steam_temperature}">
      <br><br>
      Pre-infusion time (s): <input type="text" name="pre_infusion_time" value = "{pre_infusion_time}">
      <br><br>
      Pre-heat time (s): <input type="text" name="pre_heat_time" value = "{pre_heat_time}">
      <br><br>
      Pressure soft-release time (s): <input type="number" name="pressure_soft_release_time" value = "{pressure_soft_release_time}">
      <br><br>
      <input type="submit" value="Set values and refresh" name="set_values_">
    </form>
    <form action="/set_value" method="get">
      <button type = "submit" name = "brew_switch" value = "true" style = "background-color:{brew_switch_color}">Brew</button>
    </form>
    <form action="/set_value" method="get">
      <button type="submit" name="water_switch" value = "true" style="background-color:{water_switch_color}">Water</button>
    </form>
    <form action="/set_value" method="get">
      <button type="submit" name="steam_switch" value = "true" style="background-color:{steam_switch_color}">Steam</button>
    </form>
  </body>
</html>"""


#<!--Lisää päivitys testausta varten-->
#    <meta http-equiv="refresh" content="2; url=http://192.168.0.99/">
#     <p>
#       Mode: {mode}
#     </p>
#     <p>
#       Temperature: {boiler_temperature}
#     </p>
