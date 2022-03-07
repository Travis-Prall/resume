import datetime as dt
import appdaemon.plugins.hass.hassapi as hass
from typing import Dict, Tuple, Union, Optional, Any



class Fish(hass.Hass):
    """
    turns off the sump in the fish tank so you can
    feed the fish without it sucking all the food
    into the sump
    """
    def initialize(self):
        self.log(f'Starting {__name__} initialization')
        self._timer: object = None  # timer object to resume normal
        self._notify_timer: object = None  # timer object to notify return to normal
        self._timer_start:dt.datetime = None  # when feed mode happened
        # Getters and Setters #
        self._sound: object = self.get_app("coyote")
        try:
            self._feed_time:int = int(self.args['feed_time']) * 60
        except KeyError:
            self._feed_time:int = 600
            self.log("Missing varible target", level="WARNING")

        try:
            self._warning_time_interval:int = int(
                (self._feed_time) / (self.args['warning_time_interval'] + 1))
        except (KeyError, ValueError):
            self._warning_time_interval:int = 600
            self.log(f"Missing varible {self._warning_time_interval=}",
                     level="WARNING")

        try:
            self._target:str = self.args['target']
        except KeyError:
            self._target:str = "foyer"
            self.log("Missing varible target", level="WARNING")

        try:
            self._sump:Optional[str] = self.args['sump']
        except KeyError:
            self._sump:Optional[str] = None
            self.log("Missing varible sump", level="WARNING")

        try:
            self._pump:str = self.args['pump']
        except KeyError:
            self._pump:str = None
            self.log("Missing varible pump", level="WARNING")

        # Check #
        self.start_app()
        # Timers #
        runtime:dt.time = dt.time(0, 3, 0)
        self.run_hourly(self.hourly_check, runtime)
        # Actions #
        self.listen_state(self.change_detected, self._sump)
        self.listen_state(self.change_detected, self._pump)

##########
# REPORT #
##########

    def start_app(self):
        """Test entities to make sure they work"""
        self.log('__function__: __module__', level="DEBUG")
        entity_start_list = [self._sump, self._pump]
        for entity in entity_start_list:
            try:
                test = self.get_state(entity)
            except (TypeError, ValueError):
                self.error(f"Unable to get {entity}", level="ERROR")
                return

            if test is None:
                self.error(f"unable to get state for {entity}", level="ERROR")
                return
        self.sump_check()
        self.log('App is now working', level="DEBUG")

############
# WATCHERS #
############

    def change_detected(self, entity, attribute, old, new, kwargs):
        """Double checks things whenever there is a change"""
        name = self.friendly_name(entity)  #gets the name of the entity
        sump = self.get_sump()
        if new != old and old is not None:
            self.log(f"{name} changed from {old} to {new}")
            if sump == 'off':
                if self._timer:
                    self.turn_off_pump()
                else:
                    self.feed_mode()
            if sump == 'on':
                self.cancel_timers()

############
# CHECKERS #
############

    def hourly_check(self, kwargs:Optional[Any]=None) -> None:
        """Checks things once an hour"""
        self.log(f' __function__ : Checking {self._sump}', level='DEBUG')
        sump = self.get_sump()
        self.log(f' __function__ : Sump is {sump}')
        self.sump_check()

    def sump_check(self) -> None:
        """Checks the sump to make sure it is running"""
        sump = self.get_sump()
        self.log(f'Sump Check: Sump is {sump}')
        if self._timer:
            self.log('__function__: timer is running', level='DEBUG')
            self.timer_check()
        elif sump == 'off':
            self.log(f' __function__ : sump is {sump}', level='DEBUG')
            self.return_to_normal()
        elif sump == 'on':
            self._timer_start:dt.datetime = None
            self.log(f' __function__ : sump is {sump} doing nothing',
                     level='DEBUG')
        else:
            self.error(
                f'Sump Check: Something went wrong {sump=} {self._timer=}',
                level='ERROR')

    def timer_check(self) -> None:
        """Checks the time to make sure it is working"""
        feed_time = (self._feed_time) / 60  # feed time in minutes
        time_left = self.get_time_left()
        if time_left > feed_time:
            self.return_to_normal()
            self.error(f'Timer Check: Timer is expired at {time_left}',
                       level='ERROR')
        elif time_left < feed_time:
            self.log('__function__: Timer Check ok ', level='DEBUG')
        else:
            self.error(f'Timer Check:  Timer check failed at {time_left}',
                       level='ERROR')

##########
# TIMERS #
##########

    def time_up(self, kwargs:Optional[Any]=None) -> None:
        self._timer = None
        self.log(
            f' __function__ : timer has ended started {self._timer_start}',
            level='DEBUG')
        self.return_to_normal()

