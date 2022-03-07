import datetime as dt
from typing import Dict, List, Sequence, Optional, Union, Any
import appdaemon.plugins.hass.hassapi as hass
from WorldConst import House, GlobalWeatherData

class Temperature:
    def __init__(self, Outside: float = DEFAULT_OUTSIDE, Inside: float = DEFAULT_INSIDE, Max: float = DEFAULT_MAX, Min: float = DEFAULT_MIN, Target: float = DEFAULT_TARGET):
        self._Outside: float = Outside
        self._Inside: float = Inside
        self._Max: float = Max
        self._Min: float = Min
        self._Target: float = Target

    @property
    def Outside(self) -> float:
        """The temperature it is outside the house"""
        return self._Outside

    @Outside.setter
    def Outside(self, value) -> None:
        self._Outside = value

    @property
    def Inside(self) -> float:
        """The temperature inside the house"""
        return self._Inside

    @Inside.setter
    def Inside(self, value) -> None:
        self._Inside = value

    @property
    def Max(self) -> float:
        """Maximun temperature tolerated"""
        return self._Max

    @Max.setter
    def Max(self, value) -> None:
        if isinstance(value, list) and value:
            self._Max: float = min(value)  # use the min hottest temp
        elif isinstance(value, float) and value:
            self._Max: float = min(value)  # use the min hottest temp
        else:
            self._Max: float = DEFAULT_MAX

    @property
    def Min(self) -> float:
        """Minimum temperature tolerated"""
        return self._Min

    @Min.setter
    def Min(self, value) -> None:
        if isinstance(value, list) and value:
            self._Min: float = max(value)  # use max coldest value
        elif isinstance(value, float) and value:
            self._Min: float = max(value)  # use max coldest value
        else:
            self._Min: float = DEFAULT_MIN

    @property
    def Target(self) -> float:
        """Perfect temperature"""
        return self._Target

    @Target.setter
    def Target(self, value) -> None:
        if isinstance(value, list) and value:
            self._Target: float = sum(
                value)/len(value)
        elif isinstance(value, float) and value:
            self._Target: float = value
        else:
            self._Target: float = DEFAULT_TARGET

    def fan_target(self) -> bool:
        """If turning on the fan will get closer to Target Temp Return True"""
        if self.compare(self._Target, self._Inside)[0] == self.compare(self._Outside, self._Inside)[0]:
            return True
        return False

    def compare(self, T1: float, T2: float) -> Tuple[str, float]:
        """Campare two temperatures if first is less than the second returns cool"""
        diff: float = T1 - T2
        if diff > 0.0:
            phase: str = 'hot'
        else:
            phase: str = 'cool'
        return (phase, diff)

    def compare_range_inside(self) -> bool:
        """Return true if inside temp is in range"""
        if self._Min <= self._Inside <= self._Max:
            return True
        return False

    def compare_range_outside(self) -> bool:
        """Return true if outside temp is in range"""
        if self._Min < self._Outside < self._Max:
            return True
        return False

    def internal_mode(self) -> Union[str, None]:
        """Returns the mode the AC should be set too"""
        if self.compare_range_outside() and self.compare_range_inside():  # Return None if it's comfortable inside and outside
            return None
        # Is it cold outside?
        if self.compare(self._Outside, self._Min)[1] < 0:
            return 'heat'
        if self.compare(self._Outside, self._Max)[1] > 0:  # Is it hot outside?
            return 'cool'
        if self.compare(self._Inside, self._Min)[1] < 0:  # Is it cold inside?
            return 'heat'
        if self.compare(self._Inside, self._Max)[1] > 0:  # Is it hot inside?
            return 'cool'
        return None

    def ambient_mode(self) -> str:
        """Trys to guess at the mode the ac should be no matter what. Returns either cool or heat not None"""
        comparison: str = self.compare(self._Target, self._Outside)[0]
        if comparison == 'hot':
            return 'heat'
        return 'cool'


