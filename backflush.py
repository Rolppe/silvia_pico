import utime
import asyncio
from machine import Pin

async def run_backflush(
    RELAY_PUMP,   
    RELAY_SOLENOID,
    RELAY_HEATER,
    SWITCH_BREW,
    SWITCH_WATER,
    SWITCH_STEAM,
    LED_BREW_SWITCH,
    LED_WATER_SWITCH,
    LED_STEAM_SWITCH,
    temperature_sensor,
    pressure_sensor,
    brew_data,
    thermostat
    ):

    
    # ────────────────────────────────────────────────
    # CONSTRAINTS
    # ────────────────────────────────────────────────
    
    TARGET_PRESSURE = 10
    MAX_PULSE_TIME_MS = 4000
    PULSES_PER_PHASE = 10
    PULSE_PAUSE_TIME_MS = 10000
    
    
    # ────────────────────────────────────────────────
    # LED HANDELING
    # ────────────────────────────────────────────────
    
    def turn_off_all_leds():
        LED_BREW_SWITCH.value(0)
        LED_WATER_SWITCH.value(0)
        LED_STEAM_SWITCH.value(0)

    async def slow_blink(led):
        led.value(1)
        await asyncio.sleep_ms(600)
        led.value(0)
        await asyncio.sleep_ms(400)

    async def fast_blink(led1, led2 = False, led3 = False):
        led1.value(1)
        if led2:
            led2.value(1)
        if led3:
            led3.value(1)
            
        await asyncio.sleep_ms(150)
        
        led1.value(0)
        if led2:
            led2.value(0)
        if led3:
            led3.value(0)
                
        await asyncio.sleep_ms(150)
        
    
    # ────────────────────────────────────────────────
    # Temperature and pressure updater
    # ────────────────────────────────────────────────
    
    async def temp_pres_handler():
        boiler_temperature = temperature_sensor.read_temperature()
        brew_data.set_boiler_temperature(boiler_temperature)
        pressure = pressure_sensor.get_pressure()
        brew_data.set_pressure(pressure)
        thermostat.run()
    
    # ────────────────────────────────────────────────
    # AUDIABLE SIGNAL
    # ────────────────────────────────────────────────
    
    
    async def signal_beep():
        for x in range(4):
            RELAY_PUMP.value(1)
            RELAY_SOLENOID.value(1)
            await asyncio.sleep_ms(200)
            RELAY_PUMP.value(0)
            RELAY_SOLENOID.value(0)
            await asyncio.sleep_ms(300)
    
    
    # ────────────────────────────────────────────────
    # PULSE
    # ────────────────────────────────────────────────
    
    async def perform_pressure_pulse():
        RELAY_SOLENOID.value(1)
        RELAY_PUMP.value(1)
        start = utime.ticks_ms()

        while True:
            await temp_pres_handler()
            
            pressure = pressure_sensor.get_pressure()
            if pressure >= TARGET_PRESSURE:
                RELAY_PUMP.value(0)
                break
            if utime.ticks_diff(utime.ticks_ms(), start) > MAX_PULSE_TIME_MS:
                RELAY_PUMP.value(0)
                print("  WARNING: Pulse timeout")
                break

        RELAY_SOLENOID.value(0)
        
        # Management between pulses
        pause_timer_start = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), pause_timer_start) < PULSE_PAUSE_TIME_MS:
            await temp_pres_handler()
            asyncio.sleep_ms(50)
    
    
    # ────────────────────────────────────────────────
    # PHASE
    # ────────────────────────────────────────────────
    
    async def run_phase(phase):
        print(f"Phase {phase}")
            
        while thermostat.get_state() != 'READY' and thermostat.get_state() != 'TEMPERATURE HIGH' :
            await temp_pres_handler()
            
            await asyncio.sleep_ms(10)

        turn_off_all_leds()
        if phase >= 2: LED_BREW_SWITCH.value(1)
        if phase == 3: LED_WATER_SWITCH.value(1)

        for i in range(PULSES_PER_PHASE):
            
            
            await perform_pressure_pulse()
            
            if phase == 1:
                await slow_blink(LED_BREW_SWITCH)
            elif phase == 2:
                await slow_blink(LED_WATER_SWITCH)
            elif phase == 3:
                await slow_blink(LED_STEAM_SWITCH)


    # ────────────────────────────────────────────────
    # PHASE END - WAIT FOR NEXT
    # ────────────────────────────────────────────────
    
    async def wait_for_next(phase):
        
        while phase == 1:
            await fast_blink(LED_WATER_SWITCH)          
            await temp_pres_handler()
            
            if SWITCH_WATER.value():
                break
        
        while phase == 2:
            await fast_blink(LED_STEAM_SWITCH)          
            await temp_pres_handler()
            
            if SWITCH_STEAM.value():
                break
            
        while phase == 3:
            await fast_blink(LED_BREW_SWITCH, LED_WATER_SWITCH, LED_STEAM_SWITCH)
            await temp_pres_handler()
            
            if not SWITCH_BREW.value() and not SWITCH_WATER.value() and not SWITCH_STEAM.value():
                break

        turn_off_all_leds()


    # ────────────────────────────────────────────────
    # MAIN SEQUENCE
    # ────────────────────────────────────────────────

    await run_phase(1)
    await signal_beep()
    brew_data.set_mode('BACKFLUSH_PHASE_2')
    print("Phase 1 complete → clean blind filter")
    await wait_for_next(1)

    await run_phase(2)
    await signal_beep()
    brew_data.set_mode('BACKFLUSH_PHASE_3')
    print("Phase 2 complete → clean blind filter")
    await wait_for_next(2)

    await run_phase(3)
    await signal_beep()
    brew_data.set_mode('BACKFLUSH_END')
    await wait_for_next(3)
    


    RELAY_PUMP.value(0)
    RELAY_SOLENOID.value(0)
    turn_off_all_leds()
    print("=== BACKFLUSH COMPLETE ===")