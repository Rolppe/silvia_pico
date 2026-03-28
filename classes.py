# ============================================================================
# PUMP RATIO CALCULATOR
# ============================================================================

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
        
        
# ============================================================================
# BREW STATS LOGGER
# ============================================================================

class BrewStatsLogger:
    def __init__(self_utime, asyncio):
        self.asyncio = asyncio_module
        self.pressure = 0
        self.start_time = 0
        self.boiler_temperature = 0
        self.pump_ratio = 0
        self.resolution = 1 # times in second
        self.file_name = "brew_log.txt"
        
        
# ============================================================================
# BREW DATA 
# ============================================================================

###### Class to share data between the cores ####
class BrewData:
    def __init__(self, Pin, ADC, PINS, TARGET_TEMPERATURES, FEATURES, heating_speed_calculator, temperature_sensor, pressure_sensor):
        self.heating_speed_calculator = heating_speed_calculator
        self.temperature_sensor       = temperature_sensor
        self.pressure_sensor          = pressure_sensor
        self.SWITCH_BREW      = Pin(PINS['SWITCH_BREW'], Pin.IN, Pin.PULL_DOWN)
        self.SWITCH_STEAM     = Pin(PINS['SWITCH_STEAM'], Pin.IN, Pin.PULL_DOWN)
        self.SWITCH_WATER     = Pin(PINS['SWITCH_WATER'], Pin.IN, Pin.PULL_DOWN)
        self.LED_SWITCH_BREW  = Pin(PINS['LED_SWITCH_BREW'], Pin.OUT, value=0)
        self.LED_SWITCH_WATER = Pin(PINS['LED_SWITCH_WATER'], Pin.OUT, value=0)
        self.LED_SWITCH_STEAM = Pin(PINS['LED_SWITCH_STEAM'], Pin.OUT, value=0)
        self.RELAY_PUMP       = Pin(PINS['RELAY_PUMP'], Pin.OUT, value=0)
        self.RELAY_SOLENOID   = Pin(PINS['RELAY_SOLENOID'], Pin.OUT, value=0)
        self.RELAY_HEATER     = Pin(PINS['RELAY_HEATER'], Pin.OUT, value=0)
        self.BACKFLUSH_PHASE_1_temperature = TARGET_TEMPERATURES['BACKFLUSH_PHASE_1']
        self.BACKFLUSH_PHASE_2_temperature = TARGET_TEMPERATURES['BACKFLUSH_PHASE_2']
        self.BACKFLUSH_PHASE_3_temperature = TARGET_TEMPERATURES['BACKFLUSH_PHASE_3']
        self.BACKFLUSH_END_temperature     = TARGET_TEMPERATURES['BACKFLUSH_END']
        self.pressure_soft_release   = FEATURES['soft_pressure_release_flag']
        self.fast_heatup_mode        = FEATURES['fast_heatup_mode_flag']
        self.pre_infusion_mode       = FEATURES['pre_infusion_mode_flag']
        self.pressure_soft_release_time = 0
        self.pre_infusion_time  = 0
        self.brew_temperature   = 97
        self.steam_temperature  = 125
        self.pre_heat_time      = 0
        self.boiler_temperature = 0
        self.brew_pressure      = 8
        self.pressure           = 0
        self.target_temperature = 0
        self.heating_speed      = 0
        self.fast_heatup_mode   = False
        self.setting_changed    = True
        self.mode               = "IDLE"
    
