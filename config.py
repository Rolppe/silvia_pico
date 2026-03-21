# ============================================================================
# FEATURES
# ============================================================================

FEATURES = {
    # Core features
    'pid_control_flag'               : True,   # PID temperature control (standby/steam)
    'pressure_control_flag'          : True,   # Dynamic pressure control
    'pre_infusion_flag'              : True,   # Pre-infusion before brewing
    'fast_heatup_mode_flag'          : False,
    'pre_infusion_mode_flag'         : True,
    'after_brew_pressure_drain_flag' : False,
    
    
    'pre_infusion_pressure_buildup_time' : 0,
    'pre_infusion_time'                  : 5,
    'soft_pressure_release_time'         : 2,
    'brew_pressure_bar'                  : 9
    }

# ============================================================================
# HARDWARE CONFIGURATION - GPIO PINS
# ============================================================================

PINS = {
    # Input switch's
    'SWITCH_BREW'      : 7,
    'SWITCH_WATER'     : 8,
    'SWITCH_STEAM'     : 9,
    
    # Switch led's
    'LED_BREW_SWITCH'  : 14,
    'LED_WATER_SWITCH' : 15,
    'LED_STEAM_SWITCH' : 16,
    
    # Output relays
    'RELAY_PUMP'       : 11,
    'RELAY_SOLENOID'   : 12,
    'RELAY_HEATER'     : 13,
    
    # Temperature MAX31865 (SPI)
    'TEMP_SCK'         : 6,
    'TEMP_MOSI'        : 3,
    'TEMP_MISO'        : 4,
    'TEMP_CS'          : 5,
    
    # Pressure sensor (ADC)
    'PRESSURE_ADC'     : 28
    }

# ============================================================================
# TEMPERATURE SENSOR MAX31865 CONFIGURATION
# ============================================================================

MAX31865_CONFIG = {
    'NUMBER_OF_WIRES'    : 3, 
    'RTD_NOMINAL'        : 100,
    'REF_RESISTOR'       : 430.0
    }

# ============================================================================
# TEMPERATURES Celsius
# ============================================================================

TARGET_TEMPERATURES = {
    'IDLE'    : 98,
    'BREW'    : 98, 
    'STEAM'   : 137,
    
    # Backflush program temperatures
    'BACKFLUSH_PHASE_1' : 95,
    'BACKFLUSH_PHASE_2' : 100,
    'BACKFLUSH_PHASE_3' : 110,
    'BACKFLUSH_END'     : 98
    }
