import os

# ============================================================================
#  PRE-INFUSION
# ============================================================================

async def pre_infusion(brew_data, utime, asyncio, pump_ratio_calculator):
    
    RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER = brew_data.get_relays()
    SWITCH_BREW = brew_data.get_switch_brew()
    
    brew_data.set_mode('pre-infusion initialization')
    pressure = brew_data.get_pressure()
    
    last_pump_ratio_time = utime.ticks_ms()
    
    # Get boiler temperature
    boiler_temperature = brew_data.get_boiler_temperature()
    
    # Open solenoid for water to flow to grouphead
    RELAY_SOLENOID.value(1)
    
    # If theres a pressure in system, let stabilize to pre-infusion pressure
    while pressure > 1.9 and SWITCH_BREW.value():
        
        brew_data.set_mode('pre-infusion pressure stabilization')
        
        # Read sensor pressure
        pressure = brew_data.get_pressure()
        
        # Get boiler temperature
        boiler_temperature = brew_data.get_boiler_temperature()

        await asyncio.sleep_ms(100)
        
        
    # ===== PRE-INFUSION PRESSURE BUILD UP ===== #
    
    # Start building pre-infusion pressure by turning pump on.
    RELAY_PUMP.value(1)
    pump_ratio_calculator.set_pump_on()

    
    # Keep pump on till almost pre-infusion pressure, just a bit under to prevent pressure overshooting
    while pressure < 1.9 and SWITCH_BREW.value():
            
        brew_data.set_mode('pre-infusion pressure build-up')
        
        # Read sensor pressure
        pressure = brew_data.get_pressure()
        
        # Get boiler temperature
        boiler_temperature = brew_data.get_boiler_temperature()
     
        await asyncio.sleep_ms(50)

    RELAY_PUMP.value(0)
    pump_ratio_calculator.set_pump_off()

    # Let pressure stabilize
    await asyncio.sleep_ms(50)
    
    # Create timer for preinfusion
    start = utime.ticks_ms()
    end = utime.ticks_add(start, 5000)       
        
    
    # ===== PREINFUSION WITH REACHED PRESSURE ===== #
    
    # Create timed preinfusion loop
    while utime.ticks_diff(end, utime.ticks_ms()) > 0 and SWITCH_BREW.value():
        
        brew_data.set_mode('pre-infusion main')
        
        # Read sensor pressure
        pressure = brew_data.get_pressure()
        
        # Get boiler temperature
        boiler_temperature = brew_data.get_boiler_temperature()
        
        
        # ===== PRESSURE HANDLING ===== #
               
        if brew_data.get_pressure() < 2.0:
            RELAY_PUMP.value(1)
            pump_ratio_calculator.set_pump_on()
            await asyncio.sleep_ms(35)
            RELAY_PUMP.value(0)
            pump_ratio_calculator.set_pump_off()

        if utime.ticks_diff(utime.ticks_ms(), last_pump_ratio_time) >= 1000:
            pump_ratio = round(pump_ratio_calculator.get_ratio())
            brew_data.set_pump_ratio(pump_ratio)
            last_pump_ratio_time = utime.ticks_ms()
            
        await asyncio.sleep_ms(50)


# ============================================================================
# FAST HEATUP
# ============================================================================

async def fast_heatup(utime, brew_data): 
        
    RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER = brew_data.get_relays()
    
    # Fill the boiler
    RELAY_SOLENOID.value(1)
    RELAY_PUMP.value(1)
    await asyncio.sleep(2)
    RELAY_PUMP.value(0)
    RELAY_SOLENOID.value(0)

    # Heat the boiler
    RELAY_HEATER.value(1)
    while brew_data.get_boiler_temperature() < 85:
        await asyncio.sleep(1)
    while brew_data.get_boiler_temperature() < 110:
        RELAY_HEATER.value(1)
        await asyncio.sleep(1)
        RELAY_HEATER.value(0)
        await asyncio.sleep(1.5)
    while brew_data.get_boiler_temperature() < 115:
        RELAY_HEATER.value(1)
        await asyncio.sleep(1)
        RELAY_HEATER.value(0)
        await asyncio.sleep(2)
    
    # keep the temperature
    for i in range(200):
        if brew_data.get_boiler_temperature() < 115:
            RELAY_HEATER.value(1)
            await asyncio.sleep(1)
            RELAY_HEATER.value(0)
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(1)
        await asyncio.sleep(1)
    
    # Cool the boiler to under 105 celsius
    while brew_data.get_boiler_temperature() > 99:
        await asyncio.sleep(1)
        
    # Fill the boiler
    RELAY_SOLENOID.value(1)
    RELAY_PUMP.value(1)
    await asyncio.sleep(0.5)
    RELAY_PUMP.value(0)
    RELAY_SOLENOID.value(0)
    
    # Sleep while boiler stabilizes
    await asyncio.sleep(15)


