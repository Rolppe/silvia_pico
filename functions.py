def fast_heatup(relay_pump, relay_solenoid, relay_heater, utime, sensor):
        
    # Fill the boiler
    relay_solenoid.value(1)
    relay_pump.value(1)
    utime.sleep(2)
    relay_pump.value(0)
    relay_solenoid.value(0)
    
   
 # Heat the boiler
    relay_heater.value(1)
    while sensor.read_temperature() < 85:
        utime.sleep(1)
    while sensor.read_temperature() < 110:
        relay_heater.value(1)
        utime.sleep(1)
        relay_heater.value(0)
        utime.sleep(1.5)
    while sensor.read_temperature() < 120:
        relay_heater.value(1)
        utime.sleep(1)
        relay_heater.value(0)
        utime.sleep(2)
    
    # keep the temperature
    for i in range(200):
        if sensor.read_temperature() < 120:
            relay_heater.value(1)
            utime.sleep(1)
            relay_heater.value(0)
            utime.sleep(2)
        else:
            relay_heater.value(0)
        utime.sleep(1)
    
    # Cool the boiler
    while sensor.read_temperature() > 105:
    
        # Fill the boiler
        relay_solenoid.value(1)
        relay_pump.value(1)
        utime.sleep(0.5)
        relay_pump.value(0)
        relay_solenoid.value(0)

# Function for printing information
def print_values(brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump):
 
    # Get boiler temperature
    boiler_temperature = sensor.read_temperature()
    
    # Get mode from object
    mode = brew_data.get_mode()
    
    ## Get settings from brew_data object
    # brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
    
    brew_switch_state, steam_switch_state, water_switch_state = brew_data.get_switches_state()
    
    # Print values
    print("Mode: ", mode)
    print("Boiler temperature: ", boiler_temperature)
    print("heating_speed", heating_speed)
    print("switch_brew: ", brew_switch_state.value())
    print("switch_water: ", water_switch_state.value()) 
    print("switch_steam: ", steam_switch_state.value())
    print("relay_heater: ", relay_heater.value())
    print("relay_solenoid: ", relay_solenoid.value())
    print("relay_pump: ", relay_pump.value())
    print("","")


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
def set_station(time_module, network_module, ssid, password):
    
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
        print('waiting for connection...')
        
        # Set delay for one second
        time_module.sleep(1)
        
    # If there's a error in connection: return False and inform from error
    if station.isconnected == False:
        raise RuntimeError('network connection failed')
        return False
    
    # Otherwise inform from succesful connection and show link to ip in browser and return True
    else:
        print('Connected')
        print('Käynnistetty. Mene selaimella <a href="http://{0}" target="_blank">{0}</a>'.format(ip_address))
        status = station.ifconfig()
        print('ip = ' , status[0])
        return True


# Function for two ways connection
def set_socket(socket,time_module):
    
    # Create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Clear port
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
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
                print(f"Port {port} is already in use. Waiting for it to become available...")
            
            # Wait for one second
            time_module.sleep(1)  
    
    # Return socket
    return s


# Function for creating HTML response
def response_HTML(brew_data):

    # Get settings from brew_data object
    brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()

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
      Brewing temperature (&#8451;): <input type="number" name="brew_temperature" value = "{brew_temperature}">
      <br><br>
      Steam temperature (&#8451;): <input type="number" name="steam_temperature" value = "{steam_temperature}">
      <br><br>
      Pre-infusion time (s): <input type="number" name="pre_infusion_time" value = "{pre_infusion_time}">
      <br><br>
      Pre-heat time (s): <input type="number" name="pre_heat_time" value = "{pre_heat_time}">
      <br><br>
      Pressure soft-release time (s): <input type="number" name="pressure_soft_release_time" value = "{pressure_soft_release_time}">
      <br><br>
      <input type="submit" value="Set values and refresh" name="set_values_">
    </form>
  </body>
</html>"""
