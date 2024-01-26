import random


class PseudoSensor:

    h_range = [0, 20, 20, 40, 40, 60, 60, 80,
               80, 90, 70, 70, 50, 50, 30, 30, 10, 10]
    t_range = [-20, -10, 0, 10, 30, 50, 70, 80, 90, 80, 60, 40, 20, 10, 0, -10]
    h_range_index = 0
    t_range_index = 0

    def __init__(self):

        self.humVal = self.h_range[self.h_range_index]
        self.tempVal = self.t_range[self.t_range_index]

    def generate_values(self):
        """
        generate_values returns a tuple pair of temperature and humidity data

        Returns:
        Tuple[float, float]: humidity, temperature
        """
        self.humVal = self.h_range[self.h_range_index] + random.uniform(0, 10)
        self.tempVal = self.t_range[self.t_range_index] + random.uniform(0, 10)
        self.h_range_index += 1

        if self.h_range_index > len(self.h_range) - 1:
            self.h_range_index = 0

        self.t_range_index += 1

        if self.t_range_index > len(self.t_range) - 1:
            self.t_range_index = 0

        return self.humVal, self.tempVal


if __name__ == "__main__":
    sensor = PseudoSensor()

    for i in range(0, 10):
        hum, temp = sensor.generate_values()
        print(i, hum, temp)
