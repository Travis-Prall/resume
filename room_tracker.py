import datetime as dt
import appdaemon.plugins.hass.hassapi as hass
import Worldglobal
import global_weather
'''
This app controls each room
'''


class Castle(hass.Hass):
    def initialize(self):
        # Getters and Setters #
        self.World = self.get_app('World')
        self._room = self.args['room']  # Room Entity by name
        self._room_name = self.args['friendly_name']
        self._room_entity = self.args['entity']
        self._room_timer = self.args['timer']
        self._keep = (f'keep.{self._room}')  # Name of keep
        self._home_mode = Worldglobal.Home_mode
        self._unknown = Worldglobal.Unknownkeep
        self.__timer = None
        try:  # Check for countdown
            self._click = float(self.args["countdown"])
        except KeyError:
            self._click = 10.0
            self.log("Missing varible countdown", level="WARNING")

        try:  # Check if room will turn off if Empty
            self._empty = self.args["empty"]
        except KeyError:
            self._empty = None
            self.log("Missing varible empty", level="DEBUG")

        try:  # Check for motion device
            self._motion = self.args["motion"]
        except KeyError:
            self._motion = None
            self.log("Missing varible motion", level="INFO")

        try:  # Check for image processing device
            self._img = self.args["image_proc"]
        except KeyError:
            self._img = None
            self.log("Missing varible image processing", level="DEBUG")

        try:  # Check for lights to turn on
            self._lights_on = self.args["lights"]["turn_on"]
        except KeyError:
            self._lights_on = None
            self.log("Missing varible lights on", level="DEBUG")

        try:  # Check for lights to turn off
            self._lights_off = self.args["lights"]["turn_off"]
        except KeyError:
            self._lights_off = None
            self.log("Missing varible lights off", level="INFO")

        try:  # Check if lights are dimmer
            self._dimmer = self.args["dimmer"]
        except KeyError:
            self._dimmer = None
            self.log("Missing varible dimmer", level="DEBUG")

        try:  # Check what time to turn on lights
            self._on_mode = self.args["on_mode"]
        except KeyError:
            self._on_mode = ['evening']
            self.log("Missing varible on_mode", level="DEBUG")

        try:  # Check for fans
            self._fans = self.args["fans"]
        except KeyError:
            self._fans = None
            self.log("Missing varible fans", level="DEBUG")

        try:  # Check for room control device
            self._control = self.args["control"]
        except KeyError:
            self._control = None
            self.log("Missing varible control", level="DEBUG")

        try:  # Check for temperature sensor
            self._room_temp = self.args["temperature"]
        except KeyError:
            self._room_temp = global_weather.inside_temp
            self.log("Missing varible temperature sensor", level="DEBUG")

        # Check #
        self.set_app_pin(False)
        self.initialize_room()
        self.config_check()
        # Timers #
        # self.__timer = None
        # runtime = dt.time(0, 0, 0)
        # self.run_hourly(self.recheck, runtime)
        # self.run_daily(self.refresh, "sunrise")
        # self.run_daily(self.refresh, "sunset")
        # Actions #
        self.listen_state(self.change_room_timer,
                          self._home_mode,
                          immediate=True)
        if self._motion:
            for device in self.split_device_list(self._motion):
                self.listen_state(self.motion_detected, device)
        if self._lights_on:
            for light in self.split_device_list(self._lights_on):
                self.listen_state(self.change_detected,
                                  light,
                                  new="on",
                                  duration=5)
        if self._lights_off:
            for light in self.split_device_list(self._lights_off):
                self.listen_state(self.change_detected,
                                  light,
                                  new="on",
                                  duration=5)
        if self._fans:
            for fan in self.split_device_list(self._fans):
                self.listen_state(self.change_detected,
                                  fan,
                                  new="on",
                                  duration=5)
        if self._img:
            self.listen_state(self.person_detected, self._img)

        if self._empty:
            self.listen_state(self.room_empty,
                              self._keep,
                              new='Empty',
                              immediate=True)

