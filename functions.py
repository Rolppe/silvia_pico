# Funktio sensorin lämpötilan lukemiseksi
def read_temperature(sensor):
    
    # Laske ja palauta keskiarvo 8 peräkkäisestä mittauksesta välttääksesi kohinaa
    while True:
        temps = []
        for i in range(7):
            temps.append(sensor.temperature)
        #print(round(sum(temps) / len(temps), 2))
        temperature = sum(temps) / len(temps)
    
        return temperature

# Funktio metriikoiden tulostamiseen käyttäen LockPrinteriä
def print_metrics(lock_printer, brew_settings, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump):
    # Hae tiedot brew_settings oliosta
    mode = brew_settings.get_mode()
    boiler_temperature = boiler.get_temperature()
    brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_settings.get_static_values()
    switch_brew, switch_steam, switch_water = brew_settings.get_switches_state()
    

    # Tulosta arvot
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


# Funktio asetusten tallentamiseen
def save_settings(brew_settings, json_module):
    
    # Hae tiedot brew_settings oliosta
    brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_settings.get_static_values()
    # Luo data
    data = {
        "brew_temperature": brew_temperature,
        "steam_temperature": steam_temperature,
        "pre_infusion_time": pre_infusion_time,
        "pressure_soft_release_time": pressure_soft_release_time,
        "pre_heat_time": pre_heat_time
    }
    
    # Tallena json muodossa tiedostoon
    with open('settings.txt', 'w') as file:
        json_module.dump(data, file)


# Funktio tiedostosta lataamiseen
def load_settings(json_module, brew_settings):
    
    # Hae data tiedostosta
    try:
        with open('settings.txt', 'r') as file:
            data = json_module.load(file)
            brew_temperature = data.get("brew_temperature")
            steam_temperature = data.get("steam_temperature")
            pre_infusion_time = data.get("pre_infusion_time")
            pressure_soft_release_time = data.get("pressure_soft_release_time")
            pre_heat_time = data.get("pre_heat_time")
        
    # Jos data ei ole saatavilla: Palauta False
    except OSError:
        return False
    
    # Muussa tapauksessa palauta asetukset
    brew_settings.set_static_values(brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time)
    return True


def set_station(time_module, network_module, ssid, password, lock_printer):
    station = network_module.WLAN(network_module.STA_IF)
    station.active(True)
    station.connect(ssid, password)
    
    # Määritä staattinen IP-osoite
    station.ifconfig(('192.168.0.99', '255.255.255.0', '192.168.0.10', '8.0.8.0'))
    # Hae ja tulosta Raspberry Pi Picon IP-osoite
    ip_address = station.ifconfig()[0]

    max_wait = 5
    while max_wait > 0:
        if station.status() < 0 or station.status() >= 3:
            break
        max_wait -= 1
        lock_printer.print('waiting for connection...')
        time_module.sleep(1)
        
    # Handle connection error
    if station.isconnected == False:
        raise RuntimeError('network connection failed')
        return False
    else:
        lock_printer.print('Connected')
        lock_printer.print('Käynnistetty. Mene selaimella <a href="http://{0}" target="_blank">{0}</a>'.format(ip_address))
        status = station.ifconfig()
        lock_printer.print('ip = ' + status[0])
        return True


def set_socket(socket,time_module, lock_printer):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 80

    while True:
        try:
            s.bind(('', port))
            s.listen(5)
            break  # Portti sidottiin onnistuneesti, poistu silmukasta
        except OSError as e:
            if e.errno == 98:
                lock_printer.print(f"Port {port} is already in use. Waiting for it to become available...")
            time_module.sleep(1)  # Odota 1 sekunti ja yritä uudelleen
    return s


def set_sensor(max31865_module):
    # MOSI -> SDI; MISO -> SDO
    sensor = max31865_module.MAX31865(
        wires = 3, rtd_nominal = 100, ref_resistor = 430,
        pin_sck = 6, pin_mosi = 3, pin_miso = 4, pin_cs = 5
    )
    return sensor


def response_HTML(brew_settings, boiler):
    mode = brew_settings.get_mode()
    boiler_temperature = boiler.get_temperature()
    brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_settings.get_static_values()
    brew_switch_state, steam_switch_state, water_switch_state = brew_settings.get_switches_state()

    if mode == "Quick heat-up start":
        brew_switch_color = "gray"
        steam_switch_color = "gray"
        water_switch_color = "gray"
    else:
        brew_switch_color = 'red' if brew_switch_state else 'green'
        steam_switch_color = 'red' if steam_switch_state else 'green'
        water_switch_color = 'red' if water_switch_state else 'green'
    

    return f"""HTTP/1.1 200 OK
Content-type:text/html

<html>
<head>
  <title>Silvia Pico</title>
  <meta http-equiv="refresh" content="5">
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
  <input type="submit" value="Set values" name="set_values_">
</form>
<p>Mode: {mode} (Refresh 5s.)</p>
<p>Temperature: {boiler_temperature} (Refresh 5s.)</p>
<form action="/set_value" method="get">
  <button type="submit" name="brew_switch" value= "true" style="background-color:{brew_switch_color}">Brew</button>
</form>
<form action="/set_value" method="get">
  <button type="submit" name="water_switch" value= "true" style="background-color:{water_switch_color}">Water</button>
</form>
<form action="/set_value" method="get">
  <button type="submit" name="steam_switch" value= "true" style="background-color:{steam_switch_color}">Steam</button>
</form>
</body>
</html>"""

