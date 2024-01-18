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


class Prj1(QWidget):
    def __init__(self):
        super().__init__()
        self.sensor = pseudoSensor.PseudoSensor()

        self.setWindowTitle("Prj1")

        self.single_read = SingleReadWidget(self.sensor)
        self.readings_table = ReadingsTableWidget(self.sensor)
        self.alarms = AlarmWidget()
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.single_read)
        self.layout.addWidget(self.alarms)
        self.layout.addWidget(self.readings_table)
        self.resize(800, 800)


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

        self.layout = QHBoxLayout(self)

        self.temp_layout = QGridLayout()
        self.temp_input = QLineEdit()
        self.temp_input.setValidator(QDoubleValidator(-20.0, 100.0, 2))
        self.temp_input.setPlaceholderText(f'{self.temp_alarm}')
        self.temp_label = QLabel("degC")
        self.temp_alarm = QLabel("")

        self.temp_layout.addWidget(self.temp_input, 0, 0)
        self.temp_layout.addWidget(self.temp_label, 0, 1)
        self.temp_layout.addWidget(self.temp_alarm, 1, 0, 1, 2)

        self.hum_layout = QGridLayout()
        self.hum_input = QLineEdit()
        self.hum_input.setValidator(QDoubleValidator(0.0, 100.0, 2))
        self.hum_input.setPlaceholderText(f'{self.hum_alarm}')
        self.hum_label = QLabel("%")
        self.hum_alarm = QLabel("")

        self.hum_layout.addWidget(self.hum_input, 0, 0)
        self.hum_layout.addWidget(self.hum_label, 0, 1)
        self.hum_layout.addWidget(self.hum_alarm, 1, 0, 1, 2)

        self.layout.addLayout(self.temp_layout)
        self.layout.addLayout(self.hum_layout)


def main():
    app = QApplication(sys.argv)

    window = Prj1()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
