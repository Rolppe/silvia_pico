class LockPrinter:
    def __init__(self, thread_module):        
        self.lock_print = thread_module.allocate_lock()

    def print(self, first_parameter, second_parameter=""):
        self.lock_print.acquire()
        print(first_parameter, second_parameter)
        self.lock_print.release()


class BrewSettings:
    def __init__(self, utime_module, thread_module):
        self.lock = thread_module.allocate_lock()
        self.utime_module = utime_module
        self.thread_module = thread_module
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
        
    def set_mode(self, mode):
        self.lock.acquire()
        self.mode = mode
        self.lock.release()
        
    def set_static_values(self, brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time):
        self.lock.acquire()
        self.brew_temperature = brew_temperature
        self.steam_temperature = steam_temperature
        self.pre_infusion_time = pre_infusion_time
        self.pressure_soft_release_time = pressure_soft_release_time
        self.pre_heat_time = pre_heat_time
        self.setting_changed = True
        self.lock.release()
        
    def set_switches_state(self, brew_switch_state, steam_switch_state, water_switch_state):
        self.lock.acquire()
        self.brew_switch_state = brew_switch_state
        self.steam_switch_state = steam_switch_state
        self.water_switch_state = water_switch_state
        self.lock.release()
        
    def set_pre_infusion_time(self, time):
        self.lock.acquire()
        self.pre_infusion_time = time
        self.setting_changed = True
        self.lock.release()
        
    def set_brew_temperature(self, temperature):
        self.lock.acquire()
        self.utime_module.sleep_ms(1)
        self.brew_temperature = temperature
        self.setting_changed = True
        self.lock.release()
        
    def get_mode(self):
        self.lock.acquire()
        mode = self.mode
        self.lock.release()
        return mode
    
    def get_static_values(self):
        self.lock.acquire()
        brew_temperature = self.brew_temperature
        steam_temperature = self.steam_temperature
        pre_infusion_time = self.pre_infusion_time
        pressure_soft_release_time = self.pressure_soft_release_time
        pre_heat_time = self.pre_heat_time
        self.lock.release()
        return brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time

    def get_switches_state(self):
        self.lock.acquire()
        brew_switch_state = self.brew_switch_state
        steam_switch_state = self.steam_switch_state 
        water_switch_state = self.water_switch_state
        self.lock.release()
        return brew_switch_state, steam_switch_state, water_switch_state
    
    def get_pre_infusion_time(self):
        self.lock.acquire()
        time = self.pre_infusion_time
        self.lock.release()
        return time
    
    def get_brew_temperature(self):
        self.lock.acquire()
        brew_temperature = self.brew_temperature
        self.lock.release()
        return brew_temperature

    def get_changed_state(self):
        self.lock.acquire()
        setting_changed = self.setting_changed
        self.setting_changed = False
        self.lock.release()
        return setting_changed
    
    def get_brew_switch_state(self):
        self.lock.acquire()
        brew_switch_state = self.brew_switch_state
        self.lock.release()
        return brew_switch_state
    
    def get_water_switch_state(self):
        self.lock.acquire()
        water_switch_state = self.water_switch_state
        self.lock.release()
        return water_switch_state
    
    def get_steam_switch_state(self):
        self.lock.acquire()
        steam_switch_state = self.steam_switch_state
        self.lock.release()
        return steam_switch_state
    
    
class VirtualBoiler:
    def __init__(self, thread_module):
        self.lock = thread_module.allocate_lock()
        self.temperature = 70
        self.heating_speed = 0

    def heat_up(self, amount = 1):
        self.lock.acquire()
        heating_speed = self.heating_speed
        temperature = self.temperature
        self.temperature = round(temperature + heating_speed, 1)
        if heating_speed < 1:
            self.heating_speed += 0.2 * amount
        self.lock.release()
        
    def cooldown(self, amount = 1):
        self.lock.acquire()
        heating_speed = self.heating_speed
        temperature = self.temperature
        self.temperature = temperature + heating_speed
        if heating_speed > -0.2:
            self.heating_speed -= 0.1 * amount
        self.lock.release()
        
    def get_temperature(self):
        self.lock.acquire()
        temperature = round(self.temperature, 1)
        self.lock.release()
        return temperature
    
    
class HeatingSpeedCalculator:
    def __init__(self, utime_module, heating_speed_multiplier):
        self.acation = 0
        self.temperature_begin = 22
        self.utime = utime_module
        self.time_start = self.utime.ticks_ms()
        self.heating_speed_multiplier = heating_speed_multiplier

        
    def get_heating_speed(self, temperature):
        time_now = self.utime.ticks_ms()
        time_between = self.utime.ticks_diff(time_now, self.time_start)
        self.time_start = time_now

        temperature_between = temperature - self.temperature_begin
        self.temperature_begin = temperature
        self.heating_speed = temperature_between / time_between
        
        heating_speed = self.heating_speed * 10000 * self.heating_speed_multiplier
        
        # Poista aloituspiikki lämpötilan muutosnopeudesta
        if heating_speed > 100:
            heating_speed = 0
            
        return heating_speed 