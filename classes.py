# Luokka joka tekee vuorottaa säikeiden tulostukset
class LockPrinter:
    def __init__(self, _threadmodule):        
        self.lock_print = _threadmodule.allocate_lock()

    # Funktio tulostukseen
    def print(self, first_parameter, second_parameter=""):
        self.lock_print.acquire()
        print(first_parameter, second_parameter)
        self.lock_print.release()

# Luokka joka sisältää datan mikä liikkuu säikeiden välillä
class BrewData:
    def __init__(self, _threadmodule):
        self.lock = _threadmodule.allocate_lock()
        self._threadmodule = _threadmodule
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
    
    # Funktio mode tilan asettamiseen
    def set_mode(self, mode):
        self.lock.acquire()
        self.mode = mode
        self.lock.release()
    
    # Funktio uuttoasetusten asettamiseen
    def set_static_values(self, brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time):
        self.lock.acquire()
        self.brew_temperature = brew_temperature
        self.steam_temperature = steam_temperature
        self.pre_infusion_time = pre_infusion_time
        self.pressure_soft_release_time = pressure_soft_release_time
        self.pre_heat_time = pre_heat_time
        self.setting_changed = True
        self.lock.release()
        
    # Funktio kytkimien arvon asettamiseen
    def set_switches_state(self, brew_switch_state, steam_switch_state, water_switch_state):
        self.lock.acquire()
        self.brew_switch_state = brew_switch_state
        self.steam_switch_state = steam_switch_state
        self.water_switch_state = water_switch_state
        self.lock.release()
    
    # Funktio pre-infusion ajan asettamiseen
    def set_pre_infusion_time(self, time):
        self.lock.acquire()
        self.pre_infusion_time = time
        self.setting_changed = True
        self.lock.release()
        
    # Funktio uuttolämpötilan asettamiseen
    def set_brew_temperature(self, temperature):
        self.lock.acquire()
        self.brew_temperature = temperature
        self.setting_changed = True
        self.lock.release()
    
    # Funktio mode tilan hakemiseen
    def get_mode(self):
        self.lock.acquire()
        mode = self.mode
        self.lock.release()
        return mode
    
    # Funktio uuttoasetusten hakemiseen
    def get_settings(self):
        self.lock.acquire()
        brew_temperature = self.brew_temperature
        steam_temperature = self.steam_temperature
        pre_infusion_time = self.pre_infusion_time
        pressure_soft_release_time = self.pressure_soft_release_time
        pre_heat_time = self.pre_heat_time
        self.lock.release()
        return brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time
    
    # Funktio kytkimien asennon hakemiseen
    def get_switches_state(self):
        self.lock.acquire()
        brew_switch_state = self.brew_switch_state
        steam_switch_state = self.steam_switch_state 
        water_switch_state = self.water_switch_state
        self.lock.release()
        return brew_switch_state, steam_switch_state, water_switch_state
    
    # Funktio pre-infuusio ajan hakemiseen
    def get_pre_infusion_time(self):
        self.lock.acquire()
        time = self.pre_infusion_time
        self.lock.release()
        return time
    
    # Funktio uuttolämpötilan hakemiseen
    def get_brew_temperature(self):
        self.lock.acquire()
        brew_temperature = self.brew_temperature
        self.lock.release()
        return brew_temperature

    # Funktio kytkinten  hakemiseen
#     def get_changed_state(self):
#         self.lock.acquire()
#         setting_changed = self.setting_changed
#         self.setting_changed = False
#         self.lock.release()
#         return setting_changed
    
    # Funktio uutto-kytkimen arvon hakemiseen
    def get_brew_switch_state(self):
        self.lock.acquire()
        brew_switch_state = self.brew_switch_state
        self.lock.release()
        return brew_switch_state
    
    # Funktio vesi-kytkimen arvon hakemiseen
    def get_water_switch_state(self):
        self.lock.acquire()
        water_switch_state = self.water_switch_state
        self.lock.release()
        return water_switch_state
    
    # Funktio höyry-kytkimen hakemiseen
    def get_steam_switch_state(self):
        self.lock.acquire()
        steam_switch_state = self.steam_switch_state
        self.lock.release()
        return steam_switch_state
    

