import sys
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QGridLayout
)

from PySide6.QtCore import (
    Slot, QTimer, QDateTime, Qt
)

from PySide6.QtGui import QDoubleValidator

from typing import Tuple
import pseudoSensor

# import sqlite3

MIN_HUM = 0  # %hum
MAX_HUM = 100  # %hum

MIN_TEMP = -20  # degC
MAX_TEMP = 120  # degC


class Prj1(QWidget):
    def __init__(self):
        super().__init__()
        self.sensor = pseudoSensor.PseudoSensor()

        self.setWindowTitle("Prj1")
        self.latest_temp = 0
        self.latest_hum = 0

        self.alarms = AlarmWidget()
        self.single_read = SingleReadWidget(self.sensor)

        self.single_read.read_btn.clicked.connect(self.get_from_single_read)
        # self.single_read.read_btn.clicked.connect(
        #     lambda: self.alarms.alarm_temp(self.latest_temp))
        # self.single_read.read_btn.clicked.connect(
        #     lambda: self.alarms.alarm_hum(self.latest_hum))

        self.readings_table = ReadingsTableWidget(self.sensor)
        self.readings_table.readings_table.readings_timer.timeout.connect(
            self.get_from_table)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.single_read)
        self.layout.addWidget(self.alarms)
        self.layout.addWidget(self.readings_table)
        self.resize(800, 800)

    @Slot()
    def get_from_single_read(self):
        self.latest_temp = self.single_read.temp
        self.latest_hum = self.single_read.hum
        self.alarms.alarm_hum(self.latest_hum)
        self.alarms.alarm_temp(self.latest_hum)

    @Slot()
    def get_from_table(self):
        curr_row = self.readings_table.readings_table.timer_count-1
        self.latest_temp = self.readings_table\
            .readings_table.readings[curr_row][1]
        self.latest_hum = self.readings_table\
            .readings_table.readings[curr_row][0]

        self.alarms.alarm_hum(self.latest_hum)
        self.alarms.alarm_temp(self.latest_hum)


class SingleReadWidget(QWidget):
    def __init__(self, ps: pseudoSensor.PseudoSensor):
        super().__init__()
        self.hum = 0
        self.temp = 0
        self.sensor = ps
        self.read_btn = QPushButton("Single Humidity/Temp Reading")
        self.read_btn.clicked.connect(self.gen_humidity_temp_reading)

        # Single Read Humidity and Temp Readings
        self.humidity_label = QLabel("20")
        self.humidity_label.setAlignment(Qt.AlignRight)
        self.humidity_layout = QHBoxLayout()
        self.humidity_layout.addWidget(self.humidity_label)
        self.humidity_layout.addWidget(QLabel("%"))

        self.temp_layout = QHBoxLayout()
        self.temp_label = QLabel("25")
        self.temp_label.setAlignment(Qt.AlignRight)
        self.temp_layout.addWidget(self.temp_label)
        self.temp_layout.addWidget(QLabel("degC"))

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.read_btn)
        self.layout.addLayout(self.humidity_layout)
        self.layout.addLayout(self.temp_layout)

    @Slot()
    def gen_humidity_temp_reading(self) -> None:
        self.hum, self.temp = self.sensor.generate_values()
        self.humidity_label.setText(f'{self.hum:.2f}')
        self.temp_label.setText(f'{self.temp:.2f}')

    def get_reading(self) -> Tuple[float, float]:
        return self.hum, self.temp


class ReadingsTableWidget(QWidget):
    def __init__(self, ps: pseudoSensor.PseudoSensor):
        super().__init__()
        self.sensor = ps
        self.read_btn = QPushButton("Ten Humidity/Temperature Readings")
        self.readings_table = ReadingsTable(self.sensor)
        self.read_btn.clicked.connect(self.readings_table.start_timer)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.read_btn)
        self.layout.addWidget(self.readings_table)


class ReadingsTable(QTableWidget):

    def __init__(self, ps: pseudoSensor.PseudoSensor):
        super().__init__()

        self.num_read = 10
        self.readings = [(0, 0, "")]*self.num_read
        self.setRowCount(self.num_read)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(
            ["Humidity", "Temperature", "Time"])
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.readings_timer = QTimer()
        self.readings_timer.timeout.connect(self.get_humidity_temp_readings)
        self.timer_count = 0
        self.sensor = ps

    @Slot()
    def get_humidity_temp_readings(self):
        humidity, temp = self.sensor.generate_values()
        item_humidity = QTableWidgetItem(f'{humidity:.2f}')
        item_temp = QTableWidgetItem(f'{temp:.2f}')

        self.setItem(self.timer_count, 0, item_humidity)
        self.setItem(self.timer_count, 1, item_temp)

        current_time = QDateTime.currentDateTime()
        formatted_time = current_time.toString('yyyy-MM-dd hh:mm:ss dddd')
        item_time = QTableWidgetItem(formatted_time)

        self.setItem(self.timer_count, 2, item_time)
        self.readings[self.timer_count] = (humidity, temp, formatted_time)
        self.timer_count = self.timer_count + 1

        if self.timer_count >= self.num_read:
            self.timer_count = 0
            self.end_timer()

    def start_timer(self):
        self.readings_timer.start(1000)

    def end_timer(self):
        self.readings_timer.stop()


class AlarmWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.temp_alarm = 60  # Celcius
        self.hum_alarm = 80  # Percent

        self.layout = QVBoxLayout(self)

        self.grid = QGridLayout()
        self.temp_input = QLineEdit()
        self.temp_input.setValidator(QDoubleValidator(MIN_TEMP, MAX_TEMP, 2))
        self.temp_input.setPlaceholderText(f'{self.temp_alarm}')
        self.temp_label = QLabel("degC")
        self.temp_alarm_box = QLabel("")

        self.grid.addWidget(self.temp_input, 0, 0)
        self.grid.addWidget(self.temp_label, 0, 1)
        self.grid.addWidget(self.temp_alarm_box, 1, 0, 1, 2)

        self.hum_input = QLineEdit()
        self.hum_input.setValidator(QDoubleValidator(MIN_HUM, MAX_HUM, 2))
        self.hum_input.setPlaceholderText(f'{self.hum_alarm}')
        self.hum_input.textEdited.connect(self.update_hum_alarm)
        self.hum_label = QLabel("%")
        self.hum_alarm_box = QLabel("")

        self.grid.addWidget(self.hum_input, 0, 2)
        self.grid.addWidget(self.hum_label, 0, 3)
        self.grid.addWidget(self.hum_alarm_box, 1, 2, 1, 2)

        self.layout.addWidget(QLabel("Alarm Settings"))
        self.layout.addLayout(self.grid)

    @Slot()
    def alarm_temp(self, temp_val):
        if temp_val > self.temp_alarm:
            self.temp_alarm_box.setStyleSheet("""
            background-color: red;
            """)

    @Slot()
    def alarm_hum(self, hum_val):
        if hum_val > self.hum_alarm:
            self.hum_alarm_box.setStyleSheet("""
            background-color: red;
            """)

    @Slot()
    def update_temp_alarm(self):
        val = float(self.temp_input.text())
        self.temp_alarm = max(MIN_TEMP, min(val, MAX_TEMP))

    @Slot()
    def update_hum_alarm(self):
        val = float(self.hum_input.text())
        self.hum_alarm = max(MIN_HUM, min(val, MAX_HUM))


def main():
    app = QApplication(sys.argv)

    window = Prj1()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