#########
# LOGIC #
#########

    def feed_mode(self) -> None:
        """Starts the feed mode"""
        self.log("__function__ : Starting Feed Mode for Fish")
        self._timer_start:dt.datetime = dt.datetime.today()
        self.log(f"__function__ : Timer start is {self._timer_start}",
                 level="DEBUG")
        self.log("__function__ : Starting Feed Mode for Fish")
        self._timer = self.run_in(
            self.time_up, self._feed_time)  # Timer until sump turn back on
        self.turn_off_pump()
        self.notify_start_feed()

    def cancel_timers(self):
        """Cancel the timer"""
        if self._timer:
            try:
                self.cancel_timer(
                    self._timer)  #Cancels the current timer if its running
                self.log(f' __function__ : Canceling {self._timer=}',
                         level='DEBUG')
            except AttributeError as e:
                self.log(f' __function__ : No timer {e}', level='DEBUG')
            self._timer = None
        if self._notify_timer:
            try:
                self.cancel_timer(self._notify_timer
                                  )  #Cancels the current timer if its running
                self.log(f' __function__ : Canceling {self._notify_timer=}',
                         level='DEBUG')
            except AttributeError as e:
                self.log(f' __function__ : No timer {e}', level='DEBUG')
            self._notify_timer = None
        self._timer_start = None
        self.log('__function__: finsihed canceling timers', level='DEBUG')

######################
#     FUNCTIONS      #
# RETURN INFORMATION #
######################

    def get_sump(self) -> str:
        """Get the state of the sump
        
        Return
        ------
        on: sump is on
        off: sump if off
        """
        try:
            sump = self.get_state(self._sump)
            return sump
        except Exception as e:
            self.error(f' Get Sump : {e} ', level='ERROR')
        return 'off'

    def get_pump(self) -> str:
        """Get the state of the pump
        
        Return
        ------
        on: pump is on
        off: pump if off
        """
        try:
            pump = self.get_state(self._pump)
            return pump
        except Exception as e:
            self.error(f' Get Pump : {e} ', level='ERROR')
        return 'off'

    def get_time_left(self) -> int:
        """Returns the minutes left"""
        if self._timer_start:
            timer_start = self._timer_start
        else:
            return 0
        self.log(f' __function__ : {timer_start=}', level='DEBUG')
        now = dt.datetime.today()
        self.log(f' __function__ : {now=}', level='DEBUG')
        delta = now - timer_start
        self.log(f' __function__ : {delta=}', level='DEBUG')
        seconds = int(delta.total_seconds())
        self.log(f' __function__ : {seconds=}', level='DEBUG')
        seconds_left = self._feed_time - seconds
        minutes = int(seconds_left / 60)
        self.log(f' __function__ : Returning {minutes}', level='DEBUG')
        return minutes


###################
#    FUNCTIONS    #
# CHANGE SETTINGS #
###################

    def return_to_normal(self) -> None:
        """Returns the fishtank to normal"""
        self.log(' __function__ : Returning to normal')
        try:
            self.turn_on(self._sump)
        except Exception as e:
            self.error(f' Return to Normal : {e} ', level='ERROR')
        self.cancel_timers()
        self.notify_area(text="Returning fish tank to normal")

    def turn_off_pump(self) -> None:
        """Turns the pump off"""
        pump = self.get_pump()
        if pump == 'on':
            try:
                self.turn_off(self._pump)
                self.log(f'__function__: pump is {pump} turning off')
            except Exception as e:
                self.error(f' Turn off Pump : {e} ', level='ERROR')
        elif pump == 'off':
            self.log('__function__: Pump is off', level='DEBUG')
        else:
            self.error(f' Turn off Pump : somethign went wrong {pump=} ',
                       level='ERROR')

    def notify_area(self, text:str) -> None:
        """Speaks an announcement"""
        self.log(f'__function__ : Sending text {text}', level='DEBUG')
        self._sound.ctts(text, target=self._target)

    def notify_start_feed(self) -> None:
        """Speaks an announcement to the area"""
        time = int((self._feed_time) / 60)
        text = f'Feed Mode started will end in {time} minutes'
        self.log(f'__function__ : Sending text {text}', level='DEBUG')
        self._sound.ctts(text, target=self._target)
        self._notify_timer = self.run_in(self.notify_time_left,
                                          self._warning_time_interval)

    def notify_time_left(self, kwargs:Optional[Any]=None) -> None:
        """Notifies how much time is left"""
        time = self.get_time_left()
        self._notify_timer = None
        if time > 1:
            grammer = 'minutes'
        else:
            grammer = 'minute'
        if time > 0:
            text = f'Fish Tank will resume normal operations in {time} {grammer}'
            self.log(f'__function__: Sending text {text}', level='DEBUG')
            self._sound.ctts(text, target=self._target)
            self._notify_timer = self.run_in(self.notify_time_left,
                                              self._warning_time_interval)
        else:
            self.log(f'__function__: Timer is {time} stopping',
                     level='DEBUG')