class Thermo(hass.Hass):
    def initialize(self):
        self.log(f'__function__: Starting {__name__}', level='INFO')
        # ! =================== Getters and Setters ===================
        self.World: object = self.get_app("World")  # Main App
        # Returns dict by RM1,RM2
        self._person_dict: Dict[str, Dict[str, str]
                                ] = self.World.get_person_dict()
        # self.log(self._person_dict, level="DEBUG")
        self.person_list: Sequence[str] = self.World.get_person_list()
        self._inactive_max_mod: float = float(
            self.args['Temps']['inactive_max'])
        self._inactive_min_mod: float = float(
            self.args['Temps']['inactive_min'])
        self.Temperature:Temperature = Temperature()
        # ! =================== Varibles ===================
        self._level: int = int(self.args['level'])
        self._switch: str = self.args['switch']
        self._switch_duration: int = self.args['switch_duration'] * 60 * 60
        self._active: str = self.args['active']
        self._occupied: bool = False  # Controls if someone on that floor is home
        self._windows: str = GlobalWeatherData.windows
        self._something_open: bool = False  # If anything is open
        self._ac_entity: str = self.args['ac_entity']
        # ! ======== TEMPS =========
        self.update_all_temperatures()  # Update all the temperatures before comparisions
        # ! ======== AC =========
        # Creats a temperoy Dict
        self._temp_dic: Dict[int, int] = self.get_temp_dict()
        # ! =================== Start ===================
        runtime = dt.time(0, 0, 0)
        self.run_hourly(self.check_ac_all, runtime)
        self.update_all()
        # ! =================== Listen ===================
        for person in self.person_list:
            self.listen_state(self.change_detected, entity_id=person)
        self.listen_state(self.change_detected,
                          entity_id=self._ac_entity, duration=360)
        self.listen_state(self.change_detected,
                          entity_id=self._ac_entity, attribute='temperature', duration=360)
        self.listen_state(self.change_detected,
                          entity_id=self._windows, duration=10)
        self.listen_state(self.change_detected, entity_id=self._active)
        for device in GlobalWeatherData.temp_device_list:
            self.listen_state(self.change_detected, device, duration=5)
        for door in GlobalWeatherData.doors:
            self.listen_state(
                self.change_detected_device_open, door, new='on', duration=360)

        self.listen_state(self.switch_back_on, self._switch,
                          new='off', duration=self._switch_duration)
        # ? =================== Test ===================
        self.check_ac_all()


# ===========================================================================
# ?                           Change Detected
# ===========================================================================


    def change_detected(self, entity: str, attribute: Optional[Any] = None, old: Optional[str] = None, new: Optional[str] = None, kwargs: Optional[Any] = None) -> None:
        """Double checks things whenever there is a change"""
        name: str = self.friendly_name(entity)  # gets the name of the entity
        self.log(
            f"__function__: {entity} changed from {old} to {new}", level='DEBUG')
        if old != new:
            self.log(f"__function__: {name} changed from {old} to {new}")
            self.update_all()

    def change_detected_device_open(self, entity: str, attribute: Optional[dict] = None, old: Optional[str] = None, new: Optional[str] = None, kwargs: Optional[dict] = None) -> None:
        """Double checks things whenever there is a change"""
        name: str = self.friendly_name(entity)  # gets the name of the entity
        self.log(
            f"__function__: {entity} changed from {old} to {new}", level='DEBUG')
        if old != new:
            self.log(f"__function__: {name} changed from {old} to {new}")
            self.update_something_open()

    def switch_back_on(self, entity: str, attribute: Optional[dict] = None, old: Optional[str] = None, new: Optional[str] = None, kwargs: Optional[dict] = None) -> None:
        """Turns the control switch back on after it has been off"""
        self.log(
            f"__function__: {entity} changed from {old} to {new}", level='DEBUG')
        if old != new:
            self.log(f"__function__: {entity} changed from {old} to {new}")
            self.turn_on(self._switch)


