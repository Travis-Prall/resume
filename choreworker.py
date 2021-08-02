from datetime import datetime as dt
from datetime import time as tt
from datetime import timedelta as td
from psycopg2 import sql
from dateutil import rrule
import appdaemon.plugins.hass.hassapi as hass
import psycopg2


class ChoreWorker(hass.Hass):
    def initialize(self):
        self.log(f'Starting {__name__}')
        # Getters and Setters #
        persons = self.get_app('persons')
        self.World = self.get_app('World')
        self._persons = persons.resident_dict
        self._user = self.args['user']
        self._password = self.args['password']
        self._host = self.args['host']
        self._port = self.args['port']
        self._database = self.args['database']
        # Start #
        self.calculate_workers()
        # self.database_generator()
        # Timers #
        runtime = tt(0, 0, 0)
        self.run_hourly(self.timer_run, runtime)

##########
# TIMERS #
##########

    def timer_run(self, kwargs):
        """ Runs a checkup on the hour """
        self.calculate_workers()

######################
# DATABASE UTILITIES #
######################

    def connect(self):
        """ Connect to the PostgreSQL database server """
        conn = None
        try:
            # connect to the PostgreSQL server
            self.log('__function__: Connecting to the PostgreSQL database...',
                     level='DEBUG')
            conn = psycopg2.connect(host=self._host,
                                    database=self._database,
                                    user=self._user,
                                    password=self._password)
        except (Exception, psycopg2.DatabaseError) as error:
            self.log(error, level='CRITCAL')
            return conn
        self.log("__function__: Connection successful", level='DEBUG')
        return conn

#########
# LOGIC #
#########

    def calculate_workers(self):
        self.log("starting calculate worker")
        for people in self._persons.values():
            person_name = people['name']
            try:
                elapsed_time = int(people['elapsed_time'])
            except (TypeError, ValueError) as error:
                self.log('__function__: Failed to get Elasped Time',
                         level='ERROR')
                elapsed_time = 1000
            self.log(
                f'__function__: {person_name} has been here for {elapsed_time} days',
                level='DEBUG')
            try:
                icon = people['default_icon']
            except (TypeError, ValueError):
                icon = "mdi:person"
            name_attr = dict()
            entity = people['worker']
            name_attr["friendly_name"] = person_name
            name_attr["icon"] = icon

            self.log(f"starting calculations for {person_name}", level='DEBUG')
            time_periods = {'life': elapsed_time, 'month': 28, 'week': 7}
            for k, v in time_periods.items():
                if elapsed_time < v:
                    self.log(f'__function__: {elapsed_time} is less than {v}',
                             level='DEBUG')
                    if elapsed_time > 0:
                        self.log(
                            f'__function__: Setting value for {k} to {elapsed_time}',
                            level='DEBUG')
                        v = elapsed_time
                    else:
                        self.log(
                            f'__function__: {elapsed_time} is less than Zero',
                            level='WARNING')
                        v = 1
                period = k
                end_time = self.get_right_now()
                start_time = self.get_start_time(v, end_time)
                new_dict = self.calculate_all_stats(person_name, period,
                                                    start_time, end_time)
                name_attr.update(new_dict)
            self.log(name_attr, level='DEBUG')
            self.set_state(entity,
                           state=name_attr['week_balance_percent'],
                           attributes=name_attr)
            self.log(f"Calculated: {person_name}", level='INFO')

    def calculate_all_stats(self, person_name, period, start_time, end_time):
        total_points = self.get_totals(person_name, 'total_points', start_time,
                                       end_time)
        earned_points = self.get_earned(person_name, start_time, end_time)
        required_points = self.get_totals(person_name, 'required_points',
                                          start_time, end_time)
        earned_percent = self.prcnt(earned_points, total_points)
        required_percent = self.prcnt(required_points, total_points)
        balance_percent = earned_percent - required_percent
        self.log(
            f'For {person_name} {total_points} {earned_points} {required_points} {earned_percent} {required_percent}',
            level='DEBUG')

        ## HA DICT ##
        new_dict = dict()
        new_dict[f'{period}_total_points'] = round(total_points)
        new_dict[f'{period}_earned_points'] = round(earned_points)
        new_dict[f'{period}_required_points'] = round(required_points)
        new_dict[f'{period}_earned_percent'] = round(earned_percent, 2)
        new_dict[f'{period}_required_percent'] = round(required_percent, 2)
        new_dict[f'{period}_balance_percent'] = round(balance_percent, 2)
        ## Database DICT ##
        data_dict = dict()
        data_dict['datetime'] = end_time
        data_dict['name'] = person_name
        data_dict['total_points'] = total_points
        data_dict['earned_points'] = earned_points
        data_dict['required_points'] = required_points
        data_dict['earned_percent'] = earned_percent
        data_dict['required_percent'] = required_percent
        data_dict['balance_percent'] = balance_percent
        self.insert_database(person_name, period, data_dict)
        ## ##
        return new_dict

