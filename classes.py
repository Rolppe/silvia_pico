# Function for getting ratio for pump on and off states.
class PumpRatioCalculator:
    def __init__(self,utime_module, asyncio_module):
        self.asyncio = asyncio_module
        self.utime = utime_module
        self.pump_ratio = 0
        self.pump_start_timer = 0
        self.pump_stop_timer = 0
        self.pump_on_time = 0
        self.pump_off_time = 0
        self.pump_is_on = False
        
    # Function to start timing brew
    def start(self):
        self.pump_stop_timer = self.utime.ticks_ms() # Start calculating pump off state
        self.pump_is_on = False
        
    # Function to start timing pump
    def set_pump_on(self):
        self.pump_is_on = True
        self.pump_start_timer = self.utime.ticks_ms() # Start calculating pump on state 
        self.pump_off_time += self.utime.ticks_diff(self.utime.ticks_ms(), self.pump_stop_timer)
        
    # Function to stop timing pump
    def set_pump_off(self):
        self.pump_is_on = False
        self.pump_stop_timer = self.utime.ticks_ms() # Start calculating pump off state
        self.pump_on_time += self.utime.ticks_diff(self.utime.ticks_ms(), self.pump_start_timer)
        
    # Function to get ratio
    def get_ratio(self):
        
        # If pump is on, add last bit to pump_on_time
        if self.pump_is_on:
            self.pump_on_time += self.utime.ticks_diff(self.utime.ticks_ms(), self.pump_start_timer)
            self.pump_start_timer = self.utime.ticks_ms()
        
        # If pump is off, add last bit to pump_off_time
        else:
            self.pump_off_time += self.utime.ticks_diff(self.utime.ticks_ms(), self.pump_stop_timer)
            self.pump_stop_timer = self.utime.ticks_ms()
                
        
        if self.pump_on_time + self.pump_off_time == 0:
            return 0
        else:
            self.pump_ratio = round(self.pump_on_time / (self.pump_on_time + self.pump_off_time) * 100, 2)
            self.pump_on_time = 0
            self.pump_off_time = 0
            return self.pump_ratio
        
        
class BrewStatsLogger:
    def __init__(self_utime, asyncio):
        self.asyncio = asyncio_module
        self.pressure = 0
        self.start_time = 0
        self.boiler_temperature = 0
        self.pump_ratio = 0
        self.resolution = 1 # times in second
        self.file_name = "brew_log.txt"
        
