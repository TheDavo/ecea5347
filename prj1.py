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
    QHeaderView
)

from PySide6.QtCore import Slot, QTimer, QDateTime, Qt
import pseudoSensor


class Prj1(QWidget):
    def __init__(self):
        super().__init__()
        self.sensor = pseudoSensor.PseudoSensor()

        self.setWindowTitle("Prj1")

        self.single_read = SingleReadWidget(self.sensor)
        self.readings_table = ReadingsTableWidget(self.sensor)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.single_read)
        self.layout.addWidget(self.readings_table)
        self.resize(800, 800)


class SingleReadWidget(QWidget):
    def __init__(self, ps: pseudoSensor.PseudoSensor):
        super().__init__()
        self.sensor = ps
        self.read_btn = QPushButton("Single Humidity/Temp Reading")
        self.read_btn.clicked.connect(self.get_humidity_temp_reading)

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
    def get_humidity_temp_reading(self):
        hum, temp = self.sensor.generate_values()
        self.humidity_label.setText(f'{hum:.2f}')
        self.temp_label.setText(f'{temp:.2f}')


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


def main():
    app = QApplication(sys.argv)

    window = Prj1()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
