This is project is about control system for
Ranchilio Silvia espresso machine. 

Code can be run on Raspberry Pi Pico W microcontroller
without connecting to other hardware. Code at this point 
is for virtualized.

There is commented what changes you need to change to make
to work with real hardware, but it is not quaranteed to
work flawlessy quite yet.



WiFi connection instructions

1. There is following text in secrets.py file:
 
ssid = 'your WiFi Id here'
password = 'your WiFi password here'

Replace field: 'your WiFi Id here' with
your wifi network name. Forexample 'myWifi'

Replace field: 'your WiFi password here' with
your network password. Forexample 'password123'

Example:
ssid = 'myWifi'
password = 'password123'

2. Save secrets.py

3. While pico is running, go to address: 
http://192.168.0.99/ with your web browser. 