# ===========================================================================
# ?                           Update
# ===========================================================================


    def update_all(self, skip_ac: Optional[bool] = False) -> None:
        """Updates Everything"""
        self.log('__function__: Updating everything', level="INFO")
        self.update_something_open()
        self.update_all_temperatures()
        if skip_ac is False:
            self.check_ac_all()

    def update_all_temperatures(self) -> None:
        """Updates all the temperatures"""
        self.log('__function__: Updating temperatures', level="DEBUG")
        self.update_current_min_temp()
        self.update_current_max_temp()
        self.update_current_target_temp()
        self.update_current_outside_temp()
        self.update_current_inside_temp()

    def update_current_min_temp(self) -> None:
        """Updates the current AC's minimum temperature by checking who is home and combining list of persons
        perfered values. If no one is home will us default"""
        self.log('__function__: Updating current minimum temperature',
                 level="DEBUG")
        temperature_list: List[float] = self.get_temp_list(
            temp_range='min_temp')
        self.Temperature.Min = temperature_list
        self.log(
            f'__function__: Current minimum temperature is {self.Temperature.Min}', level="INFO")

    def update_current_max_temp(self) -> None:
        """Updates the current AC's maxium temperature by checking who is home and combining list of persons
        perfered values. If no one is home will use default"""
        self.log('__function__: Updating current maximum temperature',
                 level="DEBUG")
        temperature_list: List[float] = self.get_temp_list(
            temp_range='max_temp')
        self.Temperature.Max = temperature_list
        self.log(
            f'__function__: Current maximum temperature is {self.Temperature.Max}', level="INFO")

    def update_current_target_temp(self) -> None:
        """Updates the current AC's minimum temperature by checking who is home and combining list of persons
        perfered values. If no one is home will use default"""
        self.log('__function__: Updating target temperature',
                 level="DEBUG")
        temperature_list: List[float] = self.get_temp_list(
            temp_range='target_temp')
        self.Temperature.Target = temperature_list
        self.log(
            f'__function__: Current Target temperature is {self.Temperature.Target}', level="INFO")

    def update_current_outside_temp(self) -> None:
        """Updates the current outside temperature"""
        self.log('__function__: Updating outside temperature',
                 level="DEBUG")
        outside_temperature: float = self.get_outside_temp()
        self.Temperature.Outside = outside_temperature
        self.log(
            f'__function__: Current outside temperature is {self.Temperature.Outside}', level="INFO")

    def update_current_inside_temp(self) -> None:
        """Updates the current Inside temperature"""
        self.log('__function__: Updating inside temperature',
                 level="DEBUG")
        inside_temperature: float = self.get_inside_temp()
        self.Temperature.Inside = inside_temperature
        self.log(
            f'__function__: Current inside temperature is {self.Temperature.Inside}', level="INFO")

    def update_ambient_mode(self) -> None:
        """Updates the ambient mode. Ambient mode is cool or heat"""
        self.log('__function__: Updating ambient mode',
                 level="DEBUG")
        self._temp_dic: Dict[int, int] = self.get_temp_dict()

    def update_something_open(self) -> None:
        """Update the varible switch if something is open"""
        self.log('__function__: Updating something open',
                 level="DEBUG")
        windows: bool = self.window_check()
        doors: bool = self.doors_check()
        if windows or doors:
            self._something_open:bool = True
        else:
            self._something_open:bool = False