##########
# REPORT #
##########

    def initialize_room(self):
        # Set up interal database
        locker = dict()  # create storage for attributes
        room = f'room.{self._room}'
        self._activity_sensor = f'sensor.activity_{self._room}'

        if self._motion:
            locker['motion_device'] = True
        else:
            locker['motion_device'] = None

        if self._img:
            locker['img_device'] = True
        else:
            locker['img_device'] = None

        if self._fans:
            locker['fan_device'] = True
        else:
            locker['fan_device'] = None

        try:
            get_state = self.get_state(room, namespace='rooms')
            if get_state:
                room_state = get_state
            else:
                room_state = 0

        except (ValueError, TypeError):
            room_state = 0

        try:
            sensor_state = float(
                self.get_state(self._activity_sensor, namespace='rooms'))
        except (ValueError, TypeError):
            sensor_state = 0

        self.set_state(room,
                       state=room_state,
                       attribute=locker,
                       namespace='rooms')
        self.set_state(self._activity_sensor,
                       state=sensor_state,
                       namespace='rooms')

        # Set up the room entity in Home Assistant
        entity = self._room_entity
        room_attr = {}
        room_attr["occupancy"] = "Empty"
        room_attr["friendly_name"] = self._room_name
        room_attr["unit_of_measurement"] = "activity"
        room_attr["icon"] = "mdi:square-outline"

        new_state = int(sensor_state)

        self.set_state(entity,
                       state=new_state,
                       attributes=room_attr,
                       namespace='default')
        self.log(f"Initialized : {entity}", level="DEBUG")

        if self.is_on():  # check if any lights are on and start the timer
            self.start_cycle()

    def config_check(self):
        # Check the config to make sure everything is working
        self.log('__function__: Checking Configuration', level="INFO")
        entity_start_list = [
            self._room_entity, self._room_timer, self._home_mode
        ]
        optional_devices = [
            self._motion, self._lights_on, self._lights_off, self._fans,
            self._control
        ]

        for entity in entity_start_list:
            try:
                test = self.get_state(entity, namespace='default')
            except (TypeError, ValueError):
                self.log(f"Unable to get {entity}",
                         level="ERROR",
                         log='important')
                return

            if test is None:
                self.log(f"unable to get state for {entity}",
                         level="ERROR",
                         log='important')
                return

        for config in optional_devices:
            if config:  #Check Config
                for device in self.split_device_list(config):
                    try:
                        device_state = self.get_state(device,
                                                      namespace='default')
                    except (TypeError, ValueError):
                        self.log(f"Unable to get {device}",
                                 level="ERROR",
                                 log='important')
                    self.log(f'{device_state=}', level='INFO')
                    if device_state not in ['off', 'on']:
                        self.log(f"Invalid Device State for {device}",
                                 level='WARNING',
                                 log='important')

            # if self._room_temp:  #Check temperature device
            #     try:
            #         device_state = self.get_state(self._room_temp)
            #     except (TypeError, ValueError):
            #         self.log(f"Unable to get {self._room_temp}",
            #                  level="ERROR",
            #                  log='important')
            #         return

            #     try:
            #         tmp = int(device_state)

            #     except ValueError:
            #         self.log("Invalid Device State",
            #                  level='WARNING',
            #                  log='important')
            #         return

        self.log('__function__:App configured correctly', level="INFO")