# ===== SETTERS  ====== #

    # ===== SETTERS MISCELIOUS ====== #
        
    def set_attribute(self, attribute_name, value):
        setattr(self, attribute_name, value)
    
    def set_setting_changed(self):
        print("brew_data.set_setting_changed()")
        self.setting_changed = True
        
        
    # ===== SETTERS - MODES ====== #

    def set_mode(self, mode):
        self.mode = mode
    
    
    def set_fast_heatup_mode(self, enabled):
        self.fast_heatup_mode = enabled
        self.setting_changed = True
        
        
    def set_pre_infusion_mode(self, enabled):
        self.pre_infusion_mode = enabled
        self.setting_changed = True
        
        
    def set_pressure_soft_release_mode(self, enabled):
        self.set_pressure_soft_release_mode = enabled
        self.setting_changed = True
        
        
    def set_pressure_soft_release_time(self, seconds):
        self.pressure_soft_release_time = seconds
        self.setting_changed = True
        
        
    # ===== SETTERS - TARGETS ====== #

    def set_target_temperature(self, target_temperature):
        self.target_temperature = target_temperature
        self.set_setting_changed()


    def set_brew_temperature(self, brew_temperature):
        print("set_brew_temperature")
        self.brew_temperature = brew_temperature
        self.setting_changed = True


    def set_steam_temperature(self, steam_temperature):
        self.steam_temperature = steam_temperature
        self.setting_changed = True


    def set_brew_pressure(self, pressure):
        self.brew_pressure   = brew_pressure
        self.setting_changed = True


    # ===== SETTERS - REALTIME DATA ====== #

    def set_boiler_stats(self, target_temperature, heating_speed):
        self.target_temperature = target_temperature
        self.heating_speed = heating_speed
        
        
    def set_heating_speed(self, heating_speed):
        self.heating_speed = heating_speed
    
    
    def set_boiler_temperature(self, boiler_temperature):
        self.boiler_temperature = boiler_temperature
        
        
    def set_pressure(self, pressure):
        self.pressure = pressure
    

    # ===== SETTERS - TIMES ====== #

    def set_pre_infusion_time(self, time):
        self.pre_infusion_time = time
        self.setting_changed = True
    
    
