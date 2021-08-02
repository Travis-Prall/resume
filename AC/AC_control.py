import datetime as dt
import global_weather
import appdaemon.plugins.hass.hassapi as hass
"""
Main controller of the AC
"""

FAN_MODES = ('auto low', 'circulation', 'low')
HVAC_MODES = ('off', 'heat', 'cool')
AC_MODES = ('Cool', 'Heat', 'Vent', 'Manuel', 'Rest', 'Away')


class Thermo(hass.Hass):
    def initialize(self):
        self.log(f'__function__: Starting {__name__}', level='INFO')
        # World App #
        World = self.get_app('World')
        persons = World.get_person_list()
        # Getters and Setters #
        self._ac = self.args['ac']
        self._ac_mode = global_weather.Ac_mode
        self._home_mode = self.args["home_mode"]
        self._ac_temp = self.args["ac_temp"]  # The Temp reading the ac has
        self.__ac_name = self.friendly_name(self._ac)
        self.__active = self.args['active']
        # System Test #
        if (self.get_state(self._ac)) == 'unavailable':
            self.error(f'{self._ac} is unavailable', level='CRITICAL')
            return

        #

        # Timers #
        self.start()
        runtime = dt.time(0, 5, 0)
        self.run_hourly(self.check_all, runtime)
        # Actions #
        self.listen_state(self.change_detected, self._ac, duration=300)
        self.listen_state(self.change_detected, self._home_mode)
        self.listen_state(self.change_detected, self._ac_mode)
        self.listen_state(self.change_detected, self.__active)
        for person in persons:
            self.listen_state(self.change_detected, person)

##########
# REPORT #
##########

    def start(self):
        # Makes Sure Everything is Connected
        home_mode = self.get_state(self._home_mode, copy=False)
        ac_mode = self.get_ac_state()  # The mode of the AC
        ac_mode_status = self.get_state(
            self._ac_mode)  # Mode of the AC Control Entity
        inside_temp = self.get_inside_temp()
        set_point = self.get_set_point(
        )  # the temperature the AC is currently set to
        thermo = self.get_thermo()
        fan = self.get_fan_mode()
        self.log(f"__function__ : starting monitoring {self.__ac_name}")
        self.log(f"__function__ : {ac_mode=}")
        self.log(f"__function__ : {home_mode=}")
        self.log(f"__function__ : {ac_mode_status=}")
        self.log(f"__function__ : {thermo=}")
        self.log(f"__function__ : {fan=}")
        self.log(
            f"__function__ : {self.__ac_name} is set to {set_point} while inside temp is {inside_temp} "
        )
        self.check_mode()
        self.check_temp()
        self.check_fan()

############################
# CHECKS AND DOUBLE CHECKS #
############################

    def check_all(self, kwargs):
        self.log('__function__: Checking all', level='DEBUG')
        # self.zwave_refresh()  #refreshs the AC controllers
        self.check_mode()
        self.check_temp()
        self.check_fan()

    def change_detected(self, entity, attribute, old, new, kwargs):
        # Double checks things whenever there is a change
        name = self.friendly_name(entity)  #gets the name of the entity
        if new != old and old is not None:
            self.log(f"__function__ : {name} changed from {old} to {new}")
            self.check_mode()
            self.check_temp()
            self.check_fan()

