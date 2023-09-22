# Function for printing information
def print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump): # (when not connected to harware)
# def print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump): # (when connected to harware)

    
    # Get boiler temperature
    boiler_temperature = boiler.get_temperature() # (when not connected to hardware)
    # boiler_temperature = sensor.get_temperature() # (when connected to hardware)
    
    # Get mode from object
    mode = brew_data.get_mode()
    
    # Get settings from brew_data object
    brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
    
    # Get the values of the switches from brew_data object
    switch_brew, switch_steam, switch_water = brew_data.get_switches_state()
    
    # Print values
    lock_printer.print("Mode: ", mode)
    lock_printer.print("Boiler temperature: ", boiler_temperature)
    lock_printer.print("heating_speed", heating_speed)
    lock_printer.print("switch_brew: ", switch_brew) # (when not connected to hardware) 
    lock_printer.print("switch_water: ", switch_water) # (when not connected to hardware) 
    lock_printer.print("switch_steam: ", switch_steam) # (when not connected to hardware) 
    # lock_printer.print("switch_brew: ", switch_brew.value()) # (when connected to hardware) 
    # lock_printer.print("switch_water: ", switch_water.value()) # (when connected to hardware) 
    # lock_printer.print("switch_steam: ", switch_steam.value()) # (when connected to hardware) 
    lock_printer.print("relay_heater: ", relay_heater.value())
    lock_printer.print("relay_solenoid: ", relay_solenoid.value())
    lock_printer.print("relay_pump: ", relay_pump.value())
    lock_printer.print("","")


# Funktion for saving settings to file
def save_settings(brew_data, json_module):
    
    # Get settings from brew_data object
    brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
    
    # Form the data
    data = {
        "brew_temperature": brew_temperature,
        "steam_temperature": steam_temperature,
        "pre_infusion_time": pre_infusion_time,
        "pressure_soft_release_time": pressure_soft_release_time,
        "pre_heat_time": pre_heat_time
    }
    
    # Save data to file in json format
    with open('settings.txt', 'w') as file:
        json_module.dump(data, file)


# Function for loading settings from file
def load_settings(json_module, brew_data):
    
    # Get values from file to variables
    try:
        with open('settings.txt', 'r') as file:
            data = json_module.load(file)
            brew_temperature = data.get("brew_temperature")
            steam_temperature = data.get("steam_temperature")
            pre_infusion_time = data.get("pre_infusion_time")
            pressure_soft_release_time = data.get("pressure_soft_release_time")
            pre_heat_time = data.get("pre_heat_time")
        
    # If data is not available: return False
    except OSError:
        return False
    
    # Set settings to brew_data object
    brew_data.set_settings(brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time)
    
    # Return True
    return True

 # Funktion for WiFi connection creation
def set_station(time_module, network_module, ssid, password, lock_printer):
    
    # Create station module
    station = network_module.WLAN(network_module.STA_IF)
    station.active(True)
    
    # Set wifi SSID and Password
    station.connect(ssid, password)
    
    # Define static ip address
    station.ifconfig(('192.168.0.99', '255.255.255.0', '192.168.0.10', '8.0.8.0'))
    
    # Create object for ip address
    ip_address = station.ifconfig()[0]
    
    # Set maxium wait time for 5 seconds 
    max_wait = 5
    
    # Create connection wait loop
    while max_wait > 0:
        
        # If connectiod succeed or failed: brake the loop
        if station.status() < 0 or station.status() >= 3:
            break
        
        # Decrease 1 second from waiting time
        max_wait -= 1
        
        # Print waiting status
        lock_printer.print('waiting for connection...')
        
        # Set delay for one second
        time_module.sleep(1)
        
    # If there's a error in connection: return False and inform from error
    if station.isconnected == False:
        raise RuntimeError('network connection failed')
        return False
    
    # Otherwise inform from succesful connection and show link to ip in browser and return True
    else:
        lock_printer.print('Connected')
        lock_printer.print('Käynnistetty. Mene selaimella <a href="http://{0}" target="_blank">{0}</a>'.format(ip_address))
        status = station.ifconfig()
        lock_printer.print('ip = ' , status[0])
        return True

# Function for two ways connection
def set_socket(socket,time_module, lock_printer):
    
    # Create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Set port to 80
    port = 80

    # Create loop for binding
    while True:
        try:
            # Bind port to socket
            s.bind(('', port))
            s.listen(5)
            
            # Break the loop
            break
        
        # If there's an error. Inform about it
        except OSError as e:
            if e.errno == 98:
                lock_printer.print(f"Port {port} is already in use. Waiting for it to become available...")
            
            # Wait for one second
            time_module.sleep(1)  
    
    # Return socket
    return s


# Function for creating HTML response
def response_HTML(brew_data):

    # Get settings from brew_data object
    brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
    
    # Get the states of the switches from brew_data object
    brew_switch_state, steam_switch_state, water_switch_state = brew_data.get_switches_state()

    # If boiler is on quick heat-up mode, color buttons as grey
    if mode == "Quick heat-up start":
        brew_switch_color = "gray"
        steam_switch_color = "gray"
        water_switch_color = "gray"
    
    # Otherwise as green if off and red if on
    else:
        brew_switch_color = 'red' if brew_switch_state else 'green'
        steam_switch_color = 'red' if steam_switch_state else 'green'
        water_switch_color = 'red' if water_switch_state else 'green'
    
    # Return HTML
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
