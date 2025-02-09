################################################################################
################################################################################
##########     ----- BREW MODE -----     -----     -----     -----     -----        
################################################################################
################################################################################


def brew_mode(brew_data, switch_brew, relay_pump, relay_solenoid, relay_heater, print_values, lock_printer, sensor, heating_speed_calculator): 

    # Set brewing time counter to 0
    counter_brewing_time = 0
        
    # Get preheat time
    pre_heat_time = brew_data.get_pre_heat_time()
    
    # Get pre-infusion time
    pre_infusion_time = brew_data.get_pre_infusion_time()
    
    # Get pressure soft release time
    pressure_soft_release_time = brew_data.get_pressure_soft_release_time()
    
    # Set solenoid to brewing (pressure) mode
    relay_solenoid.value(1)

    # Calulate pre-heat time before pre-infusion
    pre_heat_time_before_pre_infusion = pre_heat_time - pre_infusion_time
            
    # Calculate pre-heating time for pre-infusion
    if pre_heat_time_before_pre_infusion > 0:
        pre_heat_time_on_pre_infusion = pre_heat_time - pre_heat_time_before_pre_infusion #
    else:
        pre_heat_time_on_pre_infusion = pre_heat_time
    

                        
# --- Pre-heat ---
        
    # If pre-heat time exceeds pre-infusion time: Pre-heat before pre-infusion
    if pre_heat_time_before_pre_infusion > 0:
                
        # Start heating the boiler
        relay_heater.value(1)
                
        # Create for loop for pre-heat time before pre-infusion 
        for x in range(pre_heat_time_before_pre_infusion):
                    
            # Set mode to pre-heat
            brew_data.set_mode("Pre-heat " + str(x + 1) + "s.")
                    
            # Set heater on
            relay_heater.value(1)
                    
            # Get boiler temperature
            boiler_temperature = sensor.read_temperature
                    
            # Set delay 1 second
            utime.sleep(1)
            
    # Else stop heating the boiler
    else:
        relay_heater.value(0)

        
# --- PRE-INFUSION ---
        
    # Create loop for the time of the preinfusion
    for x in range(pre_infusion_time):
                
        # Start the pump
        relay_pump.value(1)
                
        # If pre-heat time matches to the time left with the preinfusion
        if (pre_heat_time_on_pre_infusion == pre_infusion_time - x):
                    
            # Start pre-heating the boiler
            relay_heater.value(1)
                    
        # If boiler is not heating set mode to "Pre-infusion"
        if relay_heater.value() == 0:
            brew_data.set_mode("Pre-infusion "+ str(x + 1) +"s.")
                
        # Else set mode to "Pre-infusion + Pre-heat"
        else:
            brew_data.set_mode( "Pre-heat "+ str(pre_heat_time_before_pre_infusion + x + 1)+ "s. " + "Pre-infusion " + str(x + 1)+ "s.")
                
        # Get the boiler temperature 
        boiler_temperature  = sensor.read_temperature()
                
        # Print essential values 
        print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump)
                
        # Set delay 0.5 seconds. this needs to be adjusted for suitable pressure when connected to hardware
        utime.sleep(0.5)
                
        # Stop the pump
        relay_pump.value(0)
                
        # Print essential values
        print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump)
                                
        ## Set delay 0.5 seconds. this needs to be adjusted for suitable pressure when connected to hardware
        utime.sleep(0.5)
            
    # Start heating the boiler for brewing
    relay_heater.value(1)
            
    # Start the pump for brewing
    relay_pump.value(1)


# --- Brew loop ---
        
    while True:

        # Set mode to "Brew"
        brew_data.set_mode("Brew " + str(counter_brewing_time) + "s.")

                
        # Get the boiler temperature
        boiler_temperature = sensor.read_temperature()
                
        # Get calculated heating speed
        heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)

        # Add 1 to brewing time counter
        counter_brewing_time += 1
        
        print("Brewing " +str(counter_brewing_time)+"s.")

                
        # If brewing switch is turned off brake loop and make (optional) Pressure soft release
        if switch_brew.value() == 0:
                    
            # Print essential values
            print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump)
        
            # Reset brewing time counter
            counter_brewing_time = 0
                    
            # Stop heating the boiler
            relay_heater.value(0)
                    
            # Stop the pump
            relay_pump.value(0)
                    
        # --- Pressure soft release ---
                    
            # Create loop for the time of pressure release
            for x in range(pressure_soft_release_time):
                        
                # Set mode to "Soft pressure release"
                brew_data.set_mode("Soft pressure release " + str(x + 1) +" s.")
                        
                # Print essential values 
                print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump)
                        
                # Set delay for 1 second
                utime.sleep(1)
                    
            # Release brewing pressure
            relay_solenoid.value(0)
                    
            # Break the brewing loop
            break


################################################################################
################################################################################
##########     ----- WATER MODE -----     -----     -----     -----     -----
################################################################################
################################################################################


def water_mode(brew_data, switch_water, relay_pump, relay_heater, relay_solenoid, print_values, lock_printer, sensor, heating_speed_calculator):
    
    # Set counter for water mode
    counter_water_time = 0
            
    # Set mode to "Brew"
    brew_data.set_mode("Water " + str(counter_water_time) + "s.")
            
    # Start heating the boiler
    relay_heater.value(1)
            
    # Start the pump
    relay_pump.value(1)
                 
    # Water loop
    while True:
                
        # Add to water counter
        counter_water_time +=1
                
        # Get the boiler temperature
        boiler_temperature = sensor.read_temperature()
                
        # Get calculated heating speed
        heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
                
        # If water switch is off
        if switch_water.value() == 0:
            
            # Print essential values
            print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump)
                    
            # Stop heating the boiler
            relay_heater.value(0)
                    
            # Stop the pump
            relay_pump.value(0)
                    
            # Break the loop
            break
        






















# --- PRE-HEATING ---

#     # If temperature at the start is below 80 degrees celcius. Make start pre-heating
#     if boiler_temperature < 80:
#         
#         # Create loop that is going while temperature is less than 130 degrees celcius
#         while boiler_temperature < 120:
#             
#             # Set the mode to "Quick heat-up start"
#             brew_data.set_mode("Quick heat-up start")
#             
#             # Calculate the heat up speed
#             heating_speed = heating_speed_calculator.get_heating_speed(boiler_temperature)
#             
#             # Start heating the boiler
#             relay_heater.value(1)
#                 
#             # Heat the virtual boiler
#             #boiler.heat_up()
#                         
#             ## Print essential values
#             print_values(lock_printer, brew_data, boiler, heating_speed, relay_heater, relay_solenoid, relay_pump) # Virtual setup
#             # print_values(lock_printer, brew_data, sensor, heating_speed, relay_heater, relay_solenoid, relay_pump) # Hardware setup
#             
#             # Aseta viive 1s. # Set up 1 second delay (to be reduced to 0.1 seconds when connected to hardware)
#             utime.sleep(1)
#             
#             # Get the boiler temperature
#             boiler_temperature = boiler.get_temperature() # Virtual setup
#             # boiler_temperature = sensor.read_temperature Hardware setup
#         
#         # Stop heating the boiler
#         relay_heater.value(0)
