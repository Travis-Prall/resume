import datetime as dt
import appdaemon.plugins.hass.hassapi as hass
import global_weather
'''
Sets the AC mode to Cool Heat Etc

    Modes:
    - Cool (It's hot outside)
    - Heat (It's cold outside)
    - Vent  (A Window is open)
    - Manuel (AC auto control is disabled)
    - Rest (AC is Off)
    - Away (No one is home)
'''


class Thermo(hass.Hass):
    def initialize(self):
        self.log(f'__function__: Starting {__name__}', level='INFO')
        # World App #
        World = self.get_app('World')
        self.__home_mode = World.get_mode_device('home')
        # Getters and Setters #
        self._ac_mode = global_weather.Ac_mode
        self.max_temp = float(self.args['max_temp'])  # MAX Hot Outside
        self.min_temp = float(self.args['min_temp'])  # MAX Cold Outside
        self.inside_temp = global_weather.inside_temp
        self.temp_stat = global_weather.inside_temp_stats  # Gathers Stats on Temp Changes
        self._high_temp = global_weather.High_temp
        self._low_temp = global_weather.Low_temp
        self._windows = global_weather.Windows
        self._weather1 = global_weather.Weather1  # DarkSky
        self._weather2 = global_weather.Weather2  # Home
        self._weather3 = global_weather.Weather3  # Device
        self.proximity = global_weather.PROXIMITY
        #Varibles#
        self.proxy = None
        # Timers #
        runtime = dt.time(0, 10, 0)
        self.run_hourly(self.watcher, runtime)
        # Actions #
        self.start()
        self.listen_state(self.home_mode_watcher, self.__home_mode)
        self.listen_state(self.window_watcher, self._windows)
        self.listen_state(self.proximity_check,
                          self.proximity,
                          attribute='dir_of_travel',
                          new='towards',
                          duration=60)

##########
# REPORT #
##########

    def start(self):
        #  Just Logs
        self.log(f'Start: {self._ac_mode =}', level='DEBUG')
        self.log(f'Start: {self.max_temp =}', level='DEBUG')
        self.log(f'Start: {self.min_temp =}', level='DEBUG')
        outside_temp = self.get_outside_temp()
        home_mode = self.get_state(self.__home_mode)
        ac_mode = self.get_state(self._ac_mode)
        windows = self.get_state(self._windows)
        today_low = self.get_low_point()
        today_high = self.get_high_point()
        self.log(f'Start: {outside_temp =}', level='INFO')
        self.log(f'Start: {today_high =}', level='INFO')
        self.log(f'Start: {today_low =}', level='INFO')
        self.log(f'Start: {home_mode =}', level='INFO')
        self.log(f'Start: {ac_mode =}', level='INFO')
        self.log(f'Start: {windows =}', level='INFO')
        self.check_all()

############
# WATCHERS #
############

    def home_mode_watcher(self, entity, attribute, old, new, kwargs=None):
        #  Watches when the homes mode changes
        name = self.friendly_name(entity)
        if new != old and old is not None:
            self.log(f"__function__: {name} changed from {old} to {new}")
            self.check_all()

    def window_watcher(self, entity, attribute, old, new, kwargs=None):
        #  Watches if any of the windows open and if all the windows close
        name = self.friendly_name(entity)
        if new != old and old is not None:
            self.log(f"__function__: {name} changed from {old} to {new}")
            self.check_all()

    # def outside_temperature_watcher(self, kwargs):
    #     #  Checks Hourly if the outside tempature is comfortable
    #     outside_temp = self.get_outside_temp()
    #     self.log(
    #         f'Outside Temperature Watcher: outside temperature is {outside_temp}',
    #         level='INFO')
    #     if self.min_temp <= outside_temp <= self.max_temp:self.log(
    #         self.check_all()

    def watcher(self, kwargs=None):
        #  Checks Hourly
        self.log('__function__: Checking', level='DEBUG')
        self.check_all()

    def proximity_check(self, entity, attribute, old, new, kwargs=None):
        # Double checks things whenever there is a change
        if new != old and old is not None:
            self.update_proxy()
            self.check_all()