############
# WATCHERS #
############

    def motion_detected(self, entity, attribute, old, new, kwargs):
        #   Motion device changed
        entity_name = self.friendly_name(entity)
        self.log(f'__function__: {entity_name} changed from {old} to {new}',
                 level='INFO')
        self.log(entity, level='DEBUG')
        if new != old and old is not None:
            if new in ("detected", "on"):
                new_state = 100
                self.apply_state(new_state)
                self.turn_on_room()  # If motion is detected
            else:
                if self._img:
                    if self.is_person():
                        return  # don't countdown if room has an image processor
                self.start_cycle()  # Start the countdown if all motion is off

    def person_detected(self, entity, attribute, old, new, kwargs):
        # Handles the detection of the image processing cameras
        entity_name = self.friendly_name(entity)
        self.log(f'__function__: {entity_name} changed from {old} to {new}',
                 level='INFO')
        self.log(entity, level='DEBUG')
        if new != old and old is not None:
            if self.is_person():
                new_state = 100
                self.apply_state(new_state)
                self.turn_on_room()  # If person is detected
            else:
                self.start_cycle(
                )  # Start the countdown if person is no longer detected

    def room_empty(self, entity, attribute, old, new, kwargs):
        #  Turns off the room if the 'keep' system thinks it's empty
        entity_name = self.friendly_name(entity)
        self.log(f'__function__: {entity_name} changed from {old} to {new}',
                 level='INFO')
        if new != old and old is not None:
            new_state = 0
            self.apply_state(new_state)
            self.turn_off_room()  # If room is empty

    def change_detected(self, entity, attribute, old, new, kwargs):
        entity_name = self.friendly_name(entity)
        self.log(f'__function__: {entity_name} changed from {old} to {new}',
                 level='DEBUG')
        if new != old and old is not None:
            self.log('__function__: checking for motion device', level='DEBUG')
            if self._img:
                self.log("__function__: image processing is True",
                         level="DEBUG")
                if self.is_person():  # Is a person detected?
                    self.log("changed_detected: is person is True",
                             level="DEBUG")
                    return  # Stop the check
            if self._motion:  # Is there a motion device?
                self.log("__function__: motion device is True", level="DEBUG")
                if self.is_motion():  # Is any motion device on?
                    self.log("changed_detected: is motion is True",
                             level="DEBUG")
                    return  # Stop the check
                self.log("__function__: is motion is False", level="DEBUG")
                self.log(
                    f"__function__: {entity_name} changed to {new} without motion",
                    level="INFO")
                new_state = 100
                self.apply_state(new_state)
                self.start_cycle()
            else:  # There is no motion device but something turned on
                self.log("__function__: motion device is False", level="DEBUG")
                new_state = 100
                self.apply_state(new_state)
                self.start_cycle()

    def change_room_timer(self, entity, attribute, old, new, kwargs):
        # Changes the default timer when the home mode changes
        entity_name = self.friendly_name(entity)
        self.log(f'__function__: {entity_name} changed from {old} to {new}',
                 level='DEBUG')
        if new != old and old is not None:
            self.reset_room_timer()  # Resets the room countdown timer rate

############
# CHECKERS #
############

    def motion_check(self):
        self.log("__function__: Checking for motion", level="DEBUG")
        if self.is_motion():  # is motion active
            self.log("__function__: There is motion in the room",
                     level="DEBUG")
            self.__timer = None  # Remove the Timer
            new_state = 100
            self.apply_state(new_state)  # Change room to fully active 100
            return True
        return None  #There is no motion or no motion device

    def person_check(self):
        self.log("__function__: Checking for image processing", level="DEBUG")
        if self.is_person():  # are people detected
            self.log("__function__: There are people in the room",
                     level="DEBUG")
            self.__timer = None  # Remove the Timer
            new_state = 100
            self.apply_state(new_state)  # Change room to fully active 100
            return True
        return None  #There are no people detected