# ===========================================================================
# ?                           Check
# ===========================================================================

    def check_ac_all(self, kwargs: Optional[dict] = None) -> None:
        """Checks what the AC is set at and compares it to what it should be set at"""
        self.log('__function__: Checking AC', level="DEBUG")
        self.update_all(skip_ac=True)
        current_ac_mode: str = self.get_ac_state()
        current_ac_temp: float = self.get_ac_set_point()
        current_ac_fan_mode: str = self.get_ac_fan_mode()
        target_ac_mode: str = self.get_ac_mode()
        target_ac_temp: float = self.get_AC_target_temp()
        target_ac_fan_mode: str = self.get_fan_mode()
        if current_ac_mode == target_ac_mode:
            self.log(
                f'__function__: ALL GOOD AC is {current_ac_mode}', level="DEBUG")
        else:
            self.log(
                f'__function__: AC mode should be {target_ac_mode} instead of {current_ac_mode}', level="INFO")
            self.set_hvac_mode(target_ac_mode)
            self.set_temperature(target_ac_temp)
        if current_ac_temp != 'off':
            if current_ac_temp == self.get_AC_target_temp():
                self.log(
                    f'__function__: ALL GOOD AC temp is {current_ac_temp}', level="DEBUG")
            else:
                self.log(
                    f'__function__: AC temperature should be {target_ac_temp} instead of {current_ac_temp}', level="INFO")
                self.set_temperature(target_ac_temp)
        else:
            self.log(
                f'__function__: AC is off but would be {target_ac_temp} ambient is {self.Temperature.ambient_mode()}', level="DEBUG")
        if current_ac_fan_mode == target_ac_fan_mode:
            self.log(
                f'__function__: ALL GOOD AC fan is {current_ac_fan_mode}', level="DEBUG")
        else:
            self.log(
                f'__function__: AC fan mode should be {target_ac_fan_mode} instead of {current_ac_fan_mode}', level="INFO")
            self.set_fan_mode(target_ac_fan_mode)

    def window_check(self) -> Optional[bool]:
        """checks to see if a window is open

        Returns
        -------
        True: window is open
        False: windows are closed
        """
        self.log('__function__: Checking Windows', level="DEBUG")
        window_status: str = self.get_state(self._windows)
        self.log(f"__function__:  {self._windows}", level="DEBUG")
        self.log(f"__function__:  Starting {window_status}", level="DEBUG")
        if window_status == "on":
            self.log(
                f"__function__:  Windows are Open {window_status=}", level="DEBUG")
            return True  # windows are open
        if window_status == "off":
            self.log(
                f"__function__:  Windows are Closed {window_status=}", level="DEBUG"
            )
            return False  # windows are closed
        self.error(
            f"Window Check:  Window Status is {window_status} logic failed",
            level="ERROR",
        )
        return None

    def doors_check(self) -> bool:
        """Checks to see if a door has been open for over 5 minutes
        
        
        Returns
        -------
        True: Door is open longer than 5 minutes
        False: all doors are closed
        """
        self.log('__function__: Checking doors', level="DEBUG")
        for door in GlobalWeatherData.doors:
            try:
                state: str = self.get_state(door)
                if state == 'on':
                    duration: int = self.World.get_last_delta(door)
                    if duration > 360:
                        self.log(
                            f'__function__: {door} has been open for {duration} seconds', level="WARNING")
                        return True
            except Exception as Error:
                self.error(
                    f'Door Check: {Error}', level='ERROR')
        return False

    def active_check(self) -> bool:
        """check if an area is active to turn the AC up or Down
        
        Returns
        -------
        True: Area is active
        False: Area is inactive
        """
        self.log("__function__ : checking for activity")
        if self._occupied:  # If the floor is occupied it's active
            return True
        try:
            activity: str = self.get_state(self._active)
            self.log(f"__function__: {activity=}", level="DEBUG")
        except Exception as Error:
            activity: str = "off"
            self.error(f"Active Check: {Error} ", level="ERROR")
        if activity == "on":
            self.log("__function__: Activity is True", level="DEBUG")
            return True
        self.log("__function__: Activity is False", level="DEBUG")
        return False

    def check_home(self, person: str) -> bool:
        """checks if a persom is home
        
        Returns
        -------
        True: Someone is home
        False: No one is home
        """
        self.log(f'__function__: checking if  {person} is home', level="DEBUG")
        try:
            status: str = self.get_state(person)
            if status == 'home':
                return True
        except Exception as Error:
            self.error(f'Check Home: {Error=}', level='ERROR')
        return False

    def check_switch(self) -> bool:
        """Checks if the AC control switch is on returns true
        also changes the switch if needed"""
        self.log(
            "__function__: checking the switch", level="DEBUG")
        state: str = self.get_state(self._switch)
        if House.empty:
            self.turn_on(self._switch)
            return True
        if self._something_open:
            if state == 'off':
                self.turn_on(self._switch)
            return True
        if state == 'on':
            return True
        return False
        # ===========================================================================
        # ?                           Temperatures
        # ===========================================================================

    def get_temp_dict(self) -> Dict[int,int]:
        """Gets a 24 hour dictionary of temperatures per hour"""
        self.log('__function__: Getting Temperature Dict', level="DEBUG")
        mod: str = self.Temperature.ambient_mode()
        try:
            base_dic: dict = self.args['Temps']
            blank_dic: Dict[int, int] = {
                k: v for (k, v) in zip(range(24), [75]*24)}
            off_peak_dic: Dict[int, Dict[str, int]] = base_dic['off_peak']
            blank_dic: Dict[int, int] = self.dic_mod(
                blank_dic, off_peak_dic, mod)
            if self.get_week() == 'weekday':
                on_peak_dic: Dict[int, Dict[str, int]] = base_dic['on_peak']
                blank_dic: Dict[int, int] = self.dic_mod(
                    blank_dic, on_peak_dic, mod)
            return blank_dic
        except Exception as Error:
            self.error(f'Get Temp Dict: {Error=}', level='ERROR')

        return None

    def dic_mod(self, dic1: Dict[int, int], dic2: Dict[int, Dict[str, int]], mod: str = 'cool') -> Dict[int,int]:
        """Modifies a dict using another dictionary

        Parameters
        ----------
        dic1 : Dict[int,int]
            dictinary to be modified
        dic2 : Dict[int,int]
            dictinary doing the modifing
        """
        self.log('__function__: Modifying dictionary', level="DEBUG")
        try:
            current_mod: int = 0
            new_dic: Dict[int, int] = dic1
            for k in dic1.keys():
                if k in dic2:
                    current_mod = new_dic[k] = dic2[k][mod]
                else:
                    new_dic[k] = current_mod
            self.log(f'__function__: Final Dic is {new_dic}', level="DEBUG")
            return new_dic
        except Exception as Error:
            self.error(f'Dict Mod: {Error=}', level='ERROR')
            return None