############
# CHECKERS #
############

    def home_mode_check(self):
        """checks to see if the house mode is away

        Returns
        -------
        true: not away
        false: away
        """
        home_mode = self.get_state(self.__home_mode)
        ac_mode = self.get_state(self._ac_mode)
        if home_mode == 'away' and self.proxy is None:  #If no onw is home and no one is heading home
            if ac_mode != 'Away':
                option = 'Away'
                self.mode_select(option)
                self.log(f'__function__:  Setting ac_mode to {option}')
                return ''  # No need for further logic
            if ac_mode == 'Away':
                self.log(
                    f'__function__:  Ac_mode is already {ac_mode} doing nothing',
                    level='DEBUG')
                return ''  # No need for further logic
            self.error(f'Home Mode Check:  Ac_mode is {ac_mode} logic failed',
                       level='ERROR')
        if home_mode != 'away':
            self.log(f'__function__:  {home_mode=}', level='DEBUG')
            return True  # Home mode is not away do more
        self.error(f'Home Mode Check:  Home_mode is {home_mode} logic failed',
                   level='ERROR')
        return ''

    def is_nice_outside_check(self):
        """ Checks to see if the temperature
        is between a certain range
        Returns
        -------
        True: if the temperature is above or below a comfortable level
        False: it is nice outside
        """
        outside_temp = self.get_outside_temp()
        if self.min_temp <= outside_temp <= self.max_temp:
            return ''
        self.log(f'Its {outside_temp=} not nice outside', level='DEBUG')
        return True

    def window_check(self):
        """checks to see if a window is open

        Returns
        -------
        true: window is open
        false: windows are closed
        """
        window_status = self.get_state(self._windows)
        self.log(f'__function__:  {self._windows}', level='DEBUG')
        self.log(f'__function__:  Starting {window_status}', level='DEBUG')
        if window_status == 'on':
            self.log(f'__function__:  Windows are Open {window_status=}',
                     level='DEBUG')
            return True  #windows are open
        if window_status == 'off':
            self.log(f'__function__:  Windows are Closed {window_status=}',
                     level='DEBUG')
            return ''  #windows are closed
        self.error(
            f'__function__:  Window Status is {window_status} logic failed',
            level='ERROR')
        return ''

