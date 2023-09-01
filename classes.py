class LockPrinter:
    def __init__(self, thread_module):        
        self.lock_print = thread_module.allocate_lock()

    def print(self, first_parameter, second_parameter=""):
        self.lock_print.acquire()
        print(first_parameter, second_parameter)
        self.lock_print.release()

class BrewSettings:
    def __init__(self, utime_module, thread_module):
        self.brew_temperature = 20
        self.lock = thread_module.allocate_lock()
        self.utime_module = utime_module
        self.thread_module = thread_module
        self.brew_button_state = False
        self.steam_button_state = False
        self.water_button_state = False
        self.setting_changed = False
        self.pre_infusion_time = 0
        
    def set_pre_infusion_time(self, time):
        self.lock.acquire()
        self.utime_module.sleep_ms(1)
        self.pre_infusion_time = time
        self.setting_changed = True
        self.lock.release()
        
    def set_numeric_values(self, temperature, time):
        self.lock.acquire()
        # Varmista että get metodin return kerkeää valmistua
        self.utime_module.sleep_ms(1)
        self.brew_temperature = temperature
        self.pre_infusion_time = time
        self.setting_changed = True
        self.lock.release()
        
    def set_brew_temperature(self, temperature):
        self.lock.acquire()
        # Varmista että get metodin return kerkeää valmistua
        self.utime_module.sleep_ms(1)
        self.brew_temperature = temperature
        self.setting_changed = True
        self.lock.release()
        
    def set_buttons_state(self, brew_button_state, steam_button_state, water_button_state):
        self.brew_button_state = brew_button_state
        self.steam_button_state = steam_button_state
        self.water_button_state = water_button_state
    
    def set_change_brew_state(self):
        state = self.brew_button_state
        self.brew_button_state = not state
        
    def get_pre_infusion_time(self):
        time = self.pre_infusion_time
        return time
    
    def get_brew_temperature(self):
        self.lock.acquire()
        brew_temperature = self.brew_temperature
        self.lock.release()
        return brew_temperature
    
    def get_buttons_state(self):
        brew_button_state = self.brew_button_state
        steam_button_state = self.steam_button_state 
        water_button_state = self.water_button_state
        return brew_button_state, steam_button_state, water_button_state

    def get_changed_state(self):
        setting_changed = self.setting_changed
        self.setting_changed = False
        return setting_changed
    
    def get_brew_button_state(self):
        brew_button_state = self.brew_button_state
        return brew_button_state
    
    def get_numeric_values(self):
        temperature = self.brew_temperature
        time = self.pre_infusion_time
        return temperature, time



class VirtualBoiler:
    def __init__(self):
        self.temperature = 70
        self.acceleration = 0

    def heat(self):
        acceleration = self.acceleration
        temperature = self.temperature
        self.temperature = temperature + acceleration
        if acceleration < 1:
            self.acceleration += 0.2
        
    def cooldown(self):
        acceleration = self.acceleration
        temperature = self.temperature
        self.temperature = temperature + acceleration
        if acceleration > -0.2:
            self.acceleration -= 0.1
        
        
    def getTemperature(self):
        temperature = self.temperature
        return temperature
    
class AccelerationCalculator:
    def __init__(self, utime_module):
        self.acation = 0
        self.temperature_begin = 22
        self.utime = utime_module
        self.time_start = self.utime.ticks_ms()

        
    def get_acceleration(self, temperature):
        time_now = self.utime.ticks_ms()
        time_between = self.utime.ticks_diff(time_now, self.time_start)
        self.time_start = time_now

        temperature_between = temperature - self.temperature_begin
        self.temperature_begin = temperature
        self.acceleration = temperature_between / time_between
        
        acceleration = self.acceleration * 10000
        return acceleration