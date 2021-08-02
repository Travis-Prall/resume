import appdaemon.plugins.hass.hassapi as hass


class Castle(hass.Hass):
    def initialize(self):
        self.log(f'__function__: Starting {__name__}', level='INFO')
        ## Database ##
        self._database = self.args['database']
        self._schema = self.args['database_schema']
        self._table = self.args['database_table']
        # Getters and Setters #
        self.database_app = self.get_app(self.args['database_app'])
        self.database_dict = self.get_database_dict()
        self.active_lock_dict = self.get_lock_dict()
        self.resident_dict = self.get_resident_dict()  # Dict Indexed by ID
        self.active_dict = self.get_active_dict()  # Dict Indexed by Name
        self.people = self.get_row_column('resident',
                                          True,
                                          'person',
                                          make_list=True)
        self.people_name = self.get_row_column('resident',
                                               True,
                                               'name',
                                               make_list=True)
        self.roommates = self.get_row_column('type',
                                             'roommate',
                                             'name',
                                             make_list=True)
        self.roommates_list = self.get_row_column('type',
                                                  'roommate',
                                                  'person',
                                                  make_list=True)
        self.master = self.get_row_column('ID', 'Master', 'person')
        self.guest_list = self.get_row_column('type',
                                              'guest',
                                              'person',
                                              make_list=True)

        # Keep #
        self.keep_dict = self.get_keep_dict()
        self.castle_dict = self.get_castle_dict()
        self.keep_icon_dict = self.get_keep_icons()

        # Start #
        # Check #

        # Timers #
        # Actions #
        # self.listen_state(self.change_detected, "entity.entity")

##########
# REPORT #
##########

    def start_app(self):
        self.log('__function__: Starting App', level="DEBUG")
        entity_start_list = [self._entity1, self._entity2]
        for entity in entity_start_list:
            try:
                test = self.get_state(entity)
            except (TypeError, ValueError):
                self.error(f"Unable to get {entity}", level="ERROR")
                return

            if test is None:
                self.error(f"unable to get state for {entity}", level="ERROR")
                return
        self.log('__function__: App is now working', level="DEBUG")

############
# WATCHERS #
############

    def change_detected(self, entity, attribute, old, new, kwargs):
        # Double checks things whenever there is a change
        name = self.friendly_name(entity)  #gets the name of the entity
        if old != new:
            self.log(f"__function__: {name} changed from {old} to {new}")

############
# CHECKERS #
############

    def get_database_dict(self):
        self.log('__function__: testing app')
        database = self._database
        data_schema = self._schema
        data_table = self._table
        dicts = self.database_app.get_data_dict(database, data_schema,
                                                data_table)
        self.log(dicts, level='DEBUG')
        return (dicts)

    def get_lock_dict(self):
        self.log('__function__: testing app')
        database = self._database
        data_schema = self._schema
        data_table = "active_locks"
        dicts = self.database_app.get_data_dict(database, data_schema,
                                                data_table)
        self.log(dicts, level='DEBUG')
        return (dicts)

##########
# TIMERS #
##########

    def timer_check(self, kwargs):
        self.log('__function__: Checking', level='DEBUG')

#########
# LOGIC #
#########

