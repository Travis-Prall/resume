import appdaemon.plugins.hass.hassapi as hass
import psycopg2
from psycopg2.extras import RealDictConnection, RealDictCursor
from psycopg2 import connect, sql, DatabaseError

#############
# FUNCTIONS #
#############


def _get_table(table):
    data = table.split(".")
    if len(data) == 1:
        return "public", table
    return data[0], data[1]


def _get_insert_sql(table, kwargs):
    keys = kwargs[0].keys() if type(kwargs) is list else kwargs.keys()
    schema, table = _get_table(table)

    raw_sql = "insert into {sch}.{tbl} ({t_fields}) values ({t_values})"
    return sql.SQL(raw_sql).format(
        sch=sql.Identifier(schema),
        tbl=sql.Identifier(table),
        t_fields=sql.SQL(', ').join(map(sql.Identifier, keys)),
        t_values=sql.SQL(', ').join(map(sql.Placeholder, keys)))


def _get_conditions(where):
    return [
        sql.SQL("{identifier} = {placeholder}").format(
            identifier=sql.Identifier(key), placeholder=sql.Placeholder(key))
        for key in where
    ]


def _get_update_sql(data, identifier, table):
    schema, table = _get_table(table)
    raw_sql = "update {sch}.{tbl} set {t_set} where {t_where}"
    qry_str = sql.SQL(raw_sql).format(
        sch=sql.Identifier(schema),
        tbl=sql.Identifier(table),
        t_set=sql.SQL(', ').join(_get_conditions(data)),
        t_where=sql.SQL(' and ').join(_get_conditions(identifier)))
    return qry_str


def _get_upsert_sql(data, identifier, table):
    raw_sql = """
        WITH
            upsert AS (
                UPDATE {sch}.{tbl}
                SET {t_set}
                WHERE {t_where}
                RETURNING {sch}.{tbl}.*),
            inserted AS (
                INSERT INTO {sch}.{tbl} ({t_fields})
                SELECT {t_select_fields}
                WHERE NOT EXISTS (SELECT 1 FROM upsert)
                RETURNING *)
        SELECT * FROM upsert
        UNION ALL
        SELECT * FROM inserted
    """
    merger_data = {**data, **identifier}
    schema, table = _get_table(table)
    qry_str = sql.SQL(raw_sql).format(
        sch=sql.Identifier(schema),
        tbl=sql.Identifier(table),
        t_set=sql.SQL(', ').join(_get_conditions(data)),
        t_where=sql.SQL(' and ').join(_get_conditions(identifier)),
        t_fields=sql.SQL(', ').join(map(sql.Identifier, merger_data.keys())),
        t_select_fields=sql.SQL(', ').join(
            map(sql.Placeholder, merger_data.keys())))

    return merger_data, qry_str


class Test(hass.Hass):
    def initialize(self):
        self.log(f'__function__: Starting {__name__}', level='INFO')
        # Getters and Setters #
        try:
            self._user = self.args['user']
        except KeyError:
            self.log("Missing varible USER", level="CRITCAL")
            return

        try:
            self._host = self.args['host']
        except KeyError:
            self.log("Missing varible HOST", level="CRITCAL")
            return

        try:
            self._port = self.args['port']
        except KeyError:
            self.log("Missing varible PORT", level="CRITCAL")
            return

        try:
            self._password = self.args['password']
        except KeyError:
            self._password = None
            self.log("Missing varible PASSWORD", level="WARNING")

        try:
            self._database = self.args['database']
        except KeyError:
            self._database = None
            self.log("Missing varible DATABASE", level="WARNING")

        self.__conn = None
        self.__cursor = None

###########
# CONNECT #
###########

    def _get_connection(self, named=True, autocommit=False):
        """ Connect to the PostgreSQL database server """
        self.log(f'__function__: getting connection to {self._database}',
                 level='DEBUG')
        self.__conn = None
        self.log('__function__: creating connection', level='DEBUG')
        try:
            # connect to the PostgreSQL server
            self.log('__function__: Connecting to the PostgreSQL database...',
                     level='DEBUG')
            self.__conn = connect(
                host=self._host,
                database=self._database,
                user=self._user,
                password=self._password,
                connection_factory=RealDictConnection if named else None)
            self.__conn.autocommit = autocommit
            self.log("__function__: Connection successful", level='DEBUG')
        except (Exception, DatabaseError) as error:
            self.log(error, level='CRITICAL')
            self.error(error, level='CRITICAL')

    def _get_cursor(self, named=True, autocommit=False):
        self._get_connection(named, autocommit)
        if self.__conn:
            if named:
                self.__cursor = self.__conn.cursor(
                    cursor_factory=RealDictCursor)
            else:
                self.__cursor = self.__conn.cursor()
            self.log('__function__: Retrieved Connection', level='DEBUG')
        else:
            self.__cursor = None
            self.log('__function__: Failed to retrieve connection',
                     level='WARNING')

