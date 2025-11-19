import ugit
from machine import Pin

switch_steam = Pin(9, Pin.IN, Pin.PULL_DOWN)

if switch_steam.value():
    ugit.pull_all()
    
# ugit.pull_all()