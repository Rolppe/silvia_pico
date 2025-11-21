import ugit
from machine import Pin
import time

time.sleep(0.1) # Power switch now is working bit slow method so giving some time

switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)

if switch_steam.value():
    ugit.pull_all()
    
# ugit.pull_all()