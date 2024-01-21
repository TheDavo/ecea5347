import sqlite3
from sqlite3 import Error


class PseudoSensorDb:

    def __init__(self, db_name="prj1_db.db"):
        self.conn = None
        self.db_name = db_name
        self.table_name = "sensor_data"

    def create_connection(self):
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_name)
        except Error as e:
            print(e)

    def create_sensor_table(self):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS {table}
        (
            id integer PRIMARY KEY,
            temperature_degC float,
            humidity_% float,
            datetime text
        );
        """.format(table=self.table_name)
        try:
            curs = self.conn.cursor()
            curs.execute(create_table_sql)
        except Error as e:
            print(e)

    def close_db(self):
        self.conn.close()

    def insert_data(self, data):
        insert_data_sql = """
        INSERT INTO {table}(temperature,humidity,datetime)
        VALUES(?,?,?)
        """.format(table=self.table_name)

        curs = self.conn.cursor()
        curs.execute(insert_data_sql, data)
        self.conn.commit()
        return curs.lastrowid