#########
# LOGIC #
#########

    def check_mode(self):
        """Checks if the AC unit
        is set to the correct mode
        """
        self.log('__function__: Checking Mode', level='DEBUG')
        ac_mode = self.get_ac_state()  # Mode of the AC unit
        if ac_mode not in HVAC_MODES:
            self.log(f'__function__: {ac_mode=} not in {HVAC_MODES}',
                     level='CRITICAL')
        new_mode = self.get_mode()  # The mode it should be
        if new_mode == 'cool':
            if ac_mode != 'cool':
                self.log(
                    f'__function__: Changeing AC from {ac_mode} to {new_mode}',
                    level='DEBUG')
                self.set_hvac_mode(new_mode)
        elif new_mode == 'heat':
            if ac_mode != 'heat':
                self.log(
                    f'__function__: Changeing AC from {ac_mode} to {new_mode}',
                    level='DEBUG')
                self.set_hvac_mode(new_mode)
        elif new_mode == 'off':
            if ac_mode != 'off':
                self.log(
                    f'__function__: Changeing AC from {ac_mode} to {new_mode}',
                    level='DEBUG')
                self.set_hvac_mode(new_mode)
        else:
            self.error(f'Check Mode: No mode = {new_mode}', level='ERROR')

    def check_temp(self):
        # Checks what the current temp setting is vs what it should be
        ac_mode = self.get_ac_state()  # The mode of the AC
        set_point = self.get_set_point()  # The ACs set point
        new_mode = self.get_mode()
        self.log(
            f'__function__ : checking temperature mode should be {new_mode}',
            level='DEBUG')
        self.log(f'__function__ :Ac mode is {ac_mode}', level='DEBUG')
        if ac_mode == 'cool':
            temp = int(self.temperature())
            if temp != set_point:
                self.log(
                    f"__function__ : temperature is {set_point} setting temperature to {temp}"
                )
                self.set_temperature(temperature=temp, hvac_mode=new_mode)
            else:
                self.log(
                    f"__function__ : temperature is {set_point} no need to worry"
                )
        elif ac_mode == 'heat':
            temp = int(self.temperature())
            if temp != set_point:
                self.log(
                    f"__function__ : temperature is {set_point} setting temperature to {temp}"
                )
                self.set_temperature(temperature=temp, hvac_mode=new_mode)
            else:
                self.log(
                    f"__function__ : temperature is {set_point} no need to worry"
                )

    def check_fan(self):
        """Checks to see if the fan mode
        matches the current mode of the AC controllers
        """
        fan = self.get_fan_mode()
        if fan:  # Just to see if you can get the fan mode
            if fan not in FAN_MODES:
                self.log(f'__function__: {fan=} not in {FAN_MODES}',
                         level='CRITCAL')
            ac_mode = self.get_ac_state()  # The mode of the AC
            ac_mode_status = self.get_state(
                self._ac_mode)  # Mode of the AC Control Entity
            self.log(
                f'__function__ :  {fan=} {ac_mode=} and {ac_mode_status=}',
                level='DEBUG')
            if ac_mode_status == 'Cool':
                self.log('__function__ :  Status is Cool', level='DEBUG')
                if fan == 'auto low':
                    self.log(f'__function__ :  {fan=} doing nothing',
                             level='DEBUG')
                else:
                    self.log(f'__function__ :  {fan=} changing to Auto low',
                             level='DEBUG')
                    self.set_fan_mode('Auto low')
            elif ac_mode_status == 'Heat':
                self.log('C__function__ :  Status is Heat', level='DEBUG')
                if fan == 'auto low':
                    self.log(f'__function__ :  {fan=} doing nothing',
                             level='DEBUG')
                else:
                    self.log(f'__function__ :  {fan=} changing to Auto low',
                             level='DEBUG')
                    self.set_fan_mode('Auto low')
            elif ac_mode_status == 'Away':
                self.log('__function__ :  Status is Away', level='DEBUG')
                if fan == 'auto low':
                    self.log(f'__function__ :  {fan=} doing nothing',
                             level='DEBUG')
                else:
                    self.log(f'__function__:  {fan=} changing to Auto low',
                             level='DEBUG')
                    self.set_fan_mode('Auto low')
            elif ac_mode_status == 'Vent':
                self.log('__function__:  Status is Vent', level='DEBUG')
                if fan == 'circulation':
                    self.log(f'__function__:  {fan=} doing nothing',
                             level='DEBUG')
                else:
                    self.log(f'__function__:  {fan=} changing to Circulation',
                             level='DEBUG')
                    self.set_fan_mode('Circulation')
            elif ac_mode_status == 'Rest':
                self.log('__function__:  Status is Rest', level='DEBUG')
                if fan == 'auto low':
                    self.log(f'__function__:  {fan=} doing nothing',
                             level='DEBUG')
                else:
                    self.log(f'__function__:  {fan=} changing to Auto Low',
                             level='DEBUG')
                    self.set_fan_mode('Auto Low')
            elif ac_mode_status == 'Manuel':
                self.log('__function__:  Status is Manuel', level='DEBUG')
                if ac_mode in ('cool',
                               'heat'):  # Checks to see if the AC is on
                    self.log(f'__function__:  AC mode is {ac_mode}',
                             level='DEBUG')
                    if fan == 'auto low':  # Makes sure the fan is running while the AC is on
                        self.log(f'__function__:  Fan is {fan} doing nothing',
                                 level='DEBUG')
                    else:
                        self.log(
                            f'__function__:  Fan is {fan} changing to Auto low',
                            level='DEBUG')
                        self.set_fan_mode('Auto low')
            else:
                self.error(f'Check Fan: No Mode Found {ac_mode_status=}',
                           level='ERROR')
        else:
            self.error('Check Fan: No Fan Found', level='ERROR')

    def temperature_active(self):
        """Checks to see if anyone is home
        if someone is home
        it checks to see if the area of the house is in use

        Returns
        -------
        away = no one is home
        regular = someone is home and the current ac is on thier level
        inactive = someone is home ,but not one is in that area
        """
        home_mode = self.get_state(self._home_mode)
        self.log('__function__ : checking which temperature app',
                 level='DEBUG')
        if home_mode != 'away':
            if self.check_home():
                self.log('__function__ : temperature is regular', level='INFO')
                return "regular"
            if self.active_check():
                self.log('__function__ : temperature is regular', level='INFO')
                return "regular"
            self.log('__function__ : temperature is inactive', level='INFO')
            return "inactive"
        self.log(f'__function__ : {home_mode=} temperature is away',
                 level='INFO')
        return "away"

    def check_home(self):
        # checks if people are home
        self.log('__function__ : checking who is home', level='INFO')
        for person in self.split_device_list(self.args['persons']):
            where = self.get_state(person)
            name = self.friendly_name(person)
            self.log(f'__function__ : {name} is {where}', level='INFO')
            if where == 'home':
                self.log('__function__ : returning true', level='DEBUG')
                return True
        self.log('__function__ : No one is home')
        return ''

    def active_check(self):
        # check if an area is active to turn the AC up or Down
        self.log('__function__ : checking for activity')
        try:
            activity = self.get_state(self.__active)
            self.log(f'__function__: {activity=}', level='DEBUG')
        except Exception as e:
            activity = 'off'
            self.error(f'Active Check: {e} ', level='ERROR')
        if activity == 'on':
            self.log('__function__: Activity is True', level='DEBUG')
            return True
        self.log('__function__: Activity is False', level='DEBUG')
        return False

        # for area in self.split_device_list(self.args['active']):
        #     state = float(self.get_state(area, default="0"))
        #     area_name = self.friendly_name(area)
        #     if state > 0:
        #         self.log(
        #             f'__function__ : {area_name} is active returning true',
        #             level='INFO')
        #         return True
        #         self.log(f'__function__ : {area_name} is inactive',
        #                  level='DEBUG')
        # self.log('__function__ : Areas are inactive')
        # return ''

    def temperature(self):
        modes = self.temperature_active()  # AWAY HOME INACTIVE
        thermo = self.get_thermo()
        now = self.time()
        now_hour = int(now.hour)
        week = self.get_week()
        now_temp = self.args[thermo][week][modes][now_hour]
        self.log(
            f'__function__ : Now regular temp is {thermo=} {week=} {modes=} {now_hour=}',
            level="INFO")
        self.log(f'__function__ : Now regular temp is {now_temp}',
                 level="INFO")
        return now_temp