#########
# LOGIC #
#########

    def is_on(self):
        #Checks to see if any lights or fans are on
        self.log('__function__: checking if devices are on', level='DEBUG')
        if self.is_light():  # Are any lights on?
            self.log("__function__: Light is On", level="DEBUG")
            return True
        if self._fans:
            if self.is_fan():  # Are any fans on?
                self.log("__function__: Fan is On", level="DEBUG")
                return True
            self.log("__function__: nothing is On", level="DEBUG")
            return False  # Nothing is on

    def turn_on_room(self):
        # Turns on the Room
        if self._control:  # Does the room have a master control switch?
            switch = self.get_state(self._control,
                                    namespace='default')  # State of switch
            if switch == "on":
                if self._lights_on:  # Are there lights that turn on?
                    self.light_turn_on()
                if self._fans:  # Are there fans in the room?
                    self.fan_turn_on()
                return
            self.log(
                f"__function__: switch is {switch} doing nothing for turn_on_room",
                level="DEBUG",
            )
            return  # Control Switch is off Room Cant be controlled
        if self._lights_on:  # Are there lights that turn on?
            self.light_turn_on()
        if self._fans:  # Are there fans in the room?
            self.fan_turn_on()

    def turn_off_room(self):
        # Turns off the room
        if self._control:  # Does the room have a master control switch?
            switch = self.get_state(self._control, namespace='default')
            if switch == "on":
                if self._lights_on or self._lights_off:  # Are there lights that turn off or on ?
                    self.light_turn_off()
                if self._fans:
                    self.fan_turn_off()
            else:  # Control Switch is off
                self.log(
                    f"__function__: switch is {switch} doing nothing for turn_off_room",
                    level="DEBUG",
                )
        else:
            if self._lights_on or self._lights_off:  # Are there lights that turn off or on ?
                self.light_turn_off()
            if self._fans:  # Are the fans?
                self.fan_turn_off()

    def reset_room_timer(self):
        #changes the room countdown speed
        timer_set = int(self.get_state(self._room_timer, namespace='default'))
        timer_options = self.get_state(self._room_timer,
                                       attribute='options',
                                       namespace='default')
        mode = self.get_state(self._home_mode, namespace='default')
        if self.args["timer_default"][mode]:  # Is there a time?
            default_time = self.args["timer_default"][
                mode]  # What should the timer be?
            default_time_str = str(
                self.args["timer_default"][mode])  # What should the timer be?
            if timer_set != default_time:  # Did the time change ?
                if default_time_str in timer_options:
                    self.select_option(self._room_timer, default_time)
                else:
                    self.error(
                        f"__function__: {timer_set} is not in {timer_options}",
                        level='ERROR')
            else:
                self.log(f"__function__: Timer is {timer_set} doing nothing",
                         level='DEBUG')
        else:
            self.error("__function__: Check Timer Default failed",
                       level='ERROR')