###### Class to share data between the cores ####
class BrewData:
    def __init__(self, brew_switch, steam_switch, water_switch):
        self.brew_switch = brew_switch
        self.steam_switch = steam_switch
        self.water_switch = water_switch
        self.setting_changed = False
        self.pre_infusion_time = 0
        self.brew_temperature = 97
        self.steam_temperature = 125
        self.pressure_soft_release_time = 0
        self.pre_heat_time = 0
        self.mode = "IDLE"
        self.boiler_temperature = 0
        self.pressure = 0
        self.target_temperature = 0
        self.heating_speed = 0
    
    
    # Function to set mode value
    def set_mode(self, mode):
        self.mode = mode
    
    def set_target_temperature(self, target_temperature):
        self.target_temperature = target_temperature
        
    # Function to set brew settings
    def set_settings(self, brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time):
        self.brew_temperature = brew_temperature
        self.steam_temperature = steam_temperature
        self.pre_infusion_time = pre_infusion_time
        self.pressure_soft_release_time = pressure_soft_release_time
        self.pre_heat_time = pre_heat_time
        self.setting_changed = True
        
    def set_boiler_stats(self, target_temperature, heating_speed):
        self.target_temperature = target_temperature
        self.heating_speed = heating_speed
        
    def set_heating_speed(self, heating_speed):
        self.heating_speed = heating_speed
    
    # Function for setting preinfusion time
    def set_pre_infusion_time(self, time):
        self.pre_infusion_time = time
        self.setting_changed = True
        
    # Function for setting brew temperature
    def set_brew_temperature(self, temperature):
        self.brew_temperature = temperature
        self.setting_changed = True
    
    def set_boiler_temperature(self, boiler_temperature):
        self.boiler_temperature = boiler_temperature
        
    def set_pressure(self, pressure):
        self.pressure = pressure
        
    # Function to get mode value
    def get_mode(self):
        mode = self.mode
        
        return mode
    
    def get_target_temperature(self):
        target_temperature = self.target_temperature
        
        return target_temperature
    
    # Function to get brew settings
    def get_settings(self):
        brew_temperature           = self.brew_temperature
        steam_temperature          = self.steam_temperature
        pre_infusion_time          = self.pre_infusion_time
        pressure_soft_release_time = self.pressure_soft_release_time
        pre_heat_time              = self.pre_heat_time
        
        return brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time
    
    
    def get_boiler_temperature(self):
        boiler_temperature = self.boiler_temperature
        
        return boiler_temperature
        
    def get_pressure(self):
        pressure = self.pressure
        
        return pressure

    # Function to get pre-infusion time
    def get_pre_infusion_time(self):
        time = self.pre_infusion_time
        
        return time
    
    # Function to get brew temperature
    def get_brew_temperature(self):
        brew_temperature = self.brew_temperature
        
        return brew_temperature
    
        # Function to get the states of the switches
    def get_switches_state(self):
        brew_switch  = self.brew_switch
        steam_switch = self.steam_switch
        water_switch = self.water_switch
        
        return brew_switch, steam_switch, water_switch
    
    # Function to get state of the brew switch
    def get_brew_switch_state(self):
        brew_switch = self.brew_switch
        
        return brew_switch
    
    # Function to get the state of the brew switch
    def get_water_switch_state(self):
        water_switch = self.water_switch
        
        return water_switch
    
    # Function to get the state of the steam switch
    def get_steam_switch_state(self):
        steam_switch = self.steam_switch
        
        return steam_switch

    def get_boiler_temperature(self):
        boiler_temperature = self.boiler_temperature
        
        return boiler_temperature
    
    def get_target_temperature(self):
        target_temperature = self.target_temperature
        
        return target_temperature

    def get_heating_speed(self):
        heating_speed = self.heating_speed
        
        return heating_speed
    
    def get_boiler_stats(self):
        boiler_temperature = self.boiler_temperature
        brew_temperature   = self.brew_temperature
        steam_temperature  = self.steam_temperature
        heating_speed      = self.heating_speed
        
        return boiler_temperature, brew_temperature, steam_temperature, heating_speed
    
    def get_pre_heat_time(self):
        pre_heat_time = self.pre_heat_time
        
        return pre_heat_time

    def get_pressure_soft_release_time(self):
        pressure_soft_release_time = self.pressure_soft_release_time
        
        return pressure_soft_release_time


##### Class for pressure monitoring #####
class PressureMonitor:
    def __init__(self, utime, asyncio_module, Pin, PINS, ADC):
        
        self.pressure_sensor  = ADC(Pin(PINS['PRESSURE_ADC']))
        self.asyncio          = asyncio_module
        self.utime            = utime
        self.number_of_cycles = 1
        self.time_start       = 0

    def get_pressure(self):
        
        pressure_sensor = self.pressure_sensor
        utime = self.utime
        pressure = 0
        pressure_measurements_values = []
        
        start = utime.ticks_us()
        end = utime.ticks_add(start, 17000) # one cycle == one Hz
        cycle_counter = 0
        # Make timed cycle for collecting sensor values
        while utime.ticks_diff(end, utime.ticks_us()) > 0:
            
            # Read value of the sensor
            pressure_sensor_value = pressure_sensor.read_u16()
            
            # Add value to lisr
            pressure_measurements_values.append(pressure_sensor_value)
            
            #increment cycle counter
            cycle_counter += 1
        
        # Calculate average for one cycle
        cycle_average = round(sum(pressure_measurements_values) / cycle_counter)
            
        # Convert pressure to bar
        pressure_bar = round((cycle_average * 0.000314936 - 3.522929),1)
        
        return pressure_bar
    
    
    def get_pressure_while(self, measure_time):
    
        pressure_sensor = self.pressure_sensor
        utime = self.utime
        pressure = 0
        number_of_cycles = self.number_of_cycles
        pressure_cycle_values = []
        pressure_measurements_values = []
        
        # Calculate time used for measurements 
        count_of_full_measurements = measure_time / (0.017 * number_of_cycles) # Later number of cycles could be calculated based of time given
        
        # Make for loop timed for whole measurement
        for x in range(count_of_full_measurements):
            
            # Make for loop for averaging measurement values
            for y in range(number_of_cycles):
                
                start = utime.ticks_us()
                end = utime.ticks_add(start, 17000) # one cycle == one Hz
                cycle_counter = 0
                # Make timed cycle for collecting sensor values
                while utime.ticks_diff(end, utime.ticks_us()) > 0:
                    
                    # Read value of the sensor
                    pressure_sensor_value = pressure_sensor.read_u16()
                    
                    # Add value to lisr
                    pressure_measurements_values.append(pressure_sensor_value)
                    
                    #increment cycle counter
                    cycle_counter += 1
                
                # Calculate average for one cycle
                cycle_average = round(sum(pressure_measurements_values) / cycle_counter)
                
                # Add cycle average to list
                pressure_cycle_values.append(cycle_average)

                # Reset measurement list
                pressure_measurements_values.clear()
                
            # Calculate pressure value from averages
            pressure = round(sum(pressure_cycle_values) / len(pressure_cycle_values))
            
            # Reset pressure_cycle_values list
            pressure_cycle_values.clear()
            
            # Convert pressure to bar
            pressure_bar = round((pressure * 0.000314936 - 3.522929),1)
            
            # Print pressure
            print("Pressure: " +str(pressure_bar) +" Bar")
    

