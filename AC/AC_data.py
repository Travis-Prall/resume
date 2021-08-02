from datetime import datetime as dt
import appdaemon.plugins.hass.hassapi as hass
# from psycopg2 import connect, sql, DatabaseError
# from psycopg2.extras import RealDictCursor
import global_weather
"""
(
    start_time timestamp with time zone,
    end_time timestamp with time zone,
    ac_name text COLLATE pg_catalog."default",
    ac_start boolean,
    temperature_s real,
    temperature_e real,
    humidity_s real,
    humidity_e real,
    ac_energy_s real,
    ac_energy_e real,
    darksky_temp_s real,
    darksky_temp_e real,
    darksky_humid_s real,
    darksky_humid_e real,
    darksky_pressure_s real,
    darksky_pressure_e real,
    weather_temp_s real,
    weather_temp_e real,
    weather_humid_s real,
    weather_humid_e real,
    weather_pressure_s real,
    weather_pressure_e real,
    sun_elv_s real,
    sun_elv_e real,
    sun_azimuth_s real,
    sun_azimuth_e real,
    other_ac_s boolean,
    other_ac_e boolean,
    other_temp_s real,
    other_temp_e real,
    other_hum_s real,
    other_hum_e real,
    other_energy_s real,
    other_energy_e real
)
"""


class Thermo(hass.Hass):
    def initialize(self):
        self.log(f'__function__: Starting {__name__}', level='INFO')
        ### Getters and Setters ###
        self._version = self.args['version']
        ac_dict = global_weather.ac_dict
        current_ac_dict = ac_dict[self._version]
        if self._version == 'lower':
            other_dict = ac_dict['upper']
        else:
            other_dict = ac_dict['lower']
        ## Database ##
        self._database = self.args['database']
        self._schema = self.args['database_schema']
        self._table_on = self.args['database_table_on']
        self._table_off = self.args['database_table_off']
        ## ACs ##
        # Entity #
        load = 'entity'
        self._ac = current_ac_dict[load]
        self._other_ac = other_dict[load]
        # Temp #
        load = 'temp'
        self._ac_temp = current_ac_dict[load]
        self._other_ac_temp = other_dict[load]
        # Humidity #
        load = 'humidity'
        self._ac_humid = current_ac_dict[load]
        self._other_ac_humid = other_dict[load]
        # Energy #
        load = 'energy'
        self._ac_energy = current_ac_dict[load]
        self._other_ac_energy = other_dict[load]
        # Action #
        load = 'action'
        self._ac_action = current_ac_dict[load]
        self._other_ac_action = other_dict[load]
        # Meter #
        load = 'meter'
        self._ac_meter = current_ac_dict[load]
        self._other_ac_meter = other_dict[load]
        # Outside Weather #
        self._darksky = global_weather.Weather1
        self._weather = global_weather.Weather2
        self._sun = global_weather.Sun

        # Time #
        self._start_time = None
        self._end_time = None

        # Data #
        self._start_data = dict()
        self._end_data = dict()
        self._ac_start = True  # This is for detecting if this is the first entry
        self._start_record = self.get_ac_status(
            self._ac)  # True if the AC is active
        self.ac_on = None  # Information about either AC being on

        self.log(f"__function__: Record is {self._start_record}",
                 level='DEBUG')

        ### Start ###
        self.start_app()
        self.check_acs()
        if self._start_record:
            self.update_start(entity=self._ac_action)
        else:
            self.update_start(entity=self._ac_temp)

        ###Test###
        # self.update_end()

        ### Actions ###
        self.listen_state(self.ac_change_detected,
                          entity=self._ac,
                          attribute='hvac_action',
                          immediate=True)
        self.listen_state(self.temp_change_detected, self._ac_temp)
        self.listen_state(self.ac_watcher,
                          entity=self._ac,
                          attribute='hvac_action')
        self.listen_state(self.ac_watcher,
                          entity=self._other_ac,
                          attribute='hvac_action')