######################
#     FUNCTIONS      #
# RETURN INFORMATION #
######################

    def is_motion(self):
        # Checks to see if the motion device is active
        self.log('__function__: Checking for motion device', level='DEBUG')
        if self._motion:  #Is there a motion device
            self.log('__function__: motion device detected', level='DEBUG')
            for device in self.split_device_list(self._motion):
                motion = self.get_state(device,
                                        default="off",
                                        namespace='default')
                self.log('__function__: checking motion device', level='DEBUG')
                if motion in ("detected", "on"):
                    self.log(
                        f'__function__: motion device is {motion} returning true',
                        motion,
                        level='DEBUG')
                    return True
                self.log(f'__function__: motion device is {motion}',
                         level='DEBUG')
        self.log('__function__: no motion detected', level='DEBUG')
        return None

    def is_person(self):
        # Checks to see if image processing is detecting a person
        self.log('__function__: Checking for image processing', level='DEBUG')
        if self._img:  #Is there img processing
            scanned_obj = self.get_state(entity_id=self._img,
                                         attribute="matches",
                                         default=None,
                                         copy=False,
                                         namespace='default')
            self.log('__function__: checking img processing', level='DEBUG')
            if scanned_obj:  # Are there objects?
                self.log('__function__: There are objects in the room',
                         level='DEBUG')
                if 'person' in scanned_obj:  # Is a Person one of the objects
                    self.log('__function__: There are people in the room',
                             level='INFO')
                    return True
            self.log('__function__: image processing is getting zero people',
                     level='DEBUG')
            return None
        self.log('__function__: no image processing detected', level='DEBUG')
        return None

    def is_light(self):
        # Checks to see if any lights are on
        self.log('__function__: checking for lights', level='DEBUG')
        if self._lights_on:  # Are there lights that turn on?
            self.log('__function__: Room has lights that turn on',
                     level='DEBUG')
            for light in self.split_device_list(self._lights_on):
                self.log('__function__: checking if lights are on',
                         level='DEBUG')
                light_state = self.get_state(
                    light, default="off",
                    namespace='default')  # Is the light on or off?
                light_name = self.friendly_name(light)
                if light_state == "on":  # Is that light on?
                    self.log(
                        f'__function__: {light_name} is {light_state} returning TRUE for lights on',
                        level='DEBUG')
                    return True
                self.log(
                    f'__function__: {light_name} is {light_state} doing nothing',
                    level='DEBUG')
        if self._lights_off:  # Are there lights that turn off in the room?
            self.log('__function__: he room has lights that turn off',
                     level='DEBUG')
            for light in self.split_device_list(self._lights_off):
                light_state = self.get_state(
                    light, default="off",
                    namespace='default')  # Is the light on or off?
                light_name = self.friendly_name(light)
                if light_state == "on":  # Is that light on?
                    self.log(
                        f'__function__: {light_name} is {light_state} returning TRUE for lights off',
                        level='DEBUG')
                    return True
                self.log(
                    f'__function__: {light_name} is {light_state} doing nothing',
                    level='DEBUG')
        self.log('__function__: no lights detected on', level='DEBUG')
        return None

    def is_fan(self):
        #Checks to see if the fan in the room is on
        self.log('__function__: checking for fan', level='DEBUG')
        if self._fans:  # Are there fans in the room?
            self.log('__function__: The Room has fans', level='DEBUG')
            for fan in self.split_device_list(self._fans):
                fan_state = self.get_state(fan,
                                           default="off",
                                           namespace='default')
                fan_name = self.friendly_name(fan)
                if fan_state == 'on':  # Is the fan on?
                    self.log(
                        f'__function__: {fan_name} is {fan_state} returning TRUE',
                        level='DEBUG')
                    return True
                self.log(
                    f'__function__: {fan_name} is {fan_state} doing nothing',
                    level='DEBUG')
        self.log('__function__: no fan detected on', level='DEBUG')
        return False

    def get_brightness(self):
        '''
        Gets the brightness a dimmable light should
        be based on the time of day
        '''
        self.log("__function__: Getting brightness", level="DEBUG")
        mode = self.get_state(self._home_mode,
                              namespace='default')  # Get Home mode
        if mode == "sleep":
            return int(25)
        if mode == "evening":
            return int(100)
        if mode == "night":
            return int(50)
        self.log(f"__function__: brightness failed mode is {mode}",
                 level="WARNING")
        return int(50)

    # def get_speed(self):
    #     # Get the fan speed based on the temperature of the room
    #     self.log("__function__: Getting speed of fans", level="DEBUG")
    #     if self._room_temp:
    #         try:
    #             temp = float(
    #                 self.get_state(self._room_temp, namespace='default'))
    #         except TypeError:
    #             self.log("__function__: temperature Failed", level="ERROR")
    #             temp = float(75.0)
    #         if temp > 85:
    #             return "high"
    #         if temp > 80:
    #             return "medium"
    #         return "low"
    #     self.log("__function__: No Temprature Sensor", level="WARNING")
    #     return "low"

    def get_speed(self):
        # Get the fan speed based on the temperature of the room
        self.log("__function__: Getting speed of fan", level="DEBUG")
        low = 72.0
        high = 82.0
        delta = high - low
        self.log(f"__function__: delta is {delta} between {low} and {high}",
                 level="DEBUG")
        if self._room_temp:
            try:
                temp = float(
                    self.get_state(self._room_temp, namespace='default'))
                self.log(f"__function__: Room temperature is {temp}",
                         level="DEBUG")
            except (TypeError, ValueError):
                self.log("__function__: temperature Failed", level="ERROR")
                return 0, 'low'
            if temp < low:
                self.log(
                    f"__function__: Room temperature {temp} is below {low}",
                    level="DEBUG")
                return 0, 'low'
            if temp > high:
                self.log(
                    f"__function__: Room temperature {temp} is above {high}",
                    level="DEBUG")
                return 100, 'high'
            adjustment = temp - low
            self.log(f"__function__: adjust temperature is {adjustment}",
                     level="DEBUG")
            final = (adjustment / delta) * 100
            self.log(f"__function__: final percentage is {final}",
                     level="DEBUG")
            return int(final), 'medium'
        self.log("__function__: No Temprature Sensor", level="WARNING")
        return 0, 'low'