#########
# FETCH #
#########

    def fetch_all(self, table, where=None, named=True, autocommit=False):
        self.log(f'__function__: fetching {table}', level='DEBUG')
        self._get_cursor(named, autocommit)
        if self.__cursor:
            schema, table = _get_table(table)
            if where:
                raw_sql = "SELECT * from {sch}.{tbl} where {t_where}"
            else:
                raw_sql = "SELECT * from {sch}.{tbl}"
                where = {}

            qry_str = sql.SQL(raw_sql).format(sch=sql.Identifier(schema),
                                              tbl=sql.Identifier(table),
                                              t_where=sql.SQL(' and ').join(
                                                  _get_conditions(where)))

            try:
                self.__cursor.execute(qry_str, where)
                qry = self.__cursor.fetchall()
                self.__cursor.close()
                return qry
            except (Exception, DatabaseError) as error:
                self.log(error, level='ERROR')
                return error
            finally:
                if self.__conn is not None:
                    self.__conn.close()
                    self.log('__function__: Database connection closed.',
                             level='INFO')
        else:
            self.log('__function__: Cursor Failed', level='ERROR')
            return None

    def fetch_one(self, table, where, column=0, named=True, autocommit=False):
        self.log(f'__function__: fetching {table} {where=}', level='DEBUG')
        self._get_cursor(named, autocommit)
        if self.__cursor:
            schema, table = _get_table(table)
            raw_sql = "SELECT * from {sch}.{tbl} where {t_where}"

            qry_str = sql.SQL(raw_sql).format(sch=sql.Identifier(schema),
                                              tbl=sql.Identifier(table),
                                              t_where=sql.SQL(' and ').join(
                                                  _get_conditions(where)))

            try:
                self.__cursor.execute(qry_str, where)
                data = self.__cursor.fetchone()
                self.__cursor.close()
                return data[column] if type(data) is tuple else list(
                    data.values())[column]
            except (Exception, DatabaseError) as error:
                self.log(error, level='ERROR')
                return error
            finally:
                if self.__conn is not None:
                    self.__conn.close()
                    self.log('__function__: Database connection closed.',
                             level='INFO')
        else:
            self.log('__function__: Cursor Failed', level='ERROR')
            return None


#########
# WRITE #
#########

    def insert(self, table, named=True, autocommit=False, data=None, **kwargs):
        self.log(f'__function__: Starting to insert {kwargs} into {table}')
        if data:
            kwargs = data
        qry_str = _get_insert_sql(table, kwargs)
        self._get_cursor(named, autocommit)
        try:
            self.__cursor.execute(qry_str, kwargs)
            self.__conn.commit()
            self.__cursor.close()
            # if type(**kwargs) is list:
            #     self.__cursor.executemany(qry_str, **kwargs)
            # else:
            #     self.__cursor.execute(qry_str, kwargs)
        except (Exception, DatabaseError) as error:
            self.log(error, level='ERROR')
            return error
        finally:
            if self.__conn is not None:
                self.__conn.close()
                self.log('__function__: Database connection closed.',
                         level='INFO')

    def update(self, table, where, named=True, autocommit=False, **kwargs):
        self.log(
            f'__function__: Starting to update {kwargs} into {table} {where=}')
        qry_str = _get_update_sql(kwargs, where, table)
        self._get_cursor(named, autocommit)
        try:
            self.__cursor.execute(qry_str, {**kwargs, **where})
            self.__conn.commit()
            self.__cursor.close()
        except (Exception, DatabaseError) as error:
            self.log(error, level='ERROR')
            return error
        finally:
            if self.__conn is not None:
                self.__conn.close()
                self.log('__function__: Database connection closed.',
                         level='INFO')

    def upsert(self,
               table,
               where,
               named=True,
               autocommit=False,
               data=None,
               **kwargs):
        self.log(
            f'__function__: Starting to update {kwargs=} into {table} {where=}'
        )
        if data:
            kwargs = data
        merger_data, qry_str = _get_upsert_sql(kwargs, where, table)
        self._get_cursor(named, autocommit)
        try:
            self.__cursor.execute(qry_str, merger_data)
            self.__conn.commit()
            self.__cursor.close()
        except (Exception, DatabaseError) as error:
            self.log(error, level='ERROR')
            return error
        finally:
            if self.__conn is not None:
                self.__conn.close()
                self.log('__function__: Database connection closed.',
                         level='INFO')