##########
# REPORT #
##########

    def start_app(self):
        self.log('__function__: Starting App', level="DEBUG")
        entity_start_list = [
            self._ac, self._other_ac, self._ac_temp, self._other_ac_temp,
            self._ac_humid, self._other_ac_humid, self._ac_energy,
            self._other_ac_energy, self._darksky, self._weather, self._sun
        ]
        for entity in entity_start_list:
            try:
                test = self.get_state(entity)
            except (TypeError, ValueError):
                self.error(f"Unable to get {entity}", level="ERROR")
                return

            if test is None:
                self.error(f"unable to get state for {entity}", level="ERROR")
                return
        self.log('__function__: App is now working', level="DEBUG")

############
# WATCHERS #
############

    def ac_change_detected(self, entity, attribute, old, new, kwargs):
        # process changes in the AC
        name = self.friendly_name(entity)  #gets the name of the entity
        self.log(f"__function__: {name} changed from {old} to {new}",
                 level='DEBUG')
        if old != new:
            self.log(f"__function__: {name} changed from {old} to {new}")
            if new == 'idle':  # If record switch is already on no need to update
                self.log(f'__function__: {new=} Doing nothing', level='DEBUG')
            elif new == 'cooling':
                self.log(
                    f"__function__: Start Record is {self._start_record} updateing start times",
                    level='DEBUG')
                self._ac_start = True
                self.update_start(entity=self._ac_action)
                self._start_record = self.get_ac_status(self._ac)
                self.log(
                    f"__function__: Setting record to {self._start_record}",
                    level='DEBUG')
            elif new is None:
                self._ac_start = True
                self.update_start(entity=self._ac_temp)
                self.log(f'__function__: {new=} Doing nothing',
                         level='WARNING')
            else:
                self.log('__function__: Something went wrong', level='WARNING')

    def temp_change_detected(self, entity, attribute, old, new, kwargs):
        """ Process changes in temperature """
        name = self.friendly_name(entity)  #gets the name of the entity
        self.log(f"__function__: {name} changed from {old} to {new}",
                 level='DEBUG')
        if old != new:
            self.log(f"__function__: {name} changed from {old} to {new}")
            self.update_entity(self._ac_meter)
            self.update_entity(self._other_ac_meter)
            self.update_end()

    def ac_watcher(self, entity, attribute, old, new, kwargs):
        """ Watches for changes in the AC units """
        name = self.friendly_name(entity)  # gets the name of the entity
        if old != new:
            self.log(f"__function__: {name} changed from {old} to {new}")
            self.check_acs()

######################
# DATABASE UTILITIES #
######################

    def insert_data(self, data_dict, table='on'):
        """[inserts data into one of two tables in postgres]

        Parameters
        ----------
        data_dict : [dict]
            [this is the data to be inserted]
        table : str, optional
            [chooses either the default table or the off table], by default 'on'
        """
        database = self._database
        schema = self._schema
        if table == 'off':
            table = self._table_off
        else:
            table = self._table_on
        database_app = self.get_app(self.args['database_app'])
        self.log(
            f'__function__: Inserting data into {database=} into {schema=} into {table=}',
            level='DEBUG')
        database_app.insert_data_dict(database=database,
                                      data_schema=schema,
                                      data_table=table,
                                      data_dict=data_dict)
        self.log(f'__function__: inserted {data_dict}', level='DEBUG')

