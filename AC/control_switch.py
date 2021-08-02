import datetime as dt
import appdaemon.plugins.hass.hassapi as hass
import global_weather


class Thermo(hass.Hass):
    def initialize(self):
        self.log(f'__function__: Starting {__name__}', level='INFO')
        # World App #
        World = self.get_app('World')
        self.__home_mode = World.get_mode_device('home')
        # Getters and Setters #
        self._windows = global_weather.Windows  # Master Switch that turns on if any window is open
        self._windows_list = global_weather.Window_list  # list of all window sensors
        self.doors = global_weather.Doors  # list of doors that lead outside

        try:
            self._switch = self.args['switch']
        except KeyError:
            self._switch = None
            self.log("Missing varible switch", level="WARNING")

        try:
            self._timeout = (int(self.args['timeout']) * 60 * 60
                             )  # Timeout in hours
        except KeyError:
            self._timeout = 1 * 60 * 60
            self.log("Missing varible timeout", level="WARNING")

        # Start #
        self.start_app()
        # Check #
        self.check_all()
        # Timers #
        runtime = dt.time(0, 15, 0)
        self.run_hourly(self.timer_check, runtime)
        # Actions #
        for door in self.doors:
            self.listen_state(self.door_changed, door, new="on", duration=300)
        self.listen_state(self.windows_changed, self._windows)
        self.listen_state(self.mode_changed, self.__home_mode)
        self.listen_state(self.change_detected, self._switch, immediate=True)
        self.listen_state(self.switch_timeout,
                          self._switch,
                          new="off",
                          immediate=True,
                          duration=self._timeout)

##########
# REPORT #
##########

    def start_app(self):
        self.log('Starting App', level="DEBUG")
        entity_start_list = [self._switch, self.__home_mode]
        for entity in entity_start_list:
            try:
                test = self.get_state(entity)
            except (TypeError, ValueError):
                self.error(f"Unable to get {entity}", level="ERROR")
                return

            if test is None:
                self.error(f"unable to get state for {entity}", level="ERROR")
                return
        self.log('App is now working', level="DEBUG")

############
# WATCHERS #
############

    def change_detected(self, entity, attribute, old, new, kwargs):
        # Double checks things whenever there is a change
        name = self.friendly_name(entity)  #gets the name of the entity
        if new != old and old is not None:
            self.log(f"__function__: {name} changed from {old} to {new}")
            self.check_all()

    def windows_changed(self, entity, attribute, old, new, kwargs):
        # Double checks things whenever there is a change
        name = self.friendly_name(entity)  # gets the name of the entity
        if new != old and old is not None:
            self.log(f"{name} changed from {old} to {new}")
            self.check_windows()

    def mode_changed(self, entity, attribute, old, new, kwargs):
        # Double checks things whenever there is a change
        name = self.friendly_name(entity)  # gets the name of the entity
        if new != old and old is not None:
            self.log(f"{name} changed from {old} to {new}")
            self.check_home_mode()

    def door_changed(self, entity, attribute, old, new, kwargs):
        # Double checks things whenever there is a change
        name = self.friendly_name(entity)  # gets the name of the entity
        if new != old and old is not None:
            self.log(f"{name} changed from {old} to {new}")
            self.control_switch_on()

############
# CHECKERS #
############

    def check_all(self):
        self.log('__function__: Checking_Everything', level='DEBUG')
        self.check_windows()
        self.check_home_mode()

    def check_windows(self):
        self.log('__function__: Checking_windows', level='DEBUG')
        if self.windows_open():
            self.log('__function__: Windows are open turning switch back on')
            self.control_switch_on()

    def check_home_mode(self):
        self.log('__function__: Checking Home Mode', level='DEBUG')
        if self.people_away():
            self.log('__function__: No one is home')
            self.control_switch_on()

##########
# TIMERS #
##########

    def timer_check(self, kwargs):
        self.log('__function__: Checking', level='DEBUG')
        self.check_all()

    def switch_timeout(self, entity, attribute, old, new, kwargs):
        time_hours = self._timeout / 60 / 60
        self.log(
            f'__function__: it has been {time_hours} setting control to auto')
        self.control_switch_on()

#########
# LOGIC #
#########

######################
#     FUNCTIONS      #
# RETURN INFORMATION #
######################

    def windows_open(self):
        self.log('__function__: Checking if windows are open', level='DEBUG')
        for window in self._windows_list:
            self.log(f'__function__: Checking {window}', level='DEBUG')
            try:
                state = self.get_state(window)
                if state == 'on':
                    return window
            except (ValueError, AttributeError):
                self.log(f'__function__: Unable to get state for {window}',
                         level='WARNING')
        return None

    def people_away(self):
        self.log('__function__: Checking if home mode is away', level='DEBUG')
        try:
            state = self.get_state(self.__home_mode)
            self.log(f'__function__: {self.__home_mode} is {state} ',
                     level='DEBUG')
            if state == 'away':
                return state
        except (ValueError, AttributeError):
            self.log(
                f'__function__: Unable to get state for {self.__home_mode}',
                level='WARNING')
        return None

###################
#    FUNCTIONS    #
# CHANGE SETTINGS #
###################

    def control_switch_on(self):
        self.log('__function__: turning switch back on', level='DEBUG')
        self.turn_on(self._switch)


#############
# TERMINATE #
#############

    def terminate(self):
        pass