######################
#     FUNCTIONS      #
# RETURN INFORMATION #
######################

    def get_row_column(self,
                       column,
                       index=False,
                       target='default',
                       make_list=False):
        self.log('__function__: Starting...', level='DEBUG')
        if target == 'default':
            target = column
        if make_list is False:
            self.log('__function__: Skipping making a list', level='DEBUG')
            for row in self.database_dict:
                if index is not False:
                    self.log(f'__function__: {index=}', level='DEBUG')
                    if row[column] == index:
                        self.log(f'__function__: Returning {row}',
                                 level='DEBUG')
                        return row[target]
                elif row[target]:
                    return row[target]
            self.log(f'__function__: unable to find {index}', level='WARNING')
            return False
        new_list = list()
        for row in self.database_dict:
            if index is not False:
                if row[column] == index:
                    new_list.append(row[target])
            elif row[target]:
                new_list.append(row[target])
        list_size = len(new_list)
        if list_size > 0:
            self.log(
                f'__function__: List size is {list_size} returning {new_list}',
                level='DEBUG')
            return tuple(new_list)
        self.log('__function__: Returning Nothing', level='WARNING')
        return False

    def get_row(self, column, index, make_list=False):
        """[summary]

        Parameters
        ----------
        column : [string]
            [Looks at what column]
        index : [Any]
            [returns any rows wehere column = index]
        make_list : bool, optional
            [makes a list or returns the first correct row], by default False

        Returns
        -------
        [Dic]
            [either a dic of dic or just one dic]
        """
        self.log('__function__: Starting...', level='DEBUG')
        row_list = list()
        for row in self.database_dict:
            self.log(f'__function__: {row=}', level='DEBUG')
            if row[column] == index:
                if make_list:
                    self.log('__function__: Appending List', level='DEBUG')
                    row_list.append(row)
                else:
                    self.log(f'__function__: {make_list=} returning {row}',
                             level='DEBUG')
                    return row
        list_size = len(row_list)
        if list_size > 0:
            self.log(f'__function__: List size is {list_size} returning {row}',
                     level='DEBUG')
            return row_list
        self.log(f'__function__: {list_size=} returning false',
                 level='WARNING')
        return False

    def get_resident_dict(self):
        self.log('__function__: Starting...', level='DEBUG')
        active_people_dict = dict()
        resident_list = self.get_row(column='resident',
                                     index=True,
                                     make_list=True)
        for row in resident_list:
            active_people_dict[row['ID']] = row
        self.log(f'__function__: returning {active_people_dict}',
                 level='DEBUG')
        return active_people_dict

    def get_active_dict(self):
        self.log('__function__: Starting...', level='DEBUG')
        active_people_dict = dict()
        resident_list = self.get_row(column='active',
                                     index=True,
                                     make_list=True)
        for row in resident_list:
            active_people_dict[row['name']] = row
        self.log(f'__function__: returning {active_people_dict}',
                 level='DEBUG')
        return active_people_dict

########
# KEEP #
########

    def get_keep_dict(self):
        self.log('__function__: Starting...', level='DEBUG')
        keep_dict = dict()
        for item in self.resident_dict.values():
            self.log(f'__function__: {item=}', level='DEBUG')
            person = item['person']
            keep = item['nest']
            keep_dict[person] = keep
        return keep_dict

    def get_castle_dict(self):
        self.log('__function__: Starting...', level='DEBUG')
        castle_dict = dict()
        for item in self.resident_dict.values():
            person = item['person']
            castle = item['castle']
            castle_dict[person] = castle
        return castle_dict

    def get_keep_icons(self):
        icon_dict = {
            "Unknown": "mdi:help",
            "Known": "mdi:account-question",
            "Ghoul": "mdi:alien",
            "Wasp": "mdi:ghost",
            "Empty": "mdi:blank",
            "Raider": "mdi:robber"
        }
        for item in self.resident_dict.values():
            name = item['name']
            person = item['person']
            icon_dict[name] = person
        return icon_dict


####################
# USEFUL FUNCTIONS #
####################

    def get_app_version(self, version):
        """ Returns a Dict of requested person """
        self.log('__function__: Starting...', level='DEBUG')
        self.log(f'__function__: Looking for {version}', level='DEBUG')
        if version in self.resident_dict.keys():
            self.log(f'__function__: Returning Dict for {version}',
                     level='DEBUG')
            return self.resident_dict[version]
        if version in self.active_dict.keys():
            self.log(f'__function__: Returning Dict for {version}',
                     level='DEBUG')
            return self.active_dict[version]
        self.log(f'__function__: No Dict for {version}', level='WARNING')
        return None