############
# CHECKERS #
############

    def check_acs(self, ac_off=False):
        """[Checks to see if any of the ACs are on
        and updates the varible. Only updates OFF at the end of a cycle
        so data is not corrupted by other ac turning on then off]

        Parameters
        ----------
        ac_off : bool, optional
            [will only change to off if cycle has completed], by default False
        """

        prime_ac = self.get_ac_status(self._ac)
        secondary_ac = self.get_ac_status(self._other_ac)
        if prime_ac:
            self.log(f'__function__: {prime_ac=} setting to True',
                     level='DEBUG')
            self.ac_on = True
        elif secondary_ac:
            self.log(f'__function__: {secondary_ac=} setting to True',
                     level='DEBUG')
            self.ac_on = True
        elif ac_off:
            self.log(
                f'__function__: {ac_off=} Setting {self.ac_on=} to False ',
                level='DEBUG')
            self.ac_on = False
        else:
            self.log(f'__function__: {ac_off=} Doing Nothing ', level='DEBUG')

    def check_update_data(self):
        """ Checks to see if data needs to be inserted into
        a table and which table """
        self.log('__function__: Checking Data', level='DEBUG')
        self.check_acs()  # Check if any of the ACs came on
        if self._start_record:  # Primary AC is on or was on record data to default table
            self.log(f'__function__: Record is {self._start_record}',
                     level='DEBUG')
            if self.data_intergity():
                data_dict = self.merge_data()  # Get Dict
                self.insert_data(data_dict)  # insert into default table
        elif self.ac_on is False:  # Record data if all ACs have been off
            self.log(f'__function__: AC is {self.ac_on}', level='DEBUG')
            if self.data_intergity():
                data_dict = self.merge_data()  # Get Dict
                self.insert_data(data_dict,
                                 table='off')  # insert into off table
        else:
            self.check_acs(
                True)  # Reset the ac_on switch to false if both acs are off
            self.log(
                f'__function__: Not recording because {self._start_record=} and {self.ac_on=}',
                level='INFO')
        self._start_record = self.get_ac_status(
            self._ac)  # Update record switch
        self.swap_data()  # Resets the cycle by swapping the end with the start
        self._ac_start = False  # Atleast one cycles has been recorded

#########
# LOGIC #
#########

    def update_start(self, entity):
        """ Updates the start varibles if the AC started """
        self.log("Updateing Start variables", level='INFO')
        self._start_time = self.get_last_changed(entity)
        self.log(f'__function__: Setting start time to {self._start_time}',
                 level='DEBUG')
        self._start_data = self.get_data_dict('s')
        self._start_data['start_time'] = self._start_time
        self.log(self._start_data, level='DEBUG')

    def update_end(self):
        """ Updates the final varibles whenever the temperature changes """
        self.log("__function__: Updating", level='INFO')
        self._end_time = self.get_last_changed(self._ac_temp)
        self.log(f'__function__: Setting end time to {self._end_time}',
                 level='DEBUG')
        self._end_data = self.get_data_dict('e')
        self._end_data['end_time'] = self._end_time
        self._end_data['start_time'] = self._start_time
        self.check_update_data()

    def merge_data(self):
        """ Merges the start data with the end data into one dict """
        self.log('__function__: Starting to merge', level='DEBUG')
        merged_data = dict()
        self.log(f'__function__: Merging {self._start_data}', level='DEBUG')
        for key, value in self._start_data.items():
            merged_data[key] = value
        self.log(f'__function__: Merged is now {merged_data}', level='DEBUG')
        self.log(f'__function__: Start data is now {self._start_data}',
                 level='DEBUG')
        self.log(f'__function__: Merging end data {self._end_data}',
                 level='DEBUG')
        for key, value in self._end_data.items():
            merged_data[key] = value
        self.log(f'__function__: Merged is now {merged_data}', level='DEBUG')
        self.log(f'__function__: Merging end datais now {self._end_data}',
                 level='DEBUG')
        self.log(merged_data, level='DEBUG')
        return merged_data

    def swap_data(self):
        """ copies the end data to the start data """
        self.log('__function__: Swapping Data', level='DEBUG')
        self.log(self._start_data, level='DEBUG')
        for key in self._end_data:
            yek = key[::-1]  # reverse the key
            if "e_" in yek:  # look for _e at the end
                new_key = (yek.replace(
                    'e_', 's_',
                    1))[::-1]  # replace _e with _s and reverse it again
                self._start_data[new_key] = self._end_data[
                    key]  # replace start with end
        self._start_time = self._end_time
        self.log(self._start_data, level='DEBUG')

    def get_data_dict(self, alpha='e'):
        """ Gathers all needed data into a dict """
        data_dict = dict()
        # Inside #
        data_dict['device_name'] = self.friendly_name(self._ac)
        data_dict['ac_start'] = self._ac_start
        data_dict['ac_on'] = self.ac_on
        data_dict[f'temperature_{alpha}'] = self.get_temp(self._ac_temp)
        data_dict[f'humidity_{alpha}'] = self.get_humid(self._ac_humid)
        data_dict[f'ac_energy_{alpha}'] = self.get_energy(self._ac_energy)
        # Outside #
        data_dict[f'darksky_temp_{alpha}'] = self.get_temp_attr(self._darksky)
        data_dict[f'darksky_humid_{alpha}'] = self.get_humid_attr(
            self._darksky)
        data_dict[f'darksky_pressure_{alpha}'] = self.get_pressure_attr(
            self._darksky)
        data_dict[f'weather_temp_{alpha}'] = self.get_temp_attr(self._weather)
        data_dict[f'weather_humid_{alpha}'] = self.get_humid_attr(
            self._weather)
        data_dict[f'weather_pressure_{alpha}'] = self.get_pressure_attr(
            self._weather)
        sun_elv, sun_azimuth = self.get_sun()
        data_dict[f'sun_elv_{alpha}'] = sun_elv
        data_dict[f'sun_azimuth_{alpha}'] = sun_azimuth
        # Other AC #
        data_dict[f'other_ac_{alpha}'] = self.get_ac_status(self._other_ac)
        data_dict[f'other_temp_{alpha}'] = self.get_temp(self._other_ac_temp)
        data_dict[f'other_hum_{alpha}'] = self.get_humid(self._other_ac_humid)
        data_dict[f'other_energy_{alpha}'] = self.get_energy(
            self._other_ac_energy)
        self.log(data_dict, level='DEBUG')
        return data_dict

