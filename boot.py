import ugit
from machine import Pin
import time

switch_water = Pin(8, Pin.IN, Pin.PULL_DOWN)

time.sleep(0.1) # Power switch now is working bit slow method so giving some time

#switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)

# If Water switch is on at the start, Check for updates from github
if switch_water.value():
    try:
        ugit.pull_all()
    except (TypeError) as err_obj:
        print("Ugit error:" + str(err_obj))

    
    