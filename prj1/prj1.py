"""
Written by Davit Khudaveryan for the ECEA5347 Course:
Rapid Prototyping Interfaces for Embedded Systems

This is a PyQT project to read measurement data from
a 'pseudo' temperature/humidity sensor and display the information
to the user in an easy to see interface

The user can read a single measurement or request ten (10) to be
read over the course of one (1) second intervals

The user can calculate the minimum, maximum, and average of the
latest ten (10) readings from a long term storage sqlite3 database
"""

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
    QGridLayout,
    QProgressBar
)

from PySide6.QtCore import (
    Slot, QTimer, QDateTime, Qt
)

from PySide6.QtGui import QDoubleValidator

from typing import Tuple
import pseudoSensor
from db import PseudoSensorDb

MIN_HUM = 0  # %hum
MAX_HUM = 100  # %hum

MIN_TEMP = -20  # degC
MAX_TEMP = 120  # degC


class Prj1(QWidget):
    def __init__(self):
        super().__init__()
        self.sensor = pseudoSensor.PseudoSensor()

        # Iniialize the database
        self.db = PseudoSensorDb()
        self.db.create_connection()
        self.db.create_sensor_table()

        self.setWindowTitle("Prj1")
        self.latest_temp = 0
        self.latest_hum = 0
        self.latest_dt = ""

        self.alarms = AlarmWidget()
        self.single_read = SingleReadWidget(self.sensor)
        self.single_read.read_btn.clicked.connect(self.get_from_single_read)
        self.single_read.read_btn.clicked.connect(self.update_alarm)
        self.single_read.read_btn.clicked.connect(self.insert_into_db)

        self.readings_table = ReadingsTableWidget(self.sensor)
        self.readings_table.timer.timeout.connect(
            self.get_from_table)
        self.readings_table.timer.timeout.connect(self.update_alarm)
        self.readings_table.timer.timeout.connect(self.insert_into_db)
        self.close_btn = QPushButton("Close Window")
        self.close_btn.clicked.connect(self.my_close)

        self.calc_widget = CalcWidget(self.db)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.alarms)
        self.layout.addWidget(self.single_read)
        self.layout.addWidget(self.readings_table)
        self.layout.addWidget(self.calc_widget)
        self.layout.addWidget(self.close_btn)
        self.resize(500, 800)

    @Slot()
    def get_from_single_read(self):
        """
        get_from_single_read retrieves data generated from the
        SingleReadWidget widget
        """
        self.latest_temp, self.latest_hum, self.latest_dt =\
            self.single_read.get_reading()

    @Slot()
    def get_from_table(self):
        """
        get_from_table retrieves data generated from the
        ReadingsTableWidget widget to store in the latest readings
        """
        curr_row = self.readings_table.timer_count-1
        self.latest_hum = self.readings_table\
            .readings[curr_row][0]
        self.latest_temp = self.readings_table\
            .readings[curr_row][1]
        self.latest_dt = self.readings_table\
            .readings[curr_row][2]

    @Slot()
    def update_alarm(self):
        """
        update_alarm sets the alarm value to be checked against
        to the latest values retrieves from the other data generating widgets
        """
        self.alarms.alarm_hum(self.latest_hum)
        self.alarms.alarm_temp(self.latest_temp)

    @Slot()
    def insert_into_db(self):
        data = (self.latest_temp, self.latest_hum, self.latest_dt)
        self.db.insert_data(data)

    @Slot()
    def my_close(self):
        if self.db.conn:
            self.db.close_db()

        self.close()

    def closeEvent(self, event):
        if self.db.conn:
            self.db.close_db()

        event.accept()


