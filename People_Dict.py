from typing import Dict, Set, List, Optional, Tuple, Union, Any
import requests
import datetime as dt
from dateutil.parser import parse
from dateutil.tz import tzlocal
from requests.auth import AuthBase
from dataclasses import dataclass
import os


class TokenAuth(AuthBase):
    """Implements a custom authentication scheme."""

    def __init__(self, token) -> None:
        self.token = token

    def __call__(self, r):
        """Attach an API token to a custom auth header."""
        r.headers['X-TokenAuth'] = f'{self.token}'  # Python 3.6+
        return r
# Example
# requests.get('https://httpbin.org/get', auth=TokenAuth('12345abcde-token'))


@dataclass
class Django:
    BASE_URL: str = os.environ.get('DJANGO_URL', "http://django:8000/api/")
    AUTH_TOKEN: str = os.environ.get('DJANGO_TOKEN')
    TIMEOUT: Tuple[int, int] = (1, 2)
    Auth: TokenAuth = TokenAuth(AUTH_TOKEN)


class RestAPI:
    """Gets data from a rest api"""
    @classmethod
    def get_people(cls) -> List[Dict[str, Any]]:
        """Gets all people in a List

        Returns:
            List[Dict[str, Any]]: List of people dicts
        """
        return cls.get_data((Django.BASE_URL+"people/"))

    @classmethod
    def get_person_dict(cls, person: str) -> Dict[str, Any]:
        """Gets a persons individul Dict

        Args:
            person (str): person name per Django

        Returns:
            Dict[str, Any]: person dict
        """
        new_url = Django.BASE_URL + "people/" + person
        return cls.get_data(new_url)

    @classmethod
    def get_data(cls, url: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        with requests.Session() as session:
            session.auth = Django.Auth
            response = session.get(url, timeout=Django.TIMEOUT)
            return response.json()


@dataclass
class Phone:
    """Class to hold person phone information"""
    device: Optional[str] = None
    phone_type: Optional[str] = None
    mobile_app: Optional[str] = None
    phone_service: Optional[str] = None


class PersonThermo:
    """Class to hold person temperature information"""

    def __init__(self, data) -> None:
        self._max_temp_device: str = data.get('max_temp_device')
        self._target_temp_device: str = data.get('max_temp_device')
        self._min_temp_device: str = data.get('max_temp_device')
        self._max_temp: int = data.get('max_temp_device')
        self._target_temp: int = data.get('max_temp_device')
        self._min_temp: int = data.get('max_temp_device')

    @property
    def max_temp_device(self) -> str:
        """Device that sets the maximum temperature"""
        return self._max_temp_device

    @property
    def target_temp_device(self) -> str:
        """Device that sets the target temperature"""
        return self._target_temp_device

    @property
    def min_temp_device(self) -> str:
        """Device that sets the minimum temperature"""
        return self._min_temp_device

    @property
    def max_temp(self) -> int:
        """maximum temperature"""
        return self._max_temp

    @property
    def target_temp(self) -> int:
        """target temperature"""
        return self._target_temp

    @property
    def min_temp(self) -> int:
        """minimum temperature"""
        return self._min_temp


class BasePerson:
    def __init__(self, data):
        self._id: str = data.pop('id')
        self._friendly_name: str = data.pop('name')
        self._startdate: dt.date = data.pop('startdate')
        self._enddate: Optional[dt.date] = data.pop('enddate')
        self._entity_id: Optional[str] = data.pop('entity')
        self._phone: Optional[str] = data.pop('phone')
        self._phone_type: Optional[str] = data.pop('phone_type')
        self._mobile_app: Optional[str] = data.pop('mobil_app')
        self._phone_service: Optional[str] = data.pop('phone_service')
        self._icon: str = data.pop('icon', 'mdi:person')
        self._image: Optional[str] = data.pop('default_image')
        self._lock_slot: Optional[int] = data.pop('lock_slot')
        self._user_code: Optional[int] = data.pop('user_code')
        self._garage_door: str = data.pop('garage_door')
        self._nest: Dict[str, Any] = data.pop('nest')
        self._thermo_dict: Dict[str, Union[str, int]] = data.pop('thermo')
        self._unused_data: Dict[str, Any] = data

    @property
    def id(self) -> str:
        """Person ID

        Returns:
            str: In the form of Master RM1 RM2
        """
        if self._id == 'M':
            return 'Master'
        return self._id

    @property
    def friendly_name(self) -> str:
        """The persons name"""
        return self._friendly_name.title()

    @property
    def entity_id(self) -> Optional[str]:
        """Persons HA ID

        Returns:
            Optional[str]: person.example
        """
        return self._entity_id

    @property
    def start(self) -> dt.date:
        """The day the person started"""
        value = self._startdate
        if isinstance(value, dt.date):
            return self._startdate
        if isinstance(value, str):
            convert = parse(value)
            return convert
        return dt.datetime.now(tzlocal())

    @property
    def end(self) -> Optional[dt.date]:
        """The day the person moves out"""
        value = self._enddate
        if isinstance(value, dt.date):
            return self._startdate
        if isinstance(value, str):
            convert = parse(value)
            return convert
        return None

    @property
    def lock(self) -> Optional[Tuple[int, int]]:
        """Lock Code"""
        if self._lock_slot and self._user_code:
            return (self._lock_slot, self._user_code)
        return None

    @property
    def phone_type(self) -> Optional[str]:
        "The type of phone the user has"
        if self._phone_type == "I":
            return "IPhone"
        if self._phone_type == "A":
            return "Andriod"
        return None

    @property
    def Phone(self) -> Phone:
        return Phone(device=self._phone, phone_type=self.phone_type, mobile_app=self._mobile_app, phone_service=self._phone_service)

    @property
    def nest(self) -> Dict[str, Any]:
        return self._nest

    @property
    def level(self) -> int:
        if self._nest:
            return self._nest['Z']
        raise KeyError(f'Missing Nest')

    @property
    def Thermo(self) -> PersonThermo:
        """Class containing thermostats"""
        return PersonThermo(self._thermo_dict)

    @property
    def icon(self) -> str:
        """The icon of the person"""
        return self._icon

    @icon.setter
    def icon(self, value) -> None:
        if isinstance(value, str):
            self._icon = value
        else:
            raise TypeError('Icon must be a string')

    @property
    def garage_door(self) -> str:
        """The switch the garage door for someone"""
        return self._garage_door

    def get_unused_data(self) -> dict:
        '''Left over data'''
        return self._unused_data

    def __str__(self) -> str:
        return f'{self.friendly_name}'

    def __repr__(self) -> str:
        return f'{self.friendly_name}'


class Barracks:
    """Class for getting people"""
    @classmethod
    def persons(cls) -> List[Dict[str, Any]]:
        """Returns everyones dict in a list

        Returns:
            List[Dict[str, Any]]: List of each persons dict
        """
        return RestAPI.get_people()

    @classmethod
    def get_person(cls, person: str) -> BasePerson:
        """Returns a person object

        Args:
            person (str): any value in the person dict

        Returns:
            BasePerson: Person Object
        """
        return BasePerson(cls.get_person_dict(person))

    @classmethod
    def get_person_dict(cls, person: str) -> Dict[str, Any]:
        """Returns a person dict

        Args:
            person (str): any value in the person dict

        Returns:
            persons dict
        """
        for player in cls.persons():
            if person in player.values():
                return player
        raise KeyError(f'{person} does not exist in database')

    @classmethod
    def get_person_list(cls, attr: Any) -> Set[str]:
        """Generate a set based on dict values

        Args:
            attr (Any): the Key of the dictionaries

        Returns:
            Set[str]: the values of the dictionaries
        """
        return {x[attr] for x in cls.persons()}

    @classmethod
    def get_dict(cls, key: str, attr: Any, where: Optional[Tuple[Any, Any]] = None) -> Dict[str, Any]:
        """Returns a specific dict

        Args:
            key (str): The KEY in the new dict {'key','value'}
            attr (Any): The Value in the new dict {'key','value'}
            where (Optional[Tuple[Any, Any]], optional): filter use key value pair. Defaults to None.

        Returns:
            Dict[str, Any]: new dictonary
        """
        person_dict = cls.persons()
        if where:
            new_dict = {x[key]: x[attr]
                        for x in person_dict if where in x.items() or any(where in d.items() for d in x.values() if isinstance(d, dict))}
        else:
            new_dict = {x[key]: x[attr]
                        for x in person_dict}
        return new_dict