# ===========================================================================
# todo                         Return Information
# ===========================================================================

    def get_temp_list(self, temp_range: str) -> List[Optional[float]]:
        """Checks to see if someone is home and that this is their floor and returns
        a list of temperatures for everyone home."""
        self.log('__function__: Getting Temperature List', level="DEBUG")
        temperature_list: List[float] = []
        for values in self._person_dict.values():
            try:
                # if values['level'] == self._level and self.check_home(values['person']):
                if values['name'] in House.at_home(level=self._level):
                    state = float(self.get_state(values[temp_range]))
                    temperature_list.append(state)
            except Exception as Error:
                self.error(f'Update_Current_Min_Temp: {Error}', level='ERROR')
        if temperature_list:
            self._occupied: bool = True
            self.log(
                f'__function__: Returning {temperature_list}', level="DEBUG")
        else:
            self._occupied: bool = False
            for values in self._person_dict.values():
                try:
                    if self.check_home(values['person']):
                        state: float = float(
                            self.get_state(values[temp_range]))
                        temperature_list.append(state)
                except Exception as Error:
                    self.error(
                        f'Update_Current_Min_Temp: {Error}', level='ERROR')
        return temperature_list

    def get_week(self) -> str:
        """ Returns if it is a weekday or weekend 
        
        Returns
        -------
        weekday: Mondday - Friday
        weekend: Saturday Sunday
        """
        self.log('__function__: Getting week', level="DEBUG")
        try:
            weekno: int = dt.datetime.today().weekday()
            self.log(f"__function__ : {weekno=}", level="DEBUG")
            if weekno > 4:  # Saturday 5 Sunday 6
                self.log(
                    f"T__function__: Today is day {weekno} a weekend", level="DEBUG")
                return "weekend"
            self.log(
                f"__function__ : {weekno=} assuming weekday", level="DEBUG")
            return "weekday"
        except Exception as Error:
            self.error(f'Get Week: {Error=}', level='ERROR')
            return "weekday"

    def get_hour(self) -> int:
        """Returns the hour in a 24 number"""
        self.log('__function__: Getting hour', level="DEBUG")
        try:
            hour_number: int = int(dt.datetime.now().hour)
            self.log(f'__function__: Hour is {hour_number}', level="DEBUG")
            return hour_number
        except Exception as Error:
            self.error(f'Get Hour: {Error=}', level='ERROR')
        return 0

    def get_outside_temp(self) -> float:
        """
        gets the temperature it is outside trying several devices

        Returns
        -------
        The temperature outside
        """
        self.log('__function__: Getting outside temp', level="DEBUG")
        for device in GlobalWeatherData.outside_temperature_devices:
            try:
                weather: float = float(self.get_state(entity_id=device))
                self.log(f"__function__: {weather=}", level="INFO")
                return weather
            except Exception as Error:
                self.error(
                    f'Get Outside Temperature: Failed for {device} {Error}', level='WARNING')
        return None

    def get_inside_temp(self) -> float:
        """Returns The temperature inside
        
        
        Returns
        -------
        The temperature inside
        """
        self.log('__function__: Getting inside temp', level="DEBUG")
        try:
            weather: float = float(self.get_state(
                entity_id=self._ac_entity, attribute='current_temperature'))
        except Exception as Error:
            self.error(
                f'Get Inside Temperature: Failed for {self._ac_entity} {Error}', level='CRITICAL')
        for device in GlobalWeatherData.inside_temperature_devices:
            try:
                weather: float = float(self.get_state(entity_id=device))
                self.log(f"__function__: {weather=}", level="INFO")
                return weather
            except Exception as Error:
                self.error(
                    f'Get Inside Temperature: Failed for {device} {Error}', level='WARNING')
        return None

    def get_AC_target_temp(self) -> float:
        """Gets the temperature the AC should be set at"""
        self.log("__function__: Getting the AC target temperature", level="DEBUG")
        modification: float = self.get_temp_mod()
        self.log(
            f"__function__: Temperature will be modified by {modification}", level="DEBUG")
        if self.Temperature.ambient_mode() == 'cool':  # Means home is in cool mode
            target_temp: float = self.Temperature.Max + \
                modification  # It's hot outside return Max
            self.log(
                f"__function__: Ambient Mode is {self.Temperature.ambient_mode()} target temp is {target_temp}", level="DEBUG")
            return target_temp
        if self.Temperature.ambient_mode() == 'heat':  # Means home is in heat mode
            # it's cold outside return min temperature
            target_temp = self.Temperature.Min + modification
            self.log(
                f"__function__: Ambient Mode is {self.Temperature.ambient_mode()} target temp is {target_temp}", level="DEBUG")
            return target_temp
        self.error('Get AC target temp: Failed', level='WARNING')
        return None

    def get_temp_mod(self) -> float:
        """Gets the number that will modify the current temperature"""
        self.log("__function__: Getting the temperature modifier", level="DEBUG")
        total: float = 0.0
        hour: int = self.get_hour()
        active: bool = self.active_check()
        if hour:
            try:
                temp_dict_mod: Dict[int, int] = self._temp_dic[hour]
                total: float = temp_dict_mod + total
            except Exception as Error:
                self.error(
                    f'Get Temperature Mod: Failed to get Temperature Dictionary {Error}', level='ERROR')
        if active is False and self._occupied is False:
            if self.Temperature.ambient_mode() == 'cool':
                total: float = total + self._inactive_max_mod
            else:
                total: float = total + self._inactive_min_mod
        return float(total)

    def get_ac_mode(self) -> str:
        """Gets the mode the AC should be set to returns off if it should be off"""
        self.log("__function__: Getting the temperature modifier", level="DEBUG")
        if self._something_open:
            return 'off'
        internal: Optional[str] = self.Temperature.internal_mode()
        if internal:
            return internal
        return 'off'

    def get_fan_mode(self) -> str:
        """Returns the mode the fan should be in
        
        Returns
        -------
        Auto low: Fan is on when needed
        Circulation: fan comes on sometimes
        Low: fan is always on
        """
        self.log("__function__: Getting the mode the fan should be in", level="DEBUG")
        ac_mode: str = self.get_ac_state()  # Is the ac in cool heat or off?
        # home_mode: str = self.get_home_mode()
        self.log(f"__function__: Ac mode is {ac_mode}", level="DEBUG")
        if ac_mode != 'off' or House.empty:
            self.log(
                f"__function__: AC is {ac_mode} and home is empty returning Auto low", level="INFO")
            return 'Auto low'
        if self._something_open:
            if self.Temperature.fan_target():
                self.log(
                    f"__function__: Something is open {self._something_open} and fan is true returning Low", level="INFO")
                return 'Low'
            self.log(
                f"__function__: Something is open {self._something_open} and fan is false returning Auto low", level="INFO")
            return 'Auto low'
        self.log("__function__: No match returning Circulation", level="INFO")
        return 'Circulation'

    def switch_status(self) -> bool:
        """Returns None if switch is off"""
        try:
            state: str = self.get_state(self._switch)
            if state == 'off':
                return None
        except Exception as Error:
            self.error(
                f'Switch Check: {Error}', level='ERROR')
        return True