# Luokka joka toimii virtuaalisena lämmitys-kattilana
class VirtualBoiler:
    def __init__(self, _threadmodule):
        self.lock = _threadmodule.allocate_lock()
        self.temperature = 70
        self.heating_speed = 0
    
    # Funktio kattilan lämmittämiseen
    def heat_up(self, amount = 1):
        self.lock.acquire()
        heating_speed = self.heating_speed
        temperature = self.temperature
        
        # lisää lämpötilaan muutos
        self.temperature = round(temperature + heating_speed, 1)
        
        # Jos muutos nopeus on alle 1 lisää muutosnopeutta
        if heating_speed < 1:
            self.heating_speed += 0.2 * amount
        self.lock.release()
    
    # Funktio kattilan jäähdyttämiseen
    def cooldown(self, amount = 1):
        self.lock.acquire()
        heating_speed = self.heating_speed
        temperature = self.temperature
        
        # Lisää muutosnopeus lämpötilaan
        self.temperature = temperature + heating_speed
        
        # Jos muutosnopeus on yli -0.2 vähennä muutos nopeutta 
        if heating_speed > -0.2:
            self.heating_speed -= 0.1 * amount
        self.lock.release()
        
    # Funktio Lämpötilan hakemiseen
    def get_temperature(self):
        self.lock.acquire()
        temperature = round(self.temperature, 1)
        self.lock.release()
        return temperature
    
    
# Luokka kattilan lämmitysnopeuden laskemiseen
class HeatingSpeedCalculator:
    def __init__(self, utime_module, heating_speed_multiplier):
        #self.acation = 0
        self.temperature_begin = 0
        self.utime = utime_module
        self.time_start = self.utime.ticks_ms()
        self.heating_speed_multiplier = heating_speed_multiplier
   
    # Funktio lämmitysnopeuden laskemiseen
    def get_heating_speed(self, temperature_now):
        
        # Hae nykyinen aika
        time_now = self.utime.ticks_ms()
        
        # Laske aika aloituspisteestä tähän hetkeen
        time_between = self.utime.ticks_diff(time_now, self.time_start)
        
        # Aseta nykyinen aika aloitusajaksi
        self.time_start = time_now
        
        # Laske lämpötilamuutos aloitus lämpötilasta tämän hetken lämpötilaan
        temperature_between = temperature_now - self.temperature_begin
        
        # Aseta tämän hetkinen lämpötila aloituslämpötilaksi
        self.temperature_begin = temperature_now
        
        # Laske lämpenemisnopeus
        self.heating_speed = temperature_between / time_between * 10000 * self.heating_speed_multiplier
        
        # Pyöristä lämpötila nopeus
        heating_speed = round(self.heating_speed, 1)
        
        # Poista aloituspiikki lämpötilan muutosnopeudesta
        if heating_speed > 100:
            heating_speed = 0
            
        return heating_speed
    

# Luokka lämpötila sensorin lukemiseen
class Sensor:
    def __init__(self, max31865, _thread, pin_module):
        self.lock = _thread.allocate_lock()
        self.sensor = max31865.MAX31865(
            wires = 3, rtd_nominal = 100, ref_resistor = 430,
            pin_sck = 6, pin_mosi = 3, pin_miso = 4, pin_cs = 5
            )
        
    # Funktio lämpötilan hakemiseen sensorilta
    def read_temperature(self):
        
        # Laske ja palauta keskiarvo 6 peräkkäisestä mittauksesta välttääksesi kohinaa
        # Luo taulukko lämpötiloille
        temps = []        
        self.lock.acquire()
        
        # Täytä taulukkoon 7 lämpötilaa
        for i in range(7):
            temps.append(self.sensor.temperature)
        self.lock.release()
        
        # Laske lämpötilojen keskiarvo
        temperature = round((sum(temps) / len(temps)), 1)
    
        return temperature