######################
#     FUNCTIONS      #
# RETURN INFORMATION #
######################

    def get_temp(self, entity):
        """Gets the current temp"""
        try:
            temperature = float(self.get_state(entity_id=entity))
            self.log(f'__function__:  {entity} temperature is {temperature}',
                     level='DEBUG')
            return temperature
        except Exception as error:
            self.error(f'Get Temp:  {entity} temp Failed {error}',
                       level='ERROR')
        self.log(f'Failed to get temperature from {entity}', level='WARNING')
        return None

    def get_humid(self, entity):
        """Gets the current humidity"""
        try:
            humidity = float(self.get_state(entity_id=entity))
            self.log(f'__function__:  {entity} humidity is {humidity}',
                     level='DEBUG')
            return humidity
        except Exception as error:
            self.error(f'Get Humidity:  {entity} humidity Failed {error}',
                       level='ERROR')
        self.log(f'Failed to get humidity from {entity}', level='WARNING')
        return None

    def get_temp_attr(self, entity):
        """Gets the current temp from an attribute"""
        try:
            temperature = float(
                self.get_state(entity_id=entity, attribute="temperature"))
            self.log(f'__function__:  {entity} temperature is {temperature}',
                     level='DEBUG')
            return temperature
        except Exception as error:
            self.error(f'Get Temp:  {entity} temp Failed {error}',
                       level='ERROR')
        self.log(f'Failed to get temperature from {entity}', level='WARNING')
        return None

    def get_humid_attr(self, entity):
        """Gets the current humidity from an attribute"""
        try:
            humidity = float(
                self.get_state(entity_id=entity, attribute="humidity"))
            self.log(f'__function__:  {entity} humidity is {humidity}',
                     level='DEBUG')
            return humidity
        except Exception as error:
            self.error(f'Get Humidity:  {entity} humidity Failed {error}',
                       level='ERROR')
        self.log(f'Failed to get humidity from {entity}', level='WARNING')
        return None

    def get_pressure_attr(self, entity):
        """Gets the current pressure from an attribute"""
        try:
            pressure = float(
                self.get_state(entity_id=entity, attribute="pressure"))
            self.log(f'__function__:  {entity} pressure is {pressure}',
                     level='DEBUG')
            return pressure
        except Exception as error:
            self.error(f'Get Pressure:  {entity} pressure Failed {error}',
                       level='ERROR')
        self.log(f'Failed to get pressure from {entity}', level='WARNING')
        return None

    def get_energy(self, entity):
        """Gets the current energy"""
        self.update_entity(entity)
        try:
            energy = float(self.get_state(entity_id=entity))
            self.log(f'__function__:  {entity} energy is {energy}',
                     level='DEBUG')
            return energy
        except Exception as error:
            self.error(f'Get Energy:  {entity} energy Failed {error}',
                       level='ERROR')
        self.log(f'Failed to get energy from {entity}', level='WARNING')
        return None

    def get_sun(self):
        """Gets the current sun's location"""
        try:
            elevation = float(
                self.get_state(entity_id=self._sun, attribute="elevation"))
            azimuth = float(
                self.get_state(entity_id=self._sun, attribute="azimuth"))
            self.log(
                f'__function__:  {self._sun} elevation is {elevation} and azimuth is {azimuth}',
                level='DEBUG')
            return elevation, azimuth
        except Exception as error:
            self.error(f'Get Sun: {self._sun} location Failed {error}',
                       level='ERROR')
        self.log(f'Failed to get locaion of {self._sun}', level='WARNING')
        return None, None

    def get_ac_status(self, entity):
        """Gets the status of the other AC unit"""
        try:
            state = self.get_state(entity_id=entity, attribute="hvac_action")
            self.log(f'__function__: {entity} state is {state}', level='DEBUG')
            if state in ('idle', 'off'):
                self.log(f"__function__: State is {state} returning False",
                         level='DEBUG')
                return False
            self.log(f"__function__: State is {state} returning True",
                     level='DEBUG')
            return True
        except Exception as error:
            self.error(f'Get Other AC Status: {entity} status Failed {error}',
                       level='ERROR')
        self.log(f'Failed to get status from {entity}', level='WARNING')
        return None

    def check_temp_diff(self):
        """checks if there is a difference between the two temperatures"""
        self.log('__function__:Checking Records ', level='DEBUG')
        current_temp = self.get_temp(self._ac_temp)
        try:
            recorded_temp = float(self._start_data['temp'])
        except Exception as error:
            self.log(error, level='WARNING')
            recorded_temp = 1.0
        if current_temp == recorded_temp:
            self.log(
                f'__function__:Current Temp {current_temp} and Recorded Temp{recorded_temp} are equal ',
                level='DEBUG')
            return True
        self.log(
            f'__function__:Current Temp {current_temp} and Recorded Temp {recorded_temp} are NOT equal ',
            level='DEBUG')
        return False

    def get_last_changed(self, entity):
        """ gets the last time an entity was changed """
        self.log('__function__: Getting last Changed ', level='DEBUG')
        try:
            last_changed = self.get_state(entity_id=entity,
                                          attribute="last_changed")
            self.log(f'__function__:  {entity} {last_changed=}', level='DEBUG')
            return last_changed
        except Exception as error:
            self.error(f'Get Last Changed:{error}', level='ERROR')
            self.log(f'__function__:{entity} {last_changed=}', level='ERROR')
        self.log(f'Failed to get last_changed from {entity}', level='WARNING')
        return dt.now()

    def data_intergity(self):
        ''' Check for data mistakes '''
        self.log('__function__: Checking data', level='DEBUG')
        try:
            start_temp = self._start_data['temperature_s']
            end_temp = self._end_data['temperature_e']
            if start_temp == end_temp:
                self.log(
                    f'__function__: {start_temp=} and {end_temp=} temperatures are equal',
                    level='WARNING')
                return False
            if start_temp is None:
                self.log('__function__: Start temp is missing',
                         level='WARNING')
                self.log(self._start_data, level='WARNING')
                return False
            if end_temp is None:
                self.log('__function__: End temp is missing', level='WARNING')
                self.log(self._end_data, level='WARNING')
                return False
        except KeyError as error:
            self.log(f'__function__: {error}', level='WARNING')
            self.log(self._start_data, level='WARNING')
            self.log(self._end_data, level='WARNING')
            return False
        try:
            start_time = self._start_data['start_time']
            end_time = self._end_data['end_time']
            if start_time == end_time:
                self.log('__function__: times are equal', level='WARNING')
                return False
        except KeyError as error:
            self.log(f'__function__: {error}', level='WARNING')
            return False
        return True


###################
#    FUNCTIONS    #
# CHANGE SETTINGS #
###################

    def update_entity(self, entity):
        """Force one or more entities to update its data rather than wait
        for the next scheduled update."""
        try:
            self.call_service("homeassistant/update_entity", entity_id=entity)
            self.log(f"__function__:  updated {entity}", level="DEBUG")
        except Exception as error:
            self.log(error, level='WARNING')


