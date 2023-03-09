from adafruit_datetime import datetime
from adafruit_requests import Session
import board
import digitalio
import secrets
import socketpool
import rtc
import wifi

request = None

def connect_wifi():
    global request

    wifi.radio.connect(ssid=secrets.ssid, password=secrets.pwd, timeout=3)
    pool = socketpool.SocketPool(wifi.radio)
    request = Session(pool)
    print(f"wifi connected to \"{wifi.radio.ap_info.ssid}\" RSSI: {wifi.radio.ap_info.rssi}")

def sync_time():
    response = request.get("http://worldtimeapi.org/api/ip", timeout=5)

    if response.status_code != 200:
        print("sync failed, no response")
        return

    json = response.json()
    response.close()

    dt = datetime.fromtimestamp(json["unixtime"] + json["raw_offset"] + json["dst_offset"])
    time_src = rtc.RTC()
    time_src.datetime = dt.timetuple()
    rtc.set_time_source(time_src)
