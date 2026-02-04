import asyncio

# ============================================================================
#   GET_IO
# ============================================================================
def get_IO(Pin, ADC, PINS):
    SWITCH_BREW     = Pin(PINS['SWITCH_BREW_PIN_NUMBER'], Pin.IN, Pin.PULL_DOWN)
    SWITCH_WATER    = Pin(PINS['SWITCH_WATER_PIN_NUMBER'], Pin.IN, Pin.PULL_DOWN)
    SWITCH_STEAM    = Pin(PINS['SWITCH_STEAM_PIN_NUMBER'], Pin.IN, Pin.PULL_DOWN)
    
    RELAY_PUMP      = Pin(PINS['RELAY_PUMP_PIN_NUMBER'], Pin.OUT, value=0)
    RELAY_SOLENOID  = Pin(PINS['RELAY_SOLENOID_PIN_NUMBER'], Pin.OUT, value=0)
    RELAY_HEATER    = Pin(PINS['RELAY_HEATER_PIN_NUMBER'], Pin.OUT, value=0)
    
    return SWITCH_BREW, SWITCH_WATER, SWITCH_STEAM, RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER


# ============================================================================
#  PRE-INFUSION
# ============================================================================
async def pre_infusion(relay_pump, relay_solenoid, relay_heater, switch_brew, utime, sensor, pressure_monitor, brew_data): #, ble_handler):
    
    # ===== PRESSURE DRAIN (TO BE MOVED) ===== #
    
    # Read sensor pressure
    pressure_bar = pressure_monitor.get_pressure()
    brew_data.set_pressure(pressure_bar)
    
    # Read pt100 sensor temperature
    boiler_temperature = sensor.read_temperature()
    brew_data.set_boiler_temperature(boiler_temperature)
    
    # Open solenoid for water to flow to grouphead
    relay_solenoid.value(1)
    
    # If theres a pressure in system, let stabilize to pre-infusion pressure
    while pressure_bar > 1.9 and switch_brew.value():
        
        print("pre-infusion pressure stabilization")
        # Read sensor pressure
        pressure_bar = pressure_monitor.get_pressure()
        brew_data.set_pressure(pressure_bar)
        
        # Read pt100 sensor temperature
        boiler_temperature = sensor.read_temperature()
        brew_data.set_boiler_temperature(boiler_temperature)

        await asyncio.sleep(0.1) # utime.sleep(0.1)
        
    # ===== PRE-INFUSION PRESSURE BUILD UP ===== #
    
    # Start building pre-infusion pressure by turning pump on.
    relay_pump.value(1)
    
    # Keep pump on till almost pre-infusion pressure, just a bit under to prevent pressure overshooting
    while pressure_bar < 1.9 and switch_brew.value():
            
        print("pre-infusion pressure build-up")
        
        # Read sensor pressure
        pressure_bar = pressure_monitor.get_pressure()
        brew_data.set_pressure(pressure_bar)
        
        # Read pt100 sensor temperature
        boiler_temperature = sensor.read_temperature()
        brew_data.set_boiler_temperature(boiler_temperature)
     
        await asyncio.sleep(0.1) # utime.sleep(0.1)

    # Let pressure stabilize
    await asyncio.sleep(0.1) # utime.sleep(0.1)
    
    # Create timer for preinfusion
    start = utime.ticks_ms()
    end = utime.ticks_add(start, 5000)       
        
    relay_pump.value(0)
    
    
    # ===== PREINFUSION WITH REACHED PRESSURE ===== #
    
    # Create timed preinfusion loop
    while utime.ticks_diff(end, utime.ticks_ms()) > 0 and switch_brew.value():
        
        print("pre-infusion main")
        
        # Read sensor pressure
        pressure_bar = pressure_monitor.get_pressure()
        brew_data.set_pressure(pressure_bar)
        
        # Read pt100 sensor temperature
        boiler_temperature = sensor.read_temperature()
        brew_data.set_boiler_temperature(boiler_temperature)
        
        # ===== PRESSURE HANDLING ===== #
               
        if pressure_monitor.get_pressure() < 2.0:
            relay_pump.value(1)
            await asyncio.sleep(0.035) # utime.sleep(0.035)
            relay_pump.value(0)
        
        await asyncio.sleep_ms(1) # utime.sleep(0.1)utime.sleep_ms(1)


