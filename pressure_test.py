from machine import Pin, ADC
import utime
import json

# Set pin for pressure sensor
pressure_sensor = ADC(Pin(28))

# Set the input pins for switches
switch_iddle = Pin(7, Pin.IN, Pin.PULL_DOWN) # BREW Switch
switch_max = Pin(9, Pin.IN, Pin.PULL_DOWN) # STEAM switch
switch_min = Pin(8, Pin.IN, Pin.PULL_DOWN) # WATER Switch

# Set the output pins for relays
relay_heater = Pin(11, Pin.OUT, value = 0)
relay_solenoid = Pin(12, Pin.OUT, value = 0)
relay_pump = Pin(13, Pin.OUT, value = 0)

#cycle_resolution = 6000
number_of_cycles = 10 # One cycle = 1Hz = 0.017second
pressure_buildup_time = 0

NO_PRESSURE_TEST = False
MAX_PRESSURE_TEST = False
IDDLE_PRESSURE_TEST = False

min_pressure_value = "No Measurement"
max_pressure_value = "No Measurement"
iddle_pressure_value = "No Measurement"
# Cycle variation .... 

def get_pressure():
    

    #time_between_measurements = 0.017 / cycle_resolution # Cycle time with 60Hz pump is 0.017s.
    pressure = 0
    pressure_cycle_values = []
    pressure_measurements_values = []
    cycle_length = 17000               # 0.017 seconds long. 1Hz with 60Hz network
    cycle_counter = 0
    
    for x in range(number_of_cycles):
        start = utime.ticks_us()
        end = utime.ticks_add(start, 17000)
        while utime.ticks_diff(end, utime.ticks_us()) > 0:
            pressure_sensor_value = pressure_sensor.read_u16()
            pressure_measurements_values.append(pressure_sensor_value)
            cycle_counter += 1
            
            #utime.sleep(time_between_measurements)
            
        cycle_average = round((sum(pressure_measurements_values) / cycle_counter))
        pressure_cycle_values.append(cycle_average)
        cycle_counter = 0
        
        pressure_measurements_values = []
        
        
    pressure = round((sum(pressure_cycle_values) / len(pressure_cycle_values)))
    
    return pressure
    

def save_data(min_pressure_value, max_pressure_value, iddle_pressure_value):
    
    # Form the data
    data = {
        "min_pressure_value": min_pressure_value,
        "max_pressure_value": max_pressure_value,
        "iddle_pressure_value": iddle_pressure_value
        
    }
    
    # Save data to file in json format
    with open('pressure_test.txt', 'w') as file:
        json.dump(data, file)

while True:
    if NO_PRESSURE_TEST or switch_iddle.value():
        # Drop pressure through solenoid valve
        for x in range(1):
            relay_solenoid.value(1)
            utime.sleep(1)
            relay_solenoid.value(0)
            utime.sleep(1)

        # Measure sensor value without pressure

        print("No Pressure test")
        print("")
        min_pressure_value = get_pressure()
        print("No Pressure test average: " +str(min_pressure_value))


    if MAX_PRESSURE_TEST or switch_max.value():
        # Raise pressure to full
        relay_solenoid.value(1)
        relay_pump.value(1)

        utime.sleep(pressure_buildup_time)

        # Measure max pressure value
        print("Max Pressure test")
        print("")
        max_pressure_value = get_pressure()
        print("Max Pressure test average: " +str(max_pressure_value))
        pressure_bar = round((max_pressure_value * 0.000314936 - 3.522929),1)
        print("paine: " +str(pressure_bar)+" bar")

        # Drop pressure
        relay_pump.value(0)
        relay_solenoid.value(0)
        
    if IDDLE_PRESSURE_TEST or switch_min.value():
        print("Iddle Pressure test")
        print("")
        iddle_pressure_value = get_pressure()
        print("Iddle Pressure test average: " +str(iddle_pressure_value))


# Save low and high pressure to file
save_data(min_pressure_value, max_pressure_value, iddle_pressure_value)