#### Class for thermostat ####  

class Thermostat:
    def __init__(self, brew_data, TARGET_TEMPERATURES, RELAY_HEATER, temperature_sensor):
        self.cycle_count = 0
        self.brew_data = brew_data
        self.brew_mode = ""
        self.TARGET_TEMPERATURES = TARGET_TEMPERATURES
        self.RELAY_HEATER = RELAY_HEATER
        self.state = 'NOT READY'
        self.temperature_sensor = temperature_sensor

        
    def run(self): # def run(self, brew_data, switch_steam, RELAY_HEATER):
        
        # Get brew mode
        mode = self.brew_data.get_mode()
        
        # Get boiler data
#        boiler_temperature, brew_temperature, steam_temperature, heating_speed =

        heating_speed = self.brew_data.get_heating_speed()
        
        boiler_temperature = self.temperature_sensor.read_temperature()
        
        
        
        
        
        
        
        # Get target temperature
        target_temperature = self.TARGET_TEMPERATURES[f'{mode}']
        print("target temperature: " + str(self.TARGET_TEMPERATURES[f'{mode}']))

        # Nullify negative heating speed values
        if heating_speed < 0:
            heating_speed = 0
            
        # If boiler temperature is lower than target temperature - heating speed
        if (boiler_temperature < (target_temperature - (heating_speed * 2))):
            
            # Start heating the boiler          
            if (Thermostat.heat_cycler(self, boiler_temperature, target_temperature)):
                print("boiler_temperature" + str(boiler_temperature))
                print("target_temperature" + str(target_temperature))
                self.RELAY_HEATER.value(1)
                print("thermostat heating")
            else:
                self.RELAY_HEATER.value(0)
                print("thermostat cooling")
                
        # Othervice, stop heating the boiler
        else:
            self.RELAY_HEATER.value(0)
    
  
        if abs(target_temperature - boiler_temperature) <= 1:
            self.state = 'READY' 
        elif boiler_temperature > target_temperature: 
            self.state = 'TEMPERATURE HIGH' 
        else:
            self.state = 'NOT READY'
    
    def get_state(self):
        state = self.state
        return state
        
        