class SingleReadWidget(QWidget):
    """
    SingleReadWidget that generates a single sample of the read
    in its own small display
    """

    def __init__(self, ps: pseudoSensor.PseudoSensor):
        super().__init__()
        self.hum = 0
        self.temp = 0
        self.dt = ""
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

        self.temp_hum_layout = QHBoxLayout()
        self.temp_hum_layout.addLayout(self.temp_layout)
        self.temp_hum_layout.addLayout(self.humidity_layout)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.read_btn)
        self.layout.addLayout(self.temp_hum_layout)

    @Slot()
    def gen_humidity_temp_reading(self) -> None:
        self.hum, self.temp = self.sensor.generate_values()
        current_time = QDateTime.currentDateTime()
        self.dt = current_time.toString('yyyy-MM-dd hh:mm:ss dddd')
        self.humidity_label.setText(f'{self.hum:.2f}')
        self.temp_label.setText(f'{self.temp:.2f}')

    def get_reading(self) -> Tuple[float, float, str]:
        return self.hum, self.temp, self.dt


class ReadingsTableWidget(QWidget):
    """
    ReadingTablesWidget contains the button to request ten readings and the
    table that shows the latest readings from the table
    """

    def __init__(self, ps: pseudoSensor.PseudoSensor):
        super().__init__()
        self.sensor = ps
        self.num_read = 10
        self.readings = [(0, 0, "")]*self.num_read

        self.read_btn = QPushButton("Ten Humidity/Temperature Readings")
        self.table = ReadingsTable(self.sensor, self.num_read)
        self.read_btn.clicked.connect(self.start_timer)

        self.progress = QProgressBar(self)
        self.progress.setValue(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.gen_humidity_temp_readings)
        self.timer.timeout.connect(self.update_progress_bar)
        self.timer_count = 0
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.read_btn)
        self.layout.addWidget(self.progress)
        self.layout.addWidget(self.table)

    @Slot()
    def gen_humidity_temp_readings(self):
        """
        gen_humidity_temp_readings is triggered from the timer in this widge
        to generate a reading value and update the data array and update
        the table ui
        """
        humidity, temp = self.sensor.generate_values()
        current_time = QDateTime.currentDateTime()
        formatted_time = current_time.toString('yyyy-MM-dd hh:mm:ss dddd')

        self.readings[self.timer_count] = (humidity, temp, formatted_time)
        self.table.update_table(self.timer_count, temp,
                                humidity, formatted_time)
        self.timer_count = self.timer_count + 1

        if self.timer_count >= self.num_read:
            self.timer_count = 0
            self.end_timer()

    def start_timer(self):
        self.timer.start(1000)

    def end_timer(self):
        self.timer.stop()

    @Slot()
    def update_progress_bar(self):
        self.progress.setValue(float(self.timer_count/self.num_read)*100)


class ReadingsTable(QTableWidget):
    """
    ReadingsTable is the table that shows the latest readings in a QTable

    This is a sub-widget of the parent 'ReadingsTableWidget' and is purely
    the UI table. The parent widget holds the data
    """

    def __init__(self, ps: pseudoSensor.PseudoSensor, num_rows: int):
        super().__init__()

        self.num_rows = num_rows
        self.readings = [(0, 0, "")]*self.num_rows
        self.setRowCount(self.num_rows)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(
            ["Humidity (%)", "Temperature (degC)", "Datetime"])
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

    def update_table(self, row, temp, humidity, datetime):
        """
        update_table updates the table ui element at 'row' with the latest
        sensor data
        """
        item_humidity = QTableWidgetItem(f'{humidity:.2f}')
        item_temp = QTableWidgetItem(f'{temp:.2f}')
        item_time = QTableWidgetItem(f'{datetime}')

        self.setItem(row, 0, item_humidity)
        self.setItem(row, 1, item_temp)
        self.setItem(row, 2, item_time)