#########
# LOGIC #
#########

    def check_all(self):
        """
        Checks all settings to see if
        Mode is correct and changes it
        If it is not correct
        """
        self.update_proxy()
        home_check = self.home_mode_check()  #  Checks if someone is home
        not_nice_outside = self.is_nice_outside_check()  # Checks outside temp
        window_check = self.window_check()  # Checks if a window is open
        outside_temp = self.get_outside_temp()  # Gets the outside temp
        inside_temp = self.get_inside_temp()  # Get Inside Temp
        hot = self.is_hot()  # Checks if it is Hot outside
        cold = self.is_cold()  # Checks if it is Cold outside
        vent = self.is_vent()  # Check if it is ok to vent air out windows
        self.log('__function__:  Starting to Check Everything', level='DEBUG')
        self.log(f'__function__:  {window_check=}', level='DEBUG')
        if home_check:  # If someone is home or heading home
            self.log('__function__:  Someone is home', level='DEBUG')
            if not_nice_outside:  # If not nice outside
                self.log('__function__:  it is not nice outside',
                         level='DEBUG')
                if window_check:  # if a window is open but someone is home
                    self.log(f'__function__:  Window is open {window_check=}',
                             level='DEBUG')
                    if vent:  # is it ok to open a window?
                        self.log(
                            f'__function__:  Window is open and outside temp is {outside_temp} but inside is {inside_temp} ',
                            level='INFO')
                        option = 'Vent'
                        self.mode_select(option)
                    else:  # If it is not ok to open a window
                        self.log(
                            f'__function__:  Window is open and outside temp is {outside_temp} ',
                            level='WARNING')
                        option = 'Rest'
                        self.mode_select(option)
                elif hot:  # Is it hot outside?
                    self.log('__function__:  It is Hot outside', level='DEBUG')
                    option = 'Cool'
                    self.mode_select(option)
                elif cold:  # Is it cold outside?
                    self.log('__function__:  It is cold outside',
                             level='DEBUG')
                    option = 'Heat'
                    self.mode_select(option)
                else:  # No need for AC
                    self.log(
                        '__function__:  It is not nice outside but its ok inside',
                        level='DEBUG')
                    option = 'Rest'
                    self.mode_select(option)
            else:  #  If nice outside
                self.log('__function__:  It is nice outside', level='DEBUG')
                if window_check:  #if a window is open
                    self.log('__function__:  a window is open', level='DEBUG')
                    option = 'Vent'
                    self.mode_select(option)
                else:  #if window is not open
                    self.log('__function__:  a window is not open',
                             level='DEBUG')
                    option = 'Rest'
                    self.mode_select(option)
                    self.log(f'__function__:  Setting ac_mode to {option}')
        else:  # no one is home
            self.log('__function__:  No one is home', level='DEBUG')
            if window_check:  # if a window is open and no one is home
                self.log('__function__:  A window is open', level='DEBUG')
                option = 'Rest'
                self.mode_select(option)
                self.log(f'__function__:  Setting ac_mode to {option}')

    def is_hot(self):
        # Judges if it is Hot Outside
        outside_temp = self.get_outside_temp()
        optimal_temp = self.get_optimal_temp()
        inside_temp = self.get_inside_temp()
        if outside_temp > self.max_temp:
            self.log(
                f'__function__: Outside {outside_temp} > {self.max_temp} ',
                level="DEBUG")
            if inside_temp > optimal_temp:
                self.log(
                    f'__function__: Inside {inside_temp} > {optimal_temp} ',
                    level="DEBUG")
                return True  # It is hot outside
        return ''  # It is not hot outside

    def is_cold(self):
        # Judges if it is cold enough outside
        outside_temp = self.get_outside_temp()
        optimal_temp = self.get_optimal_temp()
        inside_temp = self.get_inside_temp()
        if outside_temp < self.min_temp:
            self.log(
                f'__function__: Outside {outside_temp} < {self.min_temp} ',
                level="DEBUG")
            if inside_temp < optimal_temp:
                self.log(
                    f'__function__: Inside {inside_temp} < {optimal_temp} ',
                    level="DEBUG")
                return True  # It is cold outside
        return ''  # It is not cold enough outside

    def is_vent(self):
        # Judges if it is ok to open a window and vent air
        outside_temp = self.get_outside_temp()
        optimal_temp = self.get_optimal_temp()
        inside_temp = self.get_inside_temp()
        is_not_nice_outside = self.is_nice_outside_check(
        )  # Returns True if not nice outside
        if is_not_nice_outside:  # Continue if outside is questionable
            self.log(f'__function__:  It is NOT nice outside {outside_temp=}',
                     level='DEBUG')
            if outside_temp < self.min_temp:  # Is it cold outside?
                self.log(f'__function__:  It is cold outside {self.min_temp}',
                         level='DEBUG')
                if optimal_temp < inside_temp:  # Is it too hot inside?
                    self.log(
                        f'__function__:  It is too Hot inside {optimal_temp=} {inside_temp=}',
                        level='DEBUG')
                    return True  # It's cold outside ,but hot inside
                self.log(
                    f'__function__:  It is Not too Hot inside  {inside_temp=}',
                    level='DEBUG')
                return ''  #It's cold outside and inside
            if outside_temp > self.max_temp:  # Is it hot outside?
                self.log(f'__function__:  It is hot outside {self.max_temp}',
                         level='DEBUG')
                if optimal_temp > inside_temp:  # Is it Cold inside?
                    self.log(
                        f'__function__:  It is too cold inside {optimal_temp=} {inside_temp=}',
                        level='DEBUG')
                    return True  # Its Hot outside but its cold inside
                self.log(
                    f'__function__:  It is NOT cold inside {inside_temp=}',
                    level='DEBUG')
                return ''  # its hot inside and out
            return ''
        self.log(f'__function__:  It is nice outside {outside_temp=}',
                 level='DEBUG')
        return True  # It's nice outside