# ===== GETTERS ====== #
    
    # ===== GETTERS MISCELIOUS ====== #
    
    def get_setting_changed(self):
        setting_changed = self.setting_changed
        self.setting_changed = False
        
        return setting_changed
    

    def get_attribute(self, attribute_name):
            return getattr(self, attribute_name)
        

    # ===== GETTERS - MODES ====== #
    
    def get_mode(self):
        mode = self.mode
        
        return mode
     
 
     def get_fast_heatup_mode(self):
        fast_heatup_mode = self.fast_heatup_mode
        
        return fast_heatup_mode
    
    
    def get_pre_infusion_mode(self):
        pre_infusion_mode = self.pre_infusion_mode
        
        return pre_infusion_mode
    

    def get_pressure_soft_release_mode(self):
        pressure_soft_release = self.pressure_soft_release
    
        return pressure_soft_release
    
    
    # ===== GETTERS - TARGETS ====== #

    def get_brew_pressure(self):
        brew_pressure = self.brew_pressure
        
        return brew_pressure
    

    def get_brew_temperature(self):
        brew_temperature = self.brew_temperature
        
        return brew_temperature
    

    def get_steam_temperature(self):
        steam_temperature = self.steam_temperature
        
        return steam_temperature
    
    
    def get_target_temperature(self):
        if self.mode == "BREW":
            target_temperature = self.brew_temperature
        elif self.mode == "IDLE":
            target_temperature = self.brew_temperature
        elif self.mode == "STEAM":
            target_temperature = self.steam_temperature
        elif self.mode == "WATER":
            target_temperature = self.brew_temperature
        elif self.mode == "BACKFLUSH_PHASE_1":
            target_temperature = self.BACKFLUSH_PHASE_1_temperature
        elif self.mode == "BACKFLUSH_PHASE_2":
            target_temperature = self.BACKFLUSH_PHASE_2_temperature
        elif self.mode == "BACKFLUSH_PHASE_3":
            target_temperature = self.BACKFLUSH_PHASE_3_temperature
        elif self.mode == "BACKFLUSH_END":
            target_temperature = self.BACKFLUSH_END_temperature
        else:
            target_temperature = self.brew_temperature
        
        return target_temperature
    
    
    # ===== GETTERS - REALTIME DATA ====== #
    
    def get_pressure(self):
        self.pressure = self.pressure_sensor.get_pressure()
        pressure = self.pressure
        
        return pressure


    def get_boiler_temperature(self):
        self.boiler_temperature = self.temperature_sensor.read_temperature()
        boiler_temperature = self.boiler_temperature
        
        return boiler_temperature
    

    def get_heating_speed(self):
        self.heating_speed = self.heating_speed_calculator.get_heating_speed(self.boiler_temperature)
        heating_speed = self.heating_speed
        
        return heating_speed
    
    
    def get_boiler_stats(self):
        boiler_temperature = self.boiler_temperature
        brew_temperature   = self.brew_temperature
        steam_temperature  = self.steam_temperature
        heating_speed      = self.heating_speed
        
        return boiler_temperature, brew_temperature, steam_temperature, heating_speed
    
    
    # ===== GETTERS - TIMES ====== #
    
    def get_pressure_soft_release_time(self):
        pressure_soft_release_time = self.pressure_soft_release_time
    
        return pressure_soft_release_time
    
    
    def get_pre_infusion_time(self):
        time = self.pre_infusion_time
        
        return time
    
    
    def get_pre_heat_time(self):
        pre_heat_time = self.pre_heat_time
        
        return pre_heat_time
    
    
    # ===== GETTERS - SWITCHES ====== #
    
    def get_switch_brew(self):
        SWITCH_BREW = self.SWITCH_BREW
        
        return SWITCH_BREW
    
    
    def get_switch_water(self):
        SWITCH_WATER = self.SWITCH_WATER
        
        return SWITCH_WATER
    
    
    def get_SWITCH_STEAM(self):
        SWITCH_STEAM = self.SWITCH_STEAM
        
        return SWITCH_STEAM
    
    
    def get_switches(self):
        SWITCH_BREW  = self.SWITCH_BREW
        SWITCH_WATER = self.SWITCH_WATER
        SWITCH_STEAM = self.SWITCH_STEAM
        
        return SWITCH_BREW, SWITCH_WATER, SWITCH_STEAM
    
    
    # ===== GETTERS - LEDS ====== #
    
    def get_leds(self):
        LED_SWITCH_BREW  = self.LED_SWITCH_BREW  
        LED_SWITCH_WATER = self.LED_SWITCH_WATER 
        LED_SWITCH_STEAM = self.LED_SWITCH_STEAM
        
        return LED_SWITCH_BREW, LED_SWITCH_WATER, LED_SWITCH_STEAM
    
    
    # ===== GETTERS - RELAYS ====== #
    
    def get_relays(self):
        RELAY_PUMP     = self.RELAY_PUMP
        RELAY_SOLENOID = self.RELAY_SOLENOID
        RELAY_HEATER   = self.RELAY_HEATER
        
        return RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER

# ============================================================================
# PRESSURE MONITOR
# ============================================================================

class PressureSensor:
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
            #print("Pressure: " +str(pressure_bar) +" Bar")
    

# ============================================================================
# THERMOSTAT
# ============================================================================

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

        target_temperature = self.brew_data.get_target_temperature()
        

        # Nullify negative heating speed values
        if heating_speed < 0:
            heating_speed = 0
            
        # If boiler temperature is lower than target temperature - heating speed
        if (boiler_temperature < (target_temperature - (heating_speed * 2))):
            
            # Start heating the boiler          
            if (Thermostat.heat_cycler(self, boiler_temperature, target_temperature)):
                #print("target_temperature" + str(target_temperature))
                self.RELAY_HEATER.value(1)
            else:
                self.RELAY_HEATER.value(0)
                
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


# ============================================================================
# HEATING SPEED CALCULATOR
# ============================================================================

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
        
        if time_between == 0:
            return self.heating_speed
        
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
            heating_speed = 0
            
        return heating_speed
  

# ============================================================================
# TEMPERATURE SENSOR
# ============================================================================

#### Class for reading pt100 sensor temperature with max31865 ####
class TemperatureSensor:
    def __init__(self, max31865, PINS, MAX31865_CONFIG):
        self.temperature_sensor = max31865.MAX31865(
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
        temp = self.temperature_sensor.temperature
        
        # Value error handling
        while (temp < 2 or temp > 200):
            print("Temperature sensor error")
            temp = self.temperature_sensor.temperature
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

