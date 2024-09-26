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
    def __init__(self, _thread, brew_switch, steam_switch, water_switch):
        self.lock = _thread.allocate_lock()
        self._thread = _thread
        self.brew_switch = brew_switch
        self.steam_switch = steam_switch
        self.water_switch = water_switch
        self.relay_heater_value = 0
        self.relay_solenoid_value = 0
        self.relay_pump_value = 0
        self.setting_changed = False
        self.pre_infusion_time = 0
        self.brew_temperature = 100
        self.steam_temperature = 130
        self.pressure_soft_release_time = 0
        self.pre_heat_time = 0
        self.mode = ""
        self.boiler_temperature = 0
        self.target_temperature = 0
        self.heating_speed = 0
    
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
        
    def set_boiler_stats(self, target_temperature, heating_speed):
        self.lock.acquire()
        self.target_temperature = target_temperature
        self.heating_speed = heating_speed
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
    
    def set_boiler_temperature(self, boiler_temperature):
        self.lock.acquire()
        self.boiler_temperature = boiler_temperature
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
    
        # Function to get the states of the switches
    def get_switches_state(self):
        self.lock.acquire()
        brew_switch = self.brew_switch
        steam_switch = self.steam_switch
        water_switch = self.water_switch
        self.lock.release()
        return brew_switch, steam_switch, water_switch
    
    # Function to get state of the brew switch
    def get_brew_switch_state(self):
        self.lock.acquire()
        brew_switch = self.brew_switch
        self.lock.release()
        return brew_switch
    
    # Function to get the state of the brew switch
    def get_water_switch_state(self):
        self.lock.acquire()
        water_switch = self.water_switch
        self.lock.release()
        return water_switch
    
    # Function to get the state of the steam switch
    def get_steam_switch_state(self):
        self.lock.acquire()
        steam_switch = self.steam_switch
        self.lock.release()
        return steam_switch

    def get_boiler_temperature(self):
        self.lock.acquire()
        boiler_temperature = self.boiler_temperature
        self.lock.release()
        return boiler_temperature
    
    def get_target_temperature(self):
        self.lock.acquire()
        target_temperature = self.target_temperature
        self.lock.release()
        return target_temperature

    def get_heating_speed(self):
        self.lock.acquire()
        heating_speed = self.heating_speed
        self.lock.release()
        return heating_speed
    
    def get_boiler_stats(self):
        self.lock.acquire()
        boiler_temperature = self.boiler_temperature
        brew_temperature = self.brew_temperature
        steam_temperature = self.steam_temperature
        heating_speed = self.heating_speed
        self.lock.release()
        return boiler_temperature, brew_temperature, steam_temperature, heating_speed
    
    def get_pre_heat_time(self):
        self.lock.acquire()
        pre_heat_time = self.pre_heat_time
        self.lock.release()
        return pre_heat_time

    def get_pressure_soft_release_time(self):
        self.lock.acquire()
        pressure_soft_release_time = self.pressure_soft_release_time
        self.lock.release()
        return pressure_soft_release_time
        
class Thermostat:
    def __init__(self):
        self.cycle_count = 0
        
    def run(self, brew_data, switch_steam, relay_heater):
        
        # Get data
        boiler_temperature, brew_temperature, steam_temperature, heating_speed = brew_data.get_boiler_stats()
        
        # If steam switch is off: set brewing temperature as a target temperature
        if switch_steam.value() == 0:
            target_temperature = brew_temperature     
        
        # Otherwise set steam temperature as a target temperature
        else:
            target_temperature = steam_temperature
        
        # If boiler is at least 1 degree celsius lower than target temperature
        if boiler_temperature < target_temperature -1:
                
                # Set mode to "Heating"
                brew_data.set_mode("Heating")
        
        # Otherwise if target temperature is at leas 1 degree celsius warmer than target temperature
        elif boiler_temperature >  target_temperature +1:
            
            # Set mode to "Cooling down"
            brew_data.set_mode("Cooling down")
        
        # Otherwise
        else:
            
            # If target temperature is same as brewing temperature set mode to "Brew standby"
            if target_temperature == brew_temperature:
                brew_data.set_mode("Brew standby")
            
            # Otherwise set mode to "Steam standby"
            else:
                brew_data.set_mode("Steam standby") 
        
        # If boiler temperature is lower than target temperature - heating speed
        if (boiler_temperature < (target_temperature - heating_speed)):
            
            # Start heating the boiler          
            if (Thermostat.heat_cycler(self, boiler_temperature, target_temperature)):
                relay_heater.value(1)
            else:
                relay_heater.value(0)
                
        # Othervice, stop heating the boiler
        else:
            relay_heater.value(0)
            
    def heat_cycler(self, temperature, target_temperature):
        return_bool = False
        heater_limit = self.cycle_count * 10

        temperature_difference = int((temperature - target_temperature) *20)
        
        if (temperature_difference >= 0):
            print ("tääällä")
            if (self.cycle_count < 10):
                return_bool = True
            else:
                return_bool = False       
        
        else:
            if (abs(temperature_difference) > heater_limit):
                return_bool = True
            else:
                return_bool = False
        
        
        if (self.cycle_count >= 9):
            self.cycle_count = 0
        else:
            self.cycle_count = self.cycle_count +1
        
        if return_bool:
            return True
        else:
            return False
        
    # Function to get temperature
    def get_temperature(self):
        self.lock.acquire()
        temperature = round(self.temperature, 2)
        self.lock.release()
        return temperature


# Class to calculate heating speed
class HeatingSpeedCalculator:
    def __init__(self, utime_module):
        self.temperature_begin = 20.0
        self.utime = utime_module
        self.time_start = self.utime.ticks_ms()
        #self.heating_speed_multiplier = 0.8
   
    # Function to calculate heating speed
    def get_heating_speed(self, temperature_now):
        
        # Get time now
        time_now = self.utime.ticks_ms()
        
        # Calculate time between now and starting point
        time_between = self.utime.ticks_diff(time_now, self.time_start)
        
        # Set time now as start time
        self.time_start = time_now
        
#         print("Type of temperature_now:" +str(type(temperature_now)))     # For testing
#         print("Type of :" +str(type(self.temperature_begin)))
#         print("value of temperature_now:" +str(temperature_now))
#         print("value of :" +str(self.temperature_begin))

        # Calculate temperature change between now and starting point
        temperature_between = temperature_now - self.temperature_begin
        
        # Set temperature now to start temperature
        self.temperature_begin = temperature_now
        
        # Calculate heating speed
        self.heating_speed = temperature_between / time_between * 10000 # * self.heating_speed_multiplier
        
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
            wires = 3, rtd_nominal = 100.0, ref_resistor = 430.0,
            pin_sck = 6, pin_mosi = 3, pin_miso = 4, pin_cs = 5
            )

    # Function to get temperature from sensor
    def read_temperature(self):
        temperature_bias = 0.0
        # Get 7 samples of temperature and calculate average to avoid the noise
        # Create an array for temperature samples
        temps = []        
        #self.lock.acquire()
        # Get 7 temperature samples to array
        #for i in range(7):
        #    temps.append(self.sensor.temperature)
        #self.lock.release()

        # Calculate temperature average
        temperature = round((self.sensor.temperature), 2)#round((sum(temps) / len(temps)), 2)
        # Create error handling
        if temperature < 15:
            temperature = 150
            print("Temperature sensor error")
        
        # Bias temperature value
        temperature = temperature + temperature_bias
        return temperature