class AlarmWidget(QWidget):
    """
    Alarm widget notifies the user when any of the temperature or humidity
    readings are over the alarm level.

    This widget has the ability to reset the alarms.
    """

    def __init__(self):
        super().__init__()

        self.temp_alarm = 60  # Celcius
        self.hum_alarm = 80  # Percent
        self.temp_has_alarmed = False
        self.hum_has_alarmed = False
        self.layout = QVBoxLayout(self)

        self.grid = QGridLayout()
        self.temp_input = QLineEdit()
        self.temp_input.setValidator(QDoubleValidator(MIN_TEMP, MAX_TEMP, 2))
        self.temp_input.setPlaceholderText(f'{self.temp_alarm}')
        self.temp_input.textEdited.connect(self.update_temp_alarm)
        self.temp_label = QLabel("degC")
        self.temp_alarm_box = QLabel("")
        self.clear_temp_alarm_btn = QPushButton("Clear Temp Alarm")
        self.clear_temp_alarm_btn.clicked.connect(self.clear_temp_alarm)
        self.clear_temp_alarm_btn.setEnabled(False)

        self.grid.addWidget(self.temp_input, 0, 0)
        self.grid.addWidget(self.temp_label, 0, 1)
        self.grid.addWidget(self.temp_alarm_box, 1, 0, 1, 2)
        self.grid.addWidget(self.clear_temp_alarm_btn, 2, 0, 1, 2)

        self.hum_input = QLineEdit()
        self.hum_input.setValidator(QDoubleValidator(MIN_HUM, MAX_HUM, 2))
        self.hum_input.setPlaceholderText(f'{self.hum_alarm}')
        self.hum_input.textEdited.connect(self.update_hum_alarm)
        self.hum_label = QLabel("%")
        self.hum_alarm_box = QLabel("")
        self.clear_hum_alarm_btn = QPushButton("Clear Humidity Alarm")
        self.clear_hum_alarm_btn.clicked.connect(self.clear_hum_alarm)
        self.clear_hum_alarm_btn.setEnabled(False)
        self.grid.addWidget(self.clear_hum_alarm_btn, 2, 2, 1, 2)

        self.grid.addWidget(self.hum_input, 0, 2)
        self.grid.addWidget(self.hum_label, 0, 3)
        self.grid.addWidget(self.hum_alarm_box, 1, 2, 1, 2)

        self.layout.addWidget(QLabel("Alarm Settings"))
        self.layout.addLayout(self.grid)

    @Slot()
    def alarm_temp(self, temp_val):
        """
        alarm_temp checks the temperature value against the set alarm level
        and will trigger the ui element to show the user that the
        alarm level has been reached

        The alarm can be cleared if needed
        """
        if temp_val > self.temp_alarm and not self.temp_has_alarmed:
            self.clear_temp_alarm_btn.setEnabled(True)
            self.temp_has_alarmed = True
            self.temp_alarm_box.setText(f'ALARM at {temp_val:.2f}degC')
            self.temp_alarm_box.setStyleSheet("""
            background-color: red;
            """)

    @Slot()
    def alarm_hum(self, hum_val):
        """
        alarm_hum checks the humidity value against the set alarm level
        and will trigger the ui element to show the user that the
        alarm level has been reached

        The alarm can be cleared if needed
        """
        if hum_val > self.hum_alarm and not self.hum_has_alarmed:
            self.clear_hum_alarm_btn.setEnabled(True)
            self.hum_has_alarmed = True
            self.hum_alarm_box.setText(f'ALARM at {hum_val:.2f}%')
            self.hum_alarm_box.setStyleSheet("""
            background-color: red;
            """)

    @Slot()
    def update_temp_alarm(self):
        """
        update_temp_alarm takes in the text field, clamps it, and updates the
        widget's alarm value
        """
        if self.temp_input.text() == '':
            return
        val = float(self.temp_input.text())
        self.temp_alarm = max(MIN_TEMP, min(val, MAX_TEMP))

        # Also lock the number shown in the edit box
        if val > MAX_TEMP:
            self.temp_input.setText("120")

    @Slot()
    def update_hum_alarm(self):
        """
        update_hum_alarm takes in the text field, clamps it, and updates the
        widget's alarm value
        """
        if self.hum_input.text() == '':
            return
        val = float(self.hum_input.text())
        self.hum_alarm = max(MIN_HUM, min(val, MAX_HUM))

        # Also lock the number shown in the edit box
        if val > MAX_HUM:
            self.hum_input.setText("100")

    @Slot()
    def clear_temp_alarm(self):
        """
        clear_temp_alarm clears the alarm booleans of the widget's values
        and updates the ui to show the user the alarm is cleared
        """
        self.temp_alarm_box.setText("ALARM CLEARED")
        self.temp_alarm_box.setStyleSheet("""
        background-color: none;
        """)
        self.temp_has_alarmed = False
        self.clear_temp_alarm_btn.setEnabled(False)

    @Slot()
    def clear_hum_alarm(self):
        """
        clear_hum_alarm clears the alarm booleans of the widget's values
        and updates the ui to show the user the alarm is cleared
        """
        self.hum_alarm_box.setText("ALARM CLEARED")
        self.hum_alarm_box.setStyleSheet("""
        background-color: none;
        """)
        self.hum_has_alarmed = False
        self.clear_hum_alarm_btn.setEnabled(False)