# ===========================================================================
# !                           AC Entity
# ===========================================================================


# ===========================
# !    Get AC Info
# ===========================

    def get_ac_set_point(self) -> float:
        """
        Returns
        -------
        The temperature the AC is currently set at
        """
        self.log("__function__:  Getting AC Set point", level="DEBUG")
        try:
            set_point: float = float(self.get_state(
                entity_id=self._ac_entity, attribute="temperature"))
            self.log(f"__function__: Returning {set_point}", level="DEBUG")
            return set_point
        except TypeError:
            self.log(
                "__function__: Point is not set because the AC is off", level="INFO"
            )
            return 'off'
        except Exception as Error:
            self.error(Error, level="ERROR")
        self.log(
            "__function__: Failed to get set point because machine is off", level="INFO"
        )
        return None

    def get_ac_state(self) -> str:
        """The state of the ac unit

        Returns
        -------
        off
        heat
        cool
        """
        self.log("__function__: Getting AC state", level="DEBUG")
        try:
            ac_state: str = self.get_state(self._ac_entity)
            self.log(f"Get AC state: Returning {ac_state}", level="DEBUG")
            return ac_state
        except Exception as Error:
            self.error(f"Get AC state : {Error} ", level="ERROR")
        self.log("__function__: Failed to get AC state", level="WARNING")
        return "off"

    def get_ac_fan_mode(self) -> str:
        """Checks the current mode
        the fan is in

        Returns
        -------
        Auto low: Fan turns on when AC turns on
        Circulation: Fan comes on in intervals
        Low: Fan is always on
        """
        try:
            fan_mode: str = self.get_state(
                entity_id=self._ac_entity, attribute="fan_mode", copy=False
            )
            self.log(
                f"__function__: AC fan mode is {fan_mode}", level="DEBUG")
            return fan_mode
        except Exception as Error:
            self.error(
                f"Get Fan Mode: fan Failed {Error}", level="ERROR")
        self.log("__function__: Failed to get fan mode", level="WARNING")
        return ""


