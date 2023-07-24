def read_temperature(sensor):
    while True:
        temps = []
        for i in range(7):
            temps.append(sensor.temperature)
        #print(round(sum(temps) / len(temps), 2))
        temperature = sum(temps) / len(temps)
        return temperature

def save_settings(brew_temperature, json_module):
    data = {
        "brew_temperature": brew_temperature
    }
    with open('settings.txt', 'w') as file:
        json_module.dump(data, file)

def load_settings(json_module):
    brew_temperature = False
    try:
        with open('settings.txt', 'r') as file:
            data = json_module.load(file)
            brew_temperature = data.get("brew_temperature")
    except OSError:
        pass
    return brew_temperature


def set_station(time_module, network_module, ssid, password):
    station = network_module.WLAN(network_module.STA_IF)
    station.active(True)
    station.connect(ssid, password)
    
    
    # Määritä staattinen IP-osoite
    station.ifconfig(('192.168.0.99', '255.255.255.0', '192.168.0.10', '8.8.8.8'))
    # Hae ja tulosta Raspberry Pi Picon IP-osoite
    ip_address = station.ifconfig()[0]
    print('Käynnistetty. Mene selaimella <a href="http://{0}" target="_blank">{0}</a>'.format(ip_address))

    max_wait = 10
    while max_wait > 0:
        if station.status() < 0 or station.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time_module.sleep(1)
        
    # Handle connection error
    if station.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('Connected')
        status = station.ifconfig()
        print('ip = ' + status[0])

def set_socket(socket,time_module):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 80

    while True:
        try:
            s.bind(('', port))
            s.listen(5)
            break  # Portti sidottiin onnistuneesti, poistu silmukasta
        except OSError as e:
            if e.errno == 98:
                print(f"Port {port} is already in use. Waiting for it to become available...")
            time_module.sleep(1)  # Odota 1 sekunti ja yritä uudelleen
    return s

def set_sensor(max31865_module):
    # MOSI -> SDI; MISO -> SDO
    sensor = max31865_module.MAX31865(
        wires = 3, rtd_nominal = 100, ref_resistor = 430,
        pin_sck = 6, pin_mosi = 3, pin_miso = 4, pin_cs = 5
    )
    return sensor

def response_HTML(brew_settings):
    temperature = brew_settings.get_brew_temperature()
    brew_button_state, steam_button_state, water_button_state = brew_settings.get_buttons_state()

    brew_button_color = 'red' if brew_button_state else 'green'
    steam_button_color = 'red' if steam_button_state else 'green'
    water_button_color = 'red' if water_button_state else 'green'

    return """HTTP/1.1 200 OK
Content-type:text/html

<html>
<head><title>Silvia Pico</title></head>
<body>
<h1>Brewing setup</h1>
<form action="/set_value" method="get">
  Brewing temperature: <input type="text" name="temperature" value="{0}" readonly><br><br>
  <input type="submit" value="Set temperature">
</form>
<br><br>
<form action="/set_value" method="get">
  <button type="submit" name="brew" value="true" style="background-color:{1}">Brew</button>
</form>
<br>
<form action="/set_value" method="get">
  <button type="submit" name="steam" value="true" style="background-color:{2}">Steam</button>
</form>
<br>
<form action="/set_value" method="get">
  <button type="submit" name="water" value="true" style="background-color:{3}">Water</button>
</form>
</body>
</html>""".format(temperature, brew_button_color, steam_button_color, water_button_color)
# def response_HTML():
#     return  """HTTP/1.1 200 OK
#     Content-type:text/html
# 
#     <html>
#     <head><title>Silvia Pico</title></head>
#     <body>
#     <h1>Brewing setup</h1>
#     <form action="/set_value" method="get">
#       Brewing temperature: <input type="text" name="temperature"><br><br>
#       <input type="submit" value="Set temperature">
#     </form>
#     </body>
#     </html>"""