###################
#    FUNCTIONS    #
# CHANGE SETTINGS #
###################

    def apply_state(self, state='100'):
        '''
        changes the state of the castle entity
        from 0 = inactive to
        100 = fresh active
        '''
        new_state = int(state)
        old_state = int(
            self.get_state(
                self._room_entity, default="0",
                namespace='default'))  # The state the castle was at before
        room_data = self.get_state(
            self._room_entity, attribute="all",
            namespace='default')  # gather the castles attributes
        room_attr = room_data["attributes"]  # reapply those attributes
        self.log(
            f"__function__: APPLYING {new_state} changed from {old_state}",
            level="DEBUG")
        if new_state >= 100:
            self.log("__function__: room is >= 100", level="DEBUG")
            room_attr["icon"] = "mdi:square"
            room_attr["occupancy"] = self.keep_check()
        elif new_state > 0:
            self.log("__function__: room is > 0", level="DEBUG")
            room_attr["icon"] = "mdi:square-medium"
            room_attr["occupancy"] = self.keep_check()
        elif new_state <= 0:
            self.log("__function__: room is <= 0", level="DEBUG")
            room_attr["icon"] = "mdi:square-outline"
            room_attr["occupancy"] = self.keep_check()
        else:
            self.log("__function__: room nothing", level="WARNING")
            self.occupancy = []
            room_attr["icon"] = "mdi:square"
            room_attr["occupancy"] = "empty"
        self.set_state(self._activity_sensor,
                       state=new_state,
                       namespace='rooms')
        if old_state != new_state:
            self.set_state(self._room_entity,
                           state=new_state,
                           attributes=room_attr,
                           namespace='default')

#############
# FUNCTIONS #
#  TURN ON  #
#############

    def light_turn_on(self):
        # Turns on the lights
        mode = self.get_state(self._home_mode, namespace='default')
        if mode in self._on_mode:
            for light in self.split_device_list(self._lights_on):
                name = self.friendly_name(light)
                if self._dimmer:  # If the light has a dim level adjust it
                    level = int(self.get_brightness())
                    self.call_service("light/turn_on",
                                      entity_id=light,
                                      brightness=level)
                    self.log(
                        f"__function__: setting brightness to {level} for {name}"
                    )
                else:
                    self.log(f"__function__: turning {name} on", level="DEBUG")
                    self.World.entity_turn_on(light)
        else:
            self.log(f"__function__: Current mode does not equal {mode}",
                     level="DEBUG")

    def fan_turn_on(self):
        # Turns on the fans
        self.log("__function__: Turning on fans", level='DEBUG')
        for fan in self.split_device_list(self._fans):
            try:
                state = self.get_state(fan)
                if state == 'off':
                    name = self.friendly_name(fan)
                    self.log(f"__function__: Turning on {name}", level='DEBUG')
                    power, fan_speed = self.get_speed()
                    # self.call_service("fan/turn_on", entity_id=fan, speed=power)
                    try:
                        self.call_service("fan/set_percentage",
                                          entity_id=fan,
                                          percentage=power)
                    except Exception as Error:
                        self.error(f'unable to set {fan} power',
                                   level='WARNING')
                        self.error(Error, level='WARNING')
                    # try:
                    #     self.call_service("fan/set_preset_mode",
                    #                       entity_id=fan,
                    #                       speed=fan_speed)
                    # except Exception as Error:
                    #     self.error(Error, level='WARNING')
                    #     self.error(f'unable to set {fan} speed',
                    #                level='WARNING')
            except Exception as Error:
                self.error(Error, level='ERROR')