class CalcWidget(QWidget):
    """
    CalcWidget displays the min, max, and average of the latest (past 10 max)
    readings and their respective minimums, maximums, and averages in a grid
    ui configuration

    The user must click on the button to read in the latest data and get the
    results
    """

    def __init__(self, db: PseudoSensorDb):
        super().__init__()

        self.db = db
        self.data = []
        self.calcs = []
        self.calc_btn = QPushButton("Calculate Avg/Min/Max of Latest Ten")
        self.calc_btn.clicked.connect(self.get_latest_data_db)
        self.calc_btn.clicked.connect(self.calculate)
        self.calc_btn.clicked.connect(self.update)
        self.grid = QGridLayout()
        self.grid.addWidget(QLabel("Min"), 0, 1, 1, 1)
        self.grid.addWidget(QLabel("Max"), 0, 2, 1, 1)
        self.grid.addWidget(QLabel("Avg"), 0, 3, 1, 1)
        self.grid.addWidget(QLabel("Temperature (degC)"), 1, 0, 1, 1)
        self.grid.addWidget(QLabel("Humidity (%)"), 2, 0, 1, 1)
        self.min_temp_label = QLabel("")
        self.max_temp_label = QLabel("")
        self.avg_temp_label = QLabel("")
        self.min_hum_label = QLabel("")
        self.max_hum_label = QLabel("")
        self.avg_hum_label = QLabel("")
        self.grid.addWidget(self.min_temp_label, 1, 1, 1, 1)
        self.grid.addWidget(self.max_temp_label, 1, 2, 1, 1)
        self.grid.addWidget(self.avg_temp_label, 1, 3, 1, 1)
        self.grid.addWidget(self.min_hum_label, 2, 1, 1, 1)
        self.grid.addWidget(self.max_hum_label, 2, 2, 1, 1)
        self.grid.addWidget(self.avg_hum_label, 2, 3, 1, 1)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.calc_btn)
        self.layout.addLayout(self.grid)

    @Slot()
    def get_latest_data_db(self):
        self.data = self.db.get_latest_10()

    @Slot()
    def calculate(self):
        if self.data is None or self.data == []:
            # (min, max, avg) of temp, humidity
            return [(0, 0, 0), (0, 0, 0)]

        temps = [row[2] for row in self.data]
        hums = [row[1] for row in self.data]

        min_temp = min(temps)
        min_hum = min(hums)
        max_temp = max(temps)
        max_hum = max(hums)
        avg_temp = sum(temps)/len(temps)
        avg_hum = sum(hums)/len(hums)

        self.calcs = [(min_temp, max_temp, avg_temp),
                      (min_hum, max_hum, avg_hum)]

    @Slot()
    def update(self):
        if self.calcs == []:
            return

        # (min, max, avg) of temp, humidity
        self.min_temp_label.setText(f'{self.calcs[0][0]:.2f}')
        self.max_temp_label.setText(f'{self.calcs[0][1]:.2f}')
        self.avg_temp_label.setText(f'{self.calcs[0][2]:.2f}')
        self.min_hum_label.setText(f'{self.calcs[1][0]:.2f}')
        self.max_hum_label.setText(f'{self.calcs[1][1]:.2f}')
        self.avg_hum_label.setText(f'{self.calcs[1][2]:.2f}')


def main():
    app = QApplication(sys.argv)

    window = Prj1()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
