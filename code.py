from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.il0398 import Adafruit_IL0398

import analogio
import adafruit_scd30
import alarm
import digitalio
import displayio
import busio
import board
import label
from math import fabs, sqrt
from microcontroller import watchdog
import net
from random import randint
import time
import sleep
from watchdog import WatchDogMode

interval = 150
significance = 0.01

watchdog.timeout = 5
watchdog.mode = WatchDogMode.RESET
watchdog.feed()

# create the spi device and pins we will need
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.IO14)
dc = digitalio.DigitalInOut(board.IO12)
rst = digitalio.DigitalInOut(board.IO6)  # can be None to not use this pin
busy = digitalio.DigitalInOut(board.IO5)  # can be None to not use this pin

# Ambient light
light = analogio.AnalogIn(board.AMB)

if light.value < 200: # if light is off skip this iteration
    sleep.go_to_sleep(interval)

# Charge level
chg = analogio.AnalogIn(board.IO1)
chgBoot = chg.value

# Power to Sensiron and Display
pwr = digitalio.DigitalInOut(board.IO21)
pwr.direction = digitalio.Direction.OUTPUT
pwr.value = True
time.sleep(0.2)

i2c = board.I2C()
scd30 = adafruit_scd30.SCD30(i2c)


print("Creating display")
display = Adafruit_IL0398(
    400,
    300,
    spi,
    cs_pin=cs,
    dc_pin=dc,
    sramcs_pin=None,
    rst_pin=rst,
    busy_pin=busy,
)

# display.rotation = 1

# display.fill(Adafruit_EPD.WHITE)
# display.display()
# display.pixel(10, 100, Adafruit_EPD.BLACK)

#  display.rect(0, 0, 280, 350, Adafruit_EPD.BLACK)
#  display.line(0, 0, display.width - 1, display.height - 1, Adafruit_EPD.BLACK)

def value_to_percent(boot, sense):
    avg = sqrt(boot * sense)
    var = fabs(boot - sense)
    value = avg - var
    MAX = 41850
    MIN = 34800

    return int((value - MIN) / (MAX - MIN) * 100)

def display_data(co2, temp, humidity, charge, now):
    # label.bg_image(display, "ui.bmp")

    display.fill(Adafruit_EPD.WHITE)
    display.display()

    offset = 60

    if alarm.sleep_memory[5] == 0:
        alarm.sleep_memory[5] = 1
        offset = offset * -1
    else:
        alarm.sleep_memory[5] = 0

    print(f"co2: {co2}; t: {temp}; humidity: {humidity}; {now.tm_hour}:{now.tm_min:02d}:{now.tm_sec:02d}; {charge}%")

    label.large(display, 120, 110 + offset, f"{co2}", Adafruit_EPD.BLACK, Adafruit_EPD.RED)
    label.large(display, 250, 110 - offset, f"{temp}C", Adafruit_EPD.BLACK, Adafruit_EPD.RED)
    label.large(display, 20, 110 - offset, f"{humidity}%", Adafruit_EPD.BLACK, Adafruit_EPD.RED)

    label.small(display, 24  + randint(-20, 20), 10, f"{charge[0]}%", Adafruit_EPD.BLACK, Adafruit_EPD.RED)
    label.small(display, 100, 10, f"{charge[1]}", Adafruit_EPD.RED, Adafruit_EPD.BLACK)
    label.small(display, 200, 10, f"{charge[2]}", Adafruit_EPD.BLACK, Adafruit_EPD.WHITE)
    label.small(display, 10 + randint(-20, 20), 270, f"{light.value}", Adafruit_EPD.RED, Adafruit_EPD.WHITE)
    label.small(display, 220 + randint(-20, 20), 270, f"{now.tm_hour}:{now.tm_min:02d}:{now.tm_sec:02d}", Adafruit_EPD.BLACK, Adafruit_EPD.RED)

    display.display()


def is_significant(a, b):
    if not a:
        return True

    return (fabs(a - b) / a) > significance

def settle_co2_sensor():
    val = 1.0;

    while True:
        time.sleep(2)

        if not scd30.data_available:
            continue

        nval = scd30.CO2
        diff = fabs(val - nval) / val
        print("co2 reading", nval, f"({diff:.2f})", chg.value, end="")

        if not is_significant(val, nval):
            print(" ready")
            break
        else:
            print(";")
            val = nval if nval > 0 else 1.0

# Time sync
rtc_hr = time.localtime().tm_hour
is_sync_hr = rtc_hr != alarm.sleep_memory[5]

if is_sync_hr: # sync once every hour
    try:
        watchdog.feed()
        net.connect_wifi()
        watchdog.feed()
        net.sync_time()
        watchdog.feed()
        alarm.sleep_memory[5] = rtc_hr
        print("Time synchronised")
    except:
        print("Could not connect to WiFi")
else:
    print("Time is still valid")

watchdog.deinit()

try:
    settle_co2_sensor()
except:
    print("Failed to settle the sensor")
    sleep.go_to_sleep()

chgSense = chg.value;

try:
    charge = (value_to_percent(chgBoot, chgSense), chgBoot, chgSense)
    co2 = int(scd30.CO2)
    temp = int(scd30.temperature)
    humidity = int(scd30.relative_humidity)
except:
    print("Failed to read values")
    sleep.go_to_sleep()

last_co2 = int.from_bytes(alarm.sleep_memory[0:2], "big")
last_temp = alarm.sleep_memory[3]
last_humidity = alarm.sleep_memory[4]

if (
    is_significant(last_co2, co2)
    or is_significant(last_temp, temp)
    or is_significant(last_humidity, humidity)
):
    co2_bytes = co2.to_bytes(2, "big")
    alarm.sleep_memory[0] = co2_bytes[0]
    alarm.sleep_memory[1] = co2_bytes[1]
    alarm.sleep_memory[3] = temp
    alarm.sleep_memory[4] = humidity
    display_data(co2, temp, humidity, charge, time.localtime())

sleep.go_to_sleep(interval)
