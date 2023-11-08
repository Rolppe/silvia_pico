# Class that gives threads turns on printing to avoid collision
class LockPrinter:
    def __init__(self, _thread):        
        self.lock_print = _thread.allocate_lock()

    # Function for printing
    def print(self, first_parameter, second_parameter=""):
        self.lock_print.acquire()
        print(first_parameter, second_parameter)
        self.lock_print.release()


# Class to share data between the cores
class BrewData:
    def __init__(self, _thread):
        self.lock = _thread.allocate_lock()
        self._thread = _thread
        self.brew_switch_state = False
        self.steam_switch_state = False
        self.water_switch_state = False
        self.relay_heater_value = 0
        self.relay_solenoid_value = 0
        self.relay_pump_value = 0
        self.setting_changed = False
        self.pre_infusion_time = 0
        self.brew_temperature = 20
        self.steam_temperature = 50
        self.pressure_soft_release_time = 0
        self.pre_heat_time = 0
        self.mode = ""
    
    # Function to set mode value
    def set_mode(self, mode):
        self.lock.acquire()
        self.mode = mode
        self.lock.release()
    
    # Function to set brew settings
    def set_settings(self, brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time):
        self.lock.acquire()
        self.brew_temperature = brew_temperature
        self.steam_temperature = steam_temperature
        self.pre_infusion_time = pre_infusion_time
        self.pressure_soft_release_time = pressure_soft_release_time
        self.pre_heat_time = pre_heat_time
        self.setting_changed = True
        self.lock.release()
        
    # Function for set the states of the switches
    def set_switches_state(self, brew_switch_state, steam_switch_state, water_switch_state):
        self.lock.acquire()
        self.brew_switch_state = brew_switch_state
        self.steam_switch_state = steam_switch_state
        self.water_switch_state = water_switch_state
        self.lock.release()
    
    # Function for setting preinfusion time
    def set_pre_infusion_time(self, time):
        self.lock.acquire()
        self.pre_infusion_time = time
        self.setting_changed = True
        self.lock.release()
        
    # Function for setting brew temperature
    def set_brew_temperature(self, temperature):
        self.lock.acquire()
        self.brew_temperature = temperature
        self.setting_changed = True
        self.lock.release()
    
    # Function to get mode value
    def get_mode(self):
        self.lock.acquire()
        mode = self.mode
        self.lock.release()
        return mode
    
    # Function to get brew settings
    def get_settings(self):
        self.lock.acquire()
        brew_temperature = self.brew_temperature
        steam_temperature = self.steam_temperature
        pre_infusion_time = self.pre_infusion_time
        pressure_soft_release_time = self.pressure_soft_release_time
        pre_heat_time = self.pre_heat_time
        self.lock.release()
        return brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time
    
    # Function to get the states of the switches
    def get_switches_state(self):
        self.lock.acquire()
        brew_switch_state = self.brew_switch_state
        steam_switch_state = self.steam_switch_state 
        water_switch_state = self.water_switch_state
        self.lock.release()
        return brew_switch_state, steam_switch_state, water_switch_state
    
    # Function to get pre-infusion time
    def get_pre_infusion_time(self):
        self.lock.acquire()
        time = self.pre_infusion_time
        self.lock.release()
        return time
    
    # Function to get brew temperature
    def get_brew_temperature(self):
        self.lock.acquire()
        brew_temperature = self.brew_temperature
        self.lock.release()
        return brew_temperature
    
    # Function to get state of the brew switch
    def get_brew_switch_state(self):
        self.lock.acquire()
        brew_switch_state = self.brew_switch_state
        self.lock.release()
        return brew_switch_state
    
    # Function to get the state of the brew switch
    def get_water_switch_state(self):
        self.lock.acquire()
        water_switch_state = self.water_switch_state
        self.lock.release()
        return water_switch_state
    
    # Function to get the state of the steam switch
    def get_steam_switch_state(self):
        self.lock.acquire()
        steam_switch_state = self.steam_switch_state
        self.lock.release()
        return steam_switch_state
    

# Class that works as a virtual boiler
class VirtualBoiler:
    def __init__(self, _thread):
        self.lock = _thread.allocate_lock()
        self.temperature = 90
        self.heating_speed = 0
    
    # Function to heat boiler
    def heat_up(self, amount = 1):
        self.lock.acquire()
        heating_speed = self.heating_speed
        temperature = self.temperature
        
        # Add a temperature chanche to the temperature
        self.temperature = round(temperature + heating_speed, 2)
        
        # If heating speed is less than 1: increase heating speed
        if heating_speed < 1:
            self.heating_speed += 0.2 * amount
        self.lock.release()
    
    # Function for fooling the boiler
    def cooldown(self, amount = 1):
        self.lock.acquire()
        heating_speed = self.heating_speed
        temperature = self.temperature
        
        # Add a temperature change to the temperature
        self.temperature = temperature + heating_speed
        
        # If temperature chanche speed is higher than -0.2: lover heating speed
        if heating_speed > -0.2:
            self.heating_speed -= 0.1 * amount
        self.lock.release()
        
    # Function to get temperature
    def get_temperature(self):
        self.lock.acquire()
        temperature = round(self.temperature, 2)
        self.lock.release()
        return temperature
    
    
# Class to calculate heating speed
class HeatingSpeedCalculator:
    def __init__(self, utime_module, heating_speed_multiplier):
        self.temperature_begin = 0
        self.utime = utime_module
        self.time_start = self.utime.ticks_ms()
        self.heating_speed_multiplier = heating_speed_multiplier
   
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
        self.heating_speed = temperature_between / time_between * 10000 * self.heating_speed_multiplier
        
        # Round heating speed
        heating_speed = round(self.heating_speed, 2)
        
        # Remove initial spike from temperature change speed
        if heating_speed > 100:
            heating_speed = 0
            
        return heating_speed
    

# Class for reading sensor temperature
class Sensor:
    def __init__(self, max31865, _thread, pin_module):
        self.lock = _thread.allocate_lock()
        self.sensor = max31865.MAX31865(
            wires = 3, rtd_nominal = 100, ref_resistor = 430,
            pin_sck = 6, pin_mosi = 3, pin_miso = 4, pin_cs = 5
            )
        
    # Function to get temperature from sensor
    def read_temperature(self):
        
        # Get 7 samples of temperature and calculate average to avoid the noise
        # Create an array for temperature samples
        temps = []        
        self.lock.acquire()
        
        # Get 7 temperature samples to array
        for i in range(7):
            temps.append(self.sensor.temperature)
        self.lock.release()
        
        # Calculate temperature average
        temperature = round((sum(temps) / len(temps)), 2)
    
        return temperature
