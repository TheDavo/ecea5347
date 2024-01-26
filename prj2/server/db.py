import sqlite3
from sqlite3 import Error


class PseudoSensorDb:

    def __init__(self, db_name="prj_db.db"):
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
            humidity_pcent float,
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
        INSERT INTO {table}(temperature_degC,humidity_pcent,datetime)
        VALUES(?,?,?)
        """.format(table=self.table_name)

        curs = self.conn.cursor()
        curs.execute(insert_data_sql, data)
        self.conn.commit()
        return curs.lastrowid

    def get_latest_10(self):
        """
        get_latest_10 generates a list of rows (tuples) from the latest
        ten readings (ordered by id)

        if the result from the db is less than ten rows long, the list
        will be the length of the db query

        Returns:
        List[Tuple[float,float,str]]
        """
        get_data_sql = """
        SELECT * FROM {table} ORDER BY id DESC LIMIT 10;
        """.format(table=self.table_name)

        curs = self.conn.cursor()
        curs.execute(get_data_sql)

        data = curs.fetchall()
        return data