######################
#     FUNCTIONS      #
# RETURN INFORMATION #
######################

    def get_set_point(self):
        """
        Returns
        -------
        The temperature the AC is currently set at
        """
        self.log('__function__:  Getting AC Set point', level='DEBUG')
        try:
            set_point = int(
                self.get_state(entity_id=self._ac, attribute="temperature"))
            self.log(f'__function__: Returning {set_point}', level='DEBUG')
            return set_point
        except TypeError:
            self.log('__function__: Point is not set because the AC is off',
                     level='INFO')
        except Exception as e:
            self.error(e, level='ERROR')
        self.log(
            '__function__: Failed to get set point because machine is off',
            level='INFO')
        return "none"

    def get_ac_state(self):
        """
        Returns
        -------
        The state of the ac unit
        'off'
        heat
        cool
        """
        self.log('__function__: Getting AC state', level='DEBUG')
        try:
            ac_state = self.get_state(self._ac)
            self.log(f'Get AC state: Returning {ac_state}', level='DEBUG')
            if ac_state.casefold() not in HVAC_MODES:
                self.log(f'__function__: {ac_state=} not in {HVAC_MODES}',
                         level='CRITICAL')
            return ac_state.casefold()
        except Exception as e:
            self.error(f'Get AC state : {e} ', level='ERROR')
        self.log('__function__: Failed to get AC state', level='WARNING')
        return 'off'

    def get_mode(self):
        """
        Returns
        -------
        The mode of the AC Controller Entity
        """
        self.log('__function__:  Getting Mode', level='DEBUG')
        try:
            ac_mode_status = self.get_state(self._ac_mode)

        except Exception as e:
            self.error(f'Get Mode: {e} ', level='ERROR')
            return 'off'
        if ac_mode_status == 'Cool':
            return 'cool'
        if ac_mode_status == 'Heat':
            return 'heat'
        if ac_mode_status == 'Rest':
            return 'off'
        if ac_mode_status == 'Vent':
            return 'off'
        if ac_mode_status == 'Away':
            return 'cool'
        self.log(f'__function__:  AC mode is {ac_mode_status}',
                 level='WARNING')
        return 'off'

    def get_inside_temp(self):
        """
        Returns
        -------
        The temperature the AC module has
        """
        self.log("__function__: Getting Inside Temp", level='DEBUG')
        try:
            temp = float(self.get_state(self._ac_temp))
            return temp
        except Exception as e:
            self.error(f'Get Inside Temp: Failed to get temp entity {e}',
                       level='WARNING')

        try:
            temp = self.get_state(entity_id=self._ac,
                                  attribute="current_temperature")
            return temp
        except Exception as e:
            self.error(f'Get Inside Temp: {e} ', level='ERROR')
        self.log('__function__: Everything Failed', level='WARNING')
        return ''

    def get_week(self):
        """
        Returns
        -------
        If it is a weekday or weekend
        """
        weekno = dt.datetime.today().weekday()
        self.log(f'__function__ : {weekno=}', level="DEBUG")
        if weekno > 4:
            self.log(f'T__function__: Today is day {weekno} a weekend',
                     level="DEBUG")
            return 'weekend'
        self.log(f"__function__ : {weekno=} assuming weekday", level="DEBUG")
        return 'weekday'

    def get_high_point(self):
        if self.get_state(self.args["high_temp"]):
            return float(self.get_state(self.args["high_temp"]))
        self.log('__function__:  failed to get high point', level='WARNING')
        return 90

    def get_low_point(self):
        if self.get_state(self.args["low_temp"]):
            return float(self.get_state(self.args["low_temp"]))
        self.log('__function__:  failed to get low point', level='WARNING')
        return 80

    def get_thermo(self):
        """Checks to see if the Home Mode
        is in Heat mode
        Otherwise defaults to cool

        Returns
        -------
        Heat if it's in Heat mode
        Otherwise default is "Cool"
        """
        self.log("__function__:  Getting AC Mode Status", level='DEBUG')
        try:
            ac_mode_status = self.get_state(
                self._ac_mode)  # Gets the current status of the AC mode
            self.log(f'__function__: {ac_mode_status=}', level='DEBUG')
        except Exception as Error:
            self.error(f'Get Thermo: {Error} ', level='ERROR')
            return 'Cool'
        if ac_mode_status == 'Heat':
            return 'Heat'
        if ac_mode_status == 'Cool':
            return 'Cool'
        self.log('__function__ : Failed to get thermo', level='WARNING')
        return 'Cool'

    def get_fan_mode(self):
        """Checks the current mode
        the fan is in
        Returns
        -------
        Auto low: Fan turns on when AC turns on
        Circulation: Fan comes on in intervals
        Low: Fan is always on
        """
        try:
            fan_mode = self.get_state(entity_id=self._ac,
                                      attribute='fan_mode',
                                      copy=False)
            self.log(f'__function__:  {self.__ac_name} {fan_mode=}',
                     level='DEBUG')
            return fan_mode.casefold()
        except Exception as e:
            self.error(f'Get Fan Mode:  {self.__ac_name} fan Failed {e}',
                       level='ERROR')
        self.log('__function__: Failed to get fan mode', level='WARNING')
        return ''