######################
#     FUNCTIONS      #
# RETURN INFORMATION #
######################

    def get_totals(self, person, column, start_time, end_time):
        """[summary]

        Parameters
        ----------
        person : [str]
            [description]
        column : [type]
            [description]
        start_time : [type]
            [description]
        end_time : [type]
            [description]

        Returns
        -------
        [type]
            [description]
        """
        self.log('__function__: Starting....', level='DEBUG')
        conn = self.connect()
        if conn:
            cur = conn.cursor()
            self.log('__function__: Connection created', level='DEBUG')
        else:
            cur = None

        self.log(start_time, level='DEBUG')
        self.log(end_time, level='DEBUG')
        if person == 'Zach':
            person_name = "{Zach}"
        if person == 'Travis':
            person_name = "{Travis}"
        if person == 'Matt':
            person_name = "{Matt}"

        try:
            qry_str = sql.SQL(
                "SELECT SUM ({}) FROM {} WHERE required_person @> {} AND datetime BETWEEN {} AND {}"
            ).format(sql.Identifier(column),
                     sql.Identifier('chore', 'history'), sql.Placeholder(),
                     sql.Placeholder(), sql.Placeholder())
            cur.execute(qry_str, (person_name, start_time, end_time))
            row = cur.fetchone()
            if row[0] is None:
                return 0
            return row[0]
        except (Exception, psycopg2.DatabaseError) as error:
            self.error(error, level='ERROR')
        finally:
            if conn is not None:
                conn.close()
                self.log('__function__: Database connection closed.',
                         level='DEBUG')

    def get_earned(self, person, start_time, end_time):
        self.log('__function__: Starting....', level='DEBUG')
        conn = self.connect()
        if conn:
            cur = conn.cursor()
            self.log('__function__: Connection created', level='DEBUG')
        else:
            cur = None

        try:
            qry_str = sql.SQL(
                "SELECT SUM (total_points) FROM {} WHERE name = {} AND datetime BETWEEN {} AND {}"
            ).format(sql.Identifier('chore', 'history'), sql.Placeholder(),
                     sql.Placeholder(), sql.Placeholder())
            # self.log(qry_str.as_string(conn))
            cur.execute(qry_str, (person, start_time, end_time))
            row = cur.fetchone()
            if row[0] is None:
                return 0
            return row[0]
        except (Exception, psycopg2.DatabaseError) as error:
            self.error(error, level='ERROR')
        finally:
            if conn is not None:
                conn.close()
                self.log('__function__: Database connection closed.',
                         level='DEBUG')

    def get_right_now(self):
        self.log('__function__: Starting....', level='DEBUG')
        now = dt.now()
        return now

    def get_start_time(self, days, end_time):
        self.log('__function__: Starting....', level='DEBUG')
        timedelta = td(days=days)
        start_time = end_time - timedelta
        return start_time

    def prcnt(self, x, y):
        self.log('__function__: Starting....', level='DEBUG')
        if not x or not y:
            self.log('x = 0%\ny = 0%', level='DEBUG')
            return int(0)
        if x < 0 or y < 0:
            self.log("can't be negative!", level='WARNING')
            return int(0)
        total = (x / y)
        return total * 100


###################
# UPDATE DATABASE #
###################

    def insert_database(self, person_name, period, data_dict):
        self.log('__function__: Starting....', level='DEBUG')
        database = self._database
        data_schema = person_name.lower()
        data_table = period

        self.World.insert_data_dict(database, data_schema, data_table,
                                    data_dict)

    # def database_generator(self):
    #     start = dt(2020, 9, 20, 1, 1, 1)
    #     end = dt.now()

    #     for end_time in rrule.rrule(rrule.HOURLY, dtstart=start, until=end):
    #         person_name = 'Matt'
    #         time_periods = {'life': 1000, 'month': 28, 'week': 7}
    #         for k, v in time_periods.items():
    #             period = k
    #             start_time = self.get_start_time(v, end_time)
    #             self.calculate_all_stats(person_name, period, start_time,
    #                                      end_time)