# ============================================================================
# FAST HEATUP
# ============================================================================
async def fast_heatup(relay_pump, relay_solenoid, relay_heater, utime, sensor): #
        
    # Fill the boiler
    relay_solenoid.value(1)
    relay_pump.value(1)
    await asyncio.sleep(2) # utime.sleep(2)
    relay_pump.value(0)
    relay_solenoid.value(0)
    
   
 # Heat the boiler
    relay_heater.value(1)
    while sensor.read_temperature() < 85:
        await asyncio.sleep(1) # utime.sleep(1)
    while sensor.read_temperature() < 110:
        relay_heater.value(1)
        await asyncio.sleep(1) # utime.sleep(1)
        relay_heater.value(0)
        await asyncio.sleep(1.5) # utime.sleep(1.5)
    while sensor.read_temperature() < 115:
        relay_heater.value(1)
        await asyncio.sleep(1) # utime.sleep(1)
        relay_heater.value(0)
        await asyncio.sleep(2) # utime.sleep(2)
    
    # keep the temperature
    for i in range(200):
        if sensor.read_temperature() < 115:
            relay_heater.value(1)
            await asyncio.sleep(1) # utime.sleep(1)
            relay_heater.value(0)
            await asyncio.sleep(2) # utime.sleep(2)
        else:
            await asyncio.sleep(1) # utime.sleep(1)
        await asyncio.sleep(1) # utime.sleep(1)
    
    # Cool the boiler to under 105 celsius
    while sensor.read_temperature() > 99:
        await asyncio.sleep(1) # utime.sleep(1)
        
    # Fill the boiler
    relay_solenoid.value(1)
    relay_pump.value(1)
    await asyncio.sleep(0.5) # utime.sleep(0.5)
    relay_pump.value(0)
    relay_solenoid.value(0)
    
    # Sleep while boiler stabilizes
    await asyncio.sleep(15) # utime.sleep(15)


# ============================================================================
# PRINT VALUES
# ============================================================================
def print_values(brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump):
 
    # Get boiler temperature
    boiler_temperature = sensor.read_temperature()
    
    # Get mode from object
    mode = brew_data.get_mode()
    
    ## Get settings from brew_data object
    # brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
    
    brew_switch_state, steam_switch_state, water_switch_state = brew_data.get_switches_state()
    
    # Print values
    print("Mode: ", mode)
    print("Boiler temperature: ", boiler_temperature)
    print("heating_speed", heating_speed)
    print("switch_brew: ", brew_switch_state.value())
    print("switch_water: ", water_switch_state.value()) 
    print("switch_steam: ", steam_switch_state.value())
    print("relay_heater: ", relay_heater.value())
    print("relay_solenoid: ", relay_solenoid.value())
    print("relay_pump: ", relay_pump.value())
    print("","")


# ============================================================================
# SAVE SETTINGS
# ============================================================================
def save_settings(brew_data, json_module):
    
    # Get settings from brew_data object
    brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time = brew_data.get_settings()
    
    # Form the data
    data = {
        "brew_temperature": brew_temperature,
        "steam_temperature": steam_temperature,
        "pre_infusion_time": pre_infusion_time,
        "pressure_soft_release_time": pressure_soft_release_time,
        "pre_heat_time": pre_heat_time
    }
    
    # Save data to file in json format
    with open('settings.txt', 'w') as file:
        json_module.dump(data, file)


# ============================================================================
# LOAD SETTINGS
# ============================================================================
def load_settings(json_module, brew_data):
    
    # Get values from file to variables
    try:
        with open('settings.txt', 'r') as file:
            data = json_module.load(file)
            brew_temperature = data.get("brew_temperature")
            steam_temperature = data.get("steam_temperature")
            pre_infusion_time = data.get("pre_infusion_time")
            pressure_soft_release_time = data.get("pressure_soft_release_time")
            pre_heat_time = data.get("pre_heat_time")
        
    # If data is not available: return False
    except OSError:
        return False
    
    # Set settings to brew_data object
    brew_data.set_settings(brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_heat_time)
    
    # Return True
    return True





