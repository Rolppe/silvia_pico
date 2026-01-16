from machine import Pin
import utime

# Set the output pins for relays
relay_heater = Pin(11, Pin.OUT, value = 0)
relay_solenoid = Pin(12, Pin.OUT, value = 0)
relay_pump = Pin(13, Pin.OUT, value = 0)


#     start = utime.ticks_us()
#     end = utime.ticks_add(start, 17000)
#     while utime.ticks_diff(end, utime.ticks_us()) > 0:
