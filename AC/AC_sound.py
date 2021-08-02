import appdaemon.plugins.hass.hassapi as hass
import global_weather


class Thermo(hass.Hass):
    def initialize(self):
        self.log('App is working')
        # Getters and Setters #
        self._ac_mode = global_weather.Ac_mode
        self.ACOn = ('Cool', 'Heat')  # List of modes that mean the AC is on
        self.ACOff = ('Vent', 'Manuel', 'Rest', 'Away'
                      )  # List of modes that mean the AC is off
        self.soundDir = self.args[
            'playerdir']  # the location of the sound files
        self.sound = self.get_app(
            "coyote")  # gets the coyote.py app to play sounds
        self._weather1 = global_weather.Weather1  # DarkSky
        self.windows = global_weather.Window_list  # list of all window sensors
        self._all_windows = global_weather.Windows  #Master Switch that turns on if any window is open
        self.doors = global_weather.Doors  # list of doors that lead outside
        self._sound_dict = global_weather.Sound_dict  # dictanory of avialbe sound files
        # Actions #
        for window in self.windows:
            self.listen_state(self.window_change, window)
        self.listen_state(self.change_detected, self._ac_mode)
        for door in self.doors:
            self.listen_state(self.door5, door, new="on", duration=300)
            self.listen_state(self.door30, door, new="on", duration=1800)
            self.listen_state(self.door1, door, new="on", duration=3600)
        self.start()

##########
# REPORT #
##########

    def start(self):
        ac_mode_status = self.get_state(
            self._ac_mode)  # Mode of the AC Control Entity
        self.log(f"{ac_mode_status=}")
        self.annouce_windows()

############
# WATCHERS #
############

    def change_detected(self, entity, attribute, old, new, kwargs):
        # Double checks things whenever there is a change
        name = self.friendly_name(entity)  #gets the name of the entity
        if old != new:  # Is Change
            self.log(f"{name} changed from {old} to {new}")
            if new == 'Vent':
                w_list = self.get_windows()  # gets a list of window
                text = (
                    f'The Following windows are open{w_list} Now changing all fans to on'
                )
                self.log(f'Change Detected: Playing {text}')
                self.sound.ctts(text)
            if old in self.ACOn:  # Was AC on
                if new == 'Rest':
                    temp = self.get_state(self._weather1, default="75")
                    text = (f'It is {temp} outside')
                    self.log(f'Change Detected: Playing {text}')
                    self.sound.ctts(text)
                    self.play_sound_file('life_off')
                elif new in self.ACOff:  # Is AC now off
                    self.play_sound_file('life_off')
            if old in self.ACOff:  # Was AC off
                if new in self.ACOn:  # Is AC now on
                    self.play_sound_file('life_on')

    def window_change(self, entity, attribute, old, new, kwargs):
        # Annouces if a Window is Closed or Opened
        name = self.friendly_name(entity)  #gets the name of the entity
        state = self.get_state(entity)
        if old != new:
            self.log(f"{name} changed from {old} to {new}")
            if state == 'on':  # Is Window Open
                text = (f'{name} is now open')
                self.log(f'Window Change: Playing {text}')
                self.sound.ctts(text)
            elif state == 'off':  # Is Window Closed
                text = (f'{name} is now closed')
                self.log(f'Window Change: Playing {text}')
                self.sound.ctts(text)
            else:
                self.error(f'Window Change: Logic Failed {state=}',
                           level='ERROR')

############
# CHECKERS #
############

#########
# LOGIC #
#########

######################
#     FUNCTIONS      #
# RETURN INFORMATION #
######################

    def annouce_windows(self):
        """Annouces the names of any open windows
        """
        for window in self.windows:
            state = self.get_state(window, default="off")
            name = self.friendly_name(window)
            if state == 'on':
                text = (f'{name} is open')
                self.log(f'Announce Window: Playing {text}')
                self.sound.ctts(text)

    def get_windows(self):
        """Makes a list of open windows
        """
        window_list = []
        for window in self.windows:  # cycles though all windows
            state = self.get_state(window, default="off")  # Window state
            name = self.friendly_name(window)
            if state == 'on':  # is window open
                self.log(f'Get Windows: adding {name} to the list',
                         level="DEBUG")
                window_list.append(name)  # add window to list
        if window_list:  # check to make sure list is not empty
            return window_list
        self.log(f'Get Windows: Logic Failed {window_list=}', level="ERROR")
        return 'No Windows'

    # def announce_ac_off(self):
    #     source = self._life_off
    #     soundfile = str(self.soundDir + source)
    #     self.log(f'Announce AC Off: Playing {soundfile}')
    #     self.sound.ctts.cplay(path=soundfile, volume=1.0)

    def door5(self, entity, attribute, old, new, kwargs):
        """Plays a warning if a door was left open
        for over 5 minutes
        """
        name = self.friendly_name(entity)  # Name of Door
        text = (f'{name} has been open for 5 minutes')  # Text to Play
        self.log(f'Door5: Playing {text}')
        self.sound.ctts(text)

    def door30(self, entity, attribute, old, new, kwargs):
        """Plays a warning if a door was left open
        for over 30 minutes
        """
        name = self.friendly_name(entity)  # Name of Door
        text = (f'{name} has been open for 30 minutes')  # Text to Play
        self.log(f'Door30: Playing {text}')
        self.sound.ctts(text)

    def door1(self, entity, attribute, old, new, kwargs):
        """Plays a warning if a door was left open
        for over 1 hour
        """
        name = self.friendly_name(entity)  # Name of Door
        text = (f'Holy Shit {name} has been open for 1 hour')  # Text to Play
        self.log(f'Door1: Playing {text}')
        self.sound.ctts(text)


###################
#    FUNCTIONS    #
# CHANGE SETTINGS #
###################

    def play_sound_file(self, sound='deactivating'):
        """Plays a sound by pulling the file location
        from a dictonary

        Parameters
        ----------
        sound : str, optional
            [description], by default 'deactivating'

        Sound_dict = {
        'deactivating': Deactivating,
        'life_off': Life_off,
        'life_on': Life_on
}
        """
        sound_file = sound
        sound_dict = self._sound_dict
        source = sound_dict.get(sound_file)
        soundfile = str(self.soundDir + source)
        self.log(f'Play Sound: Playing {soundfile}')
        self.sound.cplay(path=soundfile, volume=1.0)


