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
    'SWITCH_BREW_PIN_NUMBER'    : 7,
    'SWITCH_WATER_PIN_NUMBER'   : 8,
    'SWITCH_STEAM_PIN_NUMBER'   : 9,

    # Output relays
    'RELAY_PUMP_PIN_NUMBER'     : 11,
    'RELAY_SOLENOID_PIN_NUMBER' : 12,
    'RELAY_HEATER_PIN_NUMBER'   : 13,
    
    # Temperature MAX31865 (SPI)
    'TEMP_SCK_PIN_NUMBER'       : 6,
    'TEMP_MOSI_PIN_NUMBER'      : 3,
    'TEMP_MISO_PIN_NUMBER'      : 4,
    'TEMP_CS_PIN_NUMBER'        : 5,
    
    # Pressure sensor (ADC)
    'PRESSURE_ADC_PIN_NUMBER'   : 28
    }

# ============================================================================
# TEMPERATURE SENSOR MAX31865 CONFIGURATION
# ============================================================================

MAX31865_CONFIG = {
    'NUMBER_OF_WIRES'    : 3, 
    'RTD_NOMINAL'        : 100,
    'REF_RESISTOR'       : 430.0
    }

            