######################
#     FUNCTIONS      #
# RETURN INFORMATION #
######################

    def get_outside_temp(self):
        """
        Returns
        -------
        The temperature outside
        """
        if self.get_state(entity_id=self._weather1, attribute="temperature"):
            self.log('__function__: returning weather1', level="DEBUG")
            weather1 = float(
                self.get_state(entity_id=self._weather1,
                               attribute="temperature"))
            self.log(f'{weather1=}', level="DEBUG")
            self.log(self._weather1, level="DEBUG")
            return weather1
        self.log('Weather1 Failed', level="WARNING")
        if self.get_state(entity_id=self._weather2, attribute="temperature"):
            self.log('__function__: returning weather2', level="DEBUG")
            return float(
                self.get_state(entity_id=self._weather2,
                               attribute="temperature"))
        self.log('weather2 Failed', level="WARNING")
        if self.get_state(entity_id=self._weather3):
            self.log('__function__: returning weather3', level="DEBUG")
            return float(
                self.get_state(entity_id=self._weather3,
                               attribute="temperature"))
        self.log('weather3 Failed', level="ERROR")
        return float(85)

    def get_high_point(self):
        if self.get_state(self._high_temp):
            return float(self.get_state(self._high_temp))
        self.log('Get High Point Failed', level="ERROR")
        return 90

    def get_low_point(self):
        if self.get_state(self._low_temp):
            return float(self.get_state(self._low_temp))
        self.log('Get Low Point Failed', level="ERROR")
        return 80

    def get_optimal_temp(self):
        now = self.time()
        now_hour = int(now.hour)
        optimal_temp = float(self.args['optimal_temp'][now_hour])
        return optimal_temp

    def get_inside_temp(self):
        try:
            inside_temp = float(self.get_state(self.inside_temp))
        except ValueError:
            self.error('Get Inside Temp: Could not get Inside Temp',
                       level='ERROR')
            inside_temp = 75.0
        return inside_temp

    def inside_temp_trajectory(self):
        """Uses a caluclation in HA
        to see how much the temp is changeing
        over the course of an hour

        Returns
        -------
        if the inside temp is increasing or descreasing
        """
        change = float(
            self.get_state(entity_id=self.temp_stat, attribute="change"))
        if change < 0:
            return 'decreasing'
        if change == 0:
            return 'static'
        if change > 0:
            return 'increasing'
        self.log(f'__function__: Failed to cal change, change is {change}',
                 level='Critcal')
        return 'static'

#############################
# FUNCTIONS UPDATE VARIABLE #
#############################

    def update_proxy(self, data_return=None):
        # Updates the status of people heading home
        try:
            distance = int(self.get_state(self.proximity))
        except Exception as Error:
            distance = None
            self.error(Error, level='WARNING')
        try:
            direction = self.get_state(self.proximity,
                                       attribute='dir_of_travel')
        except Exception as Error:
            direction = None
            self.error(Error, level='WARNING')

        if distance and direction:
            if distance < 30 and direction == 'towards':  #if someone is less than 30 miles away and heading home
                self.proxy = distance
            else:
                self.proxy = None
                self.log(
                    f'__function__: {distance=} and {direction=} doing nothng',
                    level='DEBUG')
        else:
            self.proxy = None
            self.log(
                f'__function__: Failed to get either {distance=} or {direction=}',
                level='WARNING')
        if data_return:
            return distance, direction


###################
#    FUNCTIONS    #
# CHANGE SETTINGS #
###################

    def mode_select(self, option='Cool'):
        # Changes the overall mode of the ACs
        ac_mode_status = self.get_state(
            self._ac_mode)  # Gets the current status of the AC mode
        new_mode = option
        self.log(f'__function__: Attemping to change mode to {new_mode}',
                 level='DEBUG')
        if ac_mode_status == new_mode:  # Is the AC already Mode?
            self.log(f'__function__: Mode is {ac_mode_status} doing nothing',
                     level='DEBUG')
        elif ac_mode_status != new_mode:  # AC is not new mood
            self.log(f'__function__: Setting mode to {new_mode}',
                     level='DEBUG')
            self.select_option(
                entity_id=self._ac_mode,
                option=new_mode)  # Change the Entity in Home Asisstant
        else:
            self.error(
                f'Mode Select: {ac_mode_status=} {new_mode=} Logic Failed',
                level='ERROR')