# ============================================================================
# PRINT VALUES
# ============================================================================

def print_values(brew_data):
 
    # Get state of data
    boiler_temperature = brew_data.get_boiler_temperature()
    mode               = brew_data.get_mode()
    heating_speed      = brew_data.get_heating_speed()
    
    RELAY_PUMP, RELAY_SOLENOID, RELAY_HEATER = brew_data.get_relays()
    SWITCH_BREW, SWITCH_WATER, SWITCH_STEAM  = brew_data.get_switches()
    
    # Print values
    print('Mode: ', mode)
    print('Boiler temperature: ', boiler_temperature)
    print('heating_speed: ',      heating_speed)
    print('switch_brew: ',        SWITCH_BREW.value())
    print('switch_water: ',       SWITCH_WATER.value()) 
    print('switch_steam: ',       SWITCH_STEAM.value())
    print('RELAY_HEATER: ',       RELAY_HEATER.value())
    print('RELAY_SOLENOID: ',     RELAY_SOLENOID.value())
    print('RELAY_PUMP: ',         RELAY_PUMP.value())
    print('')


# ============================================================================
# SAVE SETTINGS
# ============================================================================

def save_settings(brew_data, json_module):
    # Get settings from brew_data object
    brew_temperature           = brew_data.get_brew_temperature()
    steam_temperature          = brew_data.get_steam_temperature()
    pre_infusion_time          = brew_data.get_pre_infusion_time()
    pressure_soft_release_time = brew_data.get_pressure_soft_release_time()
    pre_heat_time              = brew_data.get_pre_heat_time()
    pre_infusion_mode          = brew_data.get_pre_infusion_mode()
    pressure_soft_release_mode = brew_data.get_pressure_soft_release_mode()
    fast_heatup_mode           = brew_data.get_fast_heatup_mode()
    
    # Form the data
    data = {
        'brew_temperature'          : brew_temperature,
        'steam_temperature'         : steam_temperature,
        'pre_infusion_time'         : pre_infusion_time,
        'pressure_soft_release_time': pressure_soft_release_time,
        'pre_infusion_mode'         : pre_infusion_mode,
        'pressure_soft_release_mode': pressure_soft_release_mode,
        'fast_heatup_mode'          : fast_heatup_mode
    }
    
    # Save data to file in json format
    with open('settings.txt', 'w') as file:
        json_module.dump(data, file)
    
    print("save_settings")


# ============================================================================
# LOAD SETTINGS
# ============================================================================

def load_settings(json_module, brew_data):
    
    # Get values from file to variables
    try:
        with open('settings.txt', 'r') as file:
            data = json_module.load(file)
            
            brew_temperature           = data.get('brew_temperature')
            steam_temperature          = data.get('steam_temperature')
            pre_infusion_time          = data.get('pre_infusion_time')
            pressure_soft_release_time = data.get('pressure_soft_release_time')
            pre_infusion_mode          = data.get('pre_infusion_mode')
            pressure_soft_release_mode = data.get('pressure_soft_release_mode')
            fast_heatup_mode           = data.get('fast_heatup_mode')
        
        # Set settings to brew_data object
        brew_data.set_brew_temperature(brew_temperature)
        brew_data.set_steam_temperature(steam_temperature)
        brew_data.set_pre_infusion_time(pre_infusion_time)
        brew_data.set_pressure_soft_release_time(pressure_soft_release_time)
        brew_data.set_pre_infusion_mode(pre_infusion_mode)
        brew_data.set_pressure_soft_release_mode(pressure_soft_release_mode)
        brew_data.set_fast_heatup_mode(fast_heatup_mode)
        
        print('Loaded settings: brew_temperature, steam_temperature, pre_infusion_time, pressure_soft_release_time, pre_infusion_mode, pressure_soft_release_mode, fast_heatup_mode')
        return True
    
    # If data is not available: remove settings file and return False
    except (OSError, ValueError):   # ValueError = JSON syntax error 
        try:
            os.remove('settings.txt')
            print('settings.txt deleted pecause of error')
        except OSError:
            print('tried to delete settings.txt pecause of error but theres error in file deleting process')
        
        return False





