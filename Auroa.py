import random
import appdaemon.plugins.hass.hassapi as hass
import WorldConst


class master_bedroom(hass.Hass):
    def initialize(self):
        self.log('App is working')
        # Getters and Setters #
        self.__timer = None
        self.__light = self.args['lightID']
        self._room = self.args['castle']
        self._service = self.args["service"]
        self.__start_time = int(WorldConst.Auroastart_time)
        self.__end_time = int(WorldConst.Auroaend_time)
        self._highest_degree = int(WorldConst.Auroahighest_degree)
        self._lowest_degree = int(WorldConst.Auroalowest_degree)
        self._color_spread = int(WorldConst.Auroacolor_spread)
        self._brit_high = WorldConst.Auroabrit_high
        self._brit_low = WorldConst.Auroabrit_low
        self.start()
        self.listen_state(self.lighting, self._room, new='100')

##########
# REPORT #
##########

    def start(self):
        self.log('Starting App', level="DEBUG")
        try:
            light = self.get_state(self.__light)
            castle = self.get_state(self._room)
        except (TypeError, ValueError):
            self.error("Unable to get entity", level="ERROR")
            return

        if None in [light, castle]:
            self.error("unable to get state", level="ERROR")
            return
        self.log('App is now working', level="DEBUG")

############
# WATCHERS #
############

    def lighting(self, entity, attribute, old, new, kwargs):
        room = entity
        self.log(f"new is {new} and old is {old}", level="DEBUG")
        if new != old and old is not None:
            name = self.friendly_name(room)
            room_act = float(new)
            self.log(f"{name} changed from {old} to {new}", level="DEBUG")
            if room_act == 100:
                self.turn_on(self.__light)
                self.set_light()
            else:
                self.end_cycle()
                self.turn_off(self.__light)

############
# CHECKERS #
############

    def check_light(self):
        self.log(f"Check Light: checking {self._room}", level="DEBUG")
        state = float(self.get_state(self._room, default="0"))
        self.log(state, level="DEBUG")
        self.__timer = None
        if state > 0:
            self.set_light()
        else:
            self.end_cycle()
            self.turn_off(self.__light)

    def check_room(self):
        self.log(f"Check Room: checking {self._room}", level="DEBUG")
        state = float(self.get_state(self._room, default="0"))
        self.log(state, level="DEBUG")
        if state > 0:
            self.log('Check Room: state is > 0', level="DEBUG")
            self.turn_on(self.__light)
            self.set_light()
        else:
            self.log('Check Room: state is NOT > 0', level="DEBUG")
            self.end_cycle()
            self.turn_off(self.__light)

#########
# TIMER #
#########

    def start_cycle(self, tran):
        ''' Start the timer '''
        self.log('__function__: Starting countdown', level='DEBUG')
        if self.__timer:
            self.log(f'__function__: attempting to cancel {self.__timer}',
                     level='DEBUG')
            try:
                self.cancel_timer(
                    self.__timer)  # Cancels the current timer if its running
                self.log('__function__: Canceling timer', level='DEBUG')
            except Exception as e:
                self.log(f'__function__: {e}', level='WARNING')
        else:
            self.log(f'__function__: No timer detected in {self.__timer} ',
                     level='DEBUG')
        self.__timer = self.run_in(self.execute_timer,
                                   tran)  # Start the new timer
        self.log(f'__function__: Checking lights in {tran} secounds',
                 level='DEBUG')

    def execute_timer(self, kwargs):
        ''' turns the timer handle off and fires the timer '''
        self.log('__function__: executing timer', level='DEBUG')
        self.__timer = None
        self.check_light()

    def end_cycle(self):
        ''' End the timer '''
        self.log('__function__: Ending countdown', level='DEBUG')
        if self.__timer:
            self.log(f'__function__ : attempting to cancel {self.__timer}',
                     level='DEBUG')
            try:
                self.cancel_timer(
                    self.__timer)  # Cancels the current timer if its running
                self.log('__function__: Canceling timer', level='DEBUG')
            except Exception as e:
                self.log(f'__function__: {e}', level='WARNING')
        self.__timer = None

#########
# LOGIC #
#########

    def get_hue(self):
        now = self.time()
        now_hour = int(now.hour)
        start = self.__start_time
        end = self.__end_time
        highest = self._highest_degree
        lowest = self._lowest_degree
        change = self._color_spread
        tick = (highest - lowest - change) / (end - start)
        self.log(f"tick = {tick}", level="DEBUG")
        if now_hour <= 12:
            now_hour = now_hour + 24
            if now_hour > end:
                self.log("now_hour > end", level="DEBUG")
                high = highest
                self.log(f"high = {high}", level="DEBUG")
                low = int(high - change)
                self.log(f"low = {low}", level="DEBUG")
                return random.randint(low, high)
            low = int(((now_hour - start) * tick) + lowest)
            self.log(f"low = {low}", level="DEBUG")
            high = int(low + change)
            self.log(f"high = {high}", level="DEBUG")
            return random.randint(low, high)
        if now_hour <= start:
            low = int(lowest)
            self.log(f"low = {low}", level="DEBUG")
            high = int(low + change)
            self.log(f"high = {high}", level="DEBUG")
            return random.randint(low, high)
        low = int(((now_hour - start) * tick) + lowest)
        self.log(f"low = {low}", level="DEBUG")
        high = int(low + change)
        self.log(f"high = {high}", level="DEBUG")
        return random.randint(low, high)

######################
#     FUNCTIONS      #
# RETURN INFORMATION #
######################

    def get_sat(self):
        low = 70
        high = 100
        return random.randint(low, high)

    def get_bright(self):
        low = self._brit_low
        high = self._brit_high
        return random.randint(low, high)

    def get_tran(self):
        high = 30
        low = 5
        return random.randint(low, high)


###################
#    FUNCTIONS    #
# CHANGE SETTINGS #
###################


    def set_light(self):
        self.log('setting light', level='DEBUG')
        tran = self.get_tran()
        hue = self.get_hue()
        sat = self.get_sat()
        bright = self.get_bright()
        self.log(f"hue is {hue}", level="DEBUG")
        self.call_service(
            self._service,
            entity_id=self.__light,
            transition=tran,
            hs_color=(hue, sat),
            brightness_pct=bright,
        )
        self.start_cycle(tran)
