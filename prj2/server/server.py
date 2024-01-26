import tornado
import tornado.websocket
import tornado.ioloop
import tornado.web
import tornado.httpserver
# import socket
import pseudoSensor
import datetime
from db import PseudoSensorDb


class WSHandler(tornado.websocket.WebSocketHandler):
    sensor = pseudoSensor.PseudoSensor()
    sensor_db = PseudoSensorDb("prj2_db.db")

    def open(self):
        print("new connection")
        self.write_message("Hello World")
        self.sensor_db.create_connection()
        self.sensor_db.create_sensor_table()

    def on_message(self, message):
        print("msg received:", message)
        match message:
            case "data req":
                self.send_humtemp_val(False)
            case "datam req":
                self.send_humtemp_val(True)
            case "shutdown":
                tornado.ioloop.IOLoop.instance().close()
            case "calcstats":
                self.send_calculate_stats()
            case _:
                self.write_message("Unrecognized message")

    def on_close(self):
        print("connection closed")

    def check_origin(self, origin):
        return True

    def send_humtemp_val(self, for_multiple):
        hum, temp = self.sensor.generate_values()
        now = datetime.datetime.now()
        strnow = now.strftime("%Y-%m-%dT%H:%M:%S")
        db_data = (temp, hum, strnow)
        self.sensor_db.insert_data(db_data)
        if not for_multiple:
            self.write_message(f'data {hum},{temp},{strnow}')
        else:
            self.write_message(f'datam {hum},{temp},{strnow}')

    def send_calculate_stats(self):
        data_rows = self.sensor_db.get_latest_10()

        # Start from '1' index because index 0 is the primary key column
        temps = [row[2] for row in data_rows]
        hums = [row[1] for row in data_rows]

        min_temp = min(temps)
        min_hum = min(hums)
        max_temp = max(temps)
        max_hum = max(hums)
        avg_temp = sum(temps)/len(temps)
        avg_hum = sum(hums)/len(hums)

        self.write_message(f"datacalc {min_temp},{max_temp},{
                           avg_temp},{min_hum},{max_hum},{avg_hum}")


if __name__ == "__main__":
    application = tornado.web.Application([(r'/ws/', WSHandler)])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888, address="localhost")
    # my_ip = socket.gethostbyname(socket.gethostname())
    print("Starting a server on localhost:8888")
    tornado.ioloop.IOLoop.instance().start()