# ===========================
# !    Set AC
# ===========================


    def set_hvac_mode(self, hvac_mode: str) -> None:
        """Sets the havc mode

        Parameter
        -------
        entity_id: Name(s) of entities to change
        hvac_mode: New value of operation mode	
        """
        self.log(
            f"__function__: Setting hvac mode to {hvac_mode}", level="INFO")
        if self.switch_status():
            try:
                self.call_service(
                    "climate/set_hvac_mode", entity_id=self._ac_entity, hvac_mode=hvac_mode
                )
                self.log(f"__function__ : Setting {hvac_mode=}", level="INFO")
            except Exception as Error:
                self.error(Error, level="WARNING")
        else:
            self.log("__function__: switch is off", level="WARNING")

    def ac_turn_off(self) -> None:
        """Turns the AC off

        Parameter
        -------
        entity_id: Name(s) of entities to change
        """
        self.log("__function__: Turning AC off", level="INFO")
        if self.switch_status():
            try:
                self.call_service("climate/turn_off",
                                  entity_id=self._ac_entity)
            except Exception as Error:
                self.error(Error, level="WARNING")
        else:
            self.log("__function__: switch is off", level="WARNING")

    def ac_turn_on(self) -> None:
        """Turns the AC on

        Parameter
        -------
        entity_id: Name(s) of entities to change.
        """
        self.log("__function__: Turning AC on", level="INFO")
        if self.switch_status():
            try:
                self.call_service("climate/turn_on", entity_id=self._ac_entity)
            except Exception as Error:
                self.error(Error, level="WARNING")
        else:
            self.log("__function__: switch is off", level="WARNING")

    def set_fan_mode(self, fan_mode: str) -> None:
        """Sets the AC fan mode

        Parameter
        -------
        entity_id: Name(s) of entities to change
        fan_mode: New value of fan mode
        """
        self.log(f"__function__: Setting fan mode to {fan_mode}", level="INFO")
        if self.switch_status():
            try:
                self.call_service(
                    "climate/set_fan_mode", entity_id=self._ac_entity, fan_mode=fan_mode
                )
                self.log(f"__function__:  {fan_mode=}", level="INFO")
            except Exception as Error:
                self.error(Error, level="WARNING")
        else:
            self.log("__function__: switch is off", level="WARNING")

    def set_temperature(self, temperature: int, hvac_mode: Optional[str] = None) -> None:
        """Sets the AC Temperature

        Parameter
        -------
        entity_id: Name(s) of entities to change.
        temperature: New target temperature for HVAC.
        target_temp_high: New target high temperature for HVAC.
        target_temp_low: New target low temperature for HVAC.
        hvac_mode: HVAC operation mode to set temperature to.
        """
        self.log(
            f"__function__: Setting temperature to {temperature=}",
            level="INFO",
        )
        if self.switch_status():
            new_target_temperature: int = int(temperature)
            self.call_service(
                "climate/set_temperature",
                entity_id=self._ac_entity,
                temperature=new_target_temperature,
            )
        else:
            self.log("__function__: switch is off", level="WARNING")