#     def get_target_temperature(switch_steam, brew_temperature, steam_temperature, mode):
#         
# 
#     # If steam switch is off: set brewing temperature as a target temperature
#         if      mode == 'IDLE':
#             target_temperature = brew_temperature     
#         
#         else if mode == 'steam':
#             target_temperature = steam_temperature
#         
#         else if mode == 'backflush_phase_1':
#             target_temperature = 80 # backflush_phase_1_temperature
#             
#         else if mode == 'backflush_phase_2':
#             target_temperature = 90 # backflush_phase_2_temperature
#             
#         else if mode == 'backflush_phase_3':
#             target_temperature = 102 # backflush_phase_3_temperature
#         
#         else:
#             target_temperature = 0
#             print('Thermostat is not supporting mode')
#         
#         return target_temperature  
      
            
    def heat_cycler(self, temperature, target_temperature):
        return_bool = False
        cycle_count = self.cycle_count
        
        # Calculate temperature difference
        temperature_difference = int((temperature - target_temperature) *100)
    
        # Calculate heating ratio of cycle from distance to target temperature
        if (abs(temperature_difference / 9) > cycle_count):
            return_bool = True
        else:
            return_bool = False
        
        if (cycle_count >= 90):
            cycle_count = 0
        else:
            cycle_count = cycle_count +10
        
        self.cycle_count = cycle_count
        
        if return_bool:
            return True
        else:
            return False


#### Class to calculate heating speed ####
class HeatingSpeedCalculator:
    def __init__(self, utime_module, asyncio_module):
        self.temperature_begin = 20.0
        self.asyncio = asyncio_module
        self.utime = utime_module
        self.time_start = 0
        self.first_measure_flag = True
   
    # Function to calculate heating speed
    def get_heating_speed(self, temperature_now):
        
        # Get time now
        time_now = self.utime.ticks_ms()
        
        # Calculate time between now and starting point
        time_between = self.utime.ticks_diff(time_now, self.time_start)
        
        # Set time now as start time
        self.time_start = time_now

        # Calculate temperature change between now and starting point
        temperature_between = temperature_now - self.temperature_begin
        
        # Set temperature now to start temperature
        self.temperature_begin = temperature_now
        
        # Calculate heating speed
        self.heating_speed = temperature_between / time_between * 10000 # * self.heating_speed_multiplier
        
        # Round heating speed
        heating_speed = round(self.heating_speed, 2)
        
        # If first measure: set speed to 0 and reset flag
        if self.first_measure_flag:
            self.first_measure_flag = False
            heating_speed = 0
            
        # If value is unacceptale, place error
        if heating_speed > 100 or heating_speed < -100:
            print("nopeus mittauksessa virhe!")
            heating_speed = 0
            
        return heating_speed
  
  
#### Class for reading pt100 sensor temperature with max31865 ####
class TemperatureSensor:
    def __init__(self, max31865, PINS, MAX31865_CONFIG):
        self.sensor = max31865.MAX31865(
            # ref_resistor arvoksi noin 438.0 tai rtd_nominal arvoksi noin 100.7
            #  OG = rtd_nominal = 102.5, ref_resistor = 430.0
            wires        = MAX31865_CONFIG['NUMBER_OF_WIRES'],
            rtd_nominal  = MAX31865_CONFIG['RTD_NOMINAL'],
            ref_resistor = MAX31865_CONFIG['REF_RESISTOR'],
            pin_sck      = PINS['TEMP_SCK'],
            pin_mosi     = PINS['TEMP_MOSI'],
            pin_miso     = PINS['TEMP_MISO'],
            pin_cs       = PINS['TEMP_CS'],
            )
        self.temps = [0, 0, 0, 0, 0 ,0 ,0]
        self.temps_i = 0

    # Function to get temperature from sensor
    def read_temperature(self):
        
        # Create value for sifting bias of the temperature
        temperature_bias = 0 # -5.0
        
        # Get 7 temperature samples to list and calculate average to avoid the noise
        fault_counter = 0
        temp = self.sensor.temperature
        
        # Value error handling
        while (temp < 2 or temp > 200):
            print("Temperature sensor error")
            print("Temp: " + str(temp))
            temp = self.sensor.temperature
            fault_counter += 1
            if fault_counter > 5:
                print("Permanent sensor error")
                return 200            
        
        self.temps[self.temps_i] = temp
        
        self.temps_i += 1
        
        if self.temps_i >= 7:
            self.temps_i = 0          

        # Calculate temperature average
        temperature = round((sum(self.temps) / len(self.temps)), 2)
        
        # Create error handling
        
        # Bias temperature value
        temperature = temperature + temperature_bias
        
        return temperature