###################
#    FUNCTIONS    #
# CHANGE SETTINGS #
###################

    def set_hvac_mode(self, hvac_mode=None):
        # Parameter     Description     Example
        # entity_id Name(s) of entities to change.  climate.nest
        # hvac_mode New value of operation mode.    heat
        if hvac_mode:
            self.call_service("climate/set_hvac_mode",
                              entity_id=self._ac,
                              hvac_mode=hvac_mode)
            self.log(f"__function__ : Setting {hvac_mode=}", level="DEBUG")
        else:
            self.log(f"__function__ : Setting {hvac_mode=}", level="ERROR")

    def ac_turn_off(self):
        # Parameter     Description     Example
        # entity_id Name(s) of entities to change.  climate.nest
        self.call_service("climate/turn_off", entity_id=self._ac)
        self.log(f"__function__ : turned off {self.__ac_name}")

    def ac_turn_on(self):
        # Parameter     Description     Example
        # entity_id Name(s) of entities to change.  climate.nest
        self.call_service("climate/turn_on", entity_id=self._ac)
        self.log(f"__function__ : turned on {self.__ac_name}")

    def set_preset_mode(self, preset_mode=None):
        # Parameter     Description     Example
        # entity_id Name(s) of entities to change.  climate.nest
        # preset_mode New value of preset mode  away
        if preset_mode:
            self.call_service("climate/set_preset_mode",
                              entity_id=self._ac,
                              preset_mode=preset_mode)
            self.log(f"__function__: {preset_mode=}", level="DEBUG")
        else:
            self.log(f"__function__: {preset_mode=}", level="ERROR")

    def set_fan_mode(self, fan_mode=None):
        # Parameter     Description     Example
        # entity_id Name(s) of entities to change.  climate.nest
        # fan_mode New value of fan mode.   On Low
        if fan_mode:
            self.call_service("climate/set_fan_mode",
                              entity_id=self._ac,
                              fan_mode=fan_mode)
            self.log(f"__function__:  {fan_mode=}", level="DEBUG")
        else:
            self.log(f"__function__:  {fan_mode=}", level="ERROR")

    def set_temperature(self, temperature=None, hvac_mode=None):
        # Parameter     Description     Example
        # entity_id Name(s) of entities to change.  climate.nest
        # temperature New target temperature for HVAC.  25
        # target_temp_high New target high temperature for HVAC.    26
        # target_temp_low New target low temperature for HVAC.  20
        # hvac_mode HVAC operation mode to set temperature to.  heat
        new_target_temperature = int(temperature)
        new_mode = hvac_mode
        target_temp_high = 90
        target_temp_low = 60
        self.call_service(
            "climate/set_temperature",
            entity_id=self._ac,
            temperature=new_target_temperature,
            hvac_mode=new_mode,
        )
        self.log(
            f"__function__:  temperature = {new_target_temperature} new_mode = {hvac_mode}",
            level="DEBUG",
        )
        self.log(
            f"__function__:  target_temp_high = {target_temp_high} target_temp_low = {target_temp_low}",
            level="DEBUG",
        )