#############
# FUNCTIONS #
# TURN OFF  #
#############

    def light_turn_off(self):
        # Turn off the lights
        if self._lights_on:  # Does the room have lights that turn on?
            self.log('__function__: Room has on lights turning them off',
                     level="DEBUG")
            for light in self.split_device_list(self._lights_on):
                name = self.friendly_name(light)
                self.log(
                    f"__function__: turning off {name}",
                    level="DEBUG",
                )
                self.turn_off(light)
        if self._lights_off:
            self.log('__function__: Room has off lights turning them off',
                     level="DEBUG")
            for light in self.split_device_list(self._lights_off):
                self.log(
                    f"__function__: turning off {light}",
                    level="DEBUG",
                )
                self.turn_off(light)

    def fan_turn_off(self):
        # Turns off the fans
        self.log('__function__: Turning off the fans', level='DEBUG')
        for fan in self.split_device_list(self._fans):
            fan_name = self.friendly_name(fan)
            self.log(f'__function__: Turning off {fan_name}', level='DEBUG')
            self.call_service("fan/turn_off", entity_id=fan)


##########
# TIMERS #
##########

# def start_cycle(self):
#     # Start Stop Timer
#     self.log('Start Cycle: Starting countdown', level='DEBUG')
#     # try:
#     #     self.cancel_timer(
#     #         self.__timer)  #Cancels the current timer if its running
#     #     self.log('Start Cycle: Canceling timer', level='DEBUG')
#     # except AttributeError:
#     #     pass
#     self.__timer = self.run_in(self.occupancy_timer_check,
#                               self._click)  # Start the new timer

    def start_cycle(self, kwargs=None):
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
                                   self._click)  # Start the new timer

    def execute_timer(self, kwargs):
        ''' turns the timer handle off and fires the timer '''
        self.log('__function__: executing timer', level='DEBUG')
        self.__timer = None
        self.occupancy_timer_check()

    def occupancy_timer_check(self):
        '''
        Checks the room entity status
        and either starts the cycle over
        or turns off the room
        '''
        room_state = float(
            self.get_state(
                self._room_entity,
                namespace='default'))  # Get the Castle state 0 - 100
        self.log('__function__: Starting', room_state, level="DEBUG")
        if self.person_check():  # Are people detected by image processing?
            return  # If people are detected by image processing stop the check
        if self.motion_check():  # Is motion on?
            return  # If motion is on stop the check
        if room_state > 0:  # If room is not at 0
            self.log("__function__: state is > 0", level="DEBUG")
            new_state = self.occupancy_tick(
                room_state
            )  # Takes the old state and figures out the new state
            self.apply_state(new_state)  # Changes the state
            self.start_cycle()  # Start timer to countdown the room
        elif room_state == 0:
            self.log(
                f"__function__: state is {room_state} no need to countdown",
                level="DEBUG")
            self.turn_off_room()  # Turns of devices in the room
            self.reset_room_timer(
            )  # Resets the room countdown timer to default
        else:  # If Room less than zero
            self.log(
                f"__function__: Something went wrong state is {room_state}",
                level="WARNING")
            self.turn_off_room()  # Turns of devices in the room
            self.apply_state(0)  # Changes the state

    def occupancy_tick(self, room_state='0'):
        # Calculates the change in room_state
        self.log("__function__: Starting", level="DEBUG")
        state = float(room_state)
        keep_state = self.get_state(self._keep, namespace='default')
        click = self._click
        if keep_state not in self._unknown:
            self.log("__function__: {keep_state} is known turning up timer}",
                     level="DEBUG")
            timer = 1800.0
        else:
            self.log("__function__: {keep_state} is unknown keeping timer}",
                     level="DEBUG")
            timer = float(self.get_state(self._room_timer,
                                         namespace='default'))
        sub = float((100 / timer) * click)
        self.log(sub, level="DEBUG")
        math = state - sub
        self.log(math, level="DEBUG")
        new_state = round(math, 2)
        self.log(f"__function__: {new_state=}", level="DEBUG")
        self.log(
            f"__function__: state = {state} timer = {timer} sub = {sub} math = {math} new_state = {new_state}",
            level="DEBUG",
        )
        if new_state < 1:
            return 0
        return new_state  # Returns the new castle state 0-100

    def keep_check(self):
        self.log("__function__: checking keep", level="DEBUG")
        keep = self._keep
        keep_state = self.get_state(keep, namespace='default')
        if keep_state:
            self.log(f"__function__: keep is {keep_state}", level="DEBUG")
            return keep_state
        self.log("__function__: keep is nothing", level="DEBUG")
        return 'unknown'


