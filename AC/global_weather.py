###########
# SENSORS #
###########

Weather1 = 'weather.dark_sky'
Weather2 = 'weather.home'
Weather3 = 'sensor.fibaro_motion_sensor_patio_temperature'
High_temp = 'sensor.dark_sky_daytime_high_temperature_0d'
Low_temp = 'sensor.dark_sky_overnight_low_temperature_0d'
inside_temp = 'sensor.inside_temperatures'
inside_temp_stats = 'sensor.inside_temp_avg'
Sun = 'sun.sun'
darksky_temp = 'sensor.dark_sky_temperature'
PROXIMITY = 'proximity.home'

###########
# DEVICES #
###########

Ac_mode = 'input_select.ac_mode'
Home_mode = 'input_select.home_mode'
Windows = 'binary_sensor.windows'
Window_list = 'binary_sensor.dinning_area_window', 'binary_sensor.foyer_window', 'binary_sensor.living_area_window', 'binary_sensor.loft_window', 'binary_sensor.master_bathroom_window', 'binary_sensor.master_bedroom_window', 'binary_sensor.ne_room_window', 'binary_sensor.se_room_window', 'binary_sensor.upper_bathroom_window'
Doors = 'binary_sensor.front_door', 'binary_sensor.garage_door'

#########
# SOUND #
#########

# sound: coyote
# sound_area: all
# sound_volume: 1.0
Playerdir = 'env/'

Deactivating = "male_pa_deactivating.mp3"
Life_off = 'male_pa_life_systems_inoperable.mp3'
Life_on = 'male_pa_life_systems_operational.mp3'
Sound_dict = {
    'deactivating': "male_pa_deactivating.mp3",
    'life_off': 'male_pa_life_systems_inoperable.mp3',
    'life_on': 'male_pa_life_systems_operational.mp3'
}

######
# AC #
######

lower_ac = 'climate.lower_ac'
lower_ac_action = 'sensor.lower_ac_action'
lower_ac_fanmode = 'sensor.lower_ac_fan_mode'
lower_ac_temp = 'sensor.lower_ac_temperature'
lower_ac_humidity = 'sensor.lower_ac_humidity'
lower_ac_energy = 'sensor.lower_ac_energy_total'
lower_ac_util = 'utility_meter.lower_ac_energy'
lower_ac_dict = {
    'entity': lower_ac,
    'action': lower_ac_action,
    'fan': lower_ac_fanmode,
    'temp': lower_ac_temp,
    'humidity': lower_ac_humidity,
    'energy': lower_ac_energy,
    'meter': lower_ac_util
}

upper_ac = 'climate.upper_ac'
upper_ac_action = 'sensor.upper_ac_action'
upper_ac_fanmode = 'sensor.upper_ac_fan_mode'
upper_ac_temp = 'sensor.upper_ac_temperature'
upper_ac_humidity = 'sensor.upper_ac_humidity'
upper_ac_energy = 'sensor.upper_ac_energy_total'
upper_ac_util = 'utility_meter.upper_ac_energy'
upper_ac_dict = {
    'entity': upper_ac,
    'action': upper_ac_action,
    'fan': upper_ac_fanmode,
    'temp': upper_ac_temp,
    'humidity': upper_ac_humidity,
    'energy': upper_ac_energy,
    'meter': upper_ac_util
}

ac_dict = {'lower': lower_ac_dict, 'upper': upper_ac_dict}


