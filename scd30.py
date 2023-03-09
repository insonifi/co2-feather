import time
import board
import adafruit_scd30

class SCD30:
    def __init__(self):
        i2c = board.I2C()
        self.scd = adafruit_scd30.SCD30(i2c)

    def get_data(self):
        if self.scd.data_available:
            return (self.scd.CO2, self.scd.temperature, self.scd.relative_humidity)
        return None